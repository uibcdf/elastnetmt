"""Generate and validate the developer-guide lifecycle indexes offline."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from devguide_reports import CLOSED_STATUSES, OPEN_STATUSES, ROOT, Report, validate_all

BEGIN = "<!-- generated: devguide_index -->"
END = "<!-- /generated -->"
INDEXES = {
    "bug": ROOT / "devguide/pending_bugs/README.md",
    "proposal": ROOT / "devguide/pending_proposals/README.md",
    "archive": ROOT / "devguide/archive/README.md",
}


def _issue_link(reference: str) -> str:
    repository, number = reference.rsplit("#", 1)
    return f"[#{number}](https://github.com/{repository}/issues/{number})"


def _line(report: Report, base: Path) -> str:
    fields = report.fields
    relative = Path(os.path.relpath(report.path, base)).as_posix()
    return (
        f"- [`{report.path.name}`]({relative}) — "
        f"{_issue_link(str(fields['issue']))} — {fields['summary']} "
        f"*({fields['status']}, {fields['verification']})*"
    )


def _render(reports: list[Report], kind: str, base: Path) -> str:
    archived = kind == "archive"
    selected = [
        report
        for report in reports
        if report.archived == archived and (archived or report.kind == kind)
    ]
    statuses = CLOSED_STATUSES if archived else OPEN_STATUSES
    lines: list[str] = []
    for status in statuses:
        group = sorted(
            (report for report in selected if report.fields["status"] == status),
            key=lambda report: report.path.name,
        )
        if group:
            lines.extend((f"### {status.title()} ({len(group)})", ""))
            lines.extend(_line(report, base) for report in group)
            lines.append("")
    return "\n".join(lines).rstrip() or "*No entries.*"


def _replace(text: str, body: str) -> str:
    if BEGIN not in text or END not in text:
        raise ValueError("generated index markers are missing")
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{BEGIN}\n\n{body}\n\n{END}{tail}"


def process(check: bool) -> list[str]:
    reports, errors = validate_all()
    if errors:
        raise ValueError("\n".join(errors))
    stale: list[str] = []
    for kind, readme in INDEXES.items():
        expected = _replace(
            readme.read_text(encoding="utf-8"), _render(reports, kind, readme.parent)
        )
        if expected == readme.read_text(encoding="utf-8"):
            continue
        stale.append(readme.relative_to(ROOT).as_posix())
        if not check:
            readme.write_text(expected, encoding="utf-8")
    return stale


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    try:
        stale = process(arguments.check)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    if arguments.check and stale:
        print("stale generated indexes: " + ", ".join(stale), file=sys.stderr)
        return 1
    for path in stale:
        print(f"wrote {path}")
    if arguments.check:
        print("Generated report indexes are current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
