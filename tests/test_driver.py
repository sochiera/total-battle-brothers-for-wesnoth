"""Tests for headless game driver transitions."""

from tbb.driver import resolve_hero_survival
from tbb.duchy import SUCCESSION_MORALE_PENALTY, Duchy
from tbb.party import Party
from tbb.unit import Unit
from tbb.world import Region, WorldMap


def test_lost_duchy_party_triggers_immutable_succession():
    region = Region("March")
    hero = Unit(training=2)
    heir = Unit(training=1)
    party = Party(hero, owner_id="north")
    duchy = Duchy("north", hero, morale=3, heir=heir, parties=(party,))
    world_before = WorldMap((region,), parties={region: party})
    world_after = WorldMap((region,))

    resolved = resolve_hero_survival(duchy, world_before, world_after)

    assert resolved.hero is heir
    assert resolved.heir is None
    assert resolved.morale == 3 - SUCCESSION_MORALE_PENALTY
    assert duchy.hero is hero
    assert duchy.heir is heir
    assert duchy.morale == 3
    assert world_before.party_at(region) is party
    assert world_after.party_at(region) is None


def test_lost_last_duchy_party_without_heir_leaves_no_hero():
    region = Region("March")
    hero = Unit(training=2)
    party = Party(hero, owner_id="north")
    duchy = Duchy("north", hero, morale=3, parties=(party,))
    world_before = WorldMap((region,), parties={region: party})
    world_after = WorldMap((region,))

    resolved = resolve_hero_survival(duchy, world_before, world_after)

    assert resolved.hero is None
    assert resolved.morale == 3 - SUCCESSION_MORALE_PENALTY
    assert duchy.hero is hero
    assert duchy.morale == 3


def test_no_duchy_party_before_or_after_keeps_hero_alive():
    region = Region("Keep")
    hero = Unit(training=2)
    duchy = Duchy("north", hero, morale=3)
    world_before = WorldMap((region,))
    world_after = WorldMap((region,))

    resolved = resolve_hero_survival(duchy, world_before, world_after)

    assert resolved is duchy
    assert resolved.hero is hero
    assert resolved.morale == 3


def test_moved_duchy_party_keeps_hero_alive():
    source = Region("March")
    destination = Region("Keep")
    hero = Unit(training=2)
    party = Party(hero, owner_id="north")
    duchy = Duchy("north", hero, morale=3, parties=(party,))
    world_before = WorldMap(
        (source, destination), parties={source: party}
    )
    world_after = WorldMap(
        (source, destination), parties={destination: party}
    )

    resolved = resolve_hero_survival(duchy, world_before, world_after)

    assert resolved is duchy
    assert world_before.party_at(source) is party
    assert world_before.party_at(destination) is None
    assert world_after.party_at(source) is None
    assert world_after.party_at(destination) is party


def test_one_remaining_duchy_party_keeps_hero_alive():
    first_region = Region("North March")
    second_region = Region("South March")
    hero = Unit(training=2)
    first_party = Party(hero, owner_id="north")
    second_party = Party(Unit(training=1), owner_id="north")
    duchy = Duchy(
        "north", hero, morale=3, parties=(first_party, second_party)
    )
    world_before = WorldMap(
        (first_region, second_region),
        parties={first_region: first_party, second_region: second_party},
    )
    world_after = WorldMap(
        (first_region, second_region), parties={second_region: second_party}
    )

    resolved = resolve_hero_survival(duchy, world_before, world_after)

    assert resolved is duchy
    assert world_before.party_at(first_region) is first_party
    assert world_after.party_at(second_region) is second_party


def test_other_owners_parties_do_not_hide_loss_of_duchy_party():
    own_region = Region("North March")
    foreign_region = Region("South March")
    hero = Unit(training=2)
    heir = Unit(training=1)
    own_party = Party(hero, owner_id="north")
    foreign_party = Party(Unit(training=2), owner_id="south")
    duchy = Duchy(
        "north", hero, morale=3, heir=heir, parties=(own_party,)
    )
    world_before = WorldMap(
        (own_region, foreign_region),
        parties={own_region: own_party, foreign_region: foreign_party},
    )
    world_after = WorldMap(
        (own_region, foreign_region), parties={foreign_region: foreign_party}
    )

    resolved = resolve_hero_survival(duchy, world_before, world_after)

    assert resolved.hero is heir
    assert resolved.morale == 3 - SUCCESSION_MORALE_PENALTY
    assert world_before.party_at(foreign_region) is foreign_party
    assert world_after.party_at(foreign_region) is foreign_party
