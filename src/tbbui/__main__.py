"""CLI entry: HTML snapshot or browser preview server (``python -m tbbui``)."""

from __future__ import annotations

import sys
from pathlib import Path

import tbb.driver as driver
import tbb.game as game
from tbb.rng import Rng
from tbb.turn import Calendar
from tbbui.gamepage import render_game_page
from tbbui.serve import GameApp, make_server

HEADLESS_SEED = 73
DEFAULT_OUTPUT = Path("out/game.html")
DEFAULT_SERVE_HOST = "127.0.0.1"


def main(argv: list[str] | None = None) -> int:
    """CLI: snapshot to HTML, or ``serve [port]`` for the interactive preview.

    Without ``serve``: run a deterministic headless party and write
    ``render_game_page`` HTML. Optional first ``argv`` entry is the output path
    (default ``out/game.html``); creates the parent directory when missing.

    With ``serve [port]``: create a fresh deterministic party, bind
    ``make_server``, and call ``serve_forever`` (optional port, default ``0`` =
    ephemeral). Returns 0 on success / clean shutdown.
    """
    args = list(sys.argv[1:] if argv is None else argv)

    if args and args[0] == "serve":
        return _run_serve(args[1:])

    out = Path(args[0]) if args else DEFAULT_OUTPUT

    world, initial_game = game.create_headless_game()
    final_world, final_game, final_calendar = driver.run_headless_game(
        world, initial_game, Rng(HEADLESS_SEED)
    )
    html = render_game_page(final_world, final_game, final_calendar)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return 0


def _run_serve(args: list[str]) -> int:
    """Start the local preview HTTP server for a fresh deterministic party."""
    port = int(args[0]) if args else 0
    world, initial_game = game.create_headless_game()
    app = GameApp(
        world,
        initial_game,
        Calendar(),
        Rng(HEADLESS_SEED),
        player_duchy_id="player",
        seed=HEADLESS_SEED,
    )
    server = make_server(app, host=DEFAULT_SERVE_HOST, port=port)
    host, bound_port = server.server_address[:2]
    print(f"Serving preview at http://{host}:{bound_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
