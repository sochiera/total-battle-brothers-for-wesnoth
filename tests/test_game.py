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


def test_headless_turn_clears_party_action_marker():
    player_region = Region("player")
    ai_region = Region("ai")
    player_settlement = Settlement("Player Keep", 1, owner_id="player")
    ai_settlement = Settlement("AI Keep", 1, owner_id="ai")
    party = Party(Unit(), owner_id="player", acted_this_month=True)
    world = WorldMap(
        (player_region, ai_region),
        settlements={
            player_region: player_settlement,
            ai_region: ai_settlement,
        },
        parties={player_region: party},
    )
    game = GameState(
        (
            Duchy(
                "player",
                Unit(),
                settlements=(player_settlement,),
                parties=(party,),
            ),
            Duchy("ai", Unit(), settlements=(ai_settlement,)),
        )
    )

    result_world, _, _ = run_headless_game(
        world, game, Rng(1), max_turns=1, player_duchy_id="player"
    )

    assert result_world.party_at(player_region).acted_this_month is False


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


def _owned_settlement_regions(world: WorldMap, owner_id: str) -> tuple[Region, ...]:
    return tuple(
        region
        for region in world.regions
        if (settlement := world.settlement_at(region)) is not None
        and settlement.owner_id == owner_id
    )


def test_headless_setup_has_two_supplied_duchies():
    """G92.2a: two duchies, four starting keeps with the previous small stocks.

    Realistic defect: create_headless_game still ships one keep per duchy (or
    a second keep with empty/weaker stocks). Old gates asserted exactly one
    settlement each, so they could not catch the missing multi-keep world.
    """
    world, game = create_headless_game()

    assert tuple(duchy.duchy_id for duchy in game.duchies) == ("player", "ai")
    assert len(world.settlements) == 4
    for duchy in game.duchies:
        assert len(duchy.settlements) == 2
        for settlement in duchy.settlements:
            assert settlement.owner_id == duchy.duchy_id
            assert settlement.population == 5
            assert settlement.occupied == 1
            assert settlement.storage.wheat == 10
            assert settlement.storage.gold == 10
            assert settlement.garrison == (Unit(training=5, equipment=12),)
        assert duchy.hero is not None
        assert duchy.hero.damage > 0


def test_headless_setup_connects_opposite_settlements_without_parties():
    """G92.2a: five connected regions, empty border, two keeps per side, no parties.

    Realistic defect: only three regions remain, or a fifth region is added
    without joining the graph / without leaving exactly one empty border that
    separates the two duchies' lands.
    """
    world, _ = create_headless_game()

    assert len(world.regions) == 5
    empty = [region for region in world.regions if world.settlement_at(region) is None]
    player_regions = _owned_settlement_regions(world, "player")
    ai_regions = _owned_settlement_regions(world, "ai")
    assert len(empty) == 1
    assert len(player_regions) == 2
    assert len(ai_regions) == 2
    assert dict(world.parties) == {}

    border = empty[0]
    # Whole map is one connected component (BFS from the first region).
    seen: set[Region] = set()
    stack = [world.regions[0]]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(world.neighbors(current))
    assert seen == set(world.regions)

    # Border sits between the sides: each side has a keep adjacent to border,
    # and no direct player↔ai edge bypasses the empty frontier.
    assert any(border in world.neighbors(region) for region in player_regions)
    assert any(border in world.neighbors(region) for region in ai_regions)
    for player_region in player_regions:
        for ai_region in ai_regions:
            assert ai_region not in world.neighbors(player_region)


def test_headless_setup_shares_settlement_objects_between_world_and_duchies():
    """World and duchy lists must hold the same settlement object identities.

    Realistic defect: create_headless_game builds parallel Settlement copies for
    world vs duchies (equal by value, not shared). Settlement is a frozen
    dataclass, so value-set equality would stay green on copies — compare by id.
    """
    world, game = create_headless_game()

    world_ids = {id(settlement) for settlement in world.settlements.values()}
    duchy_ids = {
        id(settlement)
        for duchy in game.duchies
        for settlement in duchy.settlements
    }
    assert duchy_ids == world_ids
    assert len(duchy_ids) == 4
    for duchy in game.duchies:
        for settlement in duchy.settlements:
            assert any(settlement is world_s for world_s in world.settlements.values())


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


def test_headless_losing_one_settlement_leaves_duchy_alive_and_game_running():
    """G92.2a AC3: losing one of two keeps must not defeat the duchy or end play.

    Realistic defect: start still has a single keep, so reassigning that
    settlement's owner leaves the duchy with zero settlements → is_defeated
    and (with the other side still standing) ends the game. Multi-region
    layout alone does not prove survival after one loss.
    """
    from dataclasses import replace

    world, game = create_headless_game()
    player = next(duchy for duchy in game.duchies if duchy.duchy_id == "player")
    assert len(player.settlements) == 2

    lost = player.settlements[0]
    lost_region = next(
        region
        for region in world.regions
        if world.settlement_at(region) is lost
    )
    conquered = replace(lost, owner_id="ai")
    after_world = world.with_settlement(lost_region, conquered)
    after_game = game.sync_from_world(after_world)
    after_player = next(
        duchy for duchy in after_game.duchies if duchy.duchy_id == "player"
    )

    assert len(after_player.settlements) == 1
    assert after_player.is_defeated is False
    assert after_game.is_over is False
    assert after_game.winner is None


def test_headless_start_is_symmetric_and_passive_ai_pressure_is_deterministic():
    """G90.1a / G92.2a: all four keeps match; passive AI pressure is deterministic.

    Existing headless setup tests check population/storage/heroes, but not
    garrison symmetry across every starting keep. Covers symmetry, one passive
    turn, the measured seed-73 defeat, and deterministic twin runs.
    """
    world, game = create_headless_game()
    keeps = tuple(world.settlements.values())
    assert len(keeps) == 4
    reference = keeps[0]
    for keep in keeps[1:]:
        assert keep.occupied == reference.occupied
        assert keep.garrison == reference.garrison
        assert keep.population == reference.population
        assert keep.storage == reference.storage

    player_regions = _owned_settlement_regions(world, "player")
    assert len(player_regions) == 2

    result_world, result_game, _ = run_headless_game(
        world, game, Rng(73), max_turns=1, player_duchy_id="player"
    )

    for region in player_regions:
        assert result_world.settlement_at(region).owner_id == "player"
    player = next(duchy for duchy in result_game.duchies if duchy.duchy_id == "player")
    assert len(player.settlements) >= 1

    after_ten_a = run_headless_game(
        *create_headless_game(), Rng(73), max_turns=10, player_duchy_id="player"
    )
    after_ten_b = run_headless_game(
        *create_headless_game(), Rng(73), max_turns=10, player_duchy_id="player"
    )
    world10, game10, _ = after_ten_a
    for region in player_regions:
        assert world10.settlement_at(region).owner_id == "ai"
    ai10 = next(d for d in game10.duchies if d.duchy_id == "ai")
    assert len(ai10.settlements) >= 1
    assert game10.is_over is True
    assert game10.winner is ai10
    # AC4: full run_headless_game triple (world, game, calendar), not just [:2].
    assert after_ten_a == after_ten_b


def test_one_default_recruit_before_first_turn_does_not_reduce_keep_rate():
    """G91.1a AC2: recruiting one defender must not make the first turn worse.

    Realistic defect: default recruit() inserts a unit with positive damage and
    defense (AC1) that is still too weak; on the fixed headless seed set the
    keep-rate after one passive AI turn falls (measured 4/8 passive → 1/8 with
    one recruit). Unit-stat gates only check damage>0/defense>0 and miss this.
    """
    seeds = (73, 1, 2, 7, 11, 42, 5, 9)
    assert len(seeds) >= 6

    def player_keeps_after_one_turn(seed: int, *, recruit: bool) -> bool:
        world, game = create_headless_game()
        player_regions = _owned_settlement_regions(world, "player")
        assert player_regions
        player_region = player_regions[0]
        if recruit:
            keep = world.settlement_at(player_region)
            world = world.with_settlement(player_region, keep.recruit())
            game = game.sync_from_world(world)
        result_world, _, _ = run_headless_game(
            world, game, Rng(seed), max_turns=1, player_duchy_id="player"
        )
        kept = result_world.settlement_at(player_region)
        return kept is not None and kept.owner_id == "player"

    passive_keeps = sum(
        1 for seed in seeds if player_keeps_after_one_turn(seed, recruit=False)
    )
    recruit_keeps = sum(
        1 for seed in seeds if player_keeps_after_one_turn(seed, recruit=True)
    )
    assert recruit_keeps >= passive_keeps, (
        f"one default recruit reduced first-turn keep-rate: "
        f"passive={passive_keeps}/{len(seeds)} recruit={recruit_keeps}/{len(seeds)}"
    )
