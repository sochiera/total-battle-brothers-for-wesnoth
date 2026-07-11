"""Immutable building definitions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Building:
    """A building type with its fixed population requirement."""

    name: str
    staff: int

    def __post_init__(self) -> None:
        if self.staff < 0:
            raise ValueError("staff cannot be negative")


SMITH = Building("Smith", staff=1)

