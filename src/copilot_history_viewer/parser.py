"""Parse Copilot Chat JSONL session files and extract metadata."""

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass
class SessionInfo:
    """Metadata about a single chat session file."""
    path: Path
    session_id: str
    creation_date: date
    creation_timestamp: int  # epoch ms
    request_count: int
    activity_dates: list[date]  # all dates the session had requests on

    @property
    def creation_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.creation_timestamp / 1000)

    @property
    def is_multi_day(self) -> bool:
        return len(self.activity_dates) > 1


def parse_session(path: Path) -> SessionInfo | None:
    """Parse a JSONL session file and extract metadata from the kind:0 header line.

    Returns None if the file is empty or the header can't be parsed.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if not first_line:
                return None

            header = json.loads(first_line)

            if header.get("kind") != 0:
                return None

            v = header.get("v", {})
            creation_ts = v.get("creationDate", 0)
            session_id = v.get("sessionId", path.stem)
            requests = v.get("requests", [])

            creation_dt = datetime.fromtimestamp(creation_ts / 1000)

            # Collect all dates with request activity from kind:2 lines
            activity_set: set[date] = {creation_dt.date()}
            request_count = len(requests)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("kind") == 2:
                    for req in obj.get("v", []):
                        ts = req.get("timestamp")
                        if ts:
                            activity_set.add(datetime.fromtimestamp(ts / 1000).date())
                            request_count += 1

            return SessionInfo(
                path=path,
                session_id=session_id,
                creation_date=creation_dt.date(),
                creation_timestamp=creation_ts,
                request_count=request_count,
                activity_dates=sorted(activity_set),
            )
    except (json.JSONDecodeError, OSError, ValueError, KeyError):
        return None


def parse_sessions(paths: list[Path]) -> list[SessionInfo]:
    """Parse multiple session files, skipping unparseable ones.

    Returns sessions sorted by creation date (oldest first).
    """
    sessions = []
    for p in paths:
        info = parse_session(p)
        if info is not None:
            sessions.append(info)
    return sorted(sessions, key=lambda s: s.creation_timestamp)


def group_by_date(sessions: list[SessionInfo]) -> dict[date, list[SessionInfo]]:
    """Group sessions by their creation date."""
    groups: dict[date, list[SessionInfo]] = {}
    for s in sessions:
        groups.setdefault(s.creation_date, []).append(s)
    return groups
