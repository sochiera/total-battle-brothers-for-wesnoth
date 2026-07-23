"""Tests for ``tbbbridge.__main__.main`` (G66.1c — CLI serve subcommand).

Tests live next to the module under test per task-321 "Ścieżki testów".
"""

import io
import json

from tbb.driver import run_headless_game
from tbb.game import create_headless_game
from tbb.rng import Rng
from tbbbridge.__main__ import HEADLESS_SEED, PLAYER_DUCHY_ID, main
from tbbbridge.snapshot import game_state


def test_main_serve_default_seed_runs_serve_stream_writes_one_ok_snapshot_line_returns_zero():
    """G66.1c kryt-1a: ``main(["serve"], stdin=<io z '{"type": "next_turn"}\\n'>,
    stdout=<io>)`` buduje ``new_session()`` (domyślny seed) i uruchamia
    ``serve_stream``, wypisując na ``stdout`` dokładnie jedną linię odpowiedzi z
    ``"ok": true`` i kluczem ``"snapshot"``; zwraca ``0``.

    Weryfikacja domyślnego seeda: snapshot pierwszej komendy ``next_turn`` po
    ``main(["serve"])`` musi być równy ``apply_command(new_session(),
    {"type":"next_turn"}).snapshot()`` — czyli sesji z domyślnym seedem ``73``
    z ``new_session`` (bez podania argumentu). Gdyby ``serve`` użyło innego
    seeda (np. 99), snapshoty by się różniły.
    """
    from tbbbridge.session import new_session, apply_command

    in_stream = io.StringIO('{"type": "next_turn"}\n')
    out_stream = io.StringIO()

    rc = main(["serve"], stdin=in_stream, stdout=out_stream)

    assert rc == 0
    out_lines = out_stream.getvalue().splitlines()
    assert len(out_lines) == 1
    resp = json.loads(out_lines[0])
    assert resp.get("ok") is True
    assert "snapshot" in resp

    expected_snapshot = apply_command(
        new_session(), {"type": "next_turn"}
    ).snapshot()
    assert resp["snapshot"] == expected_snapshot


def test_main_serve_with_seed_argument_uses_new_session_with_that_seed_returns_zero():
    """G66.1c kryt-1b: ``main(["serve", "99"], ...)`` używa
    ``new_session(seed=99)`` (seed z ``argv[1]``). Wypisuje jedną linię z
    ``"ok": true`` i ``"snapshot"``; zwraca ``0``.

    Asercja seeda: snapshot pierwszej komendy ``new_game`` po serve(99) daje
    świeżą partię z seedem 99 — porównujemy z ``new_session(seed=99)`` + jedną
    turą przez ``apply_command``.
    """
    from tbbbridge.session import new_session, apply_command

    in_stream = io.StringIO('{"type": "next_turn"}\n')
    out_stream = io.StringIO()

    rc = main(["serve", "99"], stdin=in_stream, stdout=out_stream)

    assert rc == 0
    out_lines = out_stream.getvalue().splitlines()
    assert len(out_lines) == 1
    resp = json.loads(out_lines[0])
    assert resp.get("ok") is True
    assert "snapshot" in resp

    expected_snapshot = apply_command(
        new_session(seed=99), {"type": "next_turn"}
    ).snapshot()
    assert resp["snapshot"] == expected_snapshot


def _reference_legacy_snapshot():
    """Referencyjna partia headless + snapshot (seed 73) jak w ``main``."""
    world, game = create_headless_game()
    world, game, calendar = run_headless_game(
        world, game, Rng(HEADLESS_SEED), player_duchy_id=PLAYER_DUCHY_ID
    )
    return game_state(world, game, calendar, player_duchy_id=PLAYER_DUCHY_ID)


def test_main_empty_argv_writes_deterministic_snapshot_to_default_path_returns_zero_without_touching_protocol_streams(
    monkeypatch, tmp_path
):
    """G66.1c kryt-2a: ``main([])`` zapisuje deterministyczny snapshot JSON do
    domyślnej ścieżki ``out/state.json``, zwraca ``0`` i **nie** czyta ani nie
    pisze strumieni protokołu (stdin/stdout). Snapshot bajt-w-bajt równy
    referencji z ``create_headless_game`` + ``run_headless_game`` (seed 73).
    """
    monkeypatch.chdir(tmp_path)
    assert not (tmp_path / "out").exists()

    # Puste strumienie-karce: legacy path nie powinien z nich czytać ani na nie
    # pisać — ukrywamy stdin/stdout, by jakikolwiek dostęp rzucił błędem.
    empty_in = io.StringIO("")
    empty_out = io.StringIO()

    rc = main([], stdin=empty_in, stdout=empty_out)

    assert rc == 0
    out_path = tmp_path / "out" / "state.json"
    assert out_path.exists()
    # Legacy path nie pisze nic do stdout (zero bajtów na strumieniu protokołu).
    assert empty_out.getvalue() == ""

    snapshot = json.loads(out_path.read_text(encoding="utf-8"))
    assert list(snapshot.keys()) == ["calendar", "duchies", "map", "result"]
    assert snapshot == _reference_legacy_snapshot()


def test_main_with_explicit_path_writes_deterministic_snapshot_to_that_path_returns_zero_without_touching_protocol_streams(
    tmp_path,
):
    """G66.1c kryt-2b: ``main(["<ścieżka>"])`` zapisuje deterministyczny snapshot
    JSON do podanej ścieżki (tworząc katalog nadrzędny), zwraca ``0`` i **nie**
    czyta ani nie pisze strumieni protokołu. Snapshot równy referencji (seed 73).
    """
    out_path = tmp_path / "nested" / "state.json"

    empty_in = io.StringIO("")
    empty_out = io.StringIO()

    rc = main([str(out_path)], stdin=empty_in, stdout=empty_out)

    assert rc == 0
    assert out_path.exists()
    # Legacy path nie pisze nic do stdout (zero bajtów na strumieniu protokołu).
    assert empty_out.getvalue() == ""

    snapshot = json.loads(out_path.read_text(encoding="utf-8"))
    assert list(snapshot.keys()) == ["calendar", "duchies", "map", "result"]
    assert snapshot == _reference_legacy_snapshot()
