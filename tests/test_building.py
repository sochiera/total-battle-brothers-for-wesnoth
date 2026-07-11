"""Tests for building definitions."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import Building, SMITH


def test_building_has_name_and_staff():
    building = Building("Mill", staff=2)

    assert building.name == "Mill"
    assert building.staff == 2


def test_building_is_immutable():
    building = Building("Mill", staff=2)

    with pytest.raises(FrozenInstanceError):
        building.staff = 3


def test_negative_staff_is_rejected():
    with pytest.raises(ValueError):
        Building("Mill", staff=-1)


def test_catalog_contains_smith_with_one_staff():
    assert SMITH.staff == 1

