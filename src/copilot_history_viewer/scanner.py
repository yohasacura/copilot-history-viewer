"""Discover Copilot Chat session JSONL files from VS Code editions."""

import os
from pathlib import Path


EDITIONS = {
    "code": "Code",
    "insiders": "Code - Insiders",
}


def _appdata_base() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA environment variable is not set")
    return Path(appdata)


def _session_dirs(edition_folder: str) -> list[Path]:
    """Return the directories that may contain .jsonl session files for one edition."""
    base = _appdata_base() / edition_folder / "User"
    return [
        base / "workspaceStorage",   # contains {id}/chatSessions/*.jsonl
        base / "globalStorage" / "emptyWindowChatSessions",  # *.jsonl directly
    ]


def scan_sessions(editions: list[str] | None = None) -> list[Path]:
    """Return all .jsonl session file paths for the requested editions.

    Args:
        editions: List of edition keys ("code", "insiders"). None means all.

    Returns:
        Sorted list of paths to .jsonl files.
    """
    if editions is None:
        editions = list(EDITIONS.keys())

    paths: list[Path] = []

    for edition_key in editions:
        edition_folder = EDITIONS[edition_key]
        for session_dir in _session_dirs(edition_folder):
            if not session_dir.exists():
                continue

            if session_dir.name == "emptyWindowChatSessions":
                # JSONL files are directly in this folder
                paths.extend(session_dir.glob("*.jsonl"))
            else:
                # workspaceStorage: look inside each workspace subfolder
                paths.extend(session_dir.glob("*/chatSessions/*.jsonl"))

    return sorted(paths)
