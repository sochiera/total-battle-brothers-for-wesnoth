"""CLI entry point for the tbbbridge snapshot package.

Pierwszy przyrost (G63.2b-1): jawna ścieżka z argv[0] deterministyczna partia
headless + zapis snapshotu JSON.
"""

import os
import sys

from tbb.driver import run_headless_game
from tbb.game import create_headless_game
from tbb.rng import Rng

from tbbbridge.snapshot import save_state


HEADLESS_SEED = 73
PLAYER_DUCHY_ID = "player"


def main(argv: list[str] | None = None) -> int:
    """Run a deterministic headless game and write its snapshot to ``path``.

    ``path`` is taken from ``argv[0]``. The parent directory is created if
    missing. Returns ``0`` on success.
    """
    if argv is None:
        argv = sys.argv[1:]
    path = argv[0]
    world, game = create_headless_game()
    world, game, calendar = run_headless_game(
        world, game, Rng(HEADLESS_SEED), player_duchy_id=PLAYER_DUCHY_ID
    )
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    save_state(world, game, calendar, path, player_duchy_id=PLAYER_DUCHY_ID)
    return 0
