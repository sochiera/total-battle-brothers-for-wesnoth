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
