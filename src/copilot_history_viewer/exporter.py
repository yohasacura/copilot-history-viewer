"""Export chat sessions as raw JSONL files grouped by date."""

from datetime import date
from pathlib import Path

from copilot_history_viewer.parser import SessionInfo


def export_by_date(
    groups: dict[date, list[SessionInfo]],
    output_dir: Path,
) -> list[Path]:
    """Write one JSONL file per date containing all raw session data for that day.

    Each output file is named YYYY-MM-DD.jsonl and contains the raw lines from
    all sessions created on that date. Sessions within the same day are separated
    by an empty line for readability.

    Args:
        groups: Sessions grouped by date (from parser.group_by_date).
        output_dir: Directory to write output files into.

    Returns:
        Sorted list of created file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    for day, sessions in sorted(groups.items()):
        out_path = output_dir / f"{day.isoformat()}.jsonl"

        with open(out_path, "w", encoding="utf-8") as out_f:
            for i, session in enumerate(sessions):
                if i > 0:
                    out_f.write("\n")  # blank line between sessions

                with open(session.path, "r", encoding="utf-8") as src_f:
                    for line in src_f:
                        out_f.write(line)

                # ensure file ends with newline
                if not line.endswith("\n"):
                    out_f.write("\n")

        created.append(out_path)

    return sorted(created)
