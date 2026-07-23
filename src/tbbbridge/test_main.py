"""Tests for ``tbbbridge.__main__.main`` (G66.1c — CLI serve subcommand).

Tests live next to the module under test per task-321 \"Ścieżki testów\".
"""

import io
import json

from tbbbridge.__main__ import main


def test_main_serve_default_seed_runs_serve_stream_writes_one_ok_snapshot_line_returns_zero():
    """G66.1c kryt-1a: ``main(["serve"], stdin=<io z '{"type": "next_turn"}\\n'>,
    stdout=<io>)`` buduje ``new_session()`` (domyślny seed) i uruchamia
    ``serve_stream``, wypisując na ``stdout`` dokładnie jedną linię odpowiedzi z
    ``"ok": true`` i kluczem ``"snapshot"``; zwraca ``0``.
    """
    in_stream = io.StringIO('{"type": "next_turn"}\n')
    out_stream = io.StringIO()

    rc = main(["serve"], stdin=in_stream, stdout=out_stream)

    assert rc == 0
    out_lines = out_stream.getvalue().splitlines()
    assert len(out_lines) == 1
    resp = json.loads(out_lines[0])
    assert resp.get("ok") is True
    assert "snapshot" in resp


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
