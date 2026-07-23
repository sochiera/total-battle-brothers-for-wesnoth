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
        assert "result" not in resp  # G66.2a: ścieżka błędu nie dokłada "result"
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
        assert "result" not in resp  # G66.2a: ścieżka błędu nie dokłada "result"
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


def test_command_result_turn_and_new_game_kinds_match_after_calendar_and_are_json_serializable():
    """G66.2a kryt-1 (gałęzie turn/new_game): ``command_result(before, after,
    {"type": "next_turn"})`` zwraca ``{"kind": "turn", "date": {"year":
    after.calendar.year, "month": after.calendar.month}}`` (wartości czerwone
    z obiektu ``after``, a nie z ``before``, oraz różne od stanu wyjściowego),
    a ``command_result(before, after, {"type": "new_game"})`` zwraca dokładnie
    ``{"kind": "new_game"}`` (bez klucza ``changed`` ani ``date``). Oba wyniki
    są json-serializowalne.
    """
    s = new_session(73, "player")
    before_calendar = dict(year=s.calendar.year, month=s.calendar.month)

    # --- next_turn -> {"kind": "turn", "date": z after.calendar} ---
    after_turn = apply_command(s, {"type": "next_turn"})
    assert after_turn.calendar is not s.calendar  # warunek scenariusza: tura poszła
    assert (after_turn.calendar.year, after_turn.calendar.month) != (
        s.calendar.year,
        s.calendar.month,
    )

    result_turn = command_result(s, after_turn, {"type": "next_turn"})

    assert result_turn == {
        "kind": "turn",
        "date": {
            "year": after_turn.calendar.year,
            "month": after_turn.calendar.month,
        },
    }
    # date pochodzi z after, nie z before:
    assert result_turn["date"] != before_calendar
    # brak klucza changed:
    assert "changed" not in result_turn
    json.dumps(result_turn)

    # --- new_game -> {"kind": "new_game"} ---
    after_new = apply_command(s, {"type": "new_game"})
    result_new = command_result(s, after_new, {"type": "new_game"})

    assert result_new == {"kind": "new_game"}
    assert "date" not in result_new
    assert "changed" not in result_new
    json.dumps(result_new)


def _build_battle_session_assault():
    """Sesja z sąsiednią wrogą osadą — ``assault`` rozegra bitwę (last_battle)."""
    from tbb.duchy import Duchy
    from tbb.party import Party
    from tbb.settlement import Settlement
    from tbb.unit import Unit
    from tbb.world import Region, WorldMap
    from tbb.turn import Calendar
    from tbb.rng import Rng
    from tbb.game import GameState

    start, near = Region("Start"), Region("Near")
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    near_keep = Settlement(
        "Near Keep", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        [start, near],
        [(start, near)],
        settlements={near: near_keep},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, morale=10, parties=(party,)),
            Duchy("south", Unit(), morale=-5, settlements=(near_keep,)),
        )
    )
    return Session(
        world=world,
        game=game,
        calendar=Calendar(year=2, month=3),
        rng=Rng(2),
        player_duchy_id="north",
        seed=2,
    )


def test_command_result_battle_order_with_last_battle_returns_kind_battle_with_outcome_and_losses():
    """G66.2b kryt-1: ``command_result(before, after, {"type": "order",
    "order": "assault"})`` gdy ``after.last_battle is not None`` zwraca
    ``{"kind": "battle", "order": "assault", "outcome": <str|None>,
    "attacker_losses": int, "defender_losses": int}`` gdzie ``outcome`` jest
    mapowane z perspektywy atakującego z ``after.last_battle.report().result.value``
    (``"attacker_win"`` → ``"zwycięstwo"``, ``"defender_win"`` → ``"porażka"``,
    ``"draw"`` → ``"remis"``), a straty == ``len(report.attacker.fallen)`` /
    ``len(report.defender.fallen)``. Wynik przechodzi ``json.dumps``.

    Scenariusz: party gracza (north) szturmem uderza na sąsiednią wrogą osadę
    (south). ``after.last_battle`` jest rozegrana bitwą z realnym
    ``BattleResult`` i poległymi, więc ``command_result`` musi odczytać raport
    zamiast zwracać gałąź ``kind: "order"``.
    """
    from tbb.battle import BattleResult

    s = _build_battle_session_assault()
    after = apply_command(s, {"type": "order", "order": "assault"})

    # Warunki scenariusza: bitwa wybuchła i jest rozstrzygnięta.
    assert after.last_battle is not None
    report = after.last_battle.report()
    assert isinstance(report.result, BattleResult)

    result = command_result(s, after, {"type": "order", "order": "assault"})

    # Oczekiwane mapowanie outcome z perspektywy atakującego.
    _outcome_from_result = {
        BattleResult.ATTACKER_WIN: "zwycięstwo",
        BattleResult.DEFENDER_WIN: "porażka",
        BattleResult.DRAW: "remis",
    }
    expected_outcome = _outcome_from_result[report.result]
    expected = {
        "kind": "battle",
        "order": "assault",
        "outcome": expected_outcome,
        "attacker_losses": len(report.attacker.fallen),
        "defender_losses": len(report.defender.fallen),
    }
    assert result == expected

    # outcome jest str (rozstrzygnięta bitwa w tym scenariuszu).
    assert isinstance(result["outcome"], str)
    assert result["outcome"] in ("zwycięstwo", "porażka", "remis")
    assert isinstance(result["attacker_losses"], int)
    assert isinstance(result["defender_losses"], int)
    # Brak klucza "changed" w gałęzi bitewnej.
    assert "changed" not in result
    # json-serializowalny.
    json.dumps(result)


def test_command_result_battle_order_without_last_battle_returns_kind_order_changed():
    """G66.2b kryt-2: gdy rozkaz bojowy (``assault``) nie rozegrał bitwy
    (``after.last_battle is None`` — guard albo brak sąsiedniego celu) →
    ``command_result`` zwraca ``{"kind": "order", "order": "assault",
    "changed": (after.world is not before.world)}``, spójnie z rozkazami
    niebitewnymi (G66.2a). Wynik przechodzi ``json.dumps``.

    Scenariusz guard: sesja bez ``player_duchy_id`` (``None``) →
    ``_resolve_player_duchy`` zwraca ``None`` i ``_apply_battle_order`` zwraca
    pochodną sesji z tymiż obiektami ``world``/``game``/``calendar`` oraz
    ``last_battle is None``, więc ``changed is False``.
    """
    s = _build_battle_session_assault()
    s.player_duchy_id = None
    after = apply_command(s, {"type": "order", "order": "assault"})

    # Warunki scenariusza: guard → no-op, brak bitwy, world niezmieniony.
    assert after.last_battle is None
    assert after.world is s.world

    result = command_result(s, after, {"type": "order", "order": "assault"})

    assert result == {
        "kind": "order",
        "order": "assault",
        "changed": False,
    }
    json.dumps(result)


def test_command_result_save_returns_kind_save_with_path():
    """G68.2a kryt-1: ``command_result(before, after, {"type": "save", "path": p})``
    zwraca ``{"kind": "save", "path": p}`` (czysta funkcja; dla ``save`` ``before``
    i ``after`` to ta sama sesja). Wynik przechodzi ``json.dumps``.
    """
    s = new_session(73, "player")
    result = command_result(s, s, {"type": "save", "path": "/tmp/test-save.json"})

    assert result == {
        "kind": "save",
        "path": "/tmp/test-save.json",
    }
    json.dumps(result)


def test_handle_command_line_save_writes_file_and_returns_same_session_with_snapshot_and_result():
    """G68.2a kryt-2: ``handle_command_line(session, '{"type": "save", "path": <p>}')``
    wywołuje ``tbbbridge.persist.save_session(session, p)`` (plik powstaje) i zwraca
    ``(session, resp)``, gdzie zwrócona sesja jest **tym samym** obiektem co wejściowa
    (``is``), a ``resp == {"ok": True, "snapshot": session.snapshot(), "result":
    {"kind": "save", "path": p}}``; ``json.dumps(resp)`` nie rzuca. ``apply_command``
    nie jest wołane dla ``save`` i pozostaje czyste (bez IO).
    """
    import os
    import tempfile
    from tbbbridge.persist import read_session

    s = new_session(73, "player")
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test-save.json")
        session_out, resp = handle_command_line(s, json.dumps({"type": "save", "path": path}))

        # Sesja wyjściowa jest tym samym obiektem co wejściowa (save nie mutuje stanu).
        assert session_out is s

        # Odpowiedź zawiera ok, snapshot i result.
        assert resp["ok"] is True
        assert resp["snapshot"] == s.snapshot()
        assert resp["result"] == {"kind": "save", "path": path}

        # Plik powstał i można go wczytać.
        assert os.path.exists(path)
        loaded = read_session(path)
        assert loaded.world.regions == s.world.regions
        assert loaded.game.duchies == s.game.duchies
        assert loaded.calendar.year == s.calendar.year
        assert loaded.calendar.month == s.calendar.month
        assert loaded.player_duchy_id == s.player_duchy_id
        assert loaded.seed == s.seed

        # json.dumps nie rzuca.
        json.dumps(resp)


def test_handle_command_line_save_missing_path_or_non_string_path_returns_error_without_write():
    """G68.2a kryt-3: Brak klucza ``path`` lub ``path`` nie będący ``str`` →
    ``(session, {"ok": False, "error": <str>})`` bez próby zapisu.
    """
    import os
    import tempfile

    s = new_session(73, "player")
    before_snapshot = s.snapshot()

    # --- Brak klucza path ---
    with tempfile.TemporaryDirectory() as tmpdir:
        # Ścieżka, która na pewno nie istnieje przed testem.
        nonexistent = os.path.join(tmpdir, "does-not-exist.json")
        session_out, resp = handle_command_line(s, json.dumps({"type": "save"}))

        assert session_out is s
        assert resp["ok"] is False
        assert isinstance(resp["error"], str)
        assert resp["error"]  # niepusty
        assert "snapshot" not in resp
        assert "result" not in resp
        # Plik nie powstał.
        assert not os.path.exists(nonexistent)
        # Sesja nie jest mutowana.
        assert s.snapshot() == before_snapshot

    # --- path nie będący str ---
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent = os.path.join(tmpdir, "does-not-exist-2.json")
        session_out, resp = handle_command_line(s, json.dumps({"type": "save", "path": 123}))

        assert session_out is s
        assert resp["ok"] is False
        assert isinstance(resp["error"], str)
        assert resp["error"]  # niepusty
        assert "snapshot" not in resp
        assert "result" not in resp
        assert not os.path.exists(nonexistent)
        assert s.snapshot() == before_snapshot

    # --- path pusty string ---
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent = os.path.join(tmpdir, "does-not-exist-3.json")
        session_out, resp = handle_command_line(s, json.dumps({"type": "save", "path": ""}))

        assert session_out is s
        assert resp["ok"] is False
        assert isinstance(resp["error"], str)
        assert resp["error"]  # niepusty
        assert "snapshot" not in resp
        assert "result" not in resp
        assert not os.path.exists(nonexistent)
        assert s.snapshot() == before_snapshot


def test_handle_command_line_save_oserror_returns_error_without_write():
    """G68.2a kryt-3 cd.: ``OSError`` z ``save_session`` (np. katalog docelowy nie
    istnieje) → ``(session, {"ok": False, "error": <str>})``.
    """
    import os
    import tempfile

    s = new_session(73, "player")
    before_snapshot = s.snapshot()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Ścieżka z nieistniejącym katalogiem nadrzędnym.
        nonexistent_dir = os.path.join(tmpdir, "nonexistent-dir", "save.json")
        session_out, resp = handle_command_line(s, json.dumps({"type": "save", "path": nonexistent_dir}))

        # save_session nie tworzy katalogów, więc OSError powinien wystąpić.
        assert session_out is s
        assert resp["ok"] is False
        assert isinstance(resp["error"], str)
        assert "snapshot" not in resp
        assert "result" not in resp
        # Katalog nie powstał.
        assert not os.path.exists(os.path.join(tmpdir, "nonexistent-dir"))
        # Sesja nie jest mutowana.
        assert s.snapshot() == before_snapshot
