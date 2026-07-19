"""Tests for headless game driver transitions."""

import tbb.ai as ai

from tbb.ai import take_duchy_turn
from tbb.driver import resolve_hero_survival, run_headless_game
from tbb.duchy import SUCCESSION_MORALE_PENALTY, Duchy
from tbb.game import GameState, create_headless_game
from tbb.party import Party
from tbb.resources import Resources
from tbb.rng import Rng
from tbb.settlement import Settlement
from tbb.turn import Calendar
from tbb.unit import Unit
from tbb.world import Region, WorldMap


def test_monthly_tick_precedes_recruitment_and_syncs_the_grown_settlement():
    north, south = map(Region, ("North", "South"))
    veteran = Unit(training=1)
    north_keep = Settlement(
        "North Keep",
        1,
        occupied=1,
        storage=Resources(wheat=2, gold=0),
        garrison=(veteran,),
        owner_id="north",
    )
    south_keep = Settlement("South Keep", 1, owner_id="south")
    world = WorldMap(
        (north, south), settlements={north: north_keep, south: south_keep}
    )
    game = GameState(
        (
            Duchy("north", Unit(), settlements=(north_keep,)),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )

    result_world, result_game, _ = run_headless_game(
        world, game, Rng(17), max_turns=1
    )

    grown_keep = result_world.settlement_at(north)
    north_duchy = next(
        duchy for duchy in result_game.duchies if duchy.duchy_id == "north"
    )
    assert grown_keep.population == 2
    assert grown_keep.storage == Resources(wheat=1, gold=0)
    assert grown_keep.occupied == 2
    assert grown_keep.garrison == (veteran, Unit())
    assert north_duchy.settlements == (grown_keep,)
    assert world.settlement_at(north) is north_keep
    assert game.duchies[0].settlements == (north_keep,)


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
    expected_world = expected_world.tick_settlements()
    expected_game = expected_game.sync_from_world(expected_world)
    for duchy_id in tuple(duchy.duchy_id for duchy in expected_game.duchies):
        duchy = next(
            duchy
            for duchy in expected_game.duchies
            if duchy.duchy_id == duchy_id
        )
        world_before = expected_world
        expected_world = take_duchy_turn(
            expected_world, duchy, expected_rng
        )
        resolved = resolve_hero_survival(
            duchy, world_before, expected_world
        )
        expected_game = GameState(
            resolved if current.duchy_id == duchy_id else current
            for current in expected_game.duchies
        ).sync_from_world(expected_world)

    result_world, result_game, _ = run_headless_game(
        world, game, Rng(17), max_turns=1
    )

    assert result_world == expected_world
    assert result_world != world
    assert result_game is not game
    assert result_game == expected_game
    assert world_snapshot == (
        world.regions,
        dict(world.settlements),
        dict(world.parties),
        game.duchies,
    )


def test_one_turn_delegates_to_live_ai_api_in_duchy_order(monkeypatch):
    north, fallen, south = map(Region, ("North", "Fallen", "South"))
    north_keep = Settlement("North Keep", 1, owner_id="north")
    fallen_keep = Settlement("Fallen Keep", 1)
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

    result_world, result_game, _ = run_headless_game(
        world, game, Rng(17), max_turns=1
    )

    assert [call[1].duchy_id for call in calls] == ["north", "south"]
    assert calls[0][0] == world.tick_settlements()
    assert calls[0][0] is not world
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

    result_world, result_game, _ = run_headless_game(
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


def test_turn_loop_stops_immediately_after_a_later_turn_ends_game(monkeypatch):
    north, south = map(Region, ("North", "South"))
    north_keep = Settlement("North Keep", 1, owner_id="north")
    south_keep = Settlement("South Keep", 1, owner_id="south")
    world = WorldMap(
        (north, south), settlements={north: north_keep, south: south_keep}
    )
    game = GameState(
        (
            Duchy("north", Unit(), settlements=(north_keep,)),
            Duchy("south", None, settlements=(south_keep,)),
        )
    )
    calls = []

    def conquer_on_norths_second_turn(current_world, duchy, rng):
        calls.append(duchy.duchy_id)
        if calls.count("north") < 2:
            return current_world
        conquered_keep = Settlement("South Keep", 1, owner_id="north")
        return WorldMap(
            current_world.regions,
            current_world.connections,
            settlements={north: north_keep, south: conquered_keep},
            parties=current_world.parties,
        )

    monkeypatch.setattr(ai, "take_duchy_turn", conquer_on_norths_second_turn)

    result_world, result_game, _ = run_headless_game(
        world, game, Rng(17), max_turns=5
    )

    assert calls == ["north", "south", "north"]
    assert result_world.settlement_at(south).owner_id == "north"
    assert result_game.is_over is True
    assert result_game.winner.duchy_id == "north"


def test_turn_ending_during_first_duchy_action_advances_calendar_once(monkeypatch):
    north, south = map(Region, ("North", "South"))
    north_keep = Settlement("North Keep", 1, owner_id="north")
    south_keep = Settlement("South Keep", 1, owner_id="south")
    world = WorldMap(
        (north, south), settlements={north: north_keep, south: south_keep}
    )
    game = GameState(
        (
            Duchy("north", Unit(), settlements=(north_keep,)),
            Duchy("south", None, settlements=(south_keep,)),
        )
    )
    starting_calendar = Calendar(year=7, month=13)
    calls = []

    def conquer_south(current_world, duchy, rng):
        calls.append(duchy.duchy_id)
        conquered_keep = Settlement("South Keep", 1, owner_id="north")
        return WorldMap(
            current_world.regions,
            current_world.connections,
            settlements={
                north: current_world.settlement_at(north),
                south: conquered_keep,
            },
            parties=current_world.parties,
        )

    monkeypatch.setattr(ai, "take_duchy_turn", conquer_south)

    _, result_game, result_calendar = run_headless_game(
        world,
        game,
        Rng(17),
        max_turns=5,
        calendar=starting_calendar,
    )

    # A turn is complete even when the game ends before every duchy acts.
    assert calls == ["north"]
    assert result_game.is_over is True
    assert result_calendar == Calendar(year=8, month=1)
    assert starting_calendar == Calendar(year=7, month=13)


def test_positive_safety_limit_runs_every_active_duchy_each_turn(monkeypatch):
    north, south = map(Region, ("North", "South"))
    north_keep = Settlement("North Keep", 1, owner_id="north")
    south_keep = Settlement("South Keep", 1, owner_id="south")
    world = WorldMap(
        (north, south), settlements={north: north_keep, south: south_keep}
    )
    game = GameState(
        (
            Duchy("north", Unit(), settlements=(north_keep,)),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )
    calls = []

    def do_nothing(current_world, duchy, rng):
        calls.append(duchy.duchy_id)
        return current_world

    monkeypatch.setattr(ai, "take_duchy_turn", do_nothing)

    result_world, result_game, _ = run_headless_game(
        world, game, Rng(17), max_turns=3
    )

    assert calls == ["north", "south"] * 3
    assert result_world == world
    assert result_world is not world
    assert result_game == game
    assert result_game.is_over is False


def test_idle_hero_without_strategic_assets_does_not_succeed(monkeypatch):
    region = Region("South")
    south_keep = Settlement("South Keep", 1, owner_id="south")
    world = WorldMap((region,), settlements={region: south_keep})
    hero = Unit(training=2)
    heir = Unit(training=1)
    game = GameState(
        (
            Duchy("north", hero, morale=3, heir=heir),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )
    monkeypatch.setattr(ai, "take_duchy_turn", lambda world, duchy, rng: world)

    _, result_game, _ = run_headless_game(world, game, Rng(17), max_turns=3)

    north = result_game.duchies[0]
    assert north.hero is hero
    assert north.heir is heir
    assert north.morale == 3
    assert result_game.is_over is False


def test_default_game_finishes_deterministically_before_safety_limit():
    first_world, first_game = create_headless_game()
    second_world, second_game = create_headless_game()
    bounded_world, bounded_game = create_headless_game()

    first_result = run_headless_game(first_world, first_game, Rng(73))
    second_result = run_headless_game(second_world, second_game, Rng(73))
    bounded_result = run_headless_game(
        bounded_world, bounded_game, Rng(73), max_turns=999
    )

    assert first_result == second_result
    assert first_result == bounded_result
    result_world, result_game, result_calendar = first_result
    assert isinstance(result_world, WorldMap)
    assert result_game.is_over is True
    assert isinstance(result_calendar, Calendar)
    assert result_game.winner in result_game.duchies
    defeated = tuple(
        duchy for duchy in result_game.duchies if duchy.is_defeated
    )
    assert len(defeated) == 1
    assert defeated[0] is not result_game.winner


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

    result_world, result_game, _ = run_headless_game(
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
    assert isinstance(finished_result[2], Calendar)
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


def test_party_mustered_and_lost_in_one_action_triggers_succession():
    region = Region("Keep")
    hero = Unit(training=2)
    heir = Unit(training=1)
    recruit = Unit()
    duchy = Duchy("north", hero, morale=3, heir=heir)
    settlement_before = Settlement(
        "Keep",
        3,
        occupied=1,
        garrison=(recruit,),
        owner_id="north",
    )
    settlement_after = Settlement("Keep", 2, owner_id="north")
    world_before = WorldMap(
        (region,), settlements={region: settlement_before}
    )
    world_after = WorldMap((region,), settlements={region: settlement_after})

    resolved = resolve_hero_survival(duchy, world_before, world_after)

    assert resolved.hero is heir
    assert resolved.heir is None
    assert resolved.morale == 3 - SUCCESSION_MORALE_PENALTY


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
