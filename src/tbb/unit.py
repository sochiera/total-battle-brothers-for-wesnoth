"""Immutable unit quality pillars and their derived combat statistics."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Unit:
    """Represent a unit through independent, non-negative quality pillars."""

    training: int = 0
    equipment: int = 0
    experience: int = 0

    def __post_init__(self) -> None:
        """Reject pillar values below zero."""
        if self.training < 0 or self.equipment < 0 or self.experience < 0:
            raise ValueError("unit quality pillars cannot be negative")

    @property
    def hp(self) -> int:
        return 10 + self.training

    @property
    def accuracy(self) -> int:
        return self.training + self.experience

    @property
    def damage(self) -> int:
        return self.equipment

    @property
    def defense(self) -> int:
        return self.equipment + self.experience
