"""Immutable terrain definitions for hex battles."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Terrain:
    """A terrain type and its movement and combat modifiers."""

    name: str
    move_cost: int
    defense_mod: int
    accuracy_mod: int

    def __post_init__(self) -> None:
        if self.move_cost < 1:
            raise ValueError("move_cost must be positive")


PLAINS = Terrain("Plains", move_cost=1, defense_mod=0, accuracy_mod=0)
FOREST = Terrain("Forest", move_cost=2, defense_mod=2, accuracy_mod=-1)
HILLS = Terrain("Hills", move_cost=2, defense_mod=1, accuracy_mod=1)
