"""Tests for headless game driver transitions."""

import tbb.ai as ai

from tbb.ai import take_duchy_turn
from tbb.driver import resolve_hero_survival, run_headless_game
from tbb.duchy import SUCCESSION_MORALE_PENALTY, Duchy
from tbb.game import GameState, create_headless_game
from tbb.party import Party
from tbb.rng import Rng
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.world import Region, WorldMap


def test_one_turn_threads_real_ai_actions_through_duchies_immutably():
    world, game = create_headless_game()
    world_snapshot = (
        world.regions,
        dict(world.settlements),
        dict(world.parties),
        game.duchies,
    )
    expected_world, expected_game = create_headless_game()
    expected_rng = Rng(17)
    for duchy in expected_game.duchies:
        expected_world = take_duchy_turn(expected_world, duchy, expected_rng)

    result_world, result_game = run_headless_game(
        world, game, Rng(17), max_turns=1
    )

    assert result_world == expected_world
    assert result_world != world
    assert result_game is not game
    assert result_game == game.sync_from_world(result_world)
    assert world_snapshot == (
        world.regions,
        dict(world.settlements),
        dict(world.parties),
        game.duchies,
    )


def test_one_turn_delegates_to_live_ai_api_in_duchy_order(monkeypatch):
    north, fallen, south = map(Region, ("North", "Fallen", "South"))
    north_keep = Settlement("North Keep", 1, owner_id="north")
    fallen_keep = Settlement("Fallen Keep", 1, owner_id="fallen")
    south_keep = Settlement("South Keep", 1, owner_id="south")
    world = WorldMap(
        (north, fallen, south),
        settlements={
            north: north_keep,
            fallen: fallen_keep,
            south: south_keep,
        },
    )
    game = GameState(
        (
            Duchy("north", Unit(), settlements=(north_keep,)),
            Duchy("fallen", None),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )
    snapshot = (
        world.regions,
        dict(world.settlements),
        dict(world.parties),
        game.duchies,
    )
    real_take_duchy_turn = ai.take_duchy_turn
    calls = []

    def recording_take_duchy_turn(current_world, duchy, rng):
        next_world = real_take_duchy_turn(current_world, duchy, rng)
        calls.append((current_world, duchy, next_world))
        return next_world

    monkeypatch.setattr(ai, "take_duchy_turn", recording_take_duchy_turn)

    result_world, result_game = run_headless_game(
        world, game, Rng(17), max_turns=1
    )

    assert [call[1].duchy_id for call in calls] == ["north", "south"]
    assert calls[0][0] is world
    assert calls[1][0] is calls[0][2]
    assert result_world is calls[1][2]
    assert result_world.settlement_at(north).garrison == (Unit(),)
    assert result_world.settlement_at(fallen).garrison == ()
    assert result_world.settlement_at(south).garrison == (Unit(),)
    assert result_game is not game
    assert result_game == game.sync_from_world(result_world)
    assert snapshot == (
        world.regions,
        dict(world.settlements),
        dict(world.parties),
        game.duchies,
    )


def test_conquest_syncs_game_and_skips_newly_defeated_duchy(monkeypatch):
    north, south = map(Region, ("North", "South"))
    north_keep = Settlement("North Keep", 1, owner_id="north")
    south_keep = Settlement("South Keep", 1, owner_id="south")
    world = WorldMap(
        (north, south),
        settlements={north: north_keep, south: south_keep},
    )
    game = GameState(
        (
            Duchy("north", Unit(), settlements=(north_keep,)),
            Duchy("south", None, settlements=(south_keep,)),
        )
    )
    calls = []

    def conquer_south(current_world, duchy, rng):
        calls.append(duchy.duchy_id)
        if duchy.duchy_id != "north":
            return current_world
        conquered_keep = Settlement("South Keep", 1, owner_id="north")
        return WorldMap(
            current_world.regions,
            current_world.connections,
            settlements={north: north_keep, south: conquered_keep},
            parties=current_world.parties,
        )

    monkeypatch.setattr(ai, "take_duchy_turn", conquer_south)

    result_world, result_game = run_headless_game(
        world, game, Rng(17), max_turns=1
    )

    result_by_id = {duchy.duchy_id: duchy for duchy in result_game.duchies}
    assert calls == ["north"]
    assert result_game is not game
    assert result_by_id["north"].settlements == tuple(
        result_world.settlements.values()
    )
    assert result_by_id["south"].settlements == ()
    assert result_by_id["south"].is_defeated is True
    assert dict(world.settlements) == {north: north_keep, south: south_keep}
    assert game.duchies[1].settlements == (south_keep,)


def test_lost_party_during_real_ai_turn_promotes_heir_before_world_sync():
    camp, keep = map(Region, ("North Camp", "South Keep"))
    hero = Unit(equipment=1)
    heir = Unit(training=1)
    attacking_party = Party(hero, owner_id="north")
    south_keep = Settlement(
        "South Keep",
        4,
        occupied=1,
        garrison=(Unit(training=5, equipment=12),),
        owner_id="south",
    )
    world = WorldMap(
        (camp, keep),
        ((camp, keep),),
        settlements={keep: south_keep},
        parties={camp: attacking_party},
    )
    game = GameState(
        (
            Duchy(
                "north",
                hero,
                morale=3,
                heir=heir,
                parties=(attacking_party,),
            ),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )
    snapshot = (dict(world.settlements), dict(world.parties), game.duchies)

    result_world, result_game = run_headless_game(
        world, game, Rng(4), max_turns=1
    )

    north = next(
        duchy for duchy in result_game.duchies if duchy.duchy_id == "north"
    )
    assert result_world.party_at(camp) is None
    assert north.hero is heir
    assert north.heir is None
    assert north.morale == 3 - SUCCESSION_MORALE_PENALTY
    assert north.parties == ()
    assert north.settlements == ()
    assert snapshot == (
        dict(world.settlements),
        dict(world.parties),
        game.duchies,
    )


def test_exit_conditions_return_typed_exact_unchanged_inputs():
    region = Region("Last Keep")
    finished_world = WorldMap((region,))
    finished_game = GameState((Duchy("north", Unit(training=2)),))
    finished_snapshot = (
        finished_world.regions,
        dict(finished_world.settlements),
        dict(finished_world.parties),
        finished_game.duchies,
    )

    finished_result = run_headless_game(
        finished_world, finished_game, Rng(7)
    )

    assert isinstance(finished_result, tuple)
    assert isinstance(finished_result[0], WorldMap)
    assert isinstance(finished_result[1], GameState)
    assert finished_result[0] is finished_world
    assert finished_result[1] is finished_game
    assert finished_snapshot == (
        finished_world.regions,
        dict(finished_world.settlements),
        dict(finished_world.parties),
        finished_game.duchies,
    )

    running_world = WorldMap((Region("North"), Region("South")))
    running_game = GameState(
        (
            Duchy("north", Unit(training=2)),
            Duchy("south", Unit(training=2)),
        )
    )
    running_snapshot = (running_world.regions, running_game.duchies)

    running_result = run_headless_game(
        running_world, running_game, Rng(11), max_turns=0
    )

    assert running_game.is_over is False
    assert running_result[0] is running_world
    assert running_result[1] is running_game
    assert running_snapshot == (running_world.regions, running_game.duchies)


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


def test_world_before_drives_succession_when_duchy_parties_are_stale():
    region = Region("March")
    hero = Unit(training=2)
    heir = Unit(training=1)
    deployed_party = Party(hero, owner_id="north")
    duchy = Duchy("north", hero, morale=3, heir=heir, parties=())
    world_before = WorldMap((region,), parties={region: deployed_party})
    world_after = WorldMap((region,))

    resolved = resolve_hero_survival(duchy, world_before, world_after)

    assert duchy.parties == ()
    assert resolved.hero is heir
    assert resolved.heir is None
    assert resolved.morale == 3 - SUCCESSION_MORALE_PENALTY
    assert world_before.party_at(region) is deployed_party
    assert world_after.party_at(region) is None
