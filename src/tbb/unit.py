"""Immutable unit quality pillars and their derived combat statistics."""

from dataclasses import dataclass

from tbb.wound import Wound


@dataclass(frozen=True)
class Unit:
    """Represent a unit through independent, non-negative quality pillars."""

    training: int = 0
    equipment: int = 0
    experience: int = 0
    ranged_range: int = 0
    wounds: tuple[Wound, ...] = ()

    def __post_init__(self) -> None:
        """Reject pillar values below zero."""
        if self.training < 0 or self.equipment < 0 or self.experience < 0:
            raise ValueError("unit quality pillars cannot be negative")
        if self.ranged_range < 0 or self.ranged_range == 1:
            raise ValueError("ranged range must be zero or at least two")
        object.__setattr__(self, "wounds", tuple(self.wounds))

    @property
    def hp(self) -> int:
        return 10 + self.training

    @property
    def accuracy(self) -> int:
        return max(0, self.training + self.experience + sum(
            wound.accuracy_mod for wound in self.wounds
        ))

    @property
    def damage(self) -> int:
        return self.equipment

    @property
    def defense(self) -> int:
        return max(0, self.equipment + self.experience + sum(
            wound.defense_mod for wound in self.wounds
        ))
