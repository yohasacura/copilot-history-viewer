"""Tests for copilot_history_viewer.parser."""

import json
import tempfile
from datetime import date, datetime
from pathlib import Path

from copilot_history_viewer.parser import parse_session, parse_sessions, group_by_date


def _make_session_file(tmp: Path, creation_ts: int, session_id: str = "test-session", requests: list | None = None, kind2_requests: list | None = None) -> Path:
    """Create a minimal JSONL session file."""
    header = {
        "kind": 0,
        "v": {
            "version": 3,
            "creationDate": creation_ts,
            "sessionId": session_id,
            "requests": requests or [],
            "inputState": {},
        },
    }
    delta = {"kind": 1, "k": ["inputState", "inputText"], "v": "hello"}

    path = tmp / f"{session_id}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(header) + "\n")
        f.write(json.dumps(delta) + "\n")
        if kind2_requests:
            kind2 = {"kind": 2, "k": ["requests"], "v": kind2_requests}
            f.write(json.dumps(kind2) + "\n")
    return path


def test_parse_session_basic(tmp_path):
    ts = 1700000000000  # 2023-11-14
    path = _make_session_file(tmp_path, ts, "sess-1")

    info = parse_session(path)
    assert info is not None
    assert info.session_id == "sess-1"
    assert info.creation_timestamp == ts
    assert info.creation_date == datetime.fromtimestamp(ts / 1000).date()
    assert info.request_count == 0
    assert info.activity_dates == [datetime.fromtimestamp(ts / 1000).date()]
    assert not info.is_multi_day


def test_parse_session_with_requests(tmp_path):
    ts = 1700000000000
    requests = [{"requestId": "r1", "timestamp": ts + 1000}, {"requestId": "r2", "timestamp": ts + 2000}]
    path = _make_session_file(tmp_path, ts, "sess-2", requests=requests)

    info = parse_session(path)
    assert info is not None
    assert info.request_count == 2


def test_parse_session_empty_file(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("")
    assert parse_session(path) is None


def test_parse_session_invalid_json(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text("not json at all\n")
    assert parse_session(path) is None


def test_parse_session_wrong_kind(tmp_path):
    path = tmp_path / "wrong.jsonl"
    path.write_text(json.dumps({"kind": 1, "k": ["x"], "v": "y"}) + "\n")
    assert parse_session(path) is None


def test_parse_sessions_sorts_by_date(tmp_path):
    ts1 = 1700000000000  # earlier
    ts2 = 1700100000000  # later
    _make_session_file(tmp_path, ts2, "later")
    _make_session_file(tmp_path, ts1, "earlier")

    paths = list(tmp_path.glob("*.jsonl"))
    sessions = parse_sessions(paths)

    assert len(sessions) == 2
    assert sessions[0].session_id == "earlier"
    assert sessions[1].session_id == "later"


def test_group_by_date(tmp_path):
    # Two sessions on same day, one on a different day
    ts_day1_a = 1700000000000  # 2023-11-14
    ts_day1_b = 1700000060000  # 2023-11-14 (1 min later)
    ts_day2 = 1700100000000    # 2023-11-16

    _make_session_file(tmp_path, ts_day1_a, "d1a")
    _make_session_file(tmp_path, ts_day1_b, "d1b")
    _make_session_file(tmp_path, ts_day2, "d2")

    sessions = parse_sessions(list(tmp_path.glob("*.jsonl")))
    groups = group_by_date(sessions)

    assert len(groups) == 2
    day1 = datetime.fromtimestamp(ts_day1_a / 1000).date()
    day2 = datetime.fromtimestamp(ts_day2 / 1000).date()
    assert len(groups[day1]) == 2
    assert len(groups[day2]) == 1


def test_multi_day_activity(tmp_path):
    """A session created on day 1 with requests on day 2 should report both activity dates."""
    day1_ts = 1700000000000  # 2023-11-14
    day2_ts = day1_ts + 86400 * 1000  # +1 day
    day3_ts = day1_ts + 2 * 86400 * 1000  # +2 days

    kind2_reqs = [
        {"requestId": "r1", "timestamp": day2_ts},
        {"requestId": "r2", "timestamp": day3_ts},
    ]
    path = _make_session_file(tmp_path, day1_ts, "multi", kind2_requests=kind2_reqs)

    info = parse_session(path)
    assert info is not None
    assert info.is_multi_day
    assert len(info.activity_dates) == 3
    assert info.activity_dates[0] == datetime.fromtimestamp(day1_ts / 1000).date()
    assert info.activity_dates[1] == datetime.fromtimestamp(day2_ts / 1000).date()
    assert info.activity_dates[2] == datetime.fromtimestamp(day3_ts / 1000).date()
    assert info.request_count == 2  # only kind:2 requests counted


def test_single_day_activity(tmp_path):
    """A session with requests on the same day is not multi-day."""
    ts = 1700000000000
    kind2_reqs = [{"requestId": "r1", "timestamp": ts + 1000}]
    path = _make_session_file(tmp_path, ts, "single", kind2_requests=kind2_reqs)

    info = parse_session(path)
    assert info is not None
    assert not info.is_multi_day
    assert info.activity_dates == [datetime.fromtimestamp(ts / 1000).date()]
