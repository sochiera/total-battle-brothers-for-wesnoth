"""Tests for the minimal immutable duchy state."""

from dataclasses import FrozenInstanceError

import pytest

from tbb.duchy import Duchy
from tbb.party import Party
from tbb.unit import Unit


def test_duchy_preserves_identifier_hero_and_morale():
    hero = Unit(training=2)

    duchy = Duchy("north", hero, morale=3)

    assert duchy.duchy_id == "north"
    assert duchy.hero is hero
    assert duchy.morale == 3


def test_duchy_morale_defaults_to_zero():
    assert Duchy("north", Unit()).morale == 0


def test_duchy_heir_defaults_to_none():
    assert Duchy("north", Unit()).heir is None


def test_duchy_preserves_heir_object():
    heir = Unit(training=1)

    duchy = Duchy("north", Unit(), heir=heir)

    assert duchy.heir is heir


@pytest.mark.parametrize("heir", ["x", 123])
def test_duchy_rejects_non_unit_heir(heir):
    with pytest.raises(TypeError):
        Duchy("north", Unit(), heir=heir)


def test_duchy_rejects_hero_as_own_heir():
    hero = Unit(training=1)

    with pytest.raises(ValueError):
        Duchy("north", hero, heir=hero)


def test_duchy_accepts_equal_but_distinct_heir():
    hero = Unit(training=1)
    heir = Unit(training=1)

    duchy = Duchy("north", hero, heir=heir)

    assert duchy.hero == duchy.heir
    assert duchy.hero is not duchy.heir


def test_duchy_rejects_empty_identifier():
    with pytest.raises(ValueError):
        Duchy("", Unit())


def test_duchy_rejects_non_text_identifier():
    with pytest.raises(TypeError):
        Duchy(123, Unit())


@pytest.mark.parametrize("hero", ["x", None])
def test_duchy_rejects_non_unit_hero(hero):
    with pytest.raises(TypeError):
        Duchy("north", hero)


@pytest.mark.parametrize("morale", [True, 1.5, "5"])
def test_duchy_rejects_non_integer_morale(morale):
    with pytest.raises(TypeError):
        Duchy("north", Unit(), morale)


def test_duchy_allows_negative_morale():
    assert Duchy("north", Unit(), morale=-4).morale == -4


def test_duchy_is_immutable():
    duchy = Duchy("north", Unit())

    with pytest.raises((FrozenInstanceError, AttributeError)):
        duchy.morale = 1


def test_duchy_identifier_is_party_owner_identifier():
    duchy = Duchy("north", Unit())

    party = Party(duchy.hero, owner_id=duchy.duchy_id)

    assert party.owner_id == duchy.duchy_id
