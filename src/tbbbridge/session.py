"""Uchwyt sesji gry dla mostu poleceń Godot↔rdzeń."""

from tbb.game import create_headless_game, GameState
from tbb.rng import Rng
from tbb.turn import Calendar
from tbb.world import WorldMap

from tbbbridge.snapshot import game_state


class Session:
    """Uchwyt sesji trzymający stan gry i RNG współdzielony z driverem.

    Pola są publiczne do odczytu:
      world            -> WorldMap
      game             -> GameState
      calendar         -> Calendar
      rng              -> Rng
      player_duchy_id  -> str | None
      seed             -> int
    """

    def __init__(
        self,
        world: WorldMap,
        game: GameState,
        calendar: Calendar,
        rng: Rng,
        player_duchy_id: str | None,
        seed: int,
    ) -> None:
        self.world = world
        self.game = game
        self.calendar = calendar
        self.rng = rng
        self.player_duchy_id = player_duchy_id
        self.seed = seed

    def snapshot(self) -> dict:
        """Zwróć json-serializowalny snapshot stanu sesji.

        Nie mutuje sesji. Deleguje do `tbbbridge.snapshot.game_state`.
        """
        return game_state(
            self.world,
            self.game,
            self.calendar,
            self.player_duchy_id,
        )


def new_session(seed: int = 73, player_duchy_id: str | None = "player") -> Session:
    """Utwórz nową sesję ze świeżą grą headless."""
    world, game = create_headless_game()
    return Session(
        world=world,
        game=game,
        calendar=Calendar(),
        rng=Rng(seed),
        player_duchy_id=player_duchy_id,
        seed=seed,
    )
