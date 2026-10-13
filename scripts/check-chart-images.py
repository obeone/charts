#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Verify that every container image a published chart renders actually exists.

Companion to ``check-chart-updates.py``. The update checker only follows the
single image declared in ``chart-sources.yaml``; a chart usually renders more
than that (init containers, sidecars, exporters, bundled dependencies). This
script renders the chart and resolves every image reference it finds against
its registry, so a bump is never committed on top of a broken manifest.

Design rules
------------
Render, never guess
    Image references are read from the rendered manifests, not from
    ``values.yaml``: the latter holds unresolved ``{{ .Chart.AppVersion }}``
    templates and empty tags.
Optional components count
    Blocks disabled by default are force-enabled for the render so their images
    are checked too. If forcing breaks the render, the nominal render is used
    and the report says so.
Published charts only
    Without explicit chart names, only charts tracked by git are checked.

Examples
--------
Check every published chart::

    python3 scripts/check-chart-images.py

Check one chart and assert the bumped tag actually landed::

    python3 scripts/check-chart-images.py firecrawl --expect-tag 2.11.125 --json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    sys.exit("PyYAML is required: python3 -m pip install --user pyyaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
CHARTS_DIR = REPO_ROOT / "charts"

CRANE_TIMEOUT = 60
HELM_TIMEOUT = 120
CONTAINER_KEYS = ("containers", "initContainers", "ephemeralContainers")
MISSING_MARKERS = ("MANIFEST_UNKNOWN", "NAME_UNKNOWN", "not found", "404")
AUTH_MARKERS = ("UNAUTHORIZED", "denied", "authentication required")


@dataclass
class ImageCheck:
    """Result of resolving a single image reference against its registry."""

    reference: str
    status: str  # ok | missing | auth | error | platform-missing
    detail: str = ""
    sources: list[str] = field(default_factory=list)


@dataclass
class ChartReport:
    """Per-chart outcome, JSON-serialisable for the updater agent."""

    chart: str
    images: list[ImageCheck] = field(default_factory=list)
    forced_toggles: bool = False
    expect_tag: str | None = None
    expect_tag_found: bool | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        healthy = all(image.status == "ok" for image in self.images)
        landed = self.expect_tag_found is not False
        return healthy and landed and not self.errors


def run(command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    """Run a command, capturing both streams as text."""
    return subprocess.run(
        command, capture_output=True, text=True, timeout=timeout, check=False
    )


def tracked_charts() -> list[str]:
    """Return the chart names tracked by git, i.e. the published ones."""
    result = run(["git", "-C", str(REPO_ROOT), "ls-files", "charts"], timeout=30)
    if result.returncode != 0:
        sys.exit(f"git ls-files failed: {result.stderr.strip()}")
    names = {line.split("/")[1] for line in result.stdout.splitlines() if "/" in line}
    return sorted(n for n in names if (CHARTS_DIR / n / "Chart.yaml").is_file())


def escape_key(key: str) -> str:
    """Escape dots so helm --set does not read them as path separators."""
    return str(key).replace(".", r"\.")


def disabled_paths(node: Any, prefix: str = "") -> Iterator[str]:
    """Yield helm paths of every mapping holding ``enabled: false``."""
    if isinstance(node, dict):
        if node.get("enabled") is False and prefix:
            yield prefix
        for key, value in node.items():
            child = f"{prefix}.{escape_key(key)}" if prefix else escape_key(key)
            yield from disabled_paths(value, child)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from disabled_paths(value, f"{prefix}[{index}]")


def force_enable_flags(chart_dir: Path) -> list[str]:
    """Build the --set flags that switch every disabled block back on."""
    values_path = chart_dir / "values.yaml"
    if not values_path.is_file():
        return []
    try:
        values = yaml.safe_load(values_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    flags: list[str] = []
    for path in disabled_paths(values):
        flags += ["--set", f"{path}.enabled=true"]
    return flags


def render_chart(chart_dir: Path) -> tuple[str, bool, list[str], list[str]]:
    """Render a chart, force-enabling optional blocks when that still works."""
    errors: list[str] = []
    warnings: list[str] = []
    base = ["helm", "template", "release-check", str(chart_dir)]
    flags = force_enable_flags(chart_dir)
    if flags:
        forced = run(base + flags, timeout=HELM_TIMEOUT)
        if forced.returncode == 0:
            return forced.stdout, True, errors, warnings
        warnings.append(
            "force-enabling optional blocks broke the render, "
            "optional components were not checked"
        )
    nominal = run(base, timeout=HELM_TIMEOUT)
    if nominal.returncode != 0:
        errors.append(f"helm template failed: {nominal.stderr.strip().splitlines()[-1]}")
        return "", False, errors, warnings
    return nominal.stdout, False, errors, warnings


def walk_images(node: Any, kind: str = "?") -> Iterator[tuple[str, str]]:
    """Yield (reference, context) for every image found in a manifest tree."""
    if isinstance(node, dict):
        kind = node.get("kind", kind) if isinstance(node.get("kind"), str) else kind
        for key in CONTAINER_KEYS:
            entries = node.get(key)
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, dict) and isinstance(entry.get("image"), str):
                        name = entry.get("name", "?")
                        yield entry["image"], f"{kind}/{key}/{name}"
        if isinstance(node.get("image"), str) and "name" not in node:
            yield node["image"], f"{kind}/image"
        for value in node.values():
            yield from walk_images(value, kind)
    elif isinstance(node, list):
        for value in node:
            yield from walk_images(value, kind)


def collect_images(rendered: str) -> dict[str, list[str]]:
    """Group every rendered image reference with the places it comes from."""
    images: dict[str, list[str]] = {}
    for document in yaml.safe_load_all(rendered):
        if not document:
            continue
        for reference, context in walk_images(document):
            images.setdefault(reference, [])
            if context not in images[reference]:
                images[reference].append(context)
    return images


def classify(stderr: str) -> tuple[str, str]:
    """Turn a crane failure into a status plus a short reason."""
    haystack = stderr.lower()
    if any(marker.lower() in haystack for marker in MISSING_MARKERS):
        return "missing", "tag or repository absent from the registry"
    if any(marker.lower() in haystack for marker in AUTH_MARKERS):
        return "auth", "registry refused anonymous access"
    return "error", stderr.strip().splitlines()[-1] if stderr.strip() else "unknown"


def platform_available(manifest: str, wanted: str) -> bool | None:
    """Tell whether a manifest index advertises the wanted os/arch."""
    try:
        payload = json.loads(manifest)
    except json.JSONDecodeError:
        return None
    entries = payload.get("manifests")
    if not isinstance(entries, list):
        return None  # single-architecture image, nothing to compare
    for entry in entries:
        platform = entry.get("platform", {})
        pair = f"{platform.get('os')}/{platform.get('architecture')}"
        if pair == wanted:
            return True
    return False


def check_image(reference: str, sources: list[str], platform: str | None) -> ImageCheck:
    """Resolve one image reference against its registry."""
    try:
        result = run(["crane", "manifest", reference], timeout=CRANE_TIMEOUT)
    except subprocess.TimeoutExpired:
        return ImageCheck(reference, "error", "crane timed out", sources)
    if result.returncode != 0:
        status, detail = classify(result.stderr)
        return ImageCheck(reference, status, detail, sources)
    if platform:
        available = platform_available(result.stdout, platform)
        if available is False:
            return ImageCheck(
                reference, "platform-missing", f"no {platform} variant", sources
            )
    return ImageCheck(reference, "ok", "", sources)


def check_chart(name: str, platform: str | None, expect_tag: str | None) -> ChartReport:
    """Render one chart and check every image it produces."""
    chart_dir = CHARTS_DIR / name
    report = ChartReport(chart=name, expect_tag=expect_tag)
    if not (chart_dir / "Chart.yaml").is_file():
        report.errors.append("no Chart.yaml, not a chart directory")
        return report
    rendered, forced, errors, warnings = render_chart(chart_dir)
    report.forced_toggles = forced
    report.errors += errors
    report.warnings += warnings
    if not rendered:
        return report
    try:
        images = collect_images(rendered)
    except yaml.YAMLError as error:
        report.errors.append(f"rendered manifests are not valid YAML: {error}")
        return report
    if not images:
        report.errors.append("render produced no image reference")
        return report
    with ThreadPoolExecutor(max_workers=8) as pool:
        report.images = sorted(
            pool.map(
                lambda item: check_image(item[0], item[1], platform), images.items()
            ),
            key=lambda check: check.reference,
        )
    if expect_tag:
        report.expect_tag_found = any(
            reference.split("@")[0].endswith(f":{expect_tag}") for reference in images
        )
    return report


def print_report(reports: list[ChartReport]) -> None:
    """Print a human-readable summary."""
    symbols = {"ok": "OK  ", "missing": "FAIL", "auth": "AUTH", "error": "ERR ",
               "platform-missing": "PLAT"}
    for report in reports:
        flag = "ok" if report.ok else "PROBLEM"
        print(f"\n== {report.chart} [{flag}]")
        if report.forced_toggles:
            print("   optional blocks force-enabled for the render")
        for image in report.images:
            suffix = f" ({image.detail})" if image.detail else ""
            print(f"   {symbols.get(image.status, '?')} {image.reference}{suffix}")
            for source in image.sources:
                print(f"        <- {source}")
        if report.expect_tag is not None:
            landed = "yes" if report.expect_tag_found else "NO"
            print(f"   expected tag {report.expect_tag} rendered: {landed}")
        for warning in report.warnings:
            print(f"   ~~ {warning}")
        for error in report.errors:
            print(f"   !! {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("charts", nargs="*", help="chart names, default: all tracked")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--platform", help="require an os/arch variant, e.g. linux/amd64")
    parser.add_argument("--expect-tag", help="assert this tag is rendered by the chart")
    args = parser.parse_args()

    for binary in ("helm", "crane", "git"):
        if run(["command", "-v", binary], timeout=10).returncode != 0 and not any(
            (Path(directory) / binary).exists()
            for directory in __import__("os").environ.get("PATH", "").split(":")
        ):
            sys.exit(f"{binary} is required and was not found in PATH")

    names = args.charts or tracked_charts()
    if args.expect_tag and len(names) != 1:
        sys.exit("--expect-tag only makes sense with exactly one chart")

    reports = [check_chart(name, args.platform, args.expect_tag) for name in names]

    if args.json:
        payload = {
            "charts": [asdict(report) for report in reports],
            "failed": [report.chart for report in reports if not report.ok],
        }
        print(json.dumps(payload, indent=2))
    else:
        print_report(reports)
        broken = [report.chart for report in reports if not report.ok]
        print(f"\n{len(reports)} chart(s) checked, {len(broken)} with problems")
        if broken:
            print("problems: " + ", ".join(broken))

    return 1 if any(not report.ok for report in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
