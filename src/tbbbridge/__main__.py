"""CLI entry point for the tbbbridge snapshot package.

Przyrost G63.2b/G66.1c/G69.2a: jawna ścieżka z ``argv[0]`` lub domyślna
``out/state.json``; deterministyczna partia headless + zapis snapshotu JSON.
Podkomenda ``serve`` startuje interaktywną sesję JSON Lines na stdin/stdout.
``serve --resume <path>`` wznawia zapisaną partię z pliku.
"""

import json
import os
import sys

from tbb.driver import run_headless_game
from tbb.game import create_headless_game
from tbb.rng import Rng

from tbbbridge.persist import read_session
from tbbbridge.protocol import serve_stream
from tbbbridge.session import Session, new_session
from tbbbridge.snapshot import save_state


DEFAULT_PATH = "out/state.json"
HEADLESS_SEED = 73
PLAYER_DUCHY_ID = "player"


def _session_for_serve(argv: list[str]) -> Session:
    """Return the Session for a ``serve`` invocation.

    ``serve --resume <path>`` loads via ``read_session``; ``serve [seed]``
    builds a fresh ``new_session``.
    """
    if len(argv) >= 3 and argv[1] == "--resume":
        return read_session(argv[2])
    seed = int(argv[1]) if len(argv) > 1 else HEADLESS_SEED
    return new_session(seed=seed, player_duchy_id=PLAYER_DUCHY_ID)


def main(
    argv: list[str] | None = None,
    *,
    stdin: object = sys.stdin,
    stdout: object = sys.stdout,
    stderr: object = sys.stderr,
) -> int:
    """CLI entry point for ``tbbbridge``.

    ``python -m tbbbridge serve [seed]`` starts an interactive JSON Lines
    session on ``stdin``/``stdout``.  ``python -m tbbbridge serve --resume
    <path>`` resumes a saved session from ``path`` via ``read_session``.
    Any other invocation runs the legacy headless snapshot path:
    ``argv[0]`` is the output path (default ``out/state.json``).
    Returns ``0`` on success.
    """
    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] == "serve":
        try:
            session = _session_for_serve(argv)
        except (OSError, json.JSONDecodeError) as exc:
            print(str(exc), file=stderr)
            return 1
        serve_stream(session, stdin, stdout)
        return 0

    path = argv[0] if argv else DEFAULT_PATH
    world, game = create_headless_game()
    world, game, calendar = run_headless_game(
        world, game, Rng(HEADLESS_SEED), player_duchy_id=PLAYER_DUCHY_ID
    )
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    save_state(world, game, calendar, path, player_duchy_id=PLAYER_DUCHY_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
