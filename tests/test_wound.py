"""Tests for temporary and permanent wounds."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import BRUISE, MAIMED, Wound


def test_wound_is_immutable():
    wound = Wound("Scratch", accuracy_mod=-1, defense_mod=0, duration_months=1)

    with pytest.raises(FrozenInstanceError):
        wound.accuracy_mod = 0


@pytest.mark.parametrize(
    "values",
    [
        {"accuracy_mod": 1, "defense_mod": 0},
        {"accuracy_mod": 0, "defense_mod": 1},
    ],
)
def test_wound_rejects_positive_modifiers(values):
    with pytest.raises(ValueError):
        Wound("Invalid", duration_months=1, **values)


@pytest.mark.parametrize("duration", [0, -1, 1.5, True])
def test_wound_rejects_non_positive_or_non_integer_duration(duration):
    with pytest.raises(ValueError):
        Wound("Invalid", accuracy_mod=0, defense_mod=0, duration_months=duration)


def test_catalog_contains_temporary_bruise_and_permanent_maiming():
    assert BRUISE == Wound("Bruise", -1, -1, 2)
    assert MAIMED == Wound("Maimed", -2, -2, None)
    assert BRUISE.duration_months == 2
    assert MAIMED.duration_months is None
