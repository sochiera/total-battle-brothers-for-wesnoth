"""TDD gate for core assault refusal diagnostics (G118.1a)."""

import random

import pytest
import tbb
import tbb.ai as ai

from tbb import Duchy, Party, Region, Settlement, Unit, WorldMap


NO_OWN_PARTY = "brak własnego oddziału"
NO_ENEMY_IN_REACH = "brak wrogiej osady w zasięgu"
TARGET_OUT_OF_REACH = "cel poza zasięgiem"
NO_ENEMY_AT_TARGET = "brak wrogiej osady w celu"
ALREADY_ACTED = "oddział już działał w tym miesiącu"

ASSAULT_REASON_CASES = (
    ("no-own-party", NO_OWN_PARTY),
    ("auto-out-of-reach", NO_ENEMY_IN_REACH),
    ("explicit-out-of-reach", TARGET_OUT_OF_REACH),
    ("no-enemy-at-target", NO_ENEMY_AT_TARGET),
    ("already-acted", ALREADY_ACTED),
    ("can-assault", None),
    ("explicit-can-assault", None),
)


def _assault_order_reason(world, duchy, target=None):
    """Fail on the public contract, not on import, until the API exists."""
    query = getattr(ai, "assault_order_reason", None)
    public_query = getattr(tbb, "assault_order_reason", None)
    assert callable(query), (
        "G118.1a requires public tbb.ai.assault_order_reason(world, duchy, target=None)"
    )
    assert public_query is query, "tbb must export assault_order_reason"
    return query(world, duchy, target=target)


def _scenario(case, owner_id="north"):
    start = Region("Start")
    near = Region("Near")
    far = Region("Far")
    home = Settlement("Home", population=2, owner_id=owner_id)
    own_target = Settlement("Own Target", population=2, owner_id=owner_id)
    enemy = Settlement("Enemy", population=2, owner_id="south")
    party = Party(
        Unit(),
        owner_id=owner_id,
        acted_this_month=case == "already-acted",
    )

    settlements = {start: home}
    parties = {}
    target = None
    if case != "no-own-party":
        parties[start] = party

    if case == "auto-out-of-reach":
        settlements[far] = enemy
    elif case == "explicit-out-of-reach":
        settlements[far] = enemy
        target = far
    elif case == "no-enemy-at-target":
        settlements[near] = own_target
        target = near
    elif case in {"already-acted", "can-assault", "explicit-can-assault"}:
        settlements[near] = enemy
        target = near if case in {"already-acted", "explicit-can-assault"} else None

    world = WorldMap(
        [start, near, far],
        [(start, near), (near, far)],
        settlements=settlements,
        parties=parties,
    )
    duchy = Duchy(
        owner_id,
        party.hero,
        settlements=(home, own_target) if case == "no-enemy-at-target" else (home,),
        parties=(party,) if case != "no-own-party" else (),
    )
    return world, duchy, target


@pytest.mark.parametrize("name, expected", ASSAULT_REASON_CASES)
def test_assault_order_reason_reports_distinct_noop_causes_and_is_pure(
    name, expected
):
    """AC1-4: refusal causes are distinct and both target modes are covered.

    Realistic defects existing assault-transition tests miss: a diagnostic can
    collapse an unreachable target into a missing party, inspect the nearest
    enemy instead of the explicit target, report success for an acted party,
    or consume randomness/mutate the world while checking a no-op.
    """
    world, duchy, target = _scenario(name)
    world_before = world
    duchy_before = duchy
    rng_before = random.getstate()

    assert _assault_order_reason(world, duchy, target) == expected, name
    assert world == world_before, name
    assert duchy == duchy_before, name
    assert random.getstate() == rng_before, name


@pytest.mark.parametrize("owner_id", ["player", "ai"])
@pytest.mark.parametrize("case", ["can-assault", "explicit-can-assault"])
def test_assault_order_reason_has_the_same_contract_for_player_and_ai(
    owner_id, case
):
    """AC4 and AC6: auto/explicit diagnosis is owner-independent."""
    world, duchy, target = _scenario(case, owner_id=owner_id)

    assert tbb.assault_order_reason(world, duchy, target=target) is None


def _recorded_assault(world, duchy, target):
    if target is None:
        return ai.assault_duchy_party_recorded(world, duchy, tbb.Rng(7))
    return ai.assault_duchy_party_to_recorded(
        world, duchy, target, tbb.Rng(7)
    )


@pytest.mark.parametrize("case", ["can-assault", "explicit-can-assault"])
def test_assault_order_reason_does_not_change_assault_or_battle(case):
    """AC5: diagnosis preserves the effective assault and battle result."""
    baseline_world, baseline_duchy, baseline_target = _scenario(case)
    expected = _recorded_assault(
        baseline_world, baseline_duchy, baseline_target
    )

    world, duchy, target = _scenario(case)
    assert tbb.assault_order_reason(world, duchy, target=target) is None
    actual = _recorded_assault(world, duchy, target)

    assert actual == expected
    assert actual[1] is not None


NO_ENEMY_PARTY_IN_REACH = "brak wrogiego wojska w zasięgu"
NO_ENEMY_PARTY_AT_TARGET = "brak wrogiego wojska w celu"
ENGAGE_TARGET_OUT_OF_REACH = "cel poza zasięgiem"

ENGAGE_REASON_CASES = (
    ("no-own-party", None, NO_OWN_PARTY),
    ("auto-no-enemy", None, NO_ENEMY_PARTY_IN_REACH),
    ("explicit-no-enemy", "Near", NO_ENEMY_PARTY_AT_TARGET),
    ("explicit-out-of-reach", "Far", ENGAGE_TARGET_OUT_OF_REACH),
    ("already-acted", None, ALREADY_ACTED),
    ("can-engage", None, None),
    ("explicit-can-engage", "Near", None),
)


def _military_order_reason(world, duchy, order, target=None):
    """Fail on the shared public contract, not on an import or attribute error."""
    query = getattr(ai, "military_order_reason", None)
    public_query = getattr(tbb, "military_order_reason", None)
    assert callable(query), (
        "G118.1b requires public tbb.ai.military_order_reason("
        "world, duchy, order, target=None)"
    )
    assert public_query is query, "tbb must export military_order_reason"
    return query(world, duchy, order, target=target)


def _engage_scenario(case, owner_id="north"):
    start, near, far = map(Region, ("Start", "Near", "Far"))
    own_party = Party(
        Unit(),
        owner_id=owner_id,
        acted_this_month=case == "already-acted",
    )
    friendly_party = Party(Unit(), owner_id=owner_id)
    enemy_party = Party(Unit(), owner_id="south")

    parties = {}
    target = None
    duchy_parties = ()
    if case != "no-own-party":
        parties[start] = own_party
        duchy_parties = (own_party,)

    if case == "no-own-party":
        parties[far] = enemy_party
    elif case == "auto-no-enemy":
        parties[far] = enemy_party
    elif case == "explicit-no-enemy":
        parties[near] = friendly_party
        parties[far] = enemy_party
        target = near
        duchy_parties = (own_party, friendly_party)
    elif case == "explicit-out-of-reach":
        parties[far] = enemy_party
        target = far
    elif case in {"already-acted", "can-engage", "explicit-can-engage"}:
        parties[near] = enemy_party
        target = near if case == "explicit-can-engage" else None

    world = WorldMap(
        [start, near, far],
        [(start, near), (near, far)],
        parties=parties,
    )
    duchy = Duchy(
        owner_id,
        own_party.hero if case != "no-own-party" else Unit(),
        parties=duchy_parties,
    )
    return world, duchy, target


@pytest.mark.parametrize("case, target_name, expected", ENGAGE_REASON_CASES)
def test_military_order_reason_reports_engage_causes_and_success(
    case, target_name, expected
):
    """AC1-2: engage diagnoses each refusal and returns no reason on success.

    Realistic defects existing engage-transition tests miss: a query can look
    for a settlement instead of an enemy party, treat a friendly party as an
    enemy, inspect the auto-target while an explicit target was supplied, or
    report success after the party already spent its monthly action.
    """
    world, duchy, scenario_target = _engage_scenario(case)
    target = next(
        (region for region in world.regions if region.name == target_name),
        None,
    )
    assert target is scenario_target, case
    world_before = world
    duchy_before = duchy
    rng_before = random.getstate()

    assert _military_order_reason(world, duchy, "engage", target=target) == expected
    assert world == world_before, case
    assert duchy == duchy_before, case
    assert random.getstate() == rng_before, case


def _recorded_engage(world, duchy, target):
    if target is None:
        return ai.engage_duchy_party_recorded(world, duchy, tbb.Rng(7))
    return ai.engage_duchy_party_to_recorded(
        world, duchy, target, tbb.Rng(7)
    )


@pytest.mark.parametrize("case", ["can-engage", "explicit-can-engage"])
def test_military_order_reason_does_not_change_engage_or_battle(case):
    """AC5: diagnosis preserves effective engage and its battle result."""
    baseline_world, baseline_duchy, baseline_target = _engage_scenario(case)
    expected = _recorded_engage(
        baseline_world, baseline_duchy, baseline_target
    )

    world, duchy, target = _engage_scenario(case)
    assert _military_order_reason(world, duchy, "engage", target=target) is None
    actual = _recorded_engage(world, duchy, target)

    assert actual == expected
    assert actual[1] is not None


def test_military_order_reason_dispatches_both_military_orders_and_rejects_unknown():
    """AC3: one order-named public entry serves assault and engage."""
    assault_world, assault_duchy, assault_target = _scenario("can-assault")
    engage_world, engage_duchy, engage_target = _engage_scenario("can-engage")

    assert (
        _military_order_reason(
            assault_world, assault_duchy, "assault", target=assault_target
        )
        is None
    )
    assert (
        _military_order_reason(
            engage_world, engage_duchy, "engage", target=engage_target
        )
        is None
    )
    with pytest.raises(ValueError):
        _military_order_reason(engage_world, engage_duchy, "raid")
