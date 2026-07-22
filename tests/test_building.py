"""Tests for building definitions."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import BARRACKS, Building, FARM, MARKET, Resources, SMITH


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


def test_building_output_defaults_to_zero_resources():
    assert Building("Mill", staff=2).output == Resources(0, 0)


def test_catalog_contains_farm_and_market_with_outputs():
    assert FARM.staff == 1
    assert FARM.output == Resources(wheat=3, gold=0)
    assert MARKET.staff == 1
    assert MARKET.output == Resources(wheat=0, gold=2)


def test_catalog_contains_barracks_with_one_staff_and_zero_output():
    assert BARRACKS.name == "Barracks"
    assert BARRACKS.staff == 1
    assert BARRACKS.output == Resources(0, 0)

