"""Immutable strategic calendar and turn-phase transitions."""

from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import ClassVar

from tbb.battle import HexBattle
from tbb.world import Region, WorldMap


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


class TurnPhase(Enum):
    """The ordered phases of one strategic turn."""

    SETTLEMENTS = auto()
    MOVEMENT = auto()
    BATTLES = auto()
    ENDED = auto()


@dataclass(frozen=True)
class StrategicTurn:
    """Immutable world, calendar, and phase state for one strategic turn."""

    world: WorldMap
    calendar: Calendar
    phase: TurnPhase = TurnPhase.SETTLEMENTS

    def move_party(
        self, source: Region, destination: Region, move_points: int
    ) -> "StrategicTurn":
        """Move a party during the movement phase."""
        if self.phase is not TurnPhase.MOVEMENT:
            raise ValueError("party movement is only allowed in the movement phase")
        return replace(
            self,
            world=self.world.move_party(source, destination, move_points),
        )

    def start_battle(self, source: Region, destination: Region) -> HexBattle:
        """Start a party battle during the battles phase."""
        if self.phase is not TurnPhase.BATTLES:
            raise ValueError("battles can only start in the battles phase")
        return self.world.start_battle(source, destination)

    def start_settlement_battle(
        self, source: Region, destination: Region
    ) -> HexBattle:
        """Start a settlement battle during the battles phase."""
        if self.phase is not TurnPhase.BATTLES:
            raise ValueError("battles can only start in the battles phase")
        return self.world.start_settlement_battle(source, destination)

    def advance_phase(self) -> "StrategicTurn":
        """Return the state after completing the current phase."""
        if self.phase is TurnPhase.SETTLEMENTS:
            return replace(
                self,
                world=self.world.tick_settlements(),
                phase=TurnPhase.MOVEMENT,
            )
        if self.phase is TurnPhase.MOVEMENT:
            return replace(self, phase=TurnPhase.BATTLES)
        if self.phase is TurnPhase.BATTLES:
            return replace(
                self,
                calendar=end_turn(self.calendar),
                phase=TurnPhase.ENDED,
            )
        raise ValueError("an ended strategic turn cannot advance")
