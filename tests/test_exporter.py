"""Tests for copilot_history_viewer.exporter."""

import json
from datetime import date, datetime
from pathlib import Path

from copilot_history_viewer.parser import parse_sessions, group_by_date
from copilot_history_viewer.exporter import export_by_date


def _make_session_file(tmp: Path, creation_ts: int, session_id: str) -> Path:
    header = {
        "kind": 0,
        "v": {
            "version": 3,
            "creationDate": creation_ts,
            "sessionId": session_id,
            "requests": [],
            "inputState": {},
        },
    }
    delta = {"kind": 1, "k": ["inputState", "inputText"], "v": "test"}
    path = tmp / f"{session_id}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(header) + "\n")
        f.write(json.dumps(delta) + "\n")
    return path


def test_export_creates_per_day_files(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out"

    ts1 = 1700000000000  # 2023-11-14
    ts2 = 1700100000000  # 2023-11-16

    _make_session_file(src, ts1, "s1")
    _make_session_file(src, ts2, "s2")

    sessions = parse_sessions(list(src.glob("*.jsonl")))
    groups = group_by_date(sessions)
    created = export_by_date(groups, out)

    assert len(created) == 2
    day1 = datetime.fromtimestamp(ts1 / 1000).date()
    day2 = datetime.fromtimestamp(ts2 / 1000).date()
    assert (out / f"{day1.isoformat()}.jsonl").exists()
    assert (out / f"{day2.isoformat()}.jsonl").exists()


def test_export_multiple_sessions_same_day(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out"

    ts_a = 1700000000000
    ts_b = 1700000060000  # same day, 1 min later

    _make_session_file(src, ts_a, "sa")
    _make_session_file(src, ts_b, "sb")

    sessions = parse_sessions(list(src.glob("*.jsonl")))
    groups = group_by_date(sessions)
    created = export_by_date(groups, out)

    assert len(created) == 1
    content = created[0].read_text(encoding="utf-8")
    # Both sessions should be in the file
    assert '"sa"' in content
    assert '"sb"' in content
    # They should be separated by a blank line
    assert "\n\n" in content


def test_export_preserves_raw_content(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out"

    ts = 1700000000000
    path = _make_session_file(src, ts, "raw")
    original = path.read_text(encoding="utf-8")

    sessions = parse_sessions([path])
    groups = group_by_date(sessions)
    export_by_date(groups, out)

    day = datetime.fromtimestamp(ts / 1000).date()
    exported = (out / f"{day.isoformat()}.jsonl").read_text(encoding="utf-8")
    assert exported == original


def test_exported_lines_are_valid_json(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out"

    _make_session_file(src, 1700000000000, "valid")

    sessions = parse_sessions(list(src.glob("*.jsonl")))
    groups = group_by_date(sessions)
    created = export_by_date(groups, out)

    for f in created:
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                json.loads(line)  # should not raise
