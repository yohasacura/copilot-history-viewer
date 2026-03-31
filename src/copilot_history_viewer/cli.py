"""CLI entry point for the chat history manager."""

import argparse
import sys
from datetime import date
from pathlib import Path

from copilot_history_viewer.scanner import EDITIONS, scan_sessions
from copilot_history_viewer.parser import parse_sessions, group_by_date
from copilot_history_viewer.exporter import export_by_date


def _parse_date(s: str) -> date:
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date: {s!r}. Use YYYY-MM-DD format.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="copilot-history-viewer",
        description="Manage and export GitHub Copilot Chat history from VS Code.",
    )
    p.add_argument(
        "--from", dest="date_from", type=_parse_date, default=None,
        help="Start date (inclusive, YYYY-MM-DD)",
    )
    p.add_argument(
        "--to", dest="date_to", type=_parse_date, default=None,
        help="End date (inclusive, YYYY-MM-DD)",
    )
    p.add_argument(
        "-o", "--output", type=Path, default=Path("./export"),
        help="Output directory (default: ./export)",
    )
    p.add_argument(
        "--list", dest="list_only", action="store_true",
        help="List sessions with dates instead of exporting",
    )
    p.add_argument(
        "--edition", choices=["code", "insiders", "all"], default="all",
        help="VS Code edition to scan (default: all)",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    # Determine editions to scan
    editions = list(EDITIONS.keys()) if args.edition == "all" else [args.edition]

    # Scan for session files
    paths = scan_sessions(editions)
    if not paths:
        print("No chat session files found.")
        sys.exit(0)

    # Parse sessions
    sessions = parse_sessions(paths)
    if not sessions:
        print(f"Found {len(paths)} files but none could be parsed.")
        sys.exit(1)

    # Filter by date range
    if args.date_from:
        sessions = [s for s in sessions if s.creation_date >= args.date_from]
    if args.date_to:
        sessions = [s for s in sessions if s.creation_date <= args.date_to]

    if not sessions:
        print("No sessions match the specified date range.")
        sys.exit(0)

    # List mode
    if args.list_only:
        multi_day = [s for s in sessions if s.is_multi_day]
        print(f"Found {len(sessions)} session(s)")
        if multi_day:
            print(f"  ({len(multi_day)} session(s) span multiple days)")
        print()
        for s in sessions:
            edition = "insiders" if "Code - Insiders" in str(s.path) else "code"
            line = f"  {s.creation_date}  [{edition:>9}]  {s.session_id}  ({s.request_count} requests)"
            if s.is_multi_day:
                days_str = ", ".join(str(d) for d in s.activity_dates)
                line += f"  active: [{days_str}]"
            print(line)
        return

    # Export mode
    groups = group_by_date(sessions)
    created = export_by_date(groups, args.output)

    total_sessions = sum(len(v) for v in groups.values())
    print(f"Exported {total_sessions} session(s) across {len(created)} day(s) to {args.output}/")
    for p in created:
        day_sessions = groups[date.fromisoformat(p.stem)]
        print(f"  {p.name}  ({len(day_sessions)} session(s))")
