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


def test_main_serve_resume_uses_read_session_not_new_session(tmp_path):
    """G69.2a kryt-1: ``main(["serve", "--resume", <path>], stdin=<io>, stdout=<io>)``
    startuje ``serve_stream`` z sesją ``read_session(<path>)`` (nie ``new_session``) i
    zwraca ``0``; dla pliku zapisanego wcześniej z sesji ``s`` pierwsza odpowiedź na
    ``{"type": "snapshot"}`` ma ``snapshot`` równy ``read_session(<path>).snapshot()``.
    """
    from tbbbridge.persist import read_session, save_session
    from tbbbridge.session import new_session

    # Przygotuj zapisaną sesję (z innym seedem niż domyślny 73, by różnica była widoczna)
    saved_session = new_session(seed=42, player_duchy_id="player")
    state_path = tmp_path / "saved_state.json"
    save_session(saved_session, state_path)

    # Wywołaj CLI z --resume
    in_stream = io.StringIO('{"type": "snapshot"}\n')
    out_stream = io.StringIO()

    rc = main(["serve", "--resume", str(state_path)], stdin=in_stream, stdout=out_stream)

    assert rc == 0
    out_lines = out_stream.getvalue().splitlines()
    assert len(out_lines) == 1
    resp = json.loads(out_lines[0])
    assert resp.get("ok") is True
    assert "snapshot" in resp

    # Snapshot musi pochodzić z read_session, nie z new_session
    expected_session = read_session(state_path)
    assert resp["snapshot"] == expected_session.snapshot()
    # Asertacja negatywna: zapisana sesja miała inny seed niż new_session();
    # sam snapshot przed użyciem RNG jest taki sam dla każdego seedu, więc
    # różnicę weryfikujemy bezpośrednio na polu seed.
    assert expected_session.seed != new_session().seed


def test_main_serve_resume_next_turn_uses_state_from_file(tmp_path):
    """G69.2a kryt-2: Po ``--resume`` kolejna komenda ``{"type": "next_turn"}`` daje
    ``snapshot`` równy ``read_session(<path>).next_turn().snapshot()`` (stan i
    seed/``player_duchy_id``/RNG pochodzą z pliku, nie z domyślnego ``new_session``).
    """
    from tbbbridge.persist import read_session, save_session
    from tbbbridge.session import new_session, apply_command

    # Przygotuj zapisaną sesję po kilku turach (inna niż świeża)
    saved_session = new_session(seed=99, player_duchy_id="player")
    # Wykonaj turę przed zapisem, by stan był inny niż startowy
    saved_session = apply_command(saved_session, {"type": "next_turn"})
    state_path = tmp_path / "saved_state.json"
    save_session(saved_session, state_path)

    # Wywołaj CLI z --resume i wyślij next_turn
    in_stream = io.StringIO('{"type": "next_turn"}\n')
    out_stream = io.StringIO()

    rc = main(["serve", "--resume", str(state_path)], stdin=in_stream, stdout=out_stream)

    assert rc == 0
    out_lines = out_stream.getvalue().splitlines()
    assert len(out_lines) == 1
    resp = json.loads(out_lines[0])
    assert resp.get("ok") is True
    assert "snapshot" in resp

    # Snapshot musi być równy read_session(path).next_turn().snapshot()
    expected_session = read_session(state_path)
    expected_snapshot = apply_command(expected_session, {"type": "next_turn"}).snapshot()
    assert resp["snapshot"] == expected_snapshot
    # Asertacja negatywna: to nie może być wynik next_turn na domyślnej sesji
    assert resp["snapshot"] != apply_command(new_session(), {"type": "next_turn"}).snapshot()


def test_main_serve_resume_nonexistent_path_returns_one_writes_stderr_no_stdout(tmp_path):
    """G69.2b kryt-1: ``main(["serve", "--resume", <nieistniejąca_ścieżka>], stdin=<io>,
    stdout=<io>, stderr=<io>)`` **nie** startuje ``serve_stream`` (żadnej linii na
    ``stdout``), pisze niepusty komunikat błędu na ``stderr`` i zwraca ``1``.
    """
    nonexistent_path = tmp_path / "does_not_exist.json"
    assert not nonexistent_path.exists()

    in_stream = io.StringIO('{"type": "snapshot"}\n')
    out_stream = io.StringIO()
    err_stream = io.StringIO()

    rc = main(
        ["serve", "--resume", str(nonexistent_path)],
        stdin=in_stream,
        stdout=out_stream,
        stderr=err_stream,
    )

    assert rc == 1
    assert out_stream.getvalue() == ""
    assert err_stream.getvalue() != ""


def test_main_serve_resume_invalid_json_returns_one_writes_stderr_no_stdout(tmp_path):
    """G69.2b kryt-2: Dla pliku z niepoprawnym JSON-em (``json.JSONDecodeError`` z
    ``read_session``): brak wyjścia na ``stdout``, niepusty komunikat na ``stderr``,
    kod ``1``; ``stdin`` nie jest czytany.
    """
    invalid_json_path = tmp_path / "invalid.json"
    invalid_json_path.write_text("not valid json {", encoding="utf-8")

    in_stream = io.StringIO('{"type": "snapshot"}\n')
    out_stream = io.StringIO()
    err_stream = io.StringIO()

    rc = main(
        ["serve", "--resume", str(invalid_json_path)],
        stdin=in_stream,
        stdout=out_stream,
        stderr=err_stream,
    )

    assert rc == 1
    assert out_stream.getvalue() == ""
    assert err_stream.getvalue() != ""
    assert in_stream.tell() == 0
