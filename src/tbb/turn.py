"""Immutable strategic calendar and turn transition."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Calendar:
    """The current year and month in the thirteen-month calendar."""

    year: int = 1
    month: int = 1
    weeks_per_turn: ClassVar[int] = 4

    def __post_init__(self) -> None:
        if self.year < 1:
            raise ValueError("calendar year must be positive")
        if not 1 <= self.month <= 13:
            raise ValueError("calendar month must be between 1 and 13")


def end_turn(calendar: Calendar) -> Calendar:
    """Return the calendar after exactly one four-week month."""

    if calendar.month == 13:
        return Calendar(year=calendar.year + 1, month=1)
    return Calendar(year=calendar.year, month=calendar.month + 1)
