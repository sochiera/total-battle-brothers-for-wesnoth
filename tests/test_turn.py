"""Tests for the immutable strategic calendar."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import Calendar
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
