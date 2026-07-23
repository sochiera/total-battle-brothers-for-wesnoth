"""Tests for the tbbbridge JSON-line protocol (G66.1a / G66.1b).

Tests live next to the module under test per task-319/320 \"Ścieżki testów\".
"""

import copy
import io
import json

from tbbbridge.session import Session, apply_command, new_session
from tbbbridge.protocol import command_result, handle_command_line, serve_stream


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
    assert resp["ok"] is True
    assert resp["snapshot"] == result_session.snapshot()
    assert resp["result"] == command_result(
        s, result_session, {"type": "next_turn"}
    )
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


class _FlushTrackingStream(io.StringIO):
    """StringIO z licznikiem wywołań ``flush``."""

    def __init__(self) -> None:
        super().__init__()
        self.flush_calls = 0

    def flush(self) -> int:  # type: ignore[override]
        self.flush_calls += 1
        return super().flush()


def test_serve_stream_two_next_turn_commands_writes_two_json_lines_advances_session_and_flushes():
    """G66.1b kryt-1: ``serve_stream(session, in, out)`` czyta linie z ``in_stream``,
    dla każdej niepustej woła ``handle_command_line``, zapisuje
    ``json.dumps(response) + "\\n"`` do ``out_stream`` i po EOF zwraca końcową
    sesję. Dla wejścia z dwiema komendami ``{"type":"next_turn"}`` (w osobnych
    liniach) ``out_stream.getvalue()`` zawiera dokładnie dwie linie JSON, każda z
    ``"ok": true`` i kluczem ``"snapshot"``, a zwrócona sesja jest wynikiem
    sekwencyjnego zastosowania obu komend (świat/gra posunięte o dwie tury).
    """
    s = new_session(73, "player")
    before_one = apply_command(s, {"type": "next_turn"})
    expected_final = apply_command(before_one, {"type": "next_turn"})
    assert expected_final.snapshot()["calendar"] != s.snapshot()["calendar"]

    in_stream = io.StringIO('{"type": "next_turn"}\n{"type": "next_turn"}\n')
    out_stream = _FlushTrackingStream()

    returned = serve_stream(s, in_stream, out_stream)

    out_lines = out_stream.getvalue().splitlines()
    assert len(out_lines) == 2

    for line in out_lines:
        resp = json.loads(line)
        assert resp.get("ok") is True
        assert "snapshot" in resp

    first_resp = json.loads(out_lines[0])
    second_resp = json.loads(out_lines[1])
    assert first_resp["snapshot"]["calendar"] == before_one.snapshot()["calendar"]
    assert second_resp["snapshot"]["calendar"] == expected_final.snapshot()["calendar"]

    assert returned.snapshot() == expected_final.snapshot()


def test_serve_stream_skips_blank_lines_bad_json_does_not_break_loop_and_flushes_each_response():
    """G66.1b kryt-2: puste i białoznakowe linie są pomijane (żadnego wpisu w
    ``out_stream``, sesja bez zmian). Linia z niepoprawnym JSON daje jedną linię
    odpowiedzi ``{"ok": false, ...}`` i **nie** przerywa pętli — kolejne linie są
    dalej obsługiwane. Po zapisaniu każdej odpowiedzi wywoływany jest
    ``out_stream.flush()``.
    """
    s = new_session(73, "player")
    before = copy.deepcopy(s.snapshot())

    in_stream = io.StringIO(
        "\n"
        "   \n"
        "\t\n"
        "{not json}\n"
        '{"type": "next_turn"}\n'
        '   \n'
        '{bad again\n'
        '{"type": "next_turn"}\n'
    )
    out_stream = _FlushTrackingStream()

    returned = serve_stream(s, in_stream, out_stream)

    out_lines = out_stream.getvalue().splitlines()

    # 4 odpowiedzi: 2 bad-JSON + 2 poprawne next_turn (puste/białoznakowe nie dają
    # żadnego wpisu).
    assert len(out_lines) == 4

    first = json.loads(out_lines[0])
    second = json.loads(out_lines[1])
    third = json.loads(out_lines[2])
    fourth = json.loads(out_lines[3])

    assert first.get("ok") is False
    assert isinstance(first.get("error"), str)
    assert "snapshot" not in first

    assert second.get("ok") is True
    assert "snapshot" in second

    assert third.get("ok") is False
    assert isinstance(third.get("error"), str)
    assert "snapshot" not in third

    assert fourth.get("ok") is True
    assert "snapshot" in fourth

    # flush po każdej odpowiedzi (4 odpowiedzi → 4 flush).
    assert out_stream.flush_calls == 4

    # Sesja wejściowa nie jest mutowana.
    assert s.snapshot() == before

    # Zwrócona sesja = sekwencyjne zastosowanie dwóch next_turn (pośrednie błędy
    # nie psują kumulacji stanu).
    expected = apply_command(
        apply_command(s, {"type": "next_turn"}),
        {"type": "next_turn"},
    )
    assert returned.snapshot() == expected.snapshot()


def test_command_result_non_battle_order_changed_flag_matches_world_identity():
    """G66.2a kryt-1: ``command_result(before, after, command)`` dla rozkazu
    niebitewnego ``{"type": "order", "order": "develop"}`` zwraca
    ``{"kind": "order", "order": "develop", "changed": <bool>}`` gdzie
    ``changed == (after.world is not before.world)``. Dwa scenariusze:

    1. Zastosowany rozkaz (świeża sesja z graczem) -> ``_apply_order`` buduje
       nowy ``WorldMap`` (``develop_duchy_settlement`` otwiera budynek), więc
       ``after.world is not before.world`` i ``changed is True``.
    2. Guard/no-op (sesja bez ``player_duchy_id``) -> ``_resolve_player_duchy``
       zwraca ``None`` i ``_apply_order`` zwraca tę samą ``(world, game,
       calendar)`` (tożsamość obiektu ``world`` zachowana), więc
       ``changed is False``.

    Wynik musi być json-serializowalny.
    """
    # --- Scenariusz 1: rozkaz zastosowany -> changed=True ---
    s_player = new_session(73, "player")
    after_player = apply_command(s_player, {"type": "order", "order": "develop"})
    assert after_player.world is not s_player.world  # warunek scenariusza

    result_changed = command_result(
        s_player, after_player, {"type": "order", "order": "develop"}
    )

    assert result_changed == {
        "kind": "order",
        "order": "develop",
        "changed": True,
    }
    # json-serializowalny
    json.dumps(result_changed)

    # --- Scenariusz 2: guard/no-op -> changed=False ---
    s_noop = new_session(73, player_duchy_id=None)
    after_noop = apply_command(s_noop, {"type": "order", "order": "develop"})
    assert after_noop.world is s_noop.world  # tożsamość obiektu zachowana

    result_unchanged = command_result(
        s_noop, after_noop, {"type": "order", "order": "develop"}
    )

    assert result_unchanged == {
        "kind": "order",
        "order": "develop",
        "changed": False,
    }
    json.dumps(result_unchanged)
