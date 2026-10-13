#!/usr/bin/env python3
"""Detect actionable appVersion updates for the published Helm charts.

This is the single source of truth for the ``charts-checker`` scheduled task.
The task must run this script and must not improvise its own version discovery.

Design rules
------------
Registry-first
    The container registry is the only authoritative signal. An upstream
    release whose image has not been published yet is not actionable, so the
    script compares ``appVersion`` against the tags that actually exist in the
    registry the chart points at.
Published charts only
    A chart directory that is not tracked by git has never been released, so it
    is out of scope. Work in progress is not the checker's business.
Rolling tags stay rolling
    A chart whose ``appVersion`` is ``latest`` (or another rolling tag listed in
    ``chart-sources.yaml``) follows a moving tag on purpose. The checker reports
    it as ``rolling`` and never proposes pinning it to a concrete version.
No guessing
    The image reference is read from the chart's own ``values.yaml``. Nothing is
    inferred from the chart name.

Examples
--------
Human-readable report::

    python3 scripts/check-chart-updates.py

Machine-readable payload for the updater agent::

    python3 scripts/check-chart-updates.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    sys.exit("PyYAML is required: python3 -m pip install --user pyyaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
CHARTS_DIR = REPO_ROOT / "charts"
CONFIG_PATH = Path(__file__).resolve().parent / "chart-sources.yaml"

HTTP_TIMEOUT = 20
USER_AGENT = "obeone-charts-update-checker/1.0"

# GHCR returns tags in push order, not newest first, and caps a page at 1000
# entries. A repository that publishes a tag per commit (firecrawl) overflows
# that page, so the newest releases only appear on later pages.
GHCR_PAGE_SIZE = 1000
GHCR_MAX_PAGES = 30
LINK_NEXT_RE = re.compile(r'<([^>]+)>\s*;[^,]*rel="next"')

# Matches 1.2, 1.2.3, v1.2.3, 1.2.3.4 with an optional pre-release suffix.
VERSION_RE = re.compile(r"^v?(\d+(?:\.\d+){1,3})(?:[-_.]?([0-9a-z.]+))?$", re.I)


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #


@dataclass
class ChartReport:
    """Outcome of checking a single chart.

    Attributes
    ----------
    name : str
        Chart directory name.
    status : str
        One of ``update`` (a newer image tag exists), ``current`` (already on the
        newest tag), ``rolling`` (pinned to a moving tag on purpose), ``skipped``
        (not published or explicitly ignored) or ``error`` (check failed).
    chart_version : str
        Current ``version:`` from Chart.yaml.
    app_version : str
        Current ``appVersion:`` from Chart.yaml.
    latest_tag : str
        Newest usable tag found in the registry, formatted to match the style of
        the current ``appVersion``.
    image : str
        Image reference the chart deploys.
    changelog : str
        Release notes URL, when configured.
    notes : str
        Free-form warning from the config, when configured.
    reason : str
        Why the chart was skipped, or the error message.
    """

    name: str
    status: str
    chart_version: str = ""
    app_version: str = ""
    latest_tag: str = ""
    image: str = ""
    changelog: str = ""
    notes: str = ""
    reason: str = ""


@dataclass
class Config:
    """Parsed ``chart-sources.yaml``."""

    rolling_tags: set[str] = field(default_factory=set)
    prerelease_markers: tuple[str, ...] = ()
    ignore: dict[str, str] = field(default_factory=dict)
    charts: dict[str, dict[str, Any]] = field(default_factory=dict)


def load_config(path: Path) -> Config:
    """Load the checker configuration.

    Parameters
    ----------
    path : Path
        Location of ``chart-sources.yaml``.

    Returns
    -------
    Config
        Configuration with policy lists normalised to lowercase.
    """
    raw = yaml.safe_load(path.read_text()) or {}
    policy = raw.get("policy", {})
    return Config(
        rolling_tags={t.lower() for t in policy.get("rolling_tags", [])},
        prerelease_markers=tuple(m.lower() for m in policy.get("prerelease_markers", [])),
        ignore=raw.get("ignore", {}) or {},
        charts=raw.get("charts", {}) or {},
    )


# --------------------------------------------------------------------------- #
# Chart introspection
# --------------------------------------------------------------------------- #


def tracked_charts() -> set[str]:
    """Return the names of chart directories tracked by git.

    A chart is considered published once its ``Chart.yaml`` is committed, since
    the release workflow only ever packages committed charts.

    Returns
    -------
    set of str
        Chart directory names.
    """
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "charts/"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {
        line.split("/")[1]
        for line in out.splitlines()
        if line.endswith("/Chart.yaml") and line.count("/") == 2
    }


def read_chart_yaml(chart_dir: Path) -> tuple[str, str]:
    """Extract ``version`` and ``appVersion`` from a chart's Chart.yaml.

    Parameters
    ----------
    chart_dir : Path
        Chart directory.

    Returns
    -------
    tuple of (str, str)
        The chart version and the app version, both as plain strings.
    """
    data = yaml.safe_load((chart_dir / "Chart.yaml").read_text()) or {}
    return str(data.get("version", "")).strip(), str(data.get("appVersion", "")).strip()


def detect_image(chart_dir: Path) -> str:
    """Find the container image a chart deploys.

    Reads the first ``repository:`` key in ``values.yaml``. This works for both
    common-library lineages used in this repo: k8s-at-home puts it under
    ``image.repository`` and bjw-s under
    ``controllers.<name>.containers.<name>.image.repository``.

    Parameters
    ----------
    chart_dir : Path
        Chart directory.

    Returns
    -------
    str
        Image reference, or an empty string when it cannot be determined.
    """
    values = chart_dir / "values.yaml"
    if not values.exists():
        return ""
    for line in values.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        match = re.match(r"^repository:\s*(\S+)", stripped)
        if match:
            candidate = match.group(1).strip("\"'")
            # Skip Helm-templated values; those need a config override.
            if "{{" in candidate:
                continue
            return candidate
    return ""


def detect_image_tag(chart_dir: Path) -> str | None:
    """Find an explicitly pinned image tag in a chart's values.yaml.

    Both common-library lineages let ``tag`` fall back to ``.Chart.AppVersion``
    when it is left empty. When it is set instead, that value wins and
    ``appVersion`` becomes decorative, which is a silent trap: the chart can
    advertise a pinned version while the cluster keeps pulling a moving tag.

    Parameters
    ----------
    chart_dir : Path
        Chart directory.

    Returns
    -------
    str or None
        The first explicit tag found, or ``None`` when the tag is absent, empty
        or Helm-templated (both of which defer to ``appVersion``).
    """
    values = chart_dir / "values.yaml"
    if not values.exists():
        return None
    for line in values.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        match = re.match(r"^tag:\s*(.*)$", stripped)
        if match:
            candidate = match.group(1).strip().strip("\"'")
            if not candidate or "{{" in candidate:
                return None
            return candidate
    return None


# --------------------------------------------------------------------------- #
# Registry access
# --------------------------------------------------------------------------- #


def _get_json_response(url: str, headers: dict[str, str] | None = None) -> tuple[Any, Any]:
    """Fetch a URL and return the decoded JSON body together with its headers.

    Parameters
    ----------
    url : str
        Absolute URL to fetch.
    headers : dict of str to str, optional
        Extra request headers.

    Returns
    -------
    tuple
        Decoded JSON payload, and the response headers as a mapping with
        case-insensitive lookup.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
        return json.load(response), response.headers


def _get_json(url: str, headers: dict[str, str] | None = None) -> Any:
    """Fetch a URL and decode the JSON body.

    Parameters
    ----------
    url : str
        Absolute URL to fetch.
    headers : dict of str to str, optional
        Extra request headers.

    Returns
    -------
    Any
        Decoded JSON payload.
    """
    return _get_json_response(url, headers)[0]


def dockerhub_tags(image: str) -> list[str]:
    """List tags for a Docker Hub image.

    Parameters
    ----------
    image : str
        Image reference such as ``klutchell/dnscrypt-proxy``. A bare name is
        treated as an official image under the ``library`` namespace.

    Returns
    -------
    list of str
        Tag names, newest first as returned by the API.
    """
    repo = image if "/" in image else f"library/{image}"
    tags: list[str] = []
    url = f"https://hub.docker.com/v2/repositories/{repo}/tags?page_size=100&ordering=last_updated"
    # Three pages is plenty to reach the newest stable release on every chart here.
    for _ in range(3):
        payload = _get_json(url)
        tags.extend(item["name"] for item in payload.get("results", []))
        url = payload.get("next")
        if not url:
            break
    return tags


def ghcr_tags(image: str) -> list[str]:
    """List every tag of a GitHub Container Registry image.

    Uses the anonymous pull token flow, which works for public packages, and
    follows the ``Link: rel="next"`` pagination the registry advertises.

    Parameters
    ----------
    image : str
        Image reference including the ``ghcr.io/`` prefix.

    Returns
    -------
    list of str
        Tag names as reported by the registry, across every page.

    Raises
    ------
    ValueError
        If the repository still advertises a next page after
        ``GHCR_MAX_PAGES``. Truncating silently would hide the newest releases
        and report an outdated chart as current.
    """
    path = image.removeprefix("ghcr.io/")
    token = _get_json(f"https://ghcr.io/token?scope=repository:{path}:pull&service=ghcr.io")["token"]
    auth = {"Authorization": f"Bearer {token}"}
    url = f"https://ghcr.io/v2/{path}/tags/list?n={GHCR_PAGE_SIZE}"

    tags: list[str] = []
    for _ in range(GHCR_MAX_PAGES):
        payload, response_headers = _get_json_response(url, headers=auth)
        tags.extend(payload.get("tags") or [])
        match = LINK_NEXT_RE.search(response_headers.get("Link", "") or "")
        if not match:
            return tags
        # The registry sends a relative URL; resolve it against the current one.
        url = urllib.parse.urljoin(url, match.group(1))

    raise ValueError(
        f"more than {GHCR_MAX_PAGES * GHCR_PAGE_SIZE} tags on {image}; "
        "raise GHCR_MAX_PAGES, the newest tags are being missed"
    )


def registry_tags(image: str) -> list[str]:
    """List the tags that exist for an image, dispatching on its registry.

    Parameters
    ----------
    image : str
        Image reference.

    Returns
    -------
    list of str
        Tag names.

    Raises
    ------
    ValueError
        If the registry is not supported by this checker.
    """
    if image.startswith("ghcr.io/"):
        return ghcr_tags(image)
    host = image.split("/")[0]
    # A first segment containing a dot or a port is a registry host we do not handle.
    if "." in host or ":" in host:
        raise ValueError(f"unsupported registry: {host}")
    return dockerhub_tags(image)


# --------------------------------------------------------------------------- #
# Version handling
# --------------------------------------------------------------------------- #


def parse_version(tag: str, prerelease_markers: tuple[str, ...]) -> tuple[int, ...] | None:
    """Convert a tag into a comparable version tuple.

    Parameters
    ----------
    tag : str
        Registry tag or appVersion string.
    prerelease_markers : tuple of str
        Substrings that disqualify a tag as a stable release.

    Returns
    -------
    tuple of int or None
        Numeric components, or ``None`` when the tag is not a stable version.
    """
    match = VERSION_RE.match(tag.strip())
    if not match:
        return None
    numeric, suffix = match.group(1), match.group(2)
    if suffix and any(marker in suffix.lower() for marker in prerelease_markers):
        return None
    return tuple(int(part) for part in numeric.split("."))


def format_like(reference: str, version: str) -> str:
    """Render a version using the prefix style of an existing value.

    Keeps ``v1.2.3`` charts on ``v`` prefixes and bare charts bare.

    Parameters
    ----------
    reference : str
        Current appVersion, used only for its style.
    version : str
        Bare numeric version to render.

    Returns
    -------
    str
        Version formatted to match ``reference``.
    """
    return f"v{version}" if reference.lower().startswith("v") else version


# --------------------------------------------------------------------------- #
# Checking
# --------------------------------------------------------------------------- #


def check_chart(name: str, config: Config) -> ChartReport:
    """Check a single chart for an actionable update.

    Parameters
    ----------
    name : str
        Chart directory name.
    config : Config
        Checker configuration.

    Returns
    -------
    ChartReport
        Result for this chart.
    """
    overrides = config.charts.get(name, {}) or {}
    chart_dir = CHARTS_DIR / name
    changelog = overrides.get("changelog", "")
    notes = overrides.get("notes", "").strip()
    # Build variant deployed in place of the plain release, e.g. '-noroot'. When
    # set, the chart is expected to pin '<appVersion><tag_suffix>' and only tags
    # carrying that suffix are deployable.
    tag_suffix = str(overrides.get("tag_suffix", "") or "").strip()

    chart_version, app_version = read_chart_yaml(chart_dir)
    explicit_tag = detect_image_tag(chart_dir)
    app_is_rolling = app_version.lower() in config.rolling_tags

    # An explicit tag overrides appVersion at render time. If the two disagree,
    # appVersion is decorative and every conclusion drawn from it is wrong, so
    # refuse to judge the chart until a human reconciles them. A declared
    # tag_suffix makes the variant pin the expected value rather than a
    # contradiction, so only a genuine version mismatch still errors.
    expected_tag = f"{app_version}{tag_suffix}"
    if explicit_tag is not None and explicit_tag.lower() != expected_tag.lower():
        if tag_suffix:
            advice = (
                f"Expected the pin to be '{expected_tag}' for tag_suffix "
                f"'{tag_suffix}'. Reconcile them, or drop the tag_suffix override."
            )
        else:
            advice = "Reconcile them, or leave tag empty so it follows appVersion."
        return ChartReport(
            name=name,
            status="error",
            chart_version=chart_version,
            app_version=app_version,
            image=overrides.get("image") or detect_image(chart_dir),
            changelog=changelog,
            notes=notes,
            reason=(
                f"values.yaml pins 'tag: {explicit_tag}' while appVersion is "
                f"'{app_version}'. The deployed image is {explicit_tag}; appVersion "
                f"is ignored. {advice}"
            ),
        )

    if app_is_rolling:
        return ChartReport(
            name=name,
            status="rolling",
            chart_version=chart_version,
            app_version=app_version,
            reason=f"appVersion is the rolling tag '{app_version}'; leave it alone.",
        )

    image = overrides.get("image") or detect_image(chart_dir)
    if not image:
        return ChartReport(
            name=name,
            status="error",
            chart_version=chart_version,
            app_version=app_version,
            reason="Could not determine the image from values.yaml; add an 'image' override.",
        )

    try:
        tags = registry_tags(image)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError) as exc:
        return ChartReport(
            name=name,
            status="error",
            chart_version=chart_version,
            app_version=app_version,
            image=image,
            changelog=changelog,
            notes=notes,
            reason=f"Registry query failed: {exc}",
        )

    candidates: dict[tuple[int, ...], str] = {}
    for tag in tags:
        core = tag
        if tag_suffix:
            # Only the variant is deployable for this chart, so plain releases
            # are not candidates and the suffix comes off before parsing.
            if not tag.lower().endswith(tag_suffix.lower()):
                continue
            core = tag[: -len(tag_suffix)]
        parsed = parse_version(core, config.prerelease_markers)
        if parsed is not None:
            # Keep the shortest tag for a given version (1.2.3 over 1.2.3-alpine).
            existing = candidates.get(parsed)
            if existing is None or len(tag) < len(existing):
                candidates[parsed] = tag

    if not candidates:
        return ChartReport(
            name=name,
            status="error",
            chart_version=chart_version,
            app_version=app_version,
            image=image,
            changelog=changelog,
            notes=notes,
            reason=(
                f"No stable semver tag found among {len(tags)} registry tags"
                + (f" carrying the '{tag_suffix}' suffix." if tag_suffix else ".")
            ),
        )

    newest = max(candidates)
    newest_str = ".".join(str(part) for part in newest)
    current = parse_version(app_version, config.prerelease_markers)

    if current is None:
        return ChartReport(
            name=name,
            status="error",
            chart_version=chart_version,
            app_version=app_version,
            image=image,
            changelog=changelog,
            notes=notes,
            reason=f"Cannot parse current appVersion '{app_version}'.",
        )

    # Compare on equal length so 1.6 and 1.6.0 are the same version.
    width = max(len(current), len(newest))
    padded_current = current + (0,) * (width - len(current))
    padded_newest = newest + (0,) * (width - len(newest))

    if padded_newest <= padded_current:
        return ChartReport(
            name=name,
            status="current",
            chart_version=chart_version,
            app_version=app_version,
            latest_tag=candidates[newest],
            image=image,
            changelog=changelog,
            notes=notes,
        )

    reason = f"Registry tag '{candidates[newest]}' exists and is newer."
    if explicit_tag is not None:
        # Bumping appVersion alone would change nothing: the pinned tag renders.
        reason += (
            f" values.yaml pins an explicit tag, so set every occurrence to "
            f"'{candidates[newest]}' in the same commit."
        )

    return ChartReport(
        name=name,
        status="update",
        chart_version=chart_version,
        app_version=app_version,
        latest_tag=format_like(app_version, newest_str),
        image=image,
        changelog=changelog,
        notes=notes,
        reason=reason,
    )


def run(only: list[str] | None = None) -> list[ChartReport]:
    """Check every monitored chart.

    Parameters
    ----------
    only : list of str, optional
        Restrict the run to these chart names.

    Returns
    -------
    list of ChartReport
        One report per chart, sorted by name.
    """
    config = load_config(CONFIG_PATH)
    published = tracked_charts()
    reports: list[ChartReport] = []

    for chart_dir in sorted(CHARTS_DIR.iterdir()):
        if not chart_dir.is_dir():
            continue
        name = chart_dir.name
        if only and name not in only:
            continue

        if name in config.ignore:
            reports.append(
                ChartReport(name=name, status="skipped", reason=config.ignore[name])
            )
            continue
        if not (chart_dir / "Chart.yaml").exists():
            reports.append(
                ChartReport(name=name, status="skipped", reason="No Chart.yaml.")
            )
            continue
        if name not in published:
            reports.append(
                ChartReport(
                    name=name,
                    status="skipped",
                    reason="Not tracked by git, so never published. Out of scope.",
                )
            )
            continue

        reports.append(check_chart(name, config))

    return reports


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def print_table(reports: list[ChartReport]) -> None:
    """Print a human-readable report grouped by status.

    Parameters
    ----------
    reports : list of ChartReport
        Reports to render.
    """
    updates = [r for r in reports if r.status == "update"]
    errors = [r for r in reports if r.status == "error"]

    print("=" * 78)
    print("ACTIONABLE UPDATES (image tag confirmed present in the registry)")
    print("=" * 78)
    if updates:
        for r in updates:
            print(f"\n  {r.name}")
            print(f"    appVersion   {r.app_version}  ->  {r.latest_tag}")
            print(f"    chart        {r.chart_version}  (must be bumped too)")
            print(f"    image        {r.image}:{r.latest_tag}")
            if r.changelog:
                print(f"    changelog    {r.changelog}")
            if r.notes:
                print(f"    note         {r.notes}")
    else:
        print("\n  None. Every published chart is on the newest published image tag.")

    if errors:
        print("\n" + "=" * 78)
        print("NEEDS A HUMAN")
        print("=" * 78)
        for r in errors:
            print(f"  {r.name:24} {r.reason}")

    print("\n" + "=" * 78)
    print("NOT ACTIONABLE")
    print("=" * 78)
    for r in reports:
        if r.status == "current":
            print(f"  up to date  {r.name:24} {r.app_version}")
        elif r.status == "rolling":
            print(f"  rolling     {r.name:24} {r.app_version}")
        elif r.status == "skipped":
            print(f"  skipped     {r.name:24} {r.reason}")


def main() -> int:
    """Entry point.

    Returns
    -------
    int
        ``0`` when the run completed, ``1`` when a chart check errored.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="emit the machine-readable payload")
    parser.add_argument("--chart", action="append", help="restrict to a chart (repeatable)")
    args = parser.parse_args()

    reports = run(only=args.chart)

    if args.json:
        payload = {
            "updates": [asdict(r) for r in reports if r.status == "update"],
            "errors": [asdict(r) for r in reports if r.status == "error"],
            "not_actionable": [asdict(r) for r in reports if r.status in {"current", "rolling", "skipped"}],
        }
        print(json.dumps(payload, indent=2))
    else:
        print_table(reports)

    return 1 if any(r.status == "error" for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
