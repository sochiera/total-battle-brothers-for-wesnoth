"""Immutable unit quality pillars and their derived combat statistics."""

from dataclasses import dataclass, replace

from tbb.progression import investment_for_level, pillar_level
from tbb.wound import Wound


@dataclass(frozen=True)
class Unit:
    """Represent a unit through independent, non-negative quality pillars."""

    training: int = 0
    equipment: int = 0
    experience: int = 0
    ranged_range: int = 0
    wounds: tuple[Wound, ...] = ()
    stunned: bool = False
    training_progress: int = 0
    equipment_progress: int = 0

    def __post_init__(self) -> None:
        """Reject pillar values below zero."""
        if self.training < 0 or self.equipment < 0 or self.experience < 0:
            raise ValueError("unit quality pillars cannot be negative")
        if not 0 <= self.training_progress <= self.training:
            raise ValueError("training progress must be between zero and training")
        if not 0 <= self.equipment_progress <= self.equipment:
            raise ValueError("equipment progress must be between zero and equipment")
        if self.ranged_range < 0 or self.ranged_range == 1:
            raise ValueError("ranged range must be zero or at least two")
        object.__setattr__(self, "wounds", tuple(self.wounds))

    def train(self, months: int) -> "Unit":
        """Return this unit after investing non-negative months in training."""
        if months < 0:
            raise ValueError("training months cannot be negative")
        if months == 0:
            return self

        total = (
            investment_for_level(self.training)
            + self.training_progress
            + months
        )
        training = pillar_level(total)
        return replace(
            self,
            training=training,
            training_progress=total - investment_for_level(training),
        )

    def equip(self, investment: int) -> "Unit":
        """Return this unit after a non-negative equipment investment."""
        if investment < 0:
            raise ValueError("equipment investment cannot be negative")
        if investment == 0:
            return self

        total = (
            investment_for_level(self.equipment)
            + self.equipment_progress
            + investment
        )
        equipment = pillar_level(total)
        return replace(
            self,
            equipment=equipment,
            equipment_progress=total - investment_for_level(equipment),
        )

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
