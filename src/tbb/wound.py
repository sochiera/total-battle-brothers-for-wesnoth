"""Immutable wounds and the initial wound catalog."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Wound:
    """A temporary or permanent penalty to a unit's combat statistics."""

    name: str
    accuracy_mod: int
    defense_mod: int
    duration_months: int | None

    def __post_init__(self) -> None:
        if self.accuracy_mod > 0 or self.defense_mod > 0:
            raise ValueError("wound modifiers cannot be positive")
        if self.duration_months is not None and (
            type(self.duration_months) is not int or self.duration_months <= 0
        ):
            raise ValueError("wound duration must be a positive integer or None")


BRUISE = Wound("Bruise", accuracy_mod=-1, defense_mod=-1, duration_months=2)
MAIMED = Wound("Maimed", accuracy_mod=-2, defense_mod=-2, duration_months=None)
