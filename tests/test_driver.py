"""Tests for headless game driver transitions."""

from tbb.ai import take_duchy_turn
from tbb.driver import resolve_hero_survival, run_headless_game
from tbb.duchy import SUCCESSION_MORALE_PENALTY, Duchy
from tbb.game import GameState, create_headless_game
from tbb.party import Party
from tbb.rng import Rng
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
    assert result_game is game
    assert world_snapshot == (
        world.regions,
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
