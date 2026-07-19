"""Headless entry point for a complete deterministic game."""

from tbb.driver import run_headless_game
from tbb.game import create_headless_game
from tbb.rng import Rng


HEADLESS_SEED = 73


def main() -> int:
    world, game = create_headless_game()
    _, result = run_headless_game(world, game, Rng(HEADLESS_SEED))

    if result.winner is None:
        print("Wynik: remis — brak zwycięzcy.")
    else:
        print(f"Zwycięzca: {result.winner.duchy_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
