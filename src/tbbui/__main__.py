"""CLI entry point: deterministic headless party → HTML snapshot (observer)."""

from __future__ import annotations

import sys
from pathlib import Path

import tbb.driver as driver
import tbb.game as game
from tbb.rng import Rng
from tbbui.gamepage import render_game_page

HEADLESS_SEED = 73
DEFAULT_OUTPUT = Path("out/game.html")


def main(argv: list[str] | None = None) -> int:
    """Run a deterministic headless party and write ``render_game_page`` HTML.

    Optional first ``argv`` entry is the output path; default ``out/game.html``.
    Creates the parent directory when missing. Returns 0 on success.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    out = Path(args[0]) if args else DEFAULT_OUTPUT

    world, initial_game = game.create_headless_game()
    final_world, final_game, final_calendar = driver.run_headless_game(
        world, initial_game, Rng(HEADLESS_SEED)
    )
    html = render_game_page(final_world, final_game, final_calendar)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
