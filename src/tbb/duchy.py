"""Minimal immutable duchy state."""

from dataclasses import dataclass

from tbb.unit import Unit


@dataclass(frozen=True)
class Duchy:
    """Identify a duchy and hold its hero, morale, and optional heir."""

    duchy_id: str
    hero: Unit
    morale: int = 0
    heir: Unit | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.duchy_id, str):
            raise TypeError("duchy_id must be text")
        if self.duchy_id == "":
            raise ValueError("duchy_id cannot be empty")
        if not isinstance(self.hero, Unit):
            raise TypeError("duchy hero must be a Unit")
        if type(self.morale) is not int:
            raise TypeError("duchy morale must be an integer")
        if self.heir is not None and not isinstance(self.heir, Unit):
            raise TypeError("duchy heir must be a Unit or None")
        if self.heir is self.hero:
            raise ValueError("duchy heir cannot be its hero")
