"""Immutable game-over state across duchies."""

from dataclasses import dataclass
from typing import Iterable

from tbb.duchy import Duchy


@dataclass(frozen=True)
class GameState:
    """Hold the duchies in a game and expose its victory state."""

    duchies: tuple[Duchy, ...]

    def __init__(self, duchies: Iterable[Duchy]) -> None:
        copied = tuple(duchies)
        if any(not isinstance(duchy, Duchy) for duchy in copied):
            raise TypeError("game duchies must be Duchies")
        duchy_ids = [duchy.duchy_id for duchy in copied]
        if len(duchy_ids) != len(set(duchy_ids)):
            raise ValueError("game duchy identifiers must be unique")
        object.__setattr__(self, "duchies", copied)

    @property
    def contenders(self) -> tuple[Duchy, ...]:
        """Return undefeated duchies in their original order."""
        return tuple(duchy for duchy in self.duchies if not duchy.is_defeated)

    @property
    def is_over(self) -> bool:
        """Report whether at most one undefeated duchy remains."""
        return len(self.contenders) <= 1

    @property
    def winner(self) -> Duchy | None:
        """Return the sole undefeated duchy, if there is exactly one."""
        contenders = self.contenders
        return contenders[0] if len(contenders) == 1 else None
