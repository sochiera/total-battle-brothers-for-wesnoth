"""Minimal immutable duchy state."""

from dataclasses import dataclass
from typing import Iterable

from tbb.party import Party
from tbb.settlement import Settlement
from tbb.unit import Unit


SUCCESSION_MORALE_PENALTY = 2


@dataclass(frozen=True)
class Duchy:
    """Identify a duchy and hold its people and owned strategic entities."""

    duchy_id: str
    hero: Unit | None
    morale: int = 0
    heir: Unit | None = None
    settlements: tuple[Settlement, ...] = ()
    parties: tuple[Party, ...] = ()

    def __init__(
        self,
        duchy_id: str,
        hero: Unit | None,
        morale: int = 0,
        heir: Unit | None = None,
        settlements: Iterable[Settlement] = (),
        parties: Iterable[Party] = (),
    ) -> None:
        object.__setattr__(self, "duchy_id", duchy_id)
        object.__setattr__(self, "hero", hero)
        object.__setattr__(self, "morale", morale)
        object.__setattr__(self, "heir", heir)
        object.__setattr__(self, "settlements", tuple(settlements))
        object.__setattr__(self, "parties", tuple(parties))
        self.__post_init__()

    def __post_init__(self) -> None:
        if not isinstance(self.duchy_id, str):
            raise TypeError("duchy_id must be text")
        if self.duchy_id == "":
            raise ValueError("duchy_id cannot be empty")
        if self.hero is not None and not isinstance(self.hero, Unit):
            raise TypeError("duchy hero must be a Unit or None")
        if type(self.morale) is not int:
            raise TypeError("duchy morale must be an integer")
        if self.heir is not None and not isinstance(self.heir, Unit):
            raise TypeError("duchy heir must be a Unit or None")
        if self.hero is None and self.heir is not None:
            raise ValueError("duchy without a hero cannot have an heir")
        if self.hero is not None and self.heir is self.hero:
            raise ValueError("duchy heir cannot be its hero")
        if any(not isinstance(item, Settlement) for item in self.settlements):
            raise TypeError("duchy settlements must be Settlements")
        if any(not isinstance(item, Party) for item in self.parties):
            raise TypeError("duchy parties must be Parties")
        if any(item.owner_id != self.duchy_id for item in self.settlements):
            raise ValueError("duchy settlements must be owned by the duchy")
        if any(item.owner_id != self.duchy_id for item in self.parties):
            raise ValueError("duchy parties must be owned by the duchy")

    @property
    def has_hero(self) -> bool:
        """Report whether the duchy currently has a living hero."""
        return self.hero is not None

    def succeed(self) -> "Duchy":
        """Resolve the hero's death by promoting an heir when available."""
        return Duchy(
            duchy_id=self.duchy_id,
            hero=self.heir,
            morale=self.morale - SUCCESSION_MORALE_PENALTY,
            settlements=self.settlements,
            parties=self.parties,
        )
