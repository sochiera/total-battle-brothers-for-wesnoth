"""Tests for immutable game-over state across duchies."""

from dataclasses import FrozenInstanceError

import pytest

from tbb.driver import run_headless_game
from tbb.duchy import Duchy
from tbb.game import GameState, create_headless_game
from tbb.party import Party
from tbb.rng import Rng
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.world import Region, WorldMap


def test_two_contenders_keep_game_running_in_input_order():
    north_settlement = Settlement("North", 1, owner_id="north")
    south_settlement = Settlement("South", 1, owner_id="south")
    north = Duchy("north", Unit(), settlements=(north_settlement,))
    south = Duchy("south", Unit(), settlements=(south_settlement,))
    game = GameState([north, south])

    assert game.contenders == (north, south)
    assert game.is_over is False
    assert game.winner is None


def test_only_undefeated_duchy_wins():
    defeated_north = Duchy("north", None)
    south_settlement = Settlement("South", 1, owner_id="south")
    south = Duchy("south", Unit(), settlements=(south_settlement,))
    defeated_west = Duchy("west", None)
    game = GameState([defeated_north, south, defeated_west])

    assert game.contenders == (south,)
    assert game.is_over is True
    assert game.winner is south


def test_all_defeated_ends_without_winner():
    game = GameState([Duchy("north", None), Duchy("south", None)])

    assert game.contenders == ()
    assert game.is_over is True
    assert game.winner is None


def test_rejects_repeated_duchy_identifier():
    with pytest.raises(ValueError):
        GameState([Duchy("north", Unit()), Duchy("north", Unit())])


def test_rejects_non_duchy_member():
    with pytest.raises(TypeError):
        GameState([Duchy("north", Unit()), object()])


def test_copies_input_and_is_frozen():
    north_settlement = Settlement("North", 1, owner_id="north")
    north = Duchy("north", Unit(), settlements=(north_settlement,))
    source = [north]
    game = GameState(source)
    source.append(Duchy("south", Unit()))

    assert game.duchies == (north,)
    assert game.contenders == (north,)
    assert game.winner is north
    with pytest.raises((FrozenInstanceError, AttributeError)):
        game.duchies = ()


def test_equal_inputs_produce_deterministic_queries():
    north_settlement = Settlement("North", 1, owner_id="north")
    # Living contender + defeated foe: equal inputs must yield identical queries.
    duchies = [
        Duchy("north", Unit(), settlements=(north_settlement,)),
        Duchy("south", None),
    ]
    first = GameState(duchies)
    second = GameState(duchies)

    assert first.contenders == second.contenders
    assert first.is_over == second.is_over
    assert first.winner == second.winner
    assert first.is_over is True
    assert first.winner is first.duchies[0]


def test_sync_from_world_rebuilds_settlements_in_region_order_by_owner():
    first = Region("first")
    second = Region("second")
    third = Region("third")
    north_first = Settlement("North First", 1, owner_id="north")
    south = Settlement("South", 1, owner_id="south")
    north_third = Settlement("North Third", 1, owner_id="north")
    world = WorldMap(
        (first, second, third),
        settlements={third: north_third, second: south, first: north_first},
    )
    stale = Settlement("Stale", 1, owner_id="north")
    north = Duchy("north", Unit(), settlements=(stale,))
    game = GameState((north, Duchy("south", Unit(), settlements=(south,))))

    synced = game.sync_from_world(world)

    assert synced is not game
    assert synced.duchies[0].settlements == (north_first, north_third)
    assert synced.duchies[0].settlements[0] is north_first
    assert synced.duchies[0].settlements[1] is north_third
    assert game.duchies[0].settlements == (stale,)
    assert tuple(world.settlements) == (third, second, first)


def test_sync_from_world_rebuilds_parties_in_region_order_and_ignores_unknown_owner():
    first = Region("first")
    second = Region("second")
    third = Region("third")
    fourth = Region("fourth")
    north_first = Party(Unit(), owner_id="north")
    unknown = Party(Unit(), owner_id="unknown")
    north_third = Party(Unit(), owner_id="north")
    south = Party(Unit(), owner_id="south")
    world = WorldMap(
        (first, second, third, fourth),
        parties={
            fourth: south,
            third: north_third,
            second: unknown,
            first: north_first,
        },
    )
    original_parties = dict(world.parties)
    game = GameState((Duchy("north", Unit()), Duchy("south", Unit())))

    first_sync = game.sync_from_world(world)
    second_sync = game.sync_from_world(world)

    assert first_sync == second_sync
    assert first_sync.duchies[0].parties == (north_first, north_third)
    assert first_sync.duchies[0].parties[0] is north_first
    assert first_sync.duchies[0].parties[1] is north_third
    assert first_sync.duchies[1].parties == (south,)
    assert all(unknown not in duchy.parties for duchy in first_sync.duchies)
    assert dict(world.parties) == original_parties
    assert world.party_at(second) is unknown


def test_sync_from_world_transfers_conquered_settlement_and_preserves_duchy_state():
    north_region = Region("north")
    conquered_region = Region("conquered")
    unknown_region = Region("unknown")
    north_settlement = Settlement("North", 1, owner_id="north")
    conquered = Settlement("Conquered", 1, owner_id="south")
    unknown = Settlement("Unknown", 1, owner_id="unknown")
    world = WorldMap(
        (north_region, conquered_region, unknown_region),
        settlements={
            unknown_region: unknown,
            conquered_region: conquered,
            north_region: north_settlement,
        },
    )
    north_hero = Unit(equipment=1)
    north_heir = Unit(equipment=2)
    south_hero = Unit(equipment=3)
    formerly_north = Settlement("Conquered", 1, owner_id="north")
    north = Duchy(
        "north",
        north_hero,
        morale=-3,
        heir=north_heir,
        settlements=(north_settlement, formerly_north),
    )
    stale_south = Settlement("Former South", 1, owner_id="south")
    south = Duchy("south", south_hero, morale=4, settlements=(stale_south,))
    game = GameState((south, north))
    original_settlements = dict(world.settlements)

    synced = game.sync_from_world(world)

    synced_south, synced_north = synced.duchies
    assert tuple(duchy.duchy_id for duchy in synced.duchies) == ("south", "north")
    assert synced_south.settlements == (conquered,)
    assert synced_south.settlements[0] is conquered
    assert synced_north.settlements == (north_settlement,)
    assert formerly_north not in synced_north.settlements
    assert all(unknown not in duchy.settlements for duchy in synced.duchies)
    assert synced_south.hero is south_hero
    assert synced_south.heir is None
    assert synced_south.morale == 4
    assert synced_north.hero is north_hero
    assert synced_north.heir is north_heir
    assert synced_north.morale == -3
    assert game.duchies == (south, north)
    assert dict(world.settlements) == original_settlements
    assert world.settlement_at(conquered_region) is conquered


def test_sync_from_world_rejects_a_value_that_is_not_a_world_map():
    game = GameState((Duchy("north", Unit()),))

    with pytest.raises(TypeError, match="world must be a WorldMap"):
        game.sync_from_world(object())


def test_headless_setup_has_two_supplied_duchies():
    world, game = create_headless_game()

    assert tuple(duchy.duchy_id for duchy in game.duchies) == ("player", "ai")
    assert len(world.settlements) == 2
    for duchy in game.duchies:
        assert len(duchy.settlements) == 1
        settlement = duchy.settlements[0]
        assert settlement.owner_id == duchy.duchy_id
        assert settlement.population > 0
        assert settlement.storage.wheat > 0
        assert settlement.storage.gold > 0
        assert duchy.hero is not None
        assert duchy.hero.damage > 0


def test_headless_setup_connects_opposite_settlements_without_parties():
    world, _ = create_headless_game()
    first, middle, last = world.regions

    assert world.settlement_at(first) is not None
    assert world.settlement_at(middle) is None
    assert world.settlement_at(last) is not None
    assert world.neighbors(first) == (middle,)
    assert world.neighbors(middle) == (first, last)
    assert world.neighbors(last) == (middle,)
    assert dict(world.parties) == {}


def test_headless_setup_shares_settlement_objects_between_world_and_duchies():
    world, game = create_headless_game()

    assert world.settlement_at(world.regions[0]) is game.duchies[0].settlements[0]
    assert world.settlement_at(world.regions[-1]) is game.duchies[1].settlements[0]


def test_headless_setup_is_deterministic_and_independent():
    first_world, first_game = create_headless_game()
    second_world, second_game = create_headless_game()

    assert first_world == second_world
    assert first_game == second_game
    assert first_world is not second_world
    assert first_game is not second_game
    assert first_world.settlements is not second_world.settlements
    assert first_world.parties is not second_world.parties
    assert first_game.duchies is not second_game.duchies


def test_headless_start_is_symmetric_and_player_keeps_lands_after_one_passive_turn():
    """G90.1a: symmetric start so passive play does not hand the keep to AI.

    Existing headless setup tests check population/storage/heroes, but not
    garrison symmetry. Without a matching starting garrison the AI conquers
    ``player lands`` on a fully passive first turn (seed 73), so the party
    cannot begin. Covers AC1–AC4: symmetry, one passive turn, ten passive
    turns, and deterministic twin runs on the same seed.
    """
    world, game = create_headless_game()
    player_region, _border, ai_region = world.regions
    player_keep = world.settlement_at(player_region)
    ai_keep = world.settlement_at(ai_region)

    assert player_keep is not None and ai_keep is not None
    assert player_keep.occupied == ai_keep.occupied
    assert player_keep.garrison == ai_keep.garrison

    result_world, result_game, _ = run_headless_game(
        world, game, Rng(73), max_turns=1, player_duchy_id="player"
    )

    assert result_world.settlement_at(player_region).owner_id == "player"
    player = next(duchy for duchy in result_game.duchies if duchy.duchy_id == "player")
    assert len(player.settlements) >= 1

    after_ten_a = run_headless_game(
        *create_headless_game(), Rng(73), max_turns=10, player_duchy_id="player"
    )
    after_ten_b = run_headless_game(
        *create_headless_game(), Rng(73), max_turns=10, player_duchy_id="player"
    )
    world10, game10, _ = after_ten_a
    assert world10.settlement_at(player_region).owner_id == "player"
    player10 = next(d for d in game10.duchies if d.duchy_id == "player")
    assert len(player10.settlements) >= 1
    # AC4: full run_headless_game triple (world, game, calendar), not just [:2].
    assert after_ten_a == after_ten_b
