"""Headless entry point for a complete deterministic game."""

import tbb.driver as driver
import tbb.game as game
from tbb.rng import Rng


HEADLESS_SEED = 73


def main() -> int:
    world, initial_game = game.create_headless_game()
    _, result, final_calendar = driver.run_headless_game(
        world, initial_game, Rng(HEADLESS_SEED)
    )

    if result.winner is None:
        outcome = "Wynik: remis — brak zwycięzcy."
    else:
        outcome = f"Zwycięzca: {result.winner.duchy_id}"
    print(
        f"{outcome} Rok: {final_calendar.year}, "
        f"miesiąc: {final_calendar.month}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
