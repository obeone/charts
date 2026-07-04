#!/usr/bin/env python3
"""Keep the root README chart table in sync with each chart's ``appVersion``.

The root ``README.md`` carries a hand-written table whose ``App`` column shows
the upstream application version of every chart. That value is the
``appVersion`` field of the chart's ``Chart.yaml``; nothing keeps the two in
sync, so the column drifts every time a chart is bumped.

This script reads ``appVersion`` from each ``charts/*/Chart.yaml`` and rewrites
the matching table row in ``README.md`` in place. It is meant to run as a
pre-commit hook: when it changes the file it exits non-zero, which aborts the
commit so the refreshed ``README.md`` can be re-staged (the same convention
helm-docs and most formatting hooks follow).

Only the ``App`` cell is touched; the emoji, the chart link and the description
are left byte-for-byte untouched.
"""
from __future__ import annotations

import pathlib
import re
import sys

# Repository layout: this file lives in <root>/scripts/.
ROOT = pathlib.Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
CHARTS_DIR = ROOT / "charts"

# Matches the chart link in the second column, e.g. "(charts/cyberchef)".
CHART_LINK_RE = re.compile(r"\(charts/([^)/]+)\)")


def chart_app_version(chart_dir: pathlib.Path) -> str | None:
    """Return the ``appVersion`` declared in a chart's ``Chart.yaml``.

    Parameters
    ----------
    chart_dir : pathlib.Path
        Path to a single chart directory (``charts/<name>``).

    Returns
    -------
    str or None
        The unquoted ``appVersion`` string, or ``None`` when the chart has no
        ``Chart.yaml`` or no top-level ``appVersion`` field.
    """
    chart_file = chart_dir / "Chart.yaml"
    if not chart_file.is_file():
        return None
    for line in chart_file.read_text(encoding="utf-8").splitlines():
        # Top-level key only: it starts at column 0, dependency versions are indented.
        if line.startswith("appVersion:"):
            value = line.split(":", 1)[1].strip()
            # Drop surrounding quotes helm allows around the value.
            return value.strip('"').strip("'")
    return None


def main() -> int:
    """Rewrite the root README table; return 1 if it changed, else 0."""
    # Collect appVersion for every chart that declares one.
    versions: dict[str, str] = {}
    for chart_dir in sorted(CHARTS_DIR.iterdir()):
        if not chart_dir.is_dir():
            continue
        app_version = chart_app_version(chart_dir)
        if app_version:
            versions[chart_dir.name] = app_version

    lines = README.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False

    for index, line in enumerate(lines):
        # Only consider Markdown table rows.
        if not line.lstrip().startswith("|"):
            continue
        match = CHART_LINK_RE.search(line)
        if not match:
            continue
        name = match.group(1)
        if name not in versions:
            continue

        # Table row cells: ['', ' emoji ', ' [link] ', ' `ver` ', ' desc ', '\n'].
        # The App column is cell index 3; descriptions never contain a pipe.
        cells = line.split("|")
        if len(cells) < 4:
            continue
        wanted = f" `{versions[name]}` "
        if cells[3] != wanted:
            cells[3] = wanted
            lines[index] = "|".join(cells)
            changed = True

    if changed:
        README.write_text("".join(lines), encoding="utf-8")
        print("README.md: App-version column synced from Chart.yaml appVersions")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
