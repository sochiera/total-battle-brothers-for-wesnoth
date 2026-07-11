"""Tests for the immutable strategic party composition."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import Party, Unit


def test_party_accepts_hero_with_zero_or_twelve_subordinates():
    hero = Unit(training=3)

    empty_party = Party(hero)
    full_party = Party(hero, [Unit(experience=i) for i in range(12)])

    assert empty_party.hero is hero
    assert empty_party.units == ()
    assert full_party.hero is hero
    assert len(full_party.units) == 12
    assert hero not in full_party.units


def test_party_owner_id_defaults_to_none_and_preserves_explicit_value():
    assert Party(Unit()).owner_id is None
    assert Party(Unit(), owner_id="north").owner_id == "north"


@pytest.mark.parametrize("owner_id", ["", 1, object()])
def test_party_rejects_empty_or_non_text_owner_id(owner_id):
    with pytest.raises((TypeError, ValueError)):
        Party(Unit(), owner_id=owner_id)


@pytest.mark.parametrize("hero", [None, "not a unit"])
def test_party_rejects_missing_or_invalid_hero(hero):
    with pytest.raises((TypeError, ValueError)):
        Party(hero)


def test_party_requires_a_hero_argument():
    with pytest.raises(TypeError):
        Party()


def test_party_rejects_thirteen_or_invalid_subordinates():
    with pytest.raises(ValueError):
        Party(Unit(), [Unit() for _ in range(13)])

    with pytest.raises(TypeError):
        Party(Unit(), [Unit(), object()])


def test_party_copies_units_to_tuple_and_is_immutable():
    hero = Unit()
    subordinate = Unit(training=1)
    source = [subordinate]
    party = Party(hero, source)

    source.append(Unit())

    assert party.units == (subordinate,)
    assert isinstance(party.units, tuple)
    with pytest.raises(FrozenInstanceError):
        party.hero = Unit()
    with pytest.raises(FrozenInstanceError):
        party.units = ()
    with pytest.raises(FrozenInstanceError):
        party.owner_id = "changed"


def test_public_api_exports_party():
    from tbb import Party as PublicParty

    assert PublicParty is Party
