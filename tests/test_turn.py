"""Tests for the immutable strategic calendar."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import Calendar, FARM, Region, Resources, Settlement, WorldMap
from tbb.turn import end_turn


def test_calendar_starts_at_first_month_and_turn_has_four_weeks():
    calendar = Calendar()

    assert (calendar.year, calendar.month) == (1, 1)
    assert calendar.weeks_per_turn == 4


def test_end_turn_advances_one_month_without_mutating_calendar():
    calendar = Calendar()

    advanced = end_turn(calendar)

    assert (advanced.year, advanced.month) == (1, 2)
    assert (calendar.year, calendar.month) == (1, 1)
    assert advanced is not calendar
    with pytest.raises(FrozenInstanceError):
        calendar.month = 2


def test_end_turn_wraps_thirteenth_month_to_next_year():
    advanced = end_turn(Calendar(year=1, month=13))

    assert (advanced.year, advanced.month) == (2, 1)


@pytest.mark.parametrize(
    ("year", "month"),
    [(0, 1), (-1, 1), (1, 0), (1, 14)],
)
def test_calendar_rejects_invalid_year_or_month(year, month):
    with pytest.raises(ValueError):
        Calendar(year=year, month=month)


def test_thirteen_turns_make_one_fifty_two_week_year():
    calendar = Calendar()
    elapsed_weeks = 0

    for _ in range(13):
        elapsed_weeks += calendar.weeks_per_turn
        calendar = end_turn(calendar)

    assert (calendar.year, calendar.month) == (2, 1)
    assert elapsed_weeks == 52


def test_public_api_exports_calendar():
    from tbb import Calendar as PublicCalendar

    assert PublicCalendar is Calendar


def test_strategic_turn_starts_with_settlements_and_given_state():
    from tbb.turn import StrategicTurn, TurnPhase

    world = WorldMap([Region("Vale")])
    calendar = Calendar(year=2, month=3)

    turn = StrategicTurn(world, calendar)

    assert turn.world is world
    assert turn.calendar is calendar
    assert turn.phase is TurnPhase.SETTLEMENTS


def test_entering_movement_ticks_settlements_exactly_once():
    from tbb.turn import StrategicTurn, TurnPhase

    vale = Region("Vale")
    settlement = Settlement(
        "Oakrest",
        population=1,
        active_buildings=(FARM,),
        storage=Resources(wheat=1, gold=0),
        capacity=3,
    )
    world = WorldMap([vale], settlements={vale: settlement})
    calendar = Calendar(year=2, month=3)

    advanced = StrategicTurn(world, calendar).advance_phase()

    assert advanced.phase is TurnPhase.MOVEMENT
    assert advanced.world.settlement_at(vale).population == 2
    assert advanced.calendar is calendar


def test_movement_to_battles_preserves_world_and_calendar():
    from tbb.turn import StrategicTurn, TurnPhase

    world = WorldMap([Region("Vale")])
    calendar = Calendar()
    turn = StrategicTurn(world, calendar, TurnPhase.MOVEMENT)

    advanced = turn.advance_phase()

    assert advanced.phase is TurnPhase.BATTLES
    assert advanced.world is world
    assert advanced.calendar is calendar


def test_battles_to_ended_advances_calendar_and_preserves_world():
    from tbb.turn import StrategicTurn, TurnPhase

    world = WorldMap([Region("Vale")])
    calendar = Calendar(year=1, month=13)
    turn = StrategicTurn(world, calendar, TurnPhase.BATTLES)

    advanced = turn.advance_phase()

    assert advanced.phase is TurnPhase.ENDED
    assert advanced.world is world
    assert advanced.calendar == Calendar(year=2, month=1)


def test_full_strategic_turn_sequence_advances_calendar_once():
    from tbb.turn import StrategicTurn, TurnPhase

    turn = StrategicTurn(WorldMap([Region("Vale")]), Calendar())
    phases = [turn.phase]
    calendars = [turn.calendar]

    for _ in range(3):
        turn = turn.advance_phase()
        phases.append(turn.phase)
        calendars.append(turn.calendar)

    assert phases == [
        TurnPhase.SETTLEMENTS,
        TurnPhase.MOVEMENT,
        TurnPhase.BATTLES,
        TurnPhase.ENDED,
    ]
    assert calendars == [Calendar(), Calendar(), Calendar(), Calendar(month=2)]


def test_ended_strategic_turn_cannot_advance():
    from tbb.turn import StrategicTurn, TurnPhase

    turn = StrategicTurn(WorldMap([]), Calendar(), TurnPhase.ENDED)

    with pytest.raises(ValueError):
        turn.advance_phase()


def test_strategic_turn_advance_returns_new_frozen_state():
    from tbb.turn import StrategicTurn, TurnPhase

    turn = StrategicTurn(WorldMap([]), Calendar())

    advanced = turn.advance_phase()

    assert advanced is not turn
    assert turn.phase is TurnPhase.SETTLEMENTS
    with pytest.raises(FrozenInstanceError):
        turn.phase = TurnPhase.MOVEMENT


def test_public_api_exports_strategic_turn_and_phase():
    from tbb import StrategicTurn, TurnPhase
    from tbb.turn import StrategicTurn as ModuleStrategicTurn
    from tbb.turn import TurnPhase as ModuleTurnPhase

    assert StrategicTurn is ModuleStrategicTurn
    assert TurnPhase is ModuleTurnPhase
