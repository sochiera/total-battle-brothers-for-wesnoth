"""Tests for the minimal immutable duchy state."""

from dataclasses import FrozenInstanceError

import pytest

from tbb.duchy import SUCCESSION_MORALE_PENALTY, Duchy
from tbb.party import Party
from tbb.settlement import Settlement
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


@pytest.mark.parametrize("hero", ["x"])
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


def test_duchy_settlements_and_parties_default_to_empty_tuples():
    duchy = Duchy("north", Unit())

    assert duchy.settlements == ()
    assert duchy.parties == ()


def test_duchy_preserves_owned_settlements_and_parties_as_tuples():
    settlement = Settlement("Keep", population=10, owner_id="north")
    party = Party(Unit(), owner_id="north")

    duchy = Duchy("north", Unit(), settlements=[settlement], parties=[party])

    assert duchy.settlements == (settlement,)
    assert duchy.settlements[0] is settlement
    assert duchy.parties == (party,)
    assert duchy.parties[0] is party
    assert isinstance(duchy.settlements, tuple)
    assert isinstance(duchy.parties, tuple)


def test_duchy_copies_settlement_and_party_collections():
    settlement = Settlement("Keep", population=10, owner_id="north")
    party = Party(Unit(), owner_id="north")
    settlements = [settlement]
    parties = [party]
    duchy = Duchy("north", Unit(), settlements=settlements, parties=parties)

    settlements.append(Settlement("Town", population=5, owner_id="north"))
    parties.append(Party(Unit(), owner_id="north"))

    assert duchy.settlements == (settlement,)
    assert duchy.parties == (party,)


def test_duchy_rejects_settlement_without_owner():
    with pytest.raises(ValueError):
        Duchy("north", Unit(), settlements=[Settlement("Keep", population=10)])


def test_duchy_rejects_party_owned_by_another_duchy():
    with pytest.raises(ValueError):
        Duchy("north", Unit(), parties=[Party(Unit(), owner_id="south")])


@pytest.mark.parametrize(
    ("collection_name", "member"),
    [("settlements", object()), ("parties", object())],
)
def test_duchy_rejects_invalid_collection_member_type(collection_name, member):
    with pytest.raises(TypeError):
        Duchy("north", Unit(), **{collection_name: [member]})


def test_duchy_settlements_are_immutable():
    duchy = Duchy("north", Unit())

    with pytest.raises((FrozenInstanceError, AttributeError)):
        duchy.settlements = ()


def test_succeed_promotes_heir_and_clears_heir():
    hero = Unit(training=2)
    heir = Unit(training=1)

    succeeded = Duchy("north", hero, heir=heir).succeed()

    assert succeeded.hero is heir
    assert succeeded.heir is None


@pytest.mark.parametrize("morale", [3, -3])
def test_succeed_applies_morale_penalty_without_a_floor(morale):
    succeeded = Duchy("north", Unit(), morale=morale, heir=Unit()).succeed()

    assert succeeded.morale == morale - SUCCESSION_MORALE_PENALTY


def test_succeed_preserves_identifier_and_owned_collections():
    settlement = Settlement("Keep", population=10, owner_id="north")
    party = Party(Unit(), owner_id="north")
    duchy = Duchy(
        "north",
        Unit(),
        heir=Unit(),
        settlements=[settlement],
        parties=[party],
    )

    succeeded = duchy.succeed()

    assert succeeded.duchy_id == duchy.duchy_id
    assert succeeded.settlements is duchy.settlements
    assert succeeded.parties is duchy.parties


def test_duchy_reports_when_it_has_a_hero():
    assert Duchy("north", Unit()).has_hero is True


def test_duchy_without_hero_is_allowed_and_reported():
    duchy = Duchy("north", None)

    assert duchy.hero is None
    assert duchy.has_hero is False


def test_duchy_without_hero_rejects_heir():
    with pytest.raises(ValueError):
        Duchy("north", None, heir=Unit())


@pytest.mark.parametrize("morale", [3, -3])
def test_succeed_without_heir_creates_hero_less_duchy(morale):
    succeeded = Duchy("north", Unit(), morale=morale).succeed()

    assert succeeded.hero is None
    assert succeeded.heir is None
    assert succeeded.has_hero is False
    assert succeeded.morale == morale - SUCCESSION_MORALE_PENALTY


def test_succeed_without_heir_preserves_identifier_and_owned_collections():
    settlement = Settlement("Keep", population=10, owner_id="north")
    party = Party(Unit(), owner_id="north")
    duchy = Duchy("north", Unit(), settlements=[settlement], parties=[party])

    succeeded = duchy.succeed()

    assert succeeded.duchy_id == duchy.duchy_id
    assert succeeded.settlements is duchy.settlements
    assert succeeded.parties is duchy.parties


def test_succeed_without_heir_does_not_mutate_original_duchy():
    hero = Unit(training=2)
    duchy = Duchy("north", hero, morale=3)

    duchy.succeed()

    assert duchy.hero is hero
    assert duchy.heir is None
    assert duchy.morale == 3


def test_succeed_does_not_mutate_original_duchy():
    hero = Unit(training=2)
    heir = Unit(training=1)
    duchy = Duchy("north", hero, morale=3, heir=heir)

    duchy.succeed()

    assert duchy.hero is hero
    assert duchy.heir is heir
    assert duchy.morale == 3


def test_duchy_without_hero_or_settlements_is_defeated():
    assert Duchy("north", None).is_defeated is True


def test_duchy_with_hero_and_without_settlements_is_not_defeated():
    assert Duchy("north", Unit()).is_defeated is False


def test_duchy_without_hero_but_with_settlement_is_not_defeated():
    settlement = Settlement("Keep", population=10, owner_id="north")

    assert Duchy("north", None, settlements=[settlement]).is_defeated is False


def test_duchy_with_hero_and_settlement_is_not_defeated():
    settlement = Settlement("Keep", population=10, owner_id="north")

    assert Duchy("north", Unit(), settlements=[settlement]).is_defeated is False


def test_parties_do_not_prevent_defeat_without_hero_or_settlements():
    party = Party(Unit(), owner_id="north")

    assert Duchy("north", None, parties=[party]).is_defeated is True
