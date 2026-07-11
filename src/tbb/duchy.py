"""Minimal immutable duchy state."""

from dataclasses import dataclass

from tbb.unit import Unit


@dataclass(frozen=True)
class Duchy:
    """Identify a duchy and hold its single hero and signed morale."""

    duchy_id: str
    hero: Unit
    morale: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.duchy_id, str):
            raise TypeError("duchy_id must be text")
        if self.duchy_id == "":
            raise ValueError("duchy_id cannot be empty")
        if not isinstance(self.hero, Unit):
            raise TypeError("duchy hero must be a Unit")
        if type(self.morale) is not int:
            raise TypeError("duchy morale must be an integer")
