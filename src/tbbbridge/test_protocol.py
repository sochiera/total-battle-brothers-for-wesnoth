"""Tests for the tbbbridge JSON-line protocol (G66.1a).

Tests live next to the module under test per task-319 \"Ścieżki testów\".
"""

import copy
import json

from tbbbridge.session import Session, apply_command, new_session
from tbbbridge.protocol import handle_command_line


def test_handle_command_line_next_turn_returns_apply_command_result_and_snapshot_dict():
    """G66.1a kryt-1: ``handle_command_line(session, '{"type": "next_turn"}')``
    zwraca krotkę ``(new_session, resp)`` gdzie ``new_session`` jest wynikiem
    ``apply_command(session, {"type": "next_turn"})`` (świat/gra posunięte o
    turę), a ``resp == {"ok": True, "snapshot": new_session.snapshot()}``;
    ``json.dumps(resp)`` nie rzuca. Wejściowa sesja nie jest mutowana.
    """
    s = new_session(73, "player")
    before = copy.deepcopy(s.snapshot())

    expected_new = apply_command(s, {"type": "next_turn"})
    assert expected_new.snapshot()["calendar"] != {"year": 1, "month": 1}

    result_session, resp = handle_command_line(s, '{"type": "next_turn"}')

    assert isinstance(result_session, Session)
    assert result_session.snapshot() == expected_new.snapshot()
    assert resp == {"ok": True, "snapshot": result_session.snapshot()}
    assert json.dumps(resp) is not None
    json.dumps(resp)
    # Wejściowa sesja nie jest mutowana.
    assert s.snapshot() == before


def test_handle_command_line_invalid_json_or_non_dict_and_valueerror_returns_same_session_error():
    """G66.1a kryt-2: niepoprawny JSON albo JSON nie będący obiektem →
    ``(session, {"ok": False, "error": <str>})`` z **tą samą** (identycznościowo)
    sesją wejściową i bez klucza ``"snapshot"``. ``ValueError`` z
    ``apply_command`` (np. ``'{"type": "bogus"}'`` albo
    ``'{"type": "order", "order": "nope"}'``) →
    ``(session, {"ok": False, "error": str(exc)})``, sesja niezmieniona (ta
    sama identycznościowo).
    """
    s = new_session(73, "player")
    before = copy.deepcopy(s.snapshot())

    # --- Niepoprawny JSON oraz JSON nie będący obiektem: ta sama sesja, error, brak snapshotu. ---
    invalid_inputs = (
        '"{oops',   # malformed JSON
        '[]',       # JSON array, not an object
        '5',        # JSON number, not an object
    )
    for line in invalid_inputs:
        returned_session, resp = handle_command_line(s, line)

        assert returned_session is s  # identycznościowo ta sama
        assert resp.get("ok") is False
        assert isinstance(resp.get("error"), str)
        assert resp.get("error")  # niepusty
        assert "snapshot" not in resp
        # Sesja nie jest mutowana.
        assert s.snapshot() == before

    # --- ValueError z apply_command: ta sama sesja, error == str(exc), brak snapshotu. ---
    error_inputs = (
        '{"type": "bogus"}',
        '{"type": "order", "order": "nope"}',
    )
    for line in error_inputs:
        # Najpierw potwierdźmy, że apply_command rzuca ValueError (warunek scenariusza).
        command = json.loads(line)
        try:
            apply_command(s, command)
            raise AssertionError(f"expected ValueError for {line!r}")
        except ValueError as exc:
            expected_msg = str(exc)

        returned_session, resp = handle_command_line(s, line)

        assert returned_session is s  # identycznościowo ta sama
        assert resp.get("ok") is False
        assert resp.get("error") == expected_msg
        assert "snapshot" not in resp
        # Sesja nie jest mutowana.
        assert s.snapshot() == before
