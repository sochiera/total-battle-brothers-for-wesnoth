"""Tests for headless game driver transitions."""

from dataclasses import replace

import tbb.ai as ai

from tbb.ai import take_duchy_turn
from tbb.building import FARM
from tbb.driver import resolve_hero_survival, run_headless_game
from tbb.duchy import SUCCESSION_MORALE_PENALTY, Duchy
from tbb.game import GameState, create_headless_game
from tbb.party import Party
from tbb.resources import Resources
from tbb.rng import Rng
from tbb.settlement import HERO_GOLD_COST, Settlement
from tbb.turn import Calendar
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbb.wound import BRUISE, MAIMED


def test_monthly_tick_precedes_recruitment_and_syncs_the_grown_settlement():
    north, south = map(Region, ("North", "South"))
    veteran = Unit(training=1)
    north_keep = Settlement(
        "North Keep",
        2,
        occupied=1,
        storage=Resources(wheat=3, gold=1),
        capacity=3,
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
    assert grown_keep.population == 3
    assert grown_keep.storage == Resources(wheat=1, gold=0)
    assert grown_keep.occupied == 3
    assert grown_keep.garrison == (veteran.train(1), Unit())
    assert north_duchy.settlements == (grown_keep,)
    assert world.settlement_at(north) is north_keep
    assert game.duchies[0].settlements == (north_keep,)


def test_headless_game_heals_party_bruise_over_two_turns_keeps_maimed(
    monkeypatch,
):
    """Driver monthly chain expires party BRUISE after two turns; MAIMED stays."""
    camp, south = map(Region, ("Camp", "South"))
    hero = Unit(training=1, wounds=(BRUISE, MAIMED))
    subordinate = Unit(equipment=1, wounds=(BRUISE,))
    party = Party(hero, (subordinate,), owner_id="north")
    south_keep = Settlement("South Keep", 2, owner_id="south")
    world = WorldMap(
        (camp, south),
        settlements={south: south_keep},
        parties={camp: party},
    )
    game = GameState(
        (
            Duchy("north", hero, parties=(party,)),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )
    monkeypatch.setattr(
        ai, "take_duchy_turn", lambda w, d, r, morale_by_owner=None: w
    )
    monkeypatch.setattr(ai, "raise_duchy_hero", lambda w, d: (w, d))

    first = run_headless_game(world, game, Rng(17), max_turns=2)
    second = run_headless_game(world, game, Rng(17), max_turns=2)
    result_world, _, _ = first
    healed = result_world.party_at(camp)

    assert healed is not None
    assert BRUISE not in healed.hero.wounds
    assert MAIMED in healed.hero.wounds
    assert healed.hero.wounds == (MAIMED,)
    assert BRUISE not in healed.units[0].wounds
    assert healed.units[0].wounds == ()
    assert first == second
    assert world.party_at(camp) is party
    assert party.hero.wounds == (BRUISE, MAIMED)
    assert party.units[0].wounds == (BRUISE,)


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
    expected_world = expected_world.tick_parties()
    expected_game = expected_game.sync_from_world(expected_world)
    for duchy_id in tuple(duchy.duchy_id for duchy in expected_game.duchies):
        duchy = next(
            duchy
            for duchy in expected_game.duchies
            if duchy.duchy_id == duchy_id
        )
        if duchy.is_defeated:
            continue
        expected_world, duchy = ai.raise_duchy_hero(expected_world, duchy)
        expected_game = GameState(
            duchy if current.duchy_id == duchy_id else current
            for current in expected_game.duchies
        ).sync_from_world(expected_world)
        expected_world, duchy = ai.designate_duchy_heir(expected_world, duchy)
        expected_game = GameState(
            duchy if current.duchy_id == duchy_id else current
            for current in expected_game.duchies
        ).sync_from_world(expected_world)
        world_before = expected_world
        morale_by_owner = {
            candidate.duchy_id: candidate.morale
            for candidate in expected_game.duchies
        }
        expected_world = take_duchy_turn(
            expected_world, duchy, expected_rng, morale_by_owner=morale_by_owner
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


def test_real_headless_game_opens_farm_in_starting_ai_settlement_immutably():
    world, game = create_headless_game()
    pristine_world, pristine_game = create_headless_game()
    ai_region = next(
        region
        for region in world.regions
        if world.settlement_at(region) is not None
        and world.settlement_at(region).owner_id == "ai"
    )

    result_world, _, _ = run_headless_game(
        world, game, Rng(17), max_turns=3
    )

    assert FARM in result_world.settlement_at(ai_region).active_buildings
    assert (world, game) == (pristine_world, pristine_game)


def test_one_turn_delegates_to_live_ai_api_in_duchy_order(monkeypatch):
    north, fallen, south = map(Region, ("North", "Fallen", "South"))
    north_keep = Settlement(
        "North Keep", 2, storage=Resources(0, 1), owner_id="north"
    )
    fallen_keep = Settlement("Fallen Keep", 1)
    south_keep = Settlement(
        "South Keep", 2, storage=Resources(0, 1), owner_id="south"
    )
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

    def recording_take_duchy_turn(
        current_world, duchy, rng, morale_by_owner=None
    ):
        next_world = real_take_duchy_turn(
            current_world, duchy, rng, morale_by_owner=morale_by_owner
        )
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


def test_run_headless_game_passes_morale_by_owner_from_game_state(monkeypatch):
    """Driver builds morale_by_owner from GameState for every take_duchy_turn call."""
    north, south = map(Region, ("North", "South"))
    north_keep = Settlement("North Keep", 1, owner_id="north")
    south_keep = Settlement("South Keep", 1, owner_id="south")
    world = WorldMap(
        (north, south),
        settlements={north: north_keep, south: south_keep},
    )
    game = GameState(
        (
            Duchy("north", Unit(), morale=17, settlements=(north_keep,)),
            Duchy("south", Unit(), morale=-9, settlements=(south_keep,)),
        )
    )
    expected_morale = {d.duchy_id: d.morale for d in game.duchies}
    captured: list[dict[str, int] | None] = []

    def recording_take(current_world, duchy, rng, morale_by_owner=None):
        captured.append(morale_by_owner)
        return current_world

    monkeypatch.setattr(ai, "take_duchy_turn", recording_take)

    run_headless_game(world, game, Rng(17), max_turns=1)

    assert len(captured) == 2
    assert captured[0] == expected_morale
    assert captured[1] == expected_morale
    assert expected_morale == {"north": 17, "south": -9}


def test_player_duchy_skips_take_duchy_turn_keeps_raise_and_heir(monkeypatch):
    """player_duchy_id skips take_duchy_turn for that duchy; AI others still act.

    Tick/sync/raise_duchy_hero/designate_duchy_heir still run for every duchy;
    only automatic develop/recruit/military policy is withheld from the player.
    Inputs stay immutable.
    """
    north, south = map(Region, ("North", "South"))
    north_keep = Settlement(
        "North Keep", 2, storage=Resources(0, 1), owner_id="north"
    )
    south_keep = Settlement(
        "South Keep", 2, storage=Resources(0, 1), owner_id="south"
    )
    world = WorldMap(
        (north, south),
        settlements={north: north_keep, south: south_keep},
    )
    game = GameState(
        (
            Duchy("north", Unit(), settlements=(north_keep,)),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )
    snapshot = (
        world.regions,
        dict(world.settlements),
        dict(world.parties),
        game.duchies,
    )
    take_calls = []
    raise_calls = []
    designate_calls = []
    real_take = ai.take_duchy_turn
    real_raise = ai.raise_duchy_hero
    real_designate = ai.designate_duchy_heir

    def recording_take(current_world, duchy, rng, morale_by_owner=None):
        take_calls.append(duchy.duchy_id)
        return real_take(
            current_world, duchy, rng, morale_by_owner=morale_by_owner
        )

    def recording_raise(current_world, duchy):
        raise_calls.append(duchy.duchy_id)
        return real_raise(current_world, duchy)

    def recording_designate(current_world, duchy):
        designate_calls.append(duchy.duchy_id)
        return real_designate(current_world, duchy)

    monkeypatch.setattr(ai, "take_duchy_turn", recording_take)
    monkeypatch.setattr(ai, "raise_duchy_hero", recording_raise)
    monkeypatch.setattr(ai, "designate_duchy_heir", recording_designate)

    result_world, result_game, _ = run_headless_game(
        world, game, Rng(17), max_turns=1, player_duchy_id="north"
    )

    assert take_calls == ["south"]
    assert raise_calls == ["north", "south"]
    assert designate_calls == ["north", "south"]
    assert result_world.settlement_at(north).garrison == ()
    assert result_world.settlement_at(south).garrison == (Unit(),)
    assert result_world is not world
    assert result_game is not game
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

    def conquer_south(current_world, duchy, rng, morale_by_owner=None):
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

    def conquer_on_norths_second_turn(
        current_world, duchy, rng, morale_by_owner=None
    ):
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

    def conquer_south(current_world, duchy, rng, morale_by_owner=None):
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

    def do_nothing(current_world, duchy, rng, morale_by_owner=None):
        calls.append(duchy.duchy_id)
        return current_world

    monkeypatch.setattr(ai, "take_duchy_turn", do_nothing)
    starting_calendar = Calendar(year=4, month=11)

    result_world, result_game, result_calendar = run_headless_game(
        world,
        game,
        Rng(17),
        max_turns=3,
        calendar=starting_calendar,
    )

    assert calls == ["north", "south"] * 3
    assert result_calendar == Calendar(year=5, month=1)
    assert starting_calendar == Calendar(year=4, month=11)
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
    monkeypatch.setattr(
        ai,
        "take_duchy_turn",
        lambda world, duchy, rng, morale_by_owner=None: world,
    )

    _, result_game, _ = run_headless_game(world, game, Rng(17), max_turns=3)

    north = result_game.duchies[0]
    assert north.hero is hero
    assert north.heir is heir
    assert north.morale == 3
    assert result_game.is_over is False


def test_default_game_is_deterministic_safety_limit_draw_after_succession():
    """Default setup + D12.3: landless survivors hit the safety-limit draw.

    With equal starting gold both duchies can seat heirs. After the opening
    assault the losing side keeps a landless hero (is_defeated stays False), so
    the fixed seed no longer yields an early AI win — it exhausts max_turns
    deterministically with winner is None.
    """
    first_world, first_game = create_headless_game()
    second_world, second_game = create_headless_game()

    first_result = run_headless_game(first_world, first_game, Rng(73))
    second_result = run_headless_game(second_world, second_game, Rng(73))

    assert first_result == second_result
    result_world, result_game, result_calendar = first_result
    assert isinstance(result_world, WorldMap)
    assert isinstance(result_calendar, Calendar)
    assert result_game.is_over is False
    assert result_game.winner is None
    assert result_calendar == Calendar(year=77, month=13)
    assert all(not duchy.is_defeated for duchy in result_game.duchies)
    assert any(duchy.has_hero for duchy in result_game.duchies)


def _development_scenario():
    north, south = map(Region, ("Development Keep", "Resolution Keep"))
    north_keep = Settlement(
        "Development Keep",
        1,
        occupied=1,
        storage=Resources(wheat=4, gold=0),
        capacity=1,
        garrison=(Unit(),),
        owner_id="north",
    )
    south_keep = Settlement(
        "Resolution Keep", 1, capacity=1, owner_id="south"
    )
    world = WorldMap(
        (north, south), settlements={north: north_keep, south: south_keep}
    )
    game = GameState(
        (
            Duchy("north", Unit(equipment=1), settlements=(north_keep,)),
            Duchy("south", None, settlements=(south_keep,)),
        )
    )
    return world, game


def _conquer_after_development(world, duchy, rng, morale_by_owner=None):
    if duchy.duchy_id != "north":
        return world
    north, south = world.regions
    developed_keep = world.settlement_at(north)
    if developed_keep.garrison[0].training < 2:
        return world

    settlements = dict(world.settlements)
    settlements[south] = replace(settlements[south], owner_id="north")
    return WorldMap(
        world.regions, world.connections, settlements, world.parties
    )


def _run_deterministic_development_scenario():
    first_world, first_game = _development_scenario()
    second_world, second_game = _development_scenario()

    first_result = run_headless_game(first_world, first_game, Rng(73))
    second_result = run_headless_game(second_world, second_game, Rng(73))

    assert first_result == second_result
    return first_result


def test_headless_game_develops_a_unit_before_resolution(monkeypatch):
    monkeypatch.setattr(ai, "take_duchy_turn", _conquer_after_development)

    result_world, result_game, _ = _run_deterministic_development_scenario()

    assert result_game.is_over is True
    developed = result_world.settlement_at(result_world.regions[0]).garrison[0]
    assert developed.training > Unit().training


def test_headless_development_spans_multiple_turns_before_resolution(monkeypatch):
    monkeypatch.setattr(ai, "take_duchy_turn", _conquer_after_development)

    _, result_game, result_calendar = _run_deterministic_development_scenario()

    elapsed_turns = (result_calendar.year - 1) * 13 + result_calendar.month - 1
    assert elapsed_turns >= 2
    assert result_game.is_over is True


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


def test_lost_hero_without_heir_regains_hero_from_settlement_next_turn(monkeypatch):
    """Heroless after death without heir; next turn raises from owned settlement.

    Isolates the raise_duchy_hero recovery path (D11.4b) by disabling automatic
    heir designation. The complementary D12.3 path (real designate → succession
    in the death turn) is covered by
    test_real_designate_heir_then_hero_death_promotes_heir_with_penalty.
    """
    monkeypatch.setattr(ai, "designate_duchy_heir", lambda w, d: (w, d))
    camp, keep, home = map(Region, ("North Camp", "South Keep", "North Home"))
    hero = Unit(equipment=1)
    attacking_party = Party(hero, owner_id="north")
    home_keep = Settlement(
        "North Home",
        population=5,
        storage=Resources(wheat=20, gold=10),
        owner_id="north",
    )
    south_keep = Settlement(
        "South Keep",
        4,
        occupied=1,
        garrison=(Unit(training=5, equipment=12),),
        owner_id="south",
    )
    world = WorldMap(
        (camp, keep, home),
        ((camp, keep),),
        settlements={home: home_keep, keep: south_keep},
        parties={camp: attacking_party},
    )
    game = GameState(
        (
            Duchy(
                "north",
                hero,
                morale=3,
                parties=(attacking_party,),
                settlements=(home_keep,),
            ),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )
    snapshot = (dict(world.settlements), dict(world.parties), game.duchies)

    after_loss_world, after_loss_game, _ = run_headless_game(
        world, game, Rng(4), max_turns=1
    )
    north_after_loss = next(
        duchy for duchy in after_loss_game.duchies if duchy.duchy_id == "north"
    )
    assert after_loss_world.party_at(camp) is None
    assert north_after_loss.has_hero is False
    assert north_after_loss.hero is None
    assert north_after_loss.heir is None
    assert north_after_loss.settlements
    assert any(
        settlement.population - settlement.occupied >= 1
        and settlement.storage.gold >= HERO_GOLD_COST
        for settlement in north_after_loss.settlements
    )

    first = run_headless_game(world, game, Rng(4), max_turns=2)
    second = run_headless_game(world, game, Rng(4), max_turns=2)
    result_world, result_game, _ = first
    north = next(
        duchy for duchy in result_game.duchies if duchy.duchy_id == "north"
    )

    assert first == second
    assert north.has_hero is True
    assert north.hero == Unit()
    assert north.heir is None
    assert result_world.settlement_at(home) is not None
    assert result_world.settlement_at(home).owner_id == "north"
    assert snapshot == (
        dict(world.settlements),
        dict(world.parties),
        game.duchies,
    )


def test_real_designate_heir_then_hero_death_promotes_heir_with_penalty():
    """D12.3 integration: real designate via driver, then death → succeed.

    Same geometry as the raise-recovery case, but without monkeypatching
    designate_duchy_heir. Driver seats an heir from the owned settlement, the
    assault kills the party, and resolve_hero_survival promotes heir → hero
    with SUCCESSION_MORALE_PENALTY. Two runs with the same Rng match.
    """
    camp, keep, home = map(Region, ("North Camp", "South Keep", "North Home"))
    hero = Unit(equipment=1)
    attacking_party = Party(hero, owner_id="north")
    home_keep = Settlement(
        "North Home",
        population=5,
        storage=Resources(wheat=20, gold=10),
        owner_id="north",
    )
    south_keep = Settlement(
        "South Keep",
        4,
        occupied=1,
        garrison=(Unit(training=5, equipment=12),),
        owner_id="south",
    )
    world = WorldMap(
        (camp, keep, home),
        ((camp, keep),),
        settlements={home: home_keep, keep: south_keep},
        parties={camp: attacking_party},
    )
    start_morale = 3
    game = GameState(
        (
            Duchy(
                "north",
                hero,
                morale=start_morale,
                parties=(attacking_party,),
                settlements=(home_keep,),
            ),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )
    snapshot = (dict(world.settlements), dict(world.parties), game.duchies)

    first = run_headless_game(world, game, Rng(4), max_turns=1)
    second = run_headless_game(world, game, Rng(4), max_turns=1)
    result_world, result_game, _ = first
    north = next(
        duchy for duchy in result_game.duchies if duchy.duchy_id == "north"
    )
    home_after = result_world.settlement_at(home)

    assert first == second
    assert result_world.party_at(camp) is None
    assert north.has_hero is True
    assert north.hero == Unit()
    assert north.heir is None
    assert north.morale == start_morale - SUCCESSION_MORALE_PENALTY
    assert home_after is not None
    assert home_after.owner_id == "north"
    # Tick leaves gold at 10; designate spends HERO_GOLD_COST (recruit may spend more).
    assert home_after.storage.gold <= 10 - HERO_GOLD_COST
    assert snapshot == (
        dict(world.settlements),
        dict(world.parties),
        game.duchies,
    )


def test_raise_duchy_hero_runs_before_take_duchy_turn_with_sync(monkeypatch):
    """Heroless duchy is raised before policy; take_duchy_turn sees the new hero."""
    home, south = map(Region, ("Home", "South"))
    home_keep = Settlement(
        "Home",
        population=5,
        storage=Resources(wheat=10, gold=HERO_GOLD_COST + 4),
        garrison=(Unit(training=1),),
        owner_id="north",
    )
    south_keep = Settlement(
        "South",
        3,
        storage=Resources(wheat=4, gold=2),
        owner_id="south",
    )
    world = WorldMap(
        (home, south),
        settlements={home: home_keep, south: south_keep},
    )
    game = GameState(
        (
            Duchy("north", None, morale=2, settlements=(home_keep,)),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )
    events = []
    real_raise = ai.raise_duchy_hero
    real_take = ai.take_duchy_turn

    def recording_raise(current_world, duchy):
        events.append(("raise_in", duchy.duchy_id, duchy.has_hero))
        result_world, result_duchy = real_raise(current_world, duchy)
        events.append(("raise_out", result_duchy.duchy_id, result_duchy.has_hero))
        return result_world, result_duchy

    def recording_take(current_world, duchy, rng, morale_by_owner=None):
        events.append(
            ("take", duchy.duchy_id, duchy.has_hero, duchy.hero, type(rng).__name__)
        )
        return real_take(
            current_world, duchy, rng, morale_by_owner=morale_by_owner
        )

    monkeypatch.setattr(ai, "raise_duchy_hero", recording_raise)
    monkeypatch.setattr(ai, "take_duchy_turn", recording_take)

    result_world, result_game, _ = run_headless_game(
        world, game, Rng(3), max_turns=1
    )
    north = next(
        duchy for duchy in result_game.duchies if duchy.duchy_id == "north"
    )
    north_events = [event for event in events if event[1] == "north"]

    assert north_events[0] == ("raise_in", "north", False)
    assert north_events[1] == ("raise_out", "north", True)
    assert north_events[2][0] == "take"
    assert north_events[2][1] == "north"
    assert north_events[2][2] is True
    assert north_events[2][3] == Unit()
    assert north_events[2][4] == "Rng"
    assert north.has_hero is True
    assert north.hero == Unit()
    assert north.morale == 2
    assert result_game.duchies[0] is north or any(
        duchy.duchy_id == "north" and duchy.has_hero for duchy in result_game.duchies
    )
    assert result_world.settlement_at(home).owner_id == "north"
    assert world.settlement_at(home) is home_keep
    assert game.duchies[0].has_hero is False


def test_exit_conditions_return_typed_exact_unchanged_inputs():
    region = Region("Last Keep")
    finished_world = WorldMap((region,))
    finished_game = GameState((Duchy("north", Unit(training=2)),))
    finished_calendar = Calendar(year=3, month=7)
    finished_snapshot = (
        finished_world.regions,
        dict(finished_world.settlements),
        dict(finished_world.parties),
        finished_game.duchies,
    )

    finished_result = run_headless_game(
        finished_world,
        finished_game,
        Rng(7),
        calendar=finished_calendar,
    )

    assert isinstance(finished_result, tuple)
    assert isinstance(finished_result[0], WorldMap)
    assert isinstance(finished_result[1], GameState)
    assert isinstance(finished_result[2], Calendar)
    assert finished_result[0] is finished_world
    assert finished_result[1] is finished_game
    assert finished_result[2] is finished_calendar
    assert finished_calendar == Calendar(year=3, month=7)
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
    running_calendar = Calendar(year=6, month=13)
    running_snapshot = (running_world.regions, running_game.duchies)

    running_result = run_headless_game(
        running_world,
        running_game,
        Rng(11),
        max_turns=0,
        calendar=running_calendar,
    )

    assert running_game.is_over is False
    assert running_result[0] is running_world
    assert running_result[1] is running_game
    assert running_result[2] is running_calendar
    assert running_calendar == Calendar(year=6, month=13)
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
