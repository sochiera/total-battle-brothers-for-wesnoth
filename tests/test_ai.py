"""Tests for deterministic strategic AI queries."""

from collections import Counter
from dataclasses import FrozenInstanceError

import pytest
import tbb
import tbb.settlement as settlement_module
from tbb.driver import run_headless_game
from tbb.game import create_headless_game
from tbb.ai import (
    assault_duchy_party,
    designate_duchy_heir,
    develop_duchy_settlement,
    march_duchy_party,
    raise_duchy_hero,
)
import tbb.ai as ai
from tests.helpers import assert_moved_party

from tbb import (
    Duchy,
    Party,
    Region,
    Resources,
    Settlement,
    Unit,
    WorldMap,
    assault_nearest_enemy_settlement,
    march_toward_nearest_enemy,
    muster_duchy_party,
    nearest_enemy_settlement,
    next_march_step,
    recruit_duchy_unit,
    take_duchy_military_action,
    take_duchy_turn,
)
from tbbbridge.snapshot import game_state
from tbbbridge.session import apply_command, new_session


def _settlement(name: str, owner_id: str | None) -> Settlement:
    return Settlement(name, population=1, owner_id=owner_id)


def _party(name: str) -> Party:
    return Party(Unit(experience=len(name)))


def _owned_party(name: str, owner_id: str = "ai") -> Party:
    return Party(Unit(experience=len(name)), owner_id=owner_id)


def test_nearest_enemy_wins_regardless_of_settlement_mapping_order():
    start = Region("Start")
    near = Region("Near")
    middle = Region("Middle")
    far = Region("Far")
    world = WorldMap(
        [start, near, middle, far],
        [(start, near), (start, middle), (middle, far)],
        settlements={far: _settlement("Far", "enemy"), near: _settlement("Near", "enemy")},
    )

    assert nearest_enemy_settlement(world, start, "ai") is near


def test_equal_distance_is_broken_by_world_region_order():
    start = Region("Start")
    first = Region("First")
    second = Region("Second")
    world = WorldMap(
        [start, first, second],
        [(start, second), (start, first)],
        settlements={second: _settlement("Second", "enemy"), first: _settlement("First", "enemy")},
    )

    assert nearest_enemy_settlement(world, start, "ai") is first


def test_own_unowned_and_disconnected_settlements_are_ignored():
    start = Region("Start")
    own = Region("Own")
    unowned = Region("Unowned")
    disconnected = Region("Disconnected")
    world = WorldMap(
        [start, own, unowned, disconnected],
        [(start, own), (own, unowned)],
        settlements={
            own: _settlement("Own", "ai"),
            unowned: _settlement("Unowned", None),
            disconnected: _settlement("Enemy", "enemy"),
        },
    )

    assert nearest_enemy_settlement(world, start, "ai") is None


def _nearest_own_garrison_settlement(world, start, owner_id):
    return ai.nearest_own_garrison_settlement(world, start, owner_id)


def test_nearest_own_garrison_settlement_is_publicly_exported():
    assert tbb.nearest_own_garrison_settlement is ai.nearest_own_garrison_settlement


def test_nearest_own_garrison_settlement_filters_empty_and_unreachable_candidates():
    start, empty, near, far, island = map(
        Region, ("Start", "Empty", "Near", "Far", "Island")
    )
    world = WorldMap(
        [start, empty, near, far, island],
        [(start, empty), (empty, near), (near, far)],
        settlements={
            empty: _settlement("Empty", "ai"),
            near: Settlement("Near", 1, garrison=(Unit(),), owner_id="ai"),
            far: Settlement("Far", 1, garrison=(Unit(),), owner_id="ai"),
            island: Settlement("Island", 1, garrison=(Unit(),), owner_id="ai"),
        },
    )

    assert _nearest_own_garrison_settlement(world, start, "ai") is near


@pytest.mark.parametrize("case", ["no_own", "all_empty", "unreachable"])
def test_nearest_own_garrison_settlement_returns_none_without_eligible_candidate(case):
    start, target, island = map(Region, ("Start", "Target", "Island"))
    settlements = {}
    connections = [(start, target)]
    if case == "no_own":
        settlements[target] = _settlement("Enemy", "enemy")
    elif case == "all_empty":
        settlements[target] = _settlement("Empty", "ai")
    else:
        settlements[island] = Settlement(
            "Island", 1, garrison=(Unit(),), owner_id="ai"
        )
    world = WorldMap([start, target, island], connections, settlements=settlements)

    assert _nearest_own_garrison_settlement(world, start, "ai") is None


def test_nearest_own_garrison_settlement_accepts_start_and_breaks_ties_by_region_order():
    start, first, second = map(Region, ("Start", "First", "Second"))
    first_settlement = Settlement("First", 1, garrison=(Unit(),), owner_id="ai")
    second_settlement = Settlement("Second", 1, garrison=(Unit(),), owner_id="ai")
    world = WorldMap(
        [start, first, second],
        [(start, second), (start, first)],
        settlements={second: second_settlement, first: first_settlement},
    )

    assert _nearest_own_garrison_settlement(world, first, "ai") is first
    assert _nearest_own_garrison_settlement(world, start, "ai") is first


@pytest.mark.parametrize(
    "query", [nearest_enemy_settlement, ai.nearest_own_garrison_settlement]
)
@pytest.mark.parametrize(
    "owner_id, expected_error",
    [("", ValueError), (None, TypeError), (7, TypeError)],
)
def test_invalid_owner_id_is_rejected_by_settlement_queries(
    query, owner_id, expected_error
):
    start = Region("Start")
    world = WorldMap([start])

    with pytest.raises(expected_error):
        query(world, start, owner_id)


@pytest.mark.parametrize(
    "query", [nearest_enemy_settlement, ai.nearest_own_garrison_settlement]
)
def test_start_region_outside_world_is_rejected_by_settlement_queries(query):
    with pytest.raises(ValueError):
        query(WorldMap([Region("Known")]), Region("Unknown"), "ai")


def test_query_does_not_mutate_world_settlement_mapping_or_settlements():
    start = Region("Start")
    target = Region("Target")
    settlement = _settlement("Target", "enemy")
    world = WorldMap([start, target], [(start, target)], {target: settlement})
    before = dict(world.settlements)

    nearest_enemy_settlement(world, start, "ai")

    assert dict(world.settlements) == before
    assert world.settlement_at(target) is settlement
    assert settlement.owner_id == "enemy"
    with pytest.raises(TypeError):
        world.settlements[start] = settlement
    with pytest.raises(FrozenInstanceError):
        settlement.owner_id = "ai"


def test_next_march_step_uses_shortest_path_when_longer_branch_is_first():
    start, long, middle, short, target = map(
        Region, ("Start", "Long", "Middle", "Short", "Target")
    )
    world = WorldMap(
        [start, long, middle, short, target],
        [(start, long), (long, middle), (middle, target), (start, short), (short, target)],
        parties={start: _party("Hero")},
    )

    assert next_march_step(world, start, target) is short


def test_next_march_step_tie_uses_region_order_not_connection_order():
    start, first, second, target = map(Region, ("Start", "First", "Second", "Target"))
    world = WorldMap(
        [start, first, second, target],
        [(start, second), (second, target), (start, first), (first, target)],
        parties={start: _party("Hero")},
    )

    assert next_march_step(world, start, target) is first


def test_next_march_step_avoids_occupied_regions_or_returns_none_when_blocked():
    start, blocked, detour, target = map(Region, ("Start", "Blocked", "Detour", "Target"))
    party = _party("Hero")
    blocker = _party("Blocker")
    world = WorldMap(
        [start, blocked, detour, target],
        [(start, blocked), (blocked, target), (start, detour), (detour, target)],
        parties={start: party, blocked: blocker},
    )

    assert next_march_step(world, start, target) is detour
    fully_blocked = WorldMap(
        world.regions,
        world.connections,
        parties={start: party, blocked: blocker, detour: _party("Other")},
    )
    assert next_march_step(fully_blocked, start, target) is None


def test_next_march_step_stops_when_target_is_adjacent():
    start, target = Region("Start"), Region("Target")
    party = _party("Hero")
    world = WorldMap([start, target], [(start, target)], parties={start: party})

    assert next_march_step(world, start, target) is None
    assert world.party_at(start) is party
    assert world.party_at(target) is None


@pytest.mark.parametrize("outside_argument", ["start", "target"])
def test_next_march_step_rejects_regions_outside_map_without_mutation(outside_argument):
    start, step, target = Region("Start"), Region("Step"), Region("Target")
    party = _party("Hero")
    world = WorldMap([start, step, target], [(start, step), (step, target)], parties={start: party})
    before = dict(world.parties)
    arguments = {
        "start": Region("Outside") if outside_argument == "start" else start,
        "target": Region("Outside") if outside_argument == "target" else target,
    }

    with pytest.raises(ValueError):
        next_march_step(world, arguments["start"], arguments["target"])

    assert dict(world.parties) == before
    assert world.party_at(start) is party


def test_region_distance_is_zero_when_start_equals_target():
    """ai.region_distance returns 0 when start and target are the same region."""
    start = Region("Start")
    other = Region("Other")
    world = WorldMap([start, other], [(start, other)])

    assert ai.region_distance(world, start, start) == 0


def test_region_distance_is_one_for_direct_neighbor():
    """ai.region_distance returns 1 when target is a direct neighbor of start."""
    start = Region("Start")
    neighbor = Region("Neighbor")
    world = WorldMap([start, neighbor], [(start, neighbor)])

    assert ai.region_distance(world, start, neighbor) == 1


def test_region_distance_is_shortest_path_and_ignores_party_occupancy():
    """BFS edge count ignores parties; blocked middle region still counts as distance 2."""
    start, middle, target = map(Region, ("Start", "Middle", "Target"))
    party = _party("Occupant")
    world = WorldMap(
        [start, middle, target],
        [(start, middle), (middle, target)],
        parties={middle: party},
    )

    assert ai.region_distance(world, start, target) == 2
    assert world.party_at(middle) is party


def test_region_distance_returns_none_when_no_path():
    """ai.region_distance returns None for disconnected graph components."""
    start = Region("Start")
    island = Region("Island")
    world = WorldMap([start, island], [])

    assert ai.region_distance(world, start, island) is None


@pytest.mark.parametrize("outside_argument", ["start", "target"])
def test_region_distance_rejects_regions_outside_map_without_mutation(outside_argument):
    """Regions outside world.regions raise ValueError; map is not mutated."""
    start, neighbor = Region("Start"), Region("Neighbor")
    party = _party("Hero")
    world = WorldMap([start, neighbor], [(start, neighbor)], parties={start: party})
    before = dict(world.parties)
    arguments = {
        "start": Region("Outside") if outside_argument == "start" else start,
        "target": Region("Outside") if outside_argument == "target" else neighbor,
    }

    with pytest.raises(ValueError):
        ai.region_distance(world, arguments["start"], arguments["target"])

    assert dict(world.parties) == before
    assert world.party_at(start) is party


def test_march_moves_exactly_one_step_and_preserves_input_and_party():
    start, step, target = map(Region, ("Start", "Step", "Target"))
    party = _owned_party("Hero")
    world = WorldMap(
        [start, step, target],
        [(start, step), (step, target)],
        settlements={target: _settlement("Target", "enemy")},
        parties={start: party},
    )

    moved = march_toward_nearest_enemy(world, start)

    assert_moved_party(moved, step, party)
    assert moved.party_at(start) is None
    assert world.party_at(start) is party
    assert world.party_at(step) is None


def test_march_duchy_party_applies_march_toward_nearest_enemy_from_party_position():
    """march_duchy_party finds the duchy party and applies one march step."""
    start, step, target = map(Region, ("Start", "Step", "Target"))
    party = _owned_party("Hero", "ai")
    world = WorldMap(
        [start, step, target],
        [(start, step), (step, target)],
        settlements={target: _settlement("Target", "enemy")},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    moved = march_duchy_party(world, duchy)

    assert moved == march_toward_nearest_enemy(world, start)
    assert_moved_party(moved, step, party)
    assert moved.party_at(start) is None
    assert world.party_at(start) is party
    assert world.party_at(step) is None


def test_march_duchy_party_second_move_in_month_is_noop_for_ai_party():
    start, first, second, target = map(
        Region, ("Start", "First", "Second", "Target")
    )
    party = _owned_party("Hero", "ai")
    world = WorldMap(
        [start, first, second, target],
        [(start, first), (first, second), (second, target)],
        settlements={target: _settlement("Target", "enemy")},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    after_first = march_duchy_party(world, duchy)
    assert_moved_party(after_first, first, party)
    after_second = march_duchy_party(after_first, duchy)

    assert after_second is after_first
    assert after_second.party_at(first) is not None
    assert after_second.party_at(second) is None


def test_march_duchy_party_is_noop_without_party_on_map():
    """When the duchy has no party on the map, march_duchy_party returns the input world."""
    home, camp = Region("Home"), Region("Camp")
    settlement = Settlement("Home", 1, owner_id="ai")
    foreign_party = _owned_party("Enemy", "enemy")
    world = WorldMap(
        [home, camp],
        settlements={home: settlement},
        parties={camp: foreign_party},
    )
    duchy = Duchy("ai", Unit())
    before = dict(world.parties)

    result = march_duchy_party(world, duchy)

    assert result is world
    assert dict(world.parties) == before
    assert world.settlement_at(home) is settlement
    assert world.party_at(camp) is foreign_party


def test_march_duchy_party_to_moves_one_step_toward_explicit_target():
    """march_duchy_party_to finds the duchy party and marches one step toward target.

    Uses an explicit target that is *not* the nearest enemy settlement, so the
    step cannot come from march_toward_nearest_enemy / march_duchy_party.
    """
    start, step_near, near, step_far, far = map(
        Region, ("Start", "StepNear", "Near", "StepFar", "Far")
    )
    party = _owned_party("Hero", "ai")
    world = WorldMap(
        [start, step_near, near, step_far, far],
        [
            (start, step_near),
            (step_near, near),
            (start, step_far),
            (step_far, far),
        ],
        settlements={
            near: _settlement("Near", "enemy"),
            far: _settlement("Far", "enemy"),
        },
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))
    expected_step = next_march_step(world, start, far)
    assert expected_step is step_far
    # Sanity: automatic nearest-enemy march would go toward ``near``, not far.
    auto = march_duchy_party(world, duchy)
    assert_moved_party(auto, step_near, party)
    assert auto.party_at(step_far) is None

    moved = ai.march_duchy_party_to(world, duchy, far)

    assert moved is not world
    assert moved == world.move_party(start, expected_step, 1)
    assert_moved_party(moved, step_far, party)
    assert moved.party_at(start) is None
    assert moved.party_at(step_near) is None
    assert world.party_at(start) is party
    assert world.party_at(step_far) is None


def test_march_duchy_party_to_is_noop_without_party_on_map():
    """When the duchy has no party on the map, march_duchy_party_to is a no-op."""
    home, camp, far = Region("Home"), Region("Camp"), Region("Far")
    settlement = Settlement("Home", 1, owner_id="ai")
    foreign_party = _owned_party("Enemy", "enemy")
    world = WorldMap(
        [home, camp, far],
        [(home, camp), (camp, far)],
        settlements={home: settlement, far: _settlement("Far", "enemy")},
        parties={camp: foreign_party},
    )
    duchy = Duchy("ai", Unit())
    before = dict(world.parties)

    result = ai.march_duchy_party_to(world, duchy, far)

    assert result is world
    assert dict(world.parties) == before
    assert world.settlement_at(home) is settlement
    assert world.party_at(camp) is foreign_party


def test_march_duchy_party_to_is_noop_when_next_march_step_is_none():
    """When next_march_step is None (adjacent/same target), march_duchy_party_to is a no-op."""
    start, target = Region("Start"), Region("Target")
    party = _owned_party("Hero", "ai")
    world = WorldMap(
        [start, target],
        [(start, target)],
        settlements={target: _settlement("Target", "enemy")},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))
    assert next_march_step(world, start, target) is None
    before = dict(world.parties)

    result = ai.march_duchy_party_to(world, duchy, target)

    assert result is world
    assert dict(world.parties) == before
    assert world.party_at(start) is party
    assert world.party_at(target) is None


def test_move_duchy_party_to_adjacent_occupies_empty_neighbor():
    """move_duchy_party_to_adjacent moves into an empty direct neighbor.

    Realistic defect: reusing march_duchy_party_to / next_march_step for a map
    click leaves adjacent targets as no-ops (next_march_step is None when the
    target is already a neighbor). Existing march tests only lock that older
    contract; they never require occupying the designated adjacent region.
    """
    start, neighbor, elsewhere = Region("Start"), Region("Neighbor"), Region("Elsewhere")
    party = _owned_party("Hero", "player")
    bystander = _owned_party("Bystander", "other")
    own_home = _settlement("Home", "player")
    world = WorldMap(
        [start, neighbor, elsewhere],
        [(start, neighbor)],
        settlements={start: own_home},
        parties={start: party, elsewhere: bystander},
    )
    duchy = Duchy("player", party.hero, parties=(party,))

    # Same inputs stay a no-op under the preserved march-toward contract.
    assert ai.march_duchy_party_to(world, duchy, neighbor) is world

    moved = ai.move_duchy_party_to_adjacent(world, duchy, neighbor)

    assert moved is not world
    assert_moved_party(moved, neighbor, party)
    assert moved.party_at(start) is None
    assert moved.party_at(elsewhere) is bystander
    assert moved.settlement_at(start) is own_home
    assert world.party_at(start) is party
    assert world.party_at(neighbor) is None
    assert world.party_at(elsewhere) is bystander
    assert world.settlement_at(start) is own_home


def test_move_duchy_party_to_adjacent_occupies_own_settlement_neighbor():
    """Adjacent own settlement without a party is a legal one-step destination."""
    start, neighbor = Region("Start"), Region("Neighbor")
    party = _owned_party("Hero", "player")
    own = _settlement("Own", "player")
    world = WorldMap(
        [start, neighbor],
        [(start, neighbor)],
        settlements={neighbor: own},
        parties={start: party},
    )
    duchy = Duchy("player", party.hero, parties=(party,))

    moved = ai.move_duchy_party_to_adjacent(world, duchy, neighbor)

    assert moved is not world
    assert_moved_party(moved, neighbor, party)
    assert moved.party_at(start) is None
    assert moved.settlement_at(neighbor) is own
    assert world.party_at(start) is party
    assert world.settlement_at(neighbor) is own


@pytest.mark.parametrize(
    "case",
    [
        "current",
        "distant",
        "occupied_party",
        "enemy_settlement",
        "unowned_settlement",
        "no_party",
    ],
)
def test_move_duchy_party_to_adjacent_is_noop(case):
    """Unsafe or impossible adjacent targets leave the world unchanged.

    Realistic defect: treating any non-party neighbor as walkable (including an
    enemy or unowned settlement) or falling through to move_party without the
    adjacency / ownership guards listed in the acceptance criteria.
    """
    start, neighbor, far = Region("Start"), Region("Neighbor"), Region("Far")
    party = _owned_party("Hero", "player")
    foreign = _owned_party("Blocker", "enemy")
    settlements: dict[Region, Settlement] = {}
    parties: dict[Region, Party] = {}
    target = neighbor
    edges = [(start, neighbor), (neighbor, far)]

    if case == "current":
        parties = {start: party}
        target = start
    elif case == "distant":
        parties = {start: party}
        target = far
    elif case == "occupied_party":
        parties = {start: party, neighbor: foreign}
    elif case == "enemy_settlement":
        parties = {start: party}
        settlements = {neighbor: _settlement("Enemy", "enemy")}
    elif case == "unowned_settlement":
        parties = {start: party}
        settlements = {neighbor: _settlement("Neutral", None)}
    elif case == "no_party":
        parties = {neighbor: foreign}
    else:  # pragma: no cover
        raise AssertionError(case)

    world = WorldMap(
        [start, neighbor, far],
        edges,
        settlements=settlements,
        parties=parties,
    )
    duchy = Duchy("player", party.hero, parties=(party,))
    before_parties = dict(world.parties)
    before_settlements = dict(world.settlements)

    result = ai.move_duchy_party_to_adjacent(world, duchy, target)

    assert result is world
    assert dict(world.parties) == before_parties
    assert dict(world.settlements) == before_settlements


def test_assault_duchy_party_applies_assault_from_party_position():
    """assault_duchy_party finds the duchy party and assaults from its region."""
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    settlement = Settlement(
        "Target", population=1, garrison=(Unit(equipment=1),), owner_id="enemy"
    )
    world = WorldMap(
        [start, target],
        [(start, target)],
        settlements={target: settlement},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))
    seed = 2
    morale_by_owner = {"ai": 10, "enemy": -5}

    resolved = assault_duchy_party(
        world, duchy, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )

    assert resolved == assault_nearest_enemy_settlement(
        world, start, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )
    assert resolved != world
    assert world.party_at(start) is party
    assert world.settlement_at(target) is settlement


def test_assault_duchy_party_is_noop_without_party_and_does_not_use_rng():
    """When the duchy has no party on the map, assault_duchy_party is a no-op."""
    home, camp = Region("Home"), Region("Camp")
    settlement = Settlement("Home", 1, owner_id="ai")
    foreign_party = _owned_party("Enemy", "enemy")
    world = WorldMap(
        [home, camp],
        settlements={home: settlement},
        parties={camp: foreign_party},
    )
    duchy = Duchy("ai", Unit())
    before = dict(world.parties)

    result = assault_duchy_party(world, duchy, _ForbiddenRng())

    assert result is world
    assert dict(world.parties) == before
    assert world.settlement_at(home) is settlement
    assert world.party_at(camp) is foreign_party


def test_assault_duchy_party_is_noop_when_nearest_enemy_not_adjacent():
    """Non-adjacent nearest enemy: same as assault_nearest_enemy_settlement (no change)."""
    start, middle, target = map(Region, ("Start", "Middle", "Target"))
    party = _owned_party("Hero", "ai")
    world = WorldMap(
        [start, middle, target],
        [(start, middle), (middle, target)],
        settlements={target: _settlement("Target", "enemy")},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result = assault_duchy_party(world, duchy, _ForbiddenRng())

    assert result is world
    assert result == assault_nearest_enemy_settlement(
        world, start, _ForbiddenRng()
    )
    assert world.party_at(start) is party


def test_assault_duchy_party_is_deterministic_and_preserves_input():
    """Same world/duchy/seed yields equal results; input map and parties unchanged."""
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    settlement = Settlement(
        "Target", population=1, garrison=(Unit(equipment=1),), owner_id="enemy"
    )
    world = WorldMap(
        [start, target],
        [(start, target)],
        settlements={target: settlement},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))
    seed = 12
    morale_by_owner = {"ai": 5, "enemy": 0}

    first = assault_duchy_party(
        world, duchy, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )
    second = assault_duchy_party(
        world, duchy, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )

    assert first == second
    assert world.party_at(start) is party
    assert world.settlement_at(target) is settlement
    assert party.units == ()
    assert settlement.owner_id == "enemy"


def test_assault_duchy_party_recorded_returns_battle_and_matches_assault_duchy_party():
    """assault_duchy_party_recorded mirrors assault_duchy_party's map, plus the battle."""
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    settlement = Settlement(
        "Target", population=1, garrison=(Unit(equipment=1),), owner_id="enemy"
    )
    world = WorldMap(
        [start, target],
        [(start, target)],
        settlements={target: settlement},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))
    seed = 2
    morale_by_owner = {"ai": 10, "enemy": -5}

    resolved_world, battle = ai.assault_duchy_party_recorded(
        world, duchy, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )

    expected_world, expected_battle = world.resolve_settlement_battle_recorded(
        start, target, tbb.Rng(seed), attacker_morale=10, defender_morale=-5
    )
    assert resolved_world == expected_world
    assert battle == expected_battle
    assert resolved_world == assault_duchy_party(
        world, duchy, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )
    assert resolved_world != world
    assert world.party_at(start) is party
    assert world.settlement_at(target) is settlement


def test_assault_duchy_party_recorded_is_noop_when_no_adjacent_enemy_settlement():
    """assault_duchy_party_recorded returns (world, None) without using RNG when no enemy is adjacent."""
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    own_settlement = Settlement("Target", population=1, owner_id="ai")
    world = WorldMap(
        [start, target],
        [(start, target)],
        settlements={target: own_settlement},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result_world, battle = ai.assault_duchy_party_recorded(
        world, duchy, _ForbiddenRng()
    )

    assert result_world is world
    assert battle is None
    assert world.party_at(start) is party
    assert world.settlement_at(target) is own_settlement


def test_assault_duchy_party_to_assaults_explicit_target_not_nearest():
    """assault_duchy_party_to resolves the explicit target, not the nearest enemy.

    ``near`` is the nearest-enemy pick; ``far`` is a second, non-nearest but
    still adjacent enemy settlement explicitly requested as the target.
    """
    start, near, far = map(Region, ("Start", "Near", "Far"))
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    near_settlement = Settlement(
        "Near", population=1, garrison=(Unit(equipment=1),), owner_id="enemy"
    )
    far_settlement = Settlement(
        "Far", population=1, garrison=(Unit(equipment=1),), owner_id="enemy"
    )
    world = WorldMap(
        [start, near, far],
        [(start, near), (start, far)],
        settlements={near: near_settlement, far: far_settlement},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))
    seed = 2
    morale_by_owner = {"ai": 10, "enemy": -5}
    assert nearest_enemy_settlement(world, start, "ai") is near

    resolved = ai.assault_duchy_party_to(
        world, duchy, far, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )

    assert resolved == world.resolve_settlement_battle(
        start, far, tbb.Rng(seed), attacker_morale=10, defender_morale=-5
    )
    assert resolved != world
    assert world.party_at(start) is party
    assert world.settlement_at(near) is near_settlement
    assert world.settlement_at(far) is far_settlement


def test_assault_duchy_party_to_recorded_returns_battle_and_matches_assault_duchy_party_to():
    """assault_duchy_party_to_recorded mirrors assault_duchy_party_to's map, plus the battle."""
    start, near, far = map(Region, ("Start", "Near", "Far"))
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    near_settlement = Settlement(
        "Near", population=1, garrison=(Unit(equipment=1),), owner_id="enemy"
    )
    far_settlement = Settlement(
        "Far", population=1, garrison=(Unit(equipment=1),), owner_id="enemy"
    )
    world = WorldMap(
        [start, near, far],
        [(start, near), (start, far)],
        settlements={near: near_settlement, far: far_settlement},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))
    seed = 2
    morale_by_owner = {"ai": 10, "enemy": -5}

    resolved_world, battle = ai.assault_duchy_party_to_recorded(
        world, duchy, far, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )

    expected_world, expected_battle = world.resolve_settlement_battle_recorded(
        start, far, tbb.Rng(seed), attacker_morale=10, defender_morale=-5
    )
    assert resolved_world == expected_world
    assert battle == expected_battle
    assert resolved_world == ai.assault_duchy_party_to(
        world, duchy, far, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )
    assert resolved_world != world
    assert world.party_at(start) is party
    assert world.settlement_at(near) is near_settlement
    assert world.settlement_at(far) is far_settlement


def test_assault_duchy_party_to_recorded_is_noop_for_own_settlement_and_does_not_use_rng():
    """assault_duchy_party_to_recorded must not assault the duchy's own settlement."""
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    own_settlement = Settlement("Target", population=1, owner_id="ai")
    world = WorldMap(
        [start, target],
        [(start, target)],
        settlements={target: own_settlement},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result_world, battle = ai.assault_duchy_party_to_recorded(
        world, duchy, target, _ForbiddenRng()
    )

    assert result_world is world
    assert battle is None
    assert world.party_at(start) is party
    assert world.settlement_at(target) is own_settlement


def test_assault_duchy_party_to_is_noop_for_own_settlement_and_does_not_use_rng():
    """assault_duchy_party_to must not assault an adjacent settlement owned by the duchy itself."""
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    own_settlement = Settlement("Target", population=1, owner_id="ai")
    world = WorldMap(
        [start, target],
        [(start, target)],
        settlements={target: own_settlement},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result = ai.assault_duchy_party_to(world, duchy, target, _ForbiddenRng())

    assert result is world
    assert world.party_at(start) is party
    assert world.settlement_at(target) is own_settlement


def test_assault_duchy_party_to_is_noop_without_party_and_does_not_use_rng():
    """When the duchy has no party on the map, assault_duchy_party_to is a no-op."""
    home, camp, target = map(Region, ("Home", "Camp", "Target"))
    settlement = Settlement("Target", population=1, owner_id="enemy")
    foreign_party = _owned_party("Enemy", "enemy")
    world = WorldMap(
        [home, camp, target],
        [(camp, target)],
        settlements={target: settlement},
        parties={camp: foreign_party},
    )
    duchy = Duchy("ai", Unit())

    result = ai.assault_duchy_party_to(world, duchy, target, _ForbiddenRng())

    assert result is world
    assert world.settlement_at(target) is settlement
    assert world.party_at(camp) is foreign_party


def test_assault_duchy_party_to_is_noop_when_target_not_adjacent_or_has_no_settlement():
    """Non-adjacent target or a target region without a settlement: no-op, no RNG use."""
    start, middle, distant_enemy, empty = map(
        Region, ("Start", "Middle", "Distant enemy", "Empty")
    )
    party = _owned_party("Hero", "ai")
    world = WorldMap(
        [start, middle, distant_enemy, empty],
        [(start, middle), (middle, distant_enemy), (start, empty)],
        settlements={distant_enemy: _settlement("Distant enemy", "enemy")},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    not_adjacent = ai.assault_duchy_party_to(
        world, duchy, distant_enemy, _ForbiddenRng()
    )
    no_settlement = ai.assault_duchy_party_to(world, duchy, empty, _ForbiddenRng())

    assert not_adjacent is world
    assert no_settlement is world
    assert world.party_at(start) is party


def test_march_target_and_route_ties_follow_world_region_order():
    start, first, second, first_target, second_target = map(
        Region, ("Start", "First", "Second", "First target", "Second target")
    )
    party = _owned_party("Hero")
    world = WorldMap(
        [start, first, second, first_target, second_target],
        [
            (start, second), (second, second_target),
            (start, first), (first, first_target),
        ],
        settlements={
            second_target: _settlement("Second target", "enemy"),
            first_target: _settlement("First target", "enemy"),
        },
        parties={start: party},
    )

    moved = march_toward_nearest_enemy(world, start)

    assert_moved_party(moved, first, party)


@pytest.mark.parametrize("case", ["adjacent", "no_enemy", "blocked"])
def test_march_stays_put_when_no_step_is_available(case):
    start, step, target = map(Region, ("Start", "Step", "Target"))
    party = _owned_party("Hero")
    connections = [(start, target)] if case == "adjacent" else [(start, step), (step, target)]
    settlements = {} if case == "no_enemy" else {target: _settlement("Target", "enemy")}
    parties = {start: party}
    if case == "blocked":
        parties[step] = _owned_party("Blocker", "other")
    world = WorldMap([start, step, target], connections, settlements, parties)

    result = march_toward_nearest_enemy(world, start)

    assert result is world
    assert result.party_at(start) is party


def test_blocking_foreign_party_region_reports_blocked_nearest_route():
    start, step, target = map(Region, ("Start", "Step", "Target"))
    world = WorldMap(
        [start, step, target],
        [(start, step), (step, target)],
        settlements={target: _settlement("Target", "enemy")},
        parties={
            start: _owned_party("Hero", "ai"),
            step: _owned_party("Blocker", "other"),
        },
    )

    assert ai.blocking_foreign_party_region(world, start, "ai") is step


@pytest.mark.parametrize("blocker_owner", ["enemy", None])
def test_blocking_foreign_party_region_reports_explicit_adjacent_target(blocker_owner):
    start, target = Region("Start"), Region("Target")
    world = WorldMap(
        [start, target],
        [(start, target)],
        parties={
            start: _owned_party("Hero"),
            target: _owned_party("Blocker", blocker_owner),
        },
    )

    assert ai.blocking_foreign_party_region(world, start, "ai", target) is target


@pytest.mark.parametrize("blocker_owner", ["enemy", None])
def test_blocking_foreign_party_region_excludes_garrisoned_destination(blocker_owner):
    start, target, step = map(Region, ("Start", "Target", "Step"))
    world = WorldMap(
        [start, target, step],
        [(start, step), (step, target)],
        settlements={target: _settlement("Target", "enemy")},
        parties={
            start: _owned_party("Hero", "ai"),
            target: _owned_party("Garrison", "enemy"),
            step: _owned_party("Blocker", blocker_owner),
        },
    )

    assert ai.blocking_foreign_party_region(world, start, "ai") is step


def test_blocking_foreign_party_region_requires_one_party_to_unblock_route():
    start, left, right, target = map(Region, ("Start", "Left", "Right", "Target"))
    world = WorldMap(
        [start, left, right, target],
        [(start, left), (left, target), (start, right), (right, target)],
        settlements={target: _settlement("Target", "enemy")},
        parties={
            start: _owned_party("Hero", "ai"),
            left: _owned_party("Left blocker", "enemy"),
            right: _owned_party("Right blocker", "enemy"),
        },
    )

    assert ai.blocking_foreign_party_region(world, start, "ai") is None


@pytest.mark.parametrize("case", ["free_step", "no_enemy", "adjacent", "own_party"])
def test_blocking_foreign_party_region_returns_none_without_foreign_blocker(case):
    start, step, target = map(Region, ("Start", "Step", "Target"))
    connections = [(start, target)] if case == "adjacent" else [(start, step), (step, target)]
    settlements = {} if case == "no_enemy" else {target: _settlement("Target", "enemy")}
    parties = {start: _owned_party("Hero", "ai")}
    if case == "no_enemy":
        parties[step] = _owned_party("Other", "enemy")
    elif case == "adjacent":
        parties[target] = _owned_party("Other", "enemy")
    elif case == "own_party":
        parties[step] = _owned_party("Ally", "ai")
    world = WorldMap([start, step, target], connections, settlements, parties)

    assert ai.blocking_foreign_party_region(world, start, "ai") is None


def test_blocking_foreign_party_region_is_pure_and_repeatable():
    start, step, target = map(Region, ("Start", "Step", "Target"))
    party = _owned_party("Hero", "ai")
    blocker = _owned_party("Blocker", "enemy")
    settlement = _settlement("Target", "enemy")
    world = WorldMap(
        [start, step, target],
        [(start, step), (step, target)],
        settlements={target: settlement},
        parties={start: party, step: blocker},
    )
    before_parties = dict(world.parties)
    before_settlements = dict(world.settlements)

    first = ai.blocking_foreign_party_region(world, start, "ai")
    second = ai.blocking_foreign_party_region(world, start, "ai")

    assert first is step
    assert second is first
    assert dict(world.parties) == before_parties
    assert dict(world.settlements) == before_settlements
    assert world.party_at(start) is party
    assert world.party_at(step) is blocker
    assert world.settlement_at(target) is settlement


@pytest.mark.parametrize("invalid", ["start", "target", "owner"])
def test_blocking_foreign_party_region_rejects_invalid_input(invalid):
    start, target = Region("Start"), Region("Target")
    world = WorldMap([start, target], [(start, target)])
    arguments = {"start": start, "owner_id": "ai", "target": target}
    if invalid == "start":
        arguments["start"] = Region("Outside")
    elif invalid == "target":
        arguments["target"] = Region("Outside")
    else:
        arguments["owner_id"] = ""

    with pytest.raises(ValueError):
        ai.blocking_foreign_party_region(world, **arguments)


@pytest.mark.parametrize("case", ["outside", "empty", "ownerless"])
def test_march_rejects_invalid_start_or_party(case):
    start = Region("Start")
    known = Region("Known")
    parties = {known: _party("Hero")} if case == "ownerless" else {}
    world = WorldMap([known], parties=parties)
    selected = start if case == "outside" else known

    with pytest.raises(ValueError):
        march_toward_nearest_enemy(world, selected)


def test_assault_resolves_adjacent_enemy_settlement():
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    settlement = Settlement(
        "Target", population=1, garrison=(Unit(equipment=1),), owner_id="enemy"
    )
    world = WorldMap(
        [start, target],
        [(start, target)],
        settlements={target: settlement},
        parties={start: party},
    )

    resolved = assault_nearest_enemy_settlement(world, start, tbb.Rng(2))

    assert resolved == world.resolve_settlement_battle(start, target, tbb.Rng(2))
    assert resolved != world


def _run_assault_route(route, world, duchy, position, rng):
    if route == "nearest":
        return assault_nearest_enemy_settlement(world, position, rng), None
    if route == "duchy":
        return assault_duchy_party(world, duchy, rng), None
    if route == "duchy_recorded":
        return ai.assault_duchy_party_recorded(world, duchy, rng)
    if route == "explicit":
        return ai.assault_duchy_party_to(world, duchy, position, rng), None
    if route == "explicit_recorded":
        return ai.assault_duchy_party_to_recorded(
            world, duchy, position, rng
        )
    assert route == "military"
    return take_duchy_military_action(world, duchy, rng), None


@pytest.mark.parametrize(
    "route",
    [
        "nearest",
        "duchy",
        "duchy_recorded",
        "explicit",
        "explicit_recorded",
        "military",
    ],
)
def test_assault_from_enemy_settlement_resolves_in_place(route):
    """Every assault entry point can attack the settlement it occupies."""
    keep = Region("Keep")
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    settlement = Settlement("Keep", population=1, owner_id="enemy")
    world = WorldMap([keep], settlements={keep: settlement}, parties={keep: party})
    duchy = Duchy("ai", party.hero, parties=(party,))

    resolved, battle = _run_assault_route(route, world, duchy, keep, tbb.Rng(2))
    if route.endswith("_recorded"):
        assert battle is not None
    else:
        assert battle is None

    assert resolved is not world
    assert resolved.settlement_at(keep).owner_id == "ai"
    assert resolved.party_at(keep) is not None
    assert resolved.party_at(keep).acted_this_month is True


class _ForbiddenRng:
    def randint(self, *_args):
        raise AssertionError("RNG must not be consumed")

    def chance(self, *_args):
        raise AssertionError("RNG must not be consumed")


class _DefenderWinsRng:
    def chance(self, probability):
        """Make attacks above 50% hit while keeping a defeated unit stunned."""
        return probability > 0.5


@pytest.mark.parametrize(
    "route",
    [
        "nearest",
        "duchy",
        "duchy_recorded",
        "explicit",
        "explicit_recorded",
        "military",
    ],
)
def test_assault_in_place_is_noop_after_monthly_action_without_rng(route):
    keep = Region("Keep")
    party = Party(
        Unit(training=5, equipment=6),
        owner_id="ai",
        acted_this_month=True,
    )
    settlement = Settlement("Keep", population=1, owner_id="enemy")
    world = WorldMap([keep], settlements={keep: settlement}, parties={keep: party})
    duchy = Duchy("ai", party.hero, parties=(party,))

    resolved, battle = _run_assault_route(
        route, world, duchy, keep, _ForbiddenRng()
    )

    assert resolved is world
    assert battle is None
    assert world.settlement_at(keep) is settlement
    assert world.party_at(keep) is party


def test_assault_from_enemy_settlement_keeps_owner_after_defeat_and_acts():
    keep = Region("Keep")
    party = Party(Unit(), owner_id="ai")
    settlement = Settlement(
        "Keep",
        population=1,
        garrison=(Unit(training=5, equipment=12),),
        owner_id="enemy",
    )
    world = WorldMap([keep], settlements={keep: settlement}, parties={keep: party})

    resolved = assault_nearest_enemy_settlement(world, keep, _DefenderWinsRng())

    assert resolved is not world
    assert resolved.settlement_at(keep).owner_id == "enemy"
    assert resolved.party_at(keep) is not None
    assert resolved.party_at(keep).acted_this_month is True


@pytest.mark.parametrize("case", ["distant", "no_enemy"])
def test_assault_is_noop_without_adjacent_enemy_and_does_not_use_rng(case):
    start, middle, target = map(Region, ("Start", "Middle", "Target"))
    settlements = (
        {target: _settlement("Target", "enemy")} if case == "distant" else {}
    )
    world = WorldMap(
        [start, middle, target],
        [(start, middle), (middle, target)],
        settlements=settlements,
        parties={start: _owned_party("Hero")},
    )

    assert assault_nearest_enemy_settlement(world, start, _ForbiddenRng()) is world


@pytest.mark.parametrize("case", ["outside", "empty", "ownerless"])
def test_assault_rejects_invalid_start_or_party(case):
    known = Region("Known")
    parties = {known: _party("Hero")} if case == "ownerless" else {}
    world = WorldMap([known], parties=parties)
    selected = Region("Outside") if case == "outside" else known

    with pytest.raises(ValueError):
        assault_nearest_enemy_settlement(world, selected, _ForbiddenRng())


def test_assault_is_deterministic_and_preserves_input_objects():
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(equipment=5), [Unit(equipment=2)], "ai")
    settlement = Settlement(
        "Target", population=2, garrison=(Unit(equipment=4),), owner_id="enemy"
    )
    world = WorldMap(
        [start, target], [(start, target)], {target: settlement}, {start: party}
    )

    first = assault_nearest_enemy_settlement(world, start, tbb.Rng(12))
    second = assault_nearest_enemy_settlement(world, start, tbb.Rng(12))

    assert first == second
    assert world.party_at(start) is party
    assert world.settlement_at(target) is settlement
    assert party.units == (Unit(equipment=2),)
    assert settlement.owner_id == "enemy"


def test_assault_transition_is_publicly_exported():
    assert tbb.assault_nearest_enemy_settlement is assault_nearest_enemy_settlement


def test_assault_with_morale_by_owner_matches_resolve_settlement_battle():
    """Equivalence: morale_by_owner maps owner ids to resolve_* side morale."""
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(training=5, equipment=6), owner_id="att")
    settlement = Settlement(
        "Target", population=1, garrison=(Unit(equipment=1),), owner_id="def"
    )
    world = WorldMap(
        [start, target],
        [(start, target)],
        settlements={target: settlement},
        parties={start: party},
    )
    seed = 7
    attacker_morale = 30
    defender_morale = -15
    morale_by_owner = {"att": attacker_morale, "def": defender_morale}

    via_assault = assault_nearest_enemy_settlement(
        world, start, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )
    via_resolve = world.resolve_settlement_battle(
        start,
        target,
        tbb.Rng(seed),
        attacker_morale=attacker_morale,
        defender_morale=defender_morale,
    )

    assert via_assault == via_resolve
    assert world.party_at(start) is party
    assert world.settlement_at(target) is settlement
    assert settlement.owner_id == "def"


def test_assault_morale_by_owner_none_matches_omitted_argument():
    """Backward compat: morale_by_owner=None is identical to omitting the arg."""
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(training=5, equipment=6), owner_id="att")
    settlement = Settlement(
        "Target", population=1, garrison=(Unit(equipment=1),), owner_id="def"
    )
    world = WorldMap(
        [start, target],
        [(start, target)],
        settlements={target: settlement},
        parties={start: party},
    )
    seed = 3

    without_arg = assault_nearest_enemy_settlement(world, start, tbb.Rng(seed))
    with_none = assault_nearest_enemy_settlement(
        world, start, tbb.Rng(seed), morale_by_owner=None
    )

    assert with_none == without_arg


def test_muster_duchy_party_moves_hero_and_garrison_without_mutating_input():
    home = Region("Home")
    hero = Unit(training=4)
    garrison = (Unit(equipment=1), Unit(experience=2))
    settlement = Settlement(
        "Home", population=3, occupied=2, garrison=garrison, owner_id="ai"
    )
    world = WorldMap([home], settlements={home: settlement})
    duchy = Duchy("ai", hero, settlements=(settlement,))

    mustered = muster_duchy_party(world, duchy)

    assert mustered.party_at(home) == Party(hero, garrison[:1], owner_id="ai")
    assert mustered.party_at(home).units == garrison[:1]
    assert mustered.settlement_at(home).garrison == garrison[1:]
    assert mustered.settlement_at(home).population == settlement.population - 1
    assert mustered.settlement_at(home).occupied == settlement.occupied - 1
    assert world.settlement_at(home) is settlement
    assert world.party_at(home) is None
    assert settlement.garrison == garrison
    assert duchy.hero is hero
    assert duchy.settlements == (settlement,)


def test_muster_duchy_party_tie_uses_world_region_order():
    first, second = Region("First"), Region("Second")
    first_settlement = Settlement("First", 1, owner_id="ai")
    second_settlement = Settlement("Second", 1, owner_id="ai")
    world = WorldMap(
        [first, second],
        settlements={second: second_settlement, first: first_settlement},
    )

    mustered = muster_duchy_party(world, Duchy("ai", Unit()))

    assert mustered.party_at(first) is not None
    assert mustered.party_at(second) is None


def test_muster_duchy_party_is_noop_when_party_already_exists():
    home, camp = Region("Home"), Region("Camp")
    hero = Unit(training=3)
    garrison = (Unit(),)
    settlement = Settlement("Home", 2, 1, garrison=garrison, owner_id="ai")
    party = Party(hero, owner_id="ai")
    world = WorldMap(
        [home, camp], settlements={home: settlement}, parties={camp: party}
    )

    assert muster_duchy_party(world, Duchy("ai", hero)) is world
    assert world.settlement_at(home).garrison == garrison


@pytest.mark.parametrize("case", ["no_hero", "no_own_settlement", "all_occupied"])
def test_muster_duchy_party_is_noop_without_eligible_source(case):
    own, other = Region("Own"), Region("Other")
    hero = None if case == "no_hero" else Unit()
    owner = "enemy" if case == "no_own_settlement" else "ai"
    settlement = Settlement("Seat", 1, owner_id=owner)
    parties = {own: Party(Unit(), owner_id="enemy")} if case == "all_occupied" else {}
    world = WorldMap([own, other], settlements={own: settlement}, parties=parties)

    assert muster_duchy_party(world, Duchy("ai", hero)) is world


def test_muster_duchy_party_transition_is_publicly_exported():
    assert tbb.muster_duchy_party is muster_duchy_party


@pytest.mark.parametrize(
    "target_name, mustered_name",
    [
        ("second", "second"),
        ("foreign", None),
        ("unowned", None),
        ("occupied", None),
        ("empty", None),
    ],
)
def test_muster_duchy_party_honors_indicated_region_target(
    target_name, mustered_name
):
    foreign, unowned, occupied, first, second, empty = map(
        Region, ("Foreign", "Unowned", "Occupied", "First", "Second", "Empty")
    )
    named = {
        "foreign": foreign,
        "unowned": unowned,
        "occupied": occupied,
        "first": first,
        "second": second,
        "empty": empty,
    }
    hero = Unit(training=3)
    guard = (Unit(equipment=1), Unit(experience=2))
    settlements = {
        foreign: Settlement(
            "Foreign", population=2, occupied=2, garrison=guard, owner_id="enemy"
        ),
        unowned: Settlement(
            "Unowned", population=2, occupied=2, garrison=guard
        ),
        occupied: Settlement(
            "Occupied", population=2, occupied=2, garrison=guard, owner_id="ai"
        ),
        first: Settlement(
            "First", population=2, occupied=2, garrison=guard, owner_id="ai"
        ),
        second: Settlement(
            "Second", population=2, occupied=2, garrison=guard, owner_id="ai"
        ),
    }
    world = WorldMap(
        [foreign, unowned, occupied, first, second, empty],
        settlements=settlements,
        parties={occupied: Party(Unit(), owner_id="enemy")},
    )
    duchy = Duchy("ai", hero)

    result = muster_duchy_party(world, duchy, target=named[target_name])

    if mustered_name is None:
        assert result is world
        for region in (first, second):
            assert result.party_at(region) is None
            assert result.settlement_at(region).garrison == guard
    else:
        mustered = named[mustered_name]
        assert result.party_at(mustered) == Party(hero, guard[:1], owner_id="ai")
        assert result.settlement_at(mustered).garrison == guard[1:]
        for region in (first, second):
            if region is not mustered:
                assert result.party_at(region) is None
                assert result.settlement_at(region).garrison == guard


def test_duchy_military_action_musters_and_marches_once():
    home, road, target = map(Region, ("Home", "Road", "Target"))
    hero = Unit(training=5, equipment=6)
    guard = Unit(equipment=2)
    home_settlement = Settlement(
        "Home", 2, occupied=1, garrison=(guard,), owner_id="ai"
    )
    enemy_settlement = Settlement(
        "Target", 1, garrison=(Unit(),), owner_id="enemy"
    )
    world = WorldMap(
        [home, road, target],
        [(home, road), (road, target)],
        {home: home_settlement, target: enemy_settlement},
    )
    duchy = Duchy("ai", hero, settlements=(home_settlement,))

    result = take_duchy_military_action(world, duchy, tbb.Rng(4))
    mustered = muster_duchy_party(world, duchy)
    marched = march_toward_nearest_enemy(mustered, home)

    assert result == marched
    assert result.party_at(road) is not None
    assert result.party_at(target) is None
    assert result.settlement_at(target) is enemy_settlement


def test_duchy_military_action_respects_monthly_marker_after_march():
    start, road, target = map(Region, ("Start", "Road", "Target"))
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    world = WorldMap(
        [start, road, target],
        [(start, road), (road, target)],
        {target: Settlement("Target", 1, garrison=(Unit(),), owner_id="enemy")},
        {start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result = take_duchy_military_action(world, duchy, tbb.Rng(8))
    marched = march_toward_nearest_enemy(world, start)

    assert result == marched
    assert result.party_at(road) is not None
    assert result.party_at(target) is None
    assert world.party_at(start) is party


def test_duchy_military_action_keeps_party_when_enemy_garrison_is_stronger():
    """A hopeless adjacent assault leaves the AI party in the field."""
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(), owner_id="ai")
    settlement = Settlement(
        "Target",
        1,
        garrison=(Unit(training=5, equipment=12),),
        owner_id="enemy",
    )
    world = WorldMap(
        [start, target],
        [(start, target)],
        {target: settlement},
        {start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result = take_duchy_military_action(world, duchy, tbb.Rng(8))

    assert result is world
    assert result.party_at(start) is party
    assert result.settlement_at(target) is settlement


def test_duchy_military_action_returns_to_adjacent_own_garrison_after_failed_assault():
    """A failed assault makes a field party take one step toward own supplies.

    Realistic defect: the existing AI falls through to the enemy march after
    rejecting an adjacent assault, so it ends the month in place even when an
    adjacent own settlement has a reachable non-empty garrison.
    """
    start, home, target = map(Region, ("Start", "Home", "Target"))
    party = Party(Unit(), owner_id="ai")
    own_settlement = Settlement(
        "Home", 1, garrison=(Unit(),), owner_id="ai"
    )
    enemy_settlement = Settlement(
        "Target",
        1,
        garrison=(Unit(training=5, equipment=12),),
        owner_id="enemy",
    )
    world = WorldMap(
        [start, home, target],
        [(start, home), (start, target)],
        settlements={home: own_settlement, target: enemy_settlement},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result = take_duchy_military_action(world, duchy, tbb.Rng(8))

    assert result is not world
    assert_moved_party(result, home, party)
    assert result.party_at(start) is None
    assert result.party_at(target) is None
    assert result.settlement_at(home) is own_settlement
    assert result.settlement_at(target) is enemy_settlement


def test_duchy_military_action_returns_to_distant_own_garrison_by_first_step():
    """A distant garrison fallback follows its first free route step."""
    start, step, home, target = map(Region, ("Start", "Step", "Home", "Target"))
    party = Party(Unit(), owner_id="ai")
    own_settlement = Settlement("Home", 1, garrison=(Unit(),), owner_id="ai")
    enemy_settlement = Settlement(
        "Target",
        1,
        garrison=(Unit(training=5, equipment=12),),
        owner_id="enemy",
    )
    world = WorldMap(
        [start, step, home, target],
        [(start, step), (step, home), (start, target)],
        settlements={home: own_settlement, target: enemy_settlement},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result = take_duchy_military_action(world, duchy, tbb.Rng(8))

    assert result is not world
    assert_moved_party(result, step, party)
    assert result.party_at(step).acted_this_month is True
    assert result.party_at(start) is None
    assert result.party_at(home) is None
    assert result.party_at(target) is None
    assert result.settlement_at(home) is own_settlement
    assert result.settlement_at(target) is enemy_settlement


def test_duchy_military_action_keeps_old_march_when_garrison_route_is_blocked():
    """A foreign party blocking the fallback route must preserve the old march."""
    start, blocked, home, enemy_road, target = map(
        Region, ("Start", "Blocked", "Home", "Enemy Road", "Target")
    )
    party = Party(Unit(), owner_id="ai")
    blocker = Party(Unit(), owner_id="enemy")
    own_settlement = Settlement(
        "Home", 1, garrison=(Unit(),), owner_id="ai"
    )
    enemy_settlement = Settlement(
        "Target",
        1,
        garrison=(Unit(training=5, equipment=12),),
        owner_id="enemy",
    )
    world = WorldMap(
        [start, blocked, home, enemy_road, target],
        [
            (start, blocked),
            (blocked, home),
            (start, enemy_road),
            (enemy_road, target),
        ],
        settlements={home: own_settlement, target: enemy_settlement},
        parties={start: party, blocked: blocker},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result = take_duchy_military_action(world, duchy, tbb.Rng(8))

    assert result == march_toward_nearest_enemy(world, start)
    assert_moved_party(result, enemy_road, party)
    assert result.party_at(blocked) is blocker
    assert result.settlement_at(home) is own_settlement
    assert result.settlement_at(target) is enemy_settlement


@pytest.mark.parametrize(
    ("defender", "expected_action"),
    [(Unit(), "assault"), (Unit(equipment=1), "return")],
)
def test_duchy_military_action_preserves_the_exact_two_to_one_assault_gate(
    defender, expected_action
):
    """The return fallback never changes the existing 2:1 assault threshold."""
    start, home, target = map(Region, ("Start", "Home", "Target"))
    party = Party(Unit(), (Unit(),), owner_id="ai")
    own_garrison = (Unit(),)
    own_settlement = Settlement(
        "Home", 1, garrison=own_garrison, owner_id="ai"
    )
    enemy_settlement = Settlement(
        "Target", 1, garrison=(defender,), owner_id="enemy"
    )
    world = WorldMap(
        [start, home, target],
        [(start, home), (start, target)],
        settlements={home: own_settlement, target: enemy_settlement},
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result = take_duchy_military_action(world, duchy, tbb.Rng(9))

    if expected_action == "assault":
        assert result == assault_nearest_enemy_settlement(world, start, tbb.Rng(9))
        assert result.settlement_at(home).garrison == own_garrison
    else:
        assert_moved_party(result, home, party)
        assert result.party_at(target) is None
        assert result.settlement_at(target) is enemy_settlement


def test_seed_73_passive_player_is_defeated_by_thirteenth_turn():
    """No player order on seed 73 still ends in an AI victory by turn 13."""
    world, game = create_headless_game()
    result_world, result_game, calendar = run_headless_game(
        world, game, tbb.Rng(73), max_turns=13, player_duchy_id="player"
    )

    elapsed_turns = (calendar.year - 1) * 13 + calendar.month - 1
    assert game_state(result_world, result_game, calendar, "player")["result"] == {
        "is_over": True,
        "winner": "ai",
        "player_result": "defeat",
    }
    assert elapsed_turns <= 13


def test_seed_73_active_player_wins_in_first_year_month_four():
    """The measured assault/engage/march player path still wins in R1M4."""
    session = new_session(73)
    commands = (
        {"type": "order", "order": "recruit"},
        {"type": "order", "order": "recruit"},
        {"type": "order", "order": "muster"},
        {"type": "order", "order": "march"},
        {"type": "next_turn"},
        {"type": "order", "order": "engage", "target": "border"},
        {"type": "next_turn"},
        {"type": "order", "order": "assault", "target": "ai outpost"},
        {"type": "next_turn"},
        {"type": "order", "order": "assault", "target": "ai lands"},
    )

    for command in commands:
        session = apply_command(session, command)

    assert session.snapshot()["result"] == {
        "is_over": True,
        "winner": "player",
        "player_result": "victory",
    }
    assert (session.calendar.year, session.calendar.month) == (1, 4)


@pytest.mark.parametrize("owner_id", ["ai", "player"])
def test_duchy_military_action_reinforces_before_march_when_assault_lacks_advantage(
    owner_id,
):
    home, road, target = map(Region, ("Home", "Road", "Target"))
    hero = Unit()
    garrison = (Unit(), Unit(experience=2))
    home_settlement = Settlement(
        "Home", 3, occupied=2, garrison=garrison, owner_id=owner_id
    )
    enemy_settlement = Settlement(
        "Target",
        1,
        garrison=(Unit(training=5, equipment=12),),
        owner_id="enemy",
    )
    party = Party(hero, owner_id=owner_id)
    world = WorldMap(
        [home, road, target],
        [(home, road), (road, target)],
        {home: home_settlement, target: enemy_settlement},
        {home: party},
    )
    duchy = Duchy(owner_id, hero, parties=(party,))

    result = take_duchy_military_action(world, duchy, tbb.Rng(8))

    reinforced = result.party_at(home)
    assert reinforced is not None
    assert len(reinforced.units) == len(garrison) - 1
    assert reinforced.acted_this_month is True
    assert result.party_at(road) is None
    remaining = result.settlement_at(home).garrison
    assert len(remaining) == 1
    assert Counter(reinforced.units) + Counter(remaining) == Counter(garrison)
    assert result.settlement_at(home).population == home_settlement.population - 1
    assert result.settlement_at(home).occupied == home_settlement.occupied - 1
    assert result.settlement_at(target).owner_id == "enemy"


@pytest.mark.parametrize(
    "case",
    ["no_settlement", "empty_garrison", "full_party", "strong_non_adjacent"],
)
def test_duchy_military_action_keeps_marching_when_reinforcement_is_not_applicable(
    case,
):
    """No-op reinforcement and a non-legal strong assault preserve the march.

    Realistic defect: an unconditional reinforcement fallback consumes the
    action when a strong party's nearest target is not legally assaultable.
    """
    home, road, target = map(Region, ("Home", "Road", "Target"))
    enemy_settlement = Settlement(
        "Target",
        1,
        garrison=(
            Unit()
            if case == "strong_non_adjacent"
            else Unit(training=100, equipment=100),
        ),
        owner_id="enemy",
    )
    own_garrison = () if case == "empty_garrison" else (Unit(),)
    settlements = {target: enemy_settlement}
    if case != "no_settlement":
        settlements[home] = Settlement(
            "Home", 1, occupied=1, garrison=own_garrison, owner_id="ai"
        )
    subordinate_count = {
        "strong_non_adjacent": Party.MAX_SUBORDINATES - 1,
        "full_party": Party.MAX_SUBORDINATES,
    }.get(case, 0)
    units = (Unit(),) * subordinate_count
    party = Party(Unit(), units, owner_id="ai")
    world = WorldMap(
        [home, road, target],
        [(home, road), (road, target)],
        settlements,
        {home: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result = take_duchy_military_action(world, duchy, tbb.Rng(8))

    assert result == march_toward_nearest_enemy(world, home)
    assert result.party_at(home) is None
    assert result.party_at(road) is not None
    assert result.party_at(road).acted_this_month is True
    assert result.settlement_at(target).owner_id == "enemy"
    if case != "no_settlement":
        assert result.settlement_at(home).garrison == own_garrison


@pytest.mark.parametrize(
    ("hero", "defender"),
    [
        (Unit(training=5, equipment=6), Unit(equipment=1)),
        (Unit(equipment=5), Unit()),
    ],
)
def test_duchy_military_action_assaults_before_reinforcing_with_advantage(
    hero, defender
):
    start, target = Region("Start"), Region("Target")
    garrison = (Unit(experience=2),)
    own_settlement = Settlement(
        "Start", 1, occupied=1, garrison=garrison, owner_id="ai"
    )
    enemy_settlement = Settlement(
        "Target", 1, garrison=(defender,), owner_id="enemy"
    )
    party = Party(hero, owner_id="ai")
    world = WorldMap(
        [start, target],
        [(start, target)],
        {start: own_settlement, target: enemy_settlement},
        {start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result = take_duchy_military_action(world, duchy, tbb.Rng(9))

    assert result == assault_nearest_enemy_settlement(world, start, tbb.Rng(9))
    assert result.settlement_at(start).garrison == garrison


@pytest.mark.parametrize("case", ["no_hero", "no_source", "no_enemy"])
def test_duchy_military_action_noop_does_not_use_rng_without_battle(case):
    home = Region("Home")
    hero = None if case == "no_hero" else Unit()
    settlements = (
        {home: Settlement("Home", 1, owner_id="ai")}
        if case != "no_source"
        else {}
    )
    parties = {home: Party(hero, owner_id="ai")} if case == "no_enemy" else {}
    world = WorldMap([home], settlements=settlements, parties=parties)

    assert take_duchy_military_action(world, Duchy("ai", hero), _ForbiddenRng()) is world


def test_duchy_military_action_discards_successful_muster_without_enemy_target():
    home = Region("Home")
    hero = Unit()
    garrison = (Unit(),)
    settlement = Settlement(
        "Home", 2, occupied=1, garrison=garrison, owner_id="ai"
    )
    world = WorldMap([home], settlements={home: settlement})

    result = take_duchy_military_action(world, Duchy("ai", hero), _ForbiddenRng())

    assert result is world
    assert world.party_at(home) is None
    assert world.settlement_at(home) is settlement
    assert settlement.garrison == garrison


def test_duchy_military_action_is_deterministic_and_preserves_inputs():
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(equipment=5), owner_id="ai")
    settlement = Settlement(
        "Target", 1, garrison=(Unit(equipment=4),), owner_id="enemy"
    )
    world = WorldMap(
        [start, target], [(start, target)], {target: settlement}, {start: party}
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    first = take_duchy_military_action(world, duchy, tbb.Rng(12))
    second = take_duchy_military_action(world, duchy, tbb.Rng(12))

    assert first == second
    assert world.party_at(start) is party
    assert world.settlement_at(target) is settlement
    assert duchy.parties == (party,)


def test_duchy_military_action_is_publicly_exported():
    assert tbb.take_duchy_military_action is take_duchy_military_action


def test_duchy_military_action_threads_morale_by_owner_to_assault():
    """Equivalence: morale_by_owner reaches assault with identical seed/map."""
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    settlement = Settlement(
        "Target", 1, garrison=(Unit(equipment=1),), owner_id="enemy"
    )
    world = WorldMap(
        [start, target],
        [(start, target)],
        {target: settlement},
        {start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))
    seed = 9
    morale_by_owner = {"ai": 40, "enemy": -20}

    via_military = take_duchy_military_action(
        world, duchy, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )
    via_assault = assault_nearest_enemy_settlement(
        world, start, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )

    assert via_military == via_assault
    assert world.party_at(start) is party
    assert world.settlement_at(target) is settlement


def test_duchy_turn_threads_morale_by_owner_when_develop_and_recruit_are_noop():
    """Equivalence: take_duchy_turn ≡ take_duchy_military_action with same morale."""
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    settlement = Settlement(
        "Target", 1, garrison=(Unit(equipment=1),), owner_id="enemy"
    )
    world = WorldMap(
        [start, target],
        [(start, target)],
        {target: settlement},
        {start: party},
    )
    # No owned settlements / free pop / gold → develop + recruit are no-ops.
    duchy = Duchy("ai", party.hero, parties=(party,))
    seed = 9
    morale_by_owner = {"ai": 40, "enemy": -20}

    via_turn = take_duchy_turn(
        world, duchy, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )
    via_military = take_duchy_military_action(
        world, duchy, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )

    assert via_turn == via_military
    assert world.party_at(start) is party
    assert world.settlement_at(target) is settlement


def test_recruit_duchy_unit_adds_exactly_one_fresh_unit_without_mutating_inputs():
    home = Region("Home")
    settlement = Settlement(
        "Home",
        3,
        occupied=1,
        storage=Resources(0, 1),
        garrison=(Unit(training=1),),
        owner_id="ai",
    )
    world = WorldMap([home], settlements={home: settlement})
    duchy = Duchy("ai", Unit(), settlements=(settlement,))

    recruited = recruit_duchy_unit(world, duchy)

    updated = recruited.settlement_at(home)
    assert updated.occupied == settlement.occupied + 1
    assert len(updated.garrison) == len(settlement.garrison) + 1
    assert updated.garrison[:-1] == settlement.garrison
    assert updated.garrison[-1].damage > 0
    assert updated.garrison[-1].defense > 0
    assert world.settlement_at(home) is settlement
    assert settlement.occupied == 1
    assert settlement.garrison == (Unit(training=1),)
    assert duchy.settlements == (settlement,)


def test_recruit_duchy_unit_uses_region_order_not_settlement_mapping_order():
    first, second = Region("First"), Region("Second")
    first_settlement = Settlement(
        "First", 1, storage=Resources(0, 1), owner_id="ai"
    )
    second_settlement = Settlement(
        "Second", 1, storage=Resources(0, 1), owner_id="ai"
    )
    world = WorldMap(
        [first, second],
        settlements={second: second_settlement, first: first_settlement},
    )

    recruited = recruit_duchy_unit(world, Duchy("ai", Unit()))

    first_garrison = recruited.settlement_at(first).garrison
    assert len(first_garrison) == 1
    assert first_garrison[0].damage > 0
    assert first_garrison[0].defense > 0
    assert recruited.settlement_at(second) is second_settlement


def test_recruit_duchy_unit_uses_settlement_module_gold_cost(monkeypatch):
    first, second = Region("First"), Region("Second")
    first_settlement = Settlement(
        "First", 1, storage=Resources(0, 1), owner_id="ai"
    )
    second_settlement = Settlement(
        "Second", 1, storage=Resources(0, 2), owner_id="ai"
    )
    world = WorldMap(
        [first, second],
        settlements={first: first_settlement, second: second_settlement},
    )
    monkeypatch.setattr(settlement_module, "RECRUIT_GOLD_COST", 2)

    recruited = recruit_duchy_unit(world, Duchy("ai", Unit()))

    assert recruited.settlement_at(first) is first_settlement
    second_garrison = recruited.settlement_at(second).garrison
    assert len(second_garrison) == 1
    assert second_garrison[0].damage > 0
    assert second_garrison[0].defense > 0
    assert recruited.settlement_at(second).storage == Resources(0, 0)


def test_recruit_duchy_unit_skips_every_ineligible_settlement():
    foreign, unowned, no_free, full, eligible = map(
        Region, ("Foreign", "Unowned", "No free", "Full", "Eligible")
    )
    full_garrison = tuple(Unit(experience=index) for index in range(12))
    settlements = {
        foreign: Settlement("Foreign", 1, owner_id="enemy"),
        unowned: Settlement("Unowned", 1),
        no_free: Settlement("No free", 1, occupied=1, owner_id="ai"),
        full: Settlement(
            "Full", 13, occupied=12, garrison=full_garrison, owner_id="ai"
        ),
        eligible: Settlement(
            "Eligible", 1, storage=Resources(0, 1), owner_id="ai"
        ),
    }
    world = WorldMap(
        [foreign, unowned, no_free, full, eligible], settlements=settlements
    )

    recruited = recruit_duchy_unit(world, Duchy("ai", Unit()))

    eligible_garrison = recruited.settlement_at(eligible).garrison
    assert len(eligible_garrison) == 1
    assert eligible_garrison[0].damage > 0
    assert eligible_garrison[0].defense > 0
    for region in (foreign, unowned, no_free, full):
        assert recruited.settlement_at(region) is settlements[region]


def test_recruit_duchy_unit_is_noop_without_eligible_settlement():
    home = Region("Home")
    settlement = Settlement("Home", 1, occupied=1, owner_id="ai")
    world = WorldMap([home], settlements={home: settlement})
    duchy = Duchy("ai", Unit(), settlements=(settlement,))

    assert recruit_duchy_unit(world, duchy) is world
    assert world.settlement_at(home) is settlement
    assert duchy.settlements == (settlement,)


def test_recruit_duchy_unit_is_publicly_exported():
    assert tbb.recruit_duchy_unit is recruit_duchy_unit


@pytest.mark.parametrize(
    "target_name, recruited_name",
    [
        ("second", "second"),
        ("foreign", None),
        ("unowned", None),
        ("no_gold", None),
        ("no_free", None),
        ("full", None),
        ("empty", None),
    ],
)
def test_recruit_duchy_unit_honors_indicated_region_target(
    target_name, recruited_name
):
    foreign, unowned, no_gold, no_free, full, first, second, empty = map(
        Region,
        (
            "Foreign",
            "Unowned",
            "No gold",
            "No free",
            "Full",
            "First",
            "Second",
            "Empty",
        ),
    )
    named = {
        "foreign": foreign,
        "unowned": unowned,
        "no_gold": no_gold,
        "no_free": no_free,
        "full": full,
        "first": first,
        "second": second,
        "empty": empty,
    }
    full_garrison = tuple(Unit(experience=index) for index in range(12))
    settlements = {
        foreign: Settlement(
            "Foreign", population=1, storage=Resources(0, 1), owner_id="enemy"
        ),
        unowned: Settlement("Unowned", population=1, storage=Resources(0, 1)),
        no_gold: Settlement("No gold", population=1, owner_id="ai"),
        no_free: Settlement(
            "No free",
            population=1,
            occupied=1,
            storage=Resources(0, 1),
            owner_id="ai",
        ),
        full: Settlement(
            "Full",
            population=13,
            occupied=12,
            garrison=full_garrison,
            storage=Resources(0, 1),
            owner_id="ai",
        ),
        first: Settlement(
            "First", population=1, storage=Resources(0, 1), owner_id="ai"
        ),
        second: Settlement(
            "Second", population=1, storage=Resources(0, 1), owner_id="ai"
        ),
    }
    world = WorldMap(
        [foreign, unowned, no_gold, no_free, full, first, second, empty],
        settlements=settlements,
    )
    duchy = Duchy("ai", Unit())

    result = recruit_duchy_unit(world, duchy, target=named[target_name])

    if recruited_name is None:
        assert result is world
        for region in (first, second):
            assert result.settlement_at(region).garrison == ()
            assert result.settlement_at(region).occupied == 0
    else:
        recruited = named[recruited_name]
        recruited_settlement = result.settlement_at(recruited)
        assert len(recruited_settlement.garrison) == 1
        assert recruited_settlement.garrison[0].damage > 0
        assert recruited_settlement.garrison[0].defense > 0
        assert recruited_settlement.occupied == 1
        assert recruited_settlement.storage == Resources(0, 0)
        for region in (first, second):
            if region is not recruited:
                assert result.settlement_at(region).garrison == ()
                assert result.settlement_at(region).occupied == 0


def test_development_priorities_are_farm_smith_barracks_market():
    """G54.1b: AI opens Barracks third, after Farm and Smith, before Market."""
    assert ai._DEVELOPMENT_PRIORITIES == (
        tbb.FARM,
        tbb.SMITH,
        tbb.BARRACKS,
        tbb.MARKET,
    )


def test_develop_duchy_settlement_fulfills_priority_selection_and_purity_contract():
    foreign, unowned, full, first, second = map(
        Region, ("Foreign", "Unowned", "Full", "First", "Second")
    )
    party = Party(Unit(), owner_id="ai")
    settlements = {
        foreign: Settlement("Foreign", population=1, owner_id="enemy"),
        unowned: Settlement("Unowned", population=1),
        full: Settlement("Full", population=1, occupied=1, owner_id="ai"),
        first: Settlement("First", population=4, owner_id="ai"),
        second: Settlement("Second", population=3, owner_id="ai"),
    }
    world_regions = [foreign, unowned, full, first, second]
    world = WorldMap(
        world_regions,
        settlements={
            region: settlements[region] for region in reversed(world_regions)
        },
        parties={second: party},
    )
    duchy = Duchy("ai", Unit())

    developed = develop_duchy_settlement(world, duchy)
    repeated = develop_duchy_settlement(world, duchy)

    assert developed.settlement_at(first).active_buildings == (tbb.FARM,)
    assert developed.settlement_at(first).occupied == tbb.FARM.staff
    assert repeated == developed
    assert developed.regions is world.regions
    assert developed.connections is world.connections
    assert developed.party_at(second) is party
    for region in (foreign, unowned, full, second):
        assert developed.settlement_at(region) is settlements[region]
    for region in world_regions:
        assert world.settlement_at(region) is settlements[region]

    with_smith = develop_duchy_settlement(developed, duchy)
    assert with_smith.settlement_at(first).active_buildings == (tbb.FARM, tbb.SMITH)
    with_barracks = develop_duchy_settlement(with_smith, duchy)
    assert with_barracks.settlement_at(first).active_buildings == (
        tbb.FARM,
        tbb.SMITH,
        tbb.BARRACKS,
    )
    with_market = develop_duchy_settlement(with_barracks, duchy)
    assert with_market.settlement_at(first).active_buildings == (
        tbb.FARM,
        tbb.SMITH,
        tbb.BARRACKS,
        tbb.MARKET,
    )

    no_candidate = develop_duchy_settlement(with_market, duchy)
    assert no_candidate.settlement_at(second).active_buildings == (tbb.FARM,)
    exhausted_world = WorldMap(
        [foreign, unowned, full],
        settlements={
            region: settlements[region] for region in (foreign, unowned, full)
        },
    )
    assert develop_duchy_settlement(exhausted_world, duchy) is exhausted_world


@pytest.mark.parametrize(
    "target_name, developed_name",
    [
        ("second", "second"),
        ("empty", None),
        ("foreign", None),
        ("unowned", None),
        ("full", None),
        ("built", None),
    ],
)
def test_develop_duchy_settlement_honors_indicated_region_target(
    target_name, developed_name
):
    foreign, unowned, full, built, first, second, empty = map(
        Region,
        ("Foreign", "Unowned", "Full", "Built", "First", "Second", "Empty"),
    )
    named = {
        "foreign": foreign,
        "unowned": unowned,
        "full": full,
        "built": built,
        "first": first,
        "second": second,
        "empty": empty,
    }
    settlements = {
        foreign: Settlement("Foreign", population=1, owner_id="enemy"),
        unowned: Settlement("Unowned", population=1),
        full: Settlement("Full", population=1, occupied=1, owner_id="ai"),
        built: Settlement(
            "Built",
            population=8,
            occupied=4,
            active_buildings=(tbb.FARM, tbb.SMITH, tbb.BARRACKS, tbb.MARKET),
            owner_id="ai",
        ),
        first: Settlement("First", population=4, owner_id="ai"),
        second: Settlement("Second", population=3, owner_id="ai"),
    }
    world = WorldMap(
        [foreign, unowned, full, built, first, second, empty],
        settlements=settlements,
    )
    duchy = Duchy("ai", Unit())

    result = develop_duchy_settlement(world, duchy, target=named[target_name])

    if developed_name is None:
        assert result == world
        assert result.settlement_at(first).active_buildings == ()
        assert result.settlement_at(second).active_buildings == ()
    else:
        developed = named[developed_name]
        assert result.settlement_at(developed).active_buildings == (tbb.FARM,)
        assert result.settlement_at(developed).occupied == tbb.FARM.staff
        for region in (first, second):
            if region is not developed:
                assert result.settlement_at(region).active_buildings == ()


def test_develop_duchy_settlement_rejects_target_outside_the_world():
    home = Region("Home")
    world = WorldMap(
        [home], settlements={home: Settlement("Home", population=4, owner_id="ai")}
    )
    duchy = Duchy("ai", Unit())

    with pytest.raises(ValueError):
        develop_duchy_settlement(world, duchy, target=Region("Outside"))


def test_duchy_turn_develops_farm_before_recruiting_one_unit():
    home = Region("Home")
    settlement = Settlement(
        "Home", population=3, storage=Resources(0, 1), owner_id="ai"
    )
    world = WorldMap([home], settlements={home: settlement})
    duchy = Duchy("ai", Unit(), settlements=(settlement,))

    result = take_duchy_turn(world, duchy, tbb.Rng(31))

    updated = result.settlement_at(home)
    assert updated.active_buildings == (tbb.FARM,)
    assert len(updated.garrison) == 1
    assert updated.garrison[0].damage > 0
    assert updated.garrison[0].defense > 0
    assert world.settlement_at(home) is settlement
    assert settlement.active_buildings == ()
    assert settlement.garrison == ()


def test_consecutive_duchy_turns_advance_from_farm_to_smith_without_enemy():
    home = Region("Home")
    hero = Unit(training=2)
    settlement = Settlement(
        "Home", population=5, storage=Resources(0, 2), owner_id="ai"
    )
    world = WorldMap([home], settlements={home: settlement})
    duchy = Duchy("ai", hero, settlements=(settlement,))

    def take_two_turns():
        rng = tbb.Rng(37)
        first = take_duchy_turn(world, duchy, rng)
        second = take_duchy_turn(first, duchy, rng)
        return first, second

    first, second = take_two_turns()
    repeated_first, repeated_second = take_two_turns()

    assert first.settlement_at(home).active_buildings == (tbb.FARM,)
    assert second.settlement_at(home).active_buildings == (tbb.FARM, tbb.SMITH)
    assert len(first.settlement_at(home).garrison) == 1
    assert len(second.settlement_at(home).garrison) == 2
    assert dict(first.parties) == {}
    assert dict(second.parties) == {}
    assert (repeated_first, repeated_second) == (first, second)

    assert world.settlement_at(home) is settlement
    assert dict(world.parties) == {}
    assert settlement.active_buildings == ()
    assert settlement.garrison == ()
    assert settlement.occupied == 0
    assert settlement.storage == Resources(0, 2)
    assert duchy.hero is hero
    assert duchy.settlements == (settlement,)
    assert duchy.parties == ()


def test_duchy_turn_development_uses_last_free_resident_before_recruitment():
    home = Region("Home")
    settlement = Settlement(
        "Home", population=1, storage=Resources(0, 1), owner_id="ai"
    )
    world = WorldMap([home], settlements={home: settlement})
    duchy = Duchy("ai", Unit(), settlements=(settlement,))

    result = take_duchy_turn(world, duchy, tbb.Rng(31))

    updated = result.settlement_at(home)
    assert updated.active_buildings == (tbb.FARM,)
    assert updated.garrison == ()
    assert updated.storage == Resources(0, 1)


def test_duchy_turn_recruits_and_marches_when_all_buildings_are_already_open():
    home, road, front, target = map(Region, ("Home", "Road", "Front", "Target"))
    hero = Unit(training=2)
    settlement = Settlement(
        "Home",
        population=5,
        occupied=4,
        active_buildings=(tbb.FARM, tbb.SMITH, tbb.BARRACKS, tbb.MARKET),
        storage=Resources(0, 1),
        owner_id="ai",
    )
    world = WorldMap(
        [home, road, front, target],
        [(home, road), (road, front), (front, target)],
        {home: settlement, target: _settlement("Target", "enemy")},
    )
    duchy = Duchy("ai", hero, settlements=(settlement,))

    result = take_duchy_turn(world, duchy, _ForbiddenRng())

    marched = result.party_at(road)
    assert marched is not None
    assert marched.hero is hero
    assert marched.owner_id == "ai"
    assert marched.units == ()
    assert len(result.settlement_at(home).garrison) == 1
    assert result.settlement_at(home).active_buildings == settlement.active_buildings
    assert result.settlement_at(home).storage == Resources(0, 0)
    assert world.settlement_at(home) is settlement
    assert world.party_at(road) is None


def test_duchy_turn_recruits_before_muster_and_march():
    home, road, target = map(Region, ("Home", "Road", "Target"))
    hero = Unit(training=8, equipment=8)
    home_settlement = Settlement(
        "Home", 2, storage=Resources(0, 1), owner_id="ai"
    )
    enemy_settlement = Settlement(
        "Target", 1, garrison=(Unit(),), owner_id="enemy"
    )
    world = WorldMap(
        [home, road, target],
        [(home, road), (road, target)],
        {home: home_settlement, target: enemy_settlement},
    )
    duchy = Duchy("ai", hero, settlements=(home_settlement,))

    result = take_duchy_turn(world, duchy, tbb.Rng(17))
    developed = develop_duchy_settlement(world, duchy)
    recruited = recruit_duchy_unit(developed, duchy)
    expected = take_duchy_military_action(recruited, duchy, tbb.Rng(17))

    assert result == expected
    assert len(result.settlement_at(home).garrison) == 1
    marched = result.party_at(road)
    assert marched is not None
    assert marched.units == ()
    assert result.party_at(target) is None
    assert result.settlement_at(target) is enemy_settlement


def test_duchy_turn_leaves_recruit_in_garrison_when_party_already_exists():
    home, start, road, target = map(Region, ("Home", "Start", "Road", "Target"))
    hero = Unit(training=2)
    veteran = Unit(equipment=2)
    party = Party(hero, (veteran,), owner_id="ai")
    home_settlement = Settlement(
        "Home", 2, storage=Resources(0, 1), owner_id="ai"
    )
    world = WorldMap(
        [home, start, road, target],
        [(start, road), (road, target)],
        {home: home_settlement, target: _settlement("Target", "enemy")},
        {start: party},
    )
    duchy = Duchy("ai", hero, settlements=(home_settlement,), parties=(party,))

    result = take_duchy_turn(world, duchy, _ForbiddenRng())

    home_garrison = result.settlement_at(home).garrison
    assert len(home_garrison) == 1
    assert home_garrison[0].damage > 0
    assert home_garrison[0].defense > 0
    assert_moved_party(result, road, party)
    assert result.party_at(road).units == (veteran,)
    assert result.party_at(target) is None


def test_duchy_turn_takes_military_action_when_recruitment_is_unavailable():
    start, road, target = map(Region, ("Start", "Road", "Target"))
    hero = Unit()
    party = Party(hero, owner_id="ai")
    world = WorldMap(
        [start, road, target],
        [(start, road), (road, target)],
        {target: _settlement("Target", "enemy")},
        {start: party},
    )
    duchy = Duchy("ai", hero, parties=(party,))

    result = take_duchy_turn(world, duchy, _ForbiddenRng())

    assert_moved_party(result, road, party)
    assert result.party_at(target) is None


def test_duchy_turn_is_deterministic_and_preserves_all_inputs():
    home, target = Region("Home"), Region("Target")
    hero = Unit(training=7, equipment=7)
    settlement = Settlement("Home", 2, owner_id="ai")
    enemy = Settlement("Target", 1, garrison=(Unit(),), owner_id="enemy")
    world = WorldMap(
        [home, target], [(home, target)], {home: settlement, target: enemy}
    )
    duchy = Duchy("ai", hero, settlements=(settlement,))

    first = take_duchy_turn(world, duchy, tbb.Rng(23))
    second = take_duchy_turn(world, duchy, tbb.Rng(23))

    assert first == second
    assert world.settlement_at(home) is settlement
    assert world.settlement_at(target) is enemy
    assert world.party_at(home) is None
    assert settlement.garrison == ()
    assert settlement.occupied == 0
    assert duchy.hero is hero
    assert duchy.settlements == (settlement,)


def test_duchy_turn_is_publicly_exported():
    assert tbb.take_duchy_turn is take_duchy_turn


def test_raise_duchy_hero_raises_from_first_owned_settlement_by_region_order():
    """Without a hero, raise from the first eligible owned settlement (region order)."""
    foreign, unowned, poor, first, second = map(
        Region, ("Foreign", "Unowned", "Poor", "First", "Second")
    )
    garrison = (Unit(training=1),)
    settlements = {
        foreign: Settlement(
            "Foreign",
            3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST),
            owner_id="enemy",
        ),
        unowned: Settlement(
            "Unowned",
            3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST),
        ),
        poor: Settlement(
            "Poor",
            3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST - 1),
            owner_id="ai",
        ),
        first: Settlement(
            "First",
            population=4,
            occupied=1,
            storage=Resources(wheat=2, gold=settlement_module.HERO_GOLD_COST + 1),
            garrison=garrison,
            owner_id="ai",
        ),
        second: Settlement(
            "Second",
            3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST + 5),
            owner_id="ai",
        ),
    }
    world_regions = [foreign, unowned, poor, first, second]
    world = WorldMap(
        world_regions,
        settlements={
            region: settlements[region] for region in reversed(world_regions)
        },
    )
    duchy = Duchy(
        "ai",
        None,
        morale=5,
        settlements=(settlements[poor], settlements[first], settlements[second]),
    )

    result = raise_duchy_hero(world, duchy)
    repeated = raise_duchy_hero(world, duchy)

    assert isinstance(result, tuple)
    assert len(result) == 2
    result_world, result_duchy = result
    assert repeated == result
    assert isinstance(result_world, WorldMap)
    assert isinstance(result_duchy, Duchy)

    expected_settlement, expected_hero = settlements[first].raise_hero()
    assert result_world.settlement_at(first) == expected_settlement
    assert result_duchy.hero == expected_hero
    assert result_duchy.hero == Unit()
    assert result_duchy.has_hero is True
    assert result_duchy.duchy_id == "ai"
    assert result_duchy.morale == 5
    assert result_duchy.heir is None
    assert result_duchy.parties == ()
    assert result_duchy.settlements == duchy.settlements
    assert result_world.settlement_at(second) is settlements[second]
    for region in (foreign, unowned, poor):
        assert result_world.settlement_at(region) is settlements[region]
    assert world.settlement_at(first) is settlements[first]
    assert duchy.hero is None
    assert duchy.morale == 5
    assert duchy.has_hero is False
    assert settlements[first].population == 4
    assert settlements[first].storage == Resources(
        wheat=2, gold=settlement_module.HERO_GOLD_COST + 1
    )
    assert settlements[first].garrison == garrison


@pytest.mark.parametrize("case", ["has_hero", "no_candidate"])
def test_raise_duchy_hero_is_noop_when_has_hero_or_no_candidate(case):
    """No-op returns the exact input world and duchy (identity) without raising."""
    home, foreign = Region("Home"), Region("Foreign")
    if case == "has_hero":
        settlement = Settlement(
            "Home",
            population=3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST),
            owner_id="ai",
        )
        hero = Unit()
        duchy = Duchy("ai", hero, morale=4, settlements=(settlement,))
    else:
        # Own seat cannot pay (no free pop, gold below cost); foreign seat is ignored.
        settlement = Settlement(
            "Home",
            population=3,
            occupied=3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST - 1),
            owner_id="ai",
        )
        duchy = Duchy("ai", None, morale=4, settlements=(settlement,))
    foreign_settlement = Settlement(
        "Foreign",
        population=5,
        storage=Resources(0, settlement_module.HERO_GOLD_COST + 10),
        owner_id="enemy",
    )
    world = WorldMap(
        [home, foreign],
        settlements={home: settlement, foreign: foreign_settlement},
    )
    snapshot = (
        duchy.hero,
        duchy.morale,
        duchy.has_hero,
        world.settlement_at(home).population,
        world.settlement_at(home).storage,
        world.settlement_at(foreign).storage,
    )

    result = raise_duchy_hero(world, duchy)
    repeated = raise_duchy_hero(world, duchy)

    assert isinstance(result, tuple)
    assert len(result) == 2
    result_world, result_duchy = result
    assert result_world is world
    assert result_duchy is duchy
    assert repeated == result
    assert snapshot == (
        duchy.hero,
        duchy.morale,
        duchy.has_hero,
        world.settlement_at(home).population,
        world.settlement_at(home).storage,
        world.settlement_at(foreign).storage,
    )


@pytest.mark.parametrize("case", ["has_heir", "no_hero", "no_candidate"])
def test_designate_duchy_heir_is_noop_when_has_heir_no_hero_or_no_candidate(case):
    """No-op returns the exact input world and duchy (identity) without designating."""
    home, foreign = Region("Home"), Region("Foreign")
    if case == "has_heir":
        settlement = Settlement(
            "Home",
            population=3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST),
            owner_id="ai",
        )
        hero = Unit(training=2)
        heir = Unit(training=1)
        duchy = Duchy("ai", hero, morale=4, heir=heir, settlements=(settlement,))
    elif case == "no_hero":
        settlement = Settlement(
            "Home",
            population=3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST),
            owner_id="ai",
        )
        duchy = Duchy("ai", None, morale=4, settlements=(settlement,))
    else:
        # Own seat cannot pay (no free pop, gold below cost); foreign seat is ignored.
        settlement = Settlement(
            "Home",
            population=3,
            occupied=3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST - 1),
            owner_id="ai",
        )
        hero = Unit(training=2)
        duchy = Duchy("ai", hero, morale=4, settlements=(settlement,))
    foreign_settlement = Settlement(
        "Foreign",
        population=5,
        storage=Resources(0, settlement_module.HERO_GOLD_COST + 10),
        owner_id="enemy",
    )
    world = WorldMap(
        [home, foreign],
        settlements={home: settlement, foreign: foreign_settlement},
    )
    snapshot = (
        duchy.hero,
        duchy.heir,
        duchy.morale,
        duchy.has_hero,
        world.settlement_at(home).population,
        world.settlement_at(home).storage,
        world.settlement_at(foreign).storage,
    )

    result = designate_duchy_heir(world, duchy)
    repeated = designate_duchy_heir(world, duchy)

    assert isinstance(result, tuple)
    assert len(result) == 2
    result_world, result_duchy = result
    assert result_world is world
    assert result_duchy is duchy
    assert repeated == result
    assert snapshot == (
        duchy.hero,
        duchy.heir,
        duchy.morale,
        duchy.has_hero,
        world.settlement_at(home).population,
        world.settlement_at(home).storage,
        world.settlement_at(foreign).storage,
    )


def test_designate_duchy_heir_raises_from_first_owned_settlement_by_region_order():
    """With a hero and no heir, designate from the first eligible owned settlement."""
    foreign, unowned, poor, first, second = map(
        Region, ("Foreign", "Unowned", "Poor", "First", "Second")
    )
    garrison = (Unit(training=1),)
    hero = Unit(training=2)
    settlements = {
        foreign: Settlement(
            "Foreign",
            3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST),
            owner_id="enemy",
        ),
        unowned: Settlement(
            "Unowned",
            3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST),
        ),
        poor: Settlement(
            "Poor",
            3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST - 1),
            owner_id="ai",
        ),
        first: Settlement(
            "First",
            population=4,
            occupied=1,
            storage=Resources(wheat=2, gold=settlement_module.HERO_GOLD_COST + 1),
            garrison=garrison,
            owner_id="ai",
        ),
        second: Settlement(
            "Second",
            3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST + 5),
            owner_id="ai",
        ),
    }
    world_regions = [foreign, unowned, poor, first, second]
    world = WorldMap(
        world_regions,
        settlements={
            region: settlements[region] for region in reversed(world_regions)
        },
    )
    duchy = Duchy(
        "ai",
        hero,
        morale=5,
        settlements=(settlements[poor], settlements[first], settlements[second]),
    )

    result = designate_duchy_heir(world, duchy)
    repeated = designate_duchy_heir(world, duchy)

    assert isinstance(result, tuple)
    assert len(result) == 2
    result_world, result_duchy = result
    assert repeated == result
    assert isinstance(result_world, WorldMap)
    assert isinstance(result_duchy, Duchy)

    expected_settlement, expected_heir = settlements[first].raise_hero()
    assert result_world.settlement_at(first) == expected_settlement
    assert result_duchy.heir == expected_heir
    assert result_duchy.heir == Unit()
    assert result_duchy.heir is not result_duchy.hero
    assert result_duchy.hero is hero
    assert result_duchy.has_hero is True
    assert result_duchy.duchy_id == "ai"
    assert result_duchy.morale == 5
    assert result_duchy.parties == ()
    assert result_duchy.settlements == duchy.settlements
    assert result_world.settlement_at(first).free == settlements[first].free - 1
    assert result_world.settlement_at(first).storage.gold == (
        settlements[first].storage.gold - settlement_module.HERO_GOLD_COST
    )
    assert result_world.settlement_at(second) is settlements[second]
    for region in (foreign, unowned, poor):
        assert result_world.settlement_at(region) is settlements[region]
    assert world.settlement_at(first) is settlements[first]
    assert duchy.hero is hero
    assert duchy.heir is None
    assert duchy.morale == 5
    assert settlements[first].population == 4
    assert settlements[first].storage == Resources(
        wheat=2, gold=settlement_module.HERO_GOLD_COST + 1
    )
    assert settlements[first].garrison == garrison


def test_engage_duchy_party_recorded_fights_first_adjacent_enemy_party_in_neighbor_order():
    """engage_duchy_party_recorded picks the first neighbor with a differently-owned party."""
    start, first, second = map(Region, ("Start", "First", "Second"))
    attacker = Party(Unit(training=5, equipment=6), owner_id="ai")
    enemy_first = Party(Unit(equipment=1), owner_id="enemy")
    enemy_second = Party(Unit(equipment=1), owner_id="enemy")
    world = WorldMap(
        [start, first, second],
        [(start, first), (start, second)],
        parties={start: attacker, first: enemy_first, second: enemy_second},
    )
    assert list(world.neighbors(start)) == [first, second]
    duchy = Duchy("ai", attacker.hero, parties=(attacker,))
    seed = 2
    morale_by_owner = {"ai": 10, "enemy": -5}

    resolved_world, battle = ai.engage_duchy_party_recorded(
        world, duchy, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )

    expected_world, expected_battle = world.resolve_party_battle_recorded(
        start, first, tbb.Rng(seed), attacker_morale=10, defender_morale=-5
    )
    assert resolved_world == expected_world
    assert battle == expected_battle
    assert resolved_world != world
    assert world.party_at(start) is attacker
    assert world.party_at(first) is enemy_first
    assert world.party_at(second) is enemy_second


def test_engage_duchy_party_to_recorded_fights_explicit_target_not_first_neighbor():
    """engage_duchy_party_to_recorded resolves the explicit target, not neighbor order."""
    start, first, second = map(Region, ("Start", "First", "Second"))
    attacker = Party(Unit(training=5, equipment=6), owner_id="ai")
    enemy_first = Party(Unit(equipment=1), owner_id="enemy")
    enemy_second = Party(Unit(equipment=1), owner_id="enemy")
    world = WorldMap(
        [start, first, second],
        [(start, first), (start, second)],
        parties={start: attacker, first: enemy_first, second: enemy_second},
    )
    assert list(world.neighbors(start)) == [first, second]
    duchy = Duchy("ai", attacker.hero, parties=(attacker,))
    seed = 2
    morale_by_owner = {"ai": 10, "enemy": -5}

    resolved_world, battle = ai.engage_duchy_party_to_recorded(
        world, duchy, second, tbb.Rng(seed), morale_by_owner=morale_by_owner
    )

    expected_world, expected_battle = world.resolve_party_battle_recorded(
        start, second, tbb.Rng(seed), attacker_morale=10, defender_morale=-5
    )
    assert resolved_world == expected_world
    assert battle == expected_battle
    assert resolved_world != world
    assert world.party_at(start) is attacker
    assert world.party_at(first) is enemy_first
    assert world.party_at(second) is enemy_second


@pytest.mark.parametrize(
    "case",
    ["not_neighbor", "no_party", "target_ownerless", "same_owner", "no_player_party"],
)
def test_engage_duchy_party_to_recorded_is_noop_and_does_not_use_rng(case):
    """engage_duchy_party_to_recorded returns (world, None) without RNG for every no-op case."""
    start, target, far = map(Region, ("Start", "Target", "Far"))
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    if case == "not_neighbor":
        edges = [(start, far), (far, target)]
    else:
        edges = [(start, target)]
    if case == "no_player_party":
        parties: dict[Region, Party] = {}
    else:
        parties = {start: party}
        if case == "target_ownerless":
            parties[target] = Party(Unit(equipment=1))
        elif case == "same_owner":
            parties[target] = Party(Unit(equipment=1), owner_id="ai")
        elif case == "not_neighbor":
            parties[target] = Party(Unit(equipment=1), owner_id="enemy")
    world = WorldMap([start, target, far], edges, parties=parties)
    duchy = Duchy("ai", party.hero, parties=(party,))

    result_world, battle = ai.engage_duchy_party_to_recorded(
        world, duchy, target, _ForbiddenRng()
    )

    assert result_world is world
    assert battle is None


def test_engage_duchy_party_recorded_is_noop_when_no_adjacent_enemy_party():
    """engage_duchy_party_recorded returns (world, None) without using RNG when no enemy party is adjacent."""
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    world = WorldMap(
        [start, target],
        [(start, target)],
        parties={start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result_world, battle = ai.engage_duchy_party_recorded(
        world, duchy, _ForbiddenRng()
    )

    assert result_world is world
    assert battle is None
    assert world.party_at(start) is party


def test_reinforce_duchy_party_leaves_one_garrison_defender_where_party_stands():
    home = Region("Home")
    hero = Unit(training=4)
    garrison = (Unit(equipment=1), Unit(experience=2))
    settlement = Settlement(
        "Home", population=6, occupied=3, garrison=garrison, owner_id="ai"
    )
    party = Party(hero, (Unit(),), owner_id="ai")
    world = WorldMap(
        [home], settlements={home: settlement}, parties={home: party}
    )

    reinforced = ai.reinforce_duchy_party(world, Duchy("ai", hero))

    reinforced_party = reinforced.party_at(home)
    reinforced_settlement = reinforced.settlement_at(home)
    assert reinforced_party.hero is hero
    assert reinforced_party.owner_id == "ai"
    assert len(reinforced_party.units) == len(party.units) + len(garrison) - 1
    assert reinforced_party.acted_this_month is True
    assert len(reinforced_settlement.garrison) == 1
    assert (
        Counter(reinforced_party.units)
        + Counter(reinforced_settlement.garrison)
        == Counter((*party.units, *garrison))
    )
    assert reinforced_settlement.population == settlement.population - 1
    assert reinforced_settlement.occupied == settlement.occupied - 1
    assert world.settlement_at(home) is settlement


def test_reinforce_duchy_party_is_noop_without_duchy_party():
    home = Region("Home")
    settlement = Settlement(
        "Home", population=6, occupied=3, garrison=(Unit(),), owner_id="ai"
    )
    enemy_party = Party(Unit(), owner_id="enemy")
    world = WorldMap(
        [home], settlements={home: settlement}, parties={home: enemy_party}
    )

    assert ai.reinforce_duchy_party(world, Duchy("ai", Unit())) is world


def test_reinforce_duchy_party_leaves_foreign_settlement_garrison_alone():
    home = Region("Home")
    garrison = (Unit(equipment=1), Unit(experience=2))
    settlement = Settlement(
        "Home", population=6, occupied=3, garrison=garrison, owner_id="enemy"
    )
    party = Party(Unit(training=4), (Unit(),), owner_id="ai")
    world = WorldMap(
        [home], settlements={home: settlement}, parties={home: party}
    )

    assert ai.reinforce_duchy_party(world, Duchy("ai", Unit())) is world
