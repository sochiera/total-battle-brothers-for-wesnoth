"""TDD gates for core economic-order refusal diagnostics (G114.1a)."""

import random

import pytest

import tbb.ai as ai
from tbb.game import create_headless_game
from tbbbridge.session import apply_command, new_session
from tbb import (
    BARRACKS,
    FARM,
    MARKET,
    SMITH,
    Duchy,
    Region,
    Resources,
    Settlement,
    Unit,
    WorldMap,
    economic_order_reason,
)


TRANSIENT_POPULATION = "brak wolnej ludności"
PERMANENT_POPULATION = "brak wolnej ludności — osada nie wyżywi przyrostu"


def _economic_order_reason(world, duchy, order):
    """Fail on the public contract, not on import, until the API exists."""
    query = getattr(ai, "economic_order_reason", None)
    assert callable(query), (
        "G114.1a requires public tbb.ai.economic_order_reason(world, duchy, order)"
    )
    assert query is economic_order_reason
    return query(world, duchy, order)


def _single_settlement_world(settlement):
    region = Region("Home")
    return (
        WorldMap([region], settlements={region: settlement}),
        Duchy("north", Unit(), settlements=(settlement,)),
    )


def test_economic_order_reason_reports_required_blockers_and_is_pure():
    """AC1: all named refusal values exist and successful orders return None.

    Realistic defects not covered by the existing transition tests: a new
    diagnostic can collapse transient hunger into permanent hunger, report a
    generic reason for the wrong guard, or mutate/query through the bridge.
    """
    complete = (FARM, SMITH, BARRACKS, MARKET)
    full_garrison = tuple(Unit(experience=index) for index in range(12))
    no_settlement_world = WorldMap([Region("Empty")])
    cases = (
        (
            "develop-no-own-settlement",
            no_settlement_world,
            Duchy("north", Unit()),
            "develop",
            "brak własnej osady",
        ),
        (
            "muster-no-own-settlement",
            no_settlement_world,
            Duchy("north", Unit()),
            "muster",
            "brak własnej osady",
        ),
        (
            "recruit-no-gold",
            *_single_settlement_world(
                Settlement("Home", 2, storage=Resources(0, 0), owner_id="north")
            ),
            "recruit",
            "brak złota",
        ),
        (
            "develop-complete-buildings",
            *_single_settlement_world(
                Settlement(
                    "Home",
                    5,
                    active_buildings=complete,
                    owner_id="north",
                )
            ),
            "develop",
            "komplet budynków",
        ),
        (
            "recruit-garrison-limit",
            *_single_settlement_world(
                Settlement(
                    "Home",
                    13,
                    occupied=12,
                    storage=Resources(0, 1),
                    garrison=full_garrison,
                    owner_id="north",
                )
            ),
            "recruit",
            "limit garnizonu",
        ),
        (
            "develop-transient-free-population",
            *_single_settlement_world(
                Settlement(
                    "Home",
                    2,
                    occupied=2,
                    storage=Resources(3, 1),
                    owner_id="north",
                )
            ),
            "develop",
            TRANSIENT_POPULATION,
        ),
        (
            "recruit-permanent-free-population",
            *_single_settlement_world(
                Settlement(
                    "Home",
                    2,
                    occupied=2,
                    storage=Resources(2, 1),
                    owner_id="north",
                )
            ),
            "recruit",
            PERMANENT_POPULATION,
        ),
    )

    for name, world, duchy, order, expected in cases:
        assert _economic_order_reason(world, duchy, order) == expected, name

    fresh_world, fresh_game = create_headless_game()
    fresh_duchy = next(d for d in fresh_game.duchies if d.duchy_id == "player")
    world_before = fresh_world
    duchy_before = fresh_duchy
    rng_before = random.getstate()
    for order in ("develop", "recruit", "muster"):
        assert _economic_order_reason(fresh_world, fresh_duchy, order) is None
    assert fresh_world == world_before
    assert fresh_duchy == duchy_before
    assert random.getstate() == rng_before


def test_population_block_reason_does_not_mutate_world():
    """The post-economy/growth diagnostic remains a pure world query."""
    world, duchy = _single_settlement_world(
        Settlement(
            "Home",
            2,
            occupied=2,
            storage=Resources(2, 1),
            owner_id="north",
        )
    )
    world_before = world
    duchy_before = duchy
    rng_before = random.getstate()

    assert _economic_order_reason(world, duchy, "recruit") == PERMANENT_POPULATION

    assert world == world_before
    assert duchy == duchy_before
    assert random.getstate() == rng_before


@pytest.mark.parametrize(
    ("name", "settlement", "order", "expected"),
    (
        (
            "positive-balance-with-room",
            Settlement(
                "Home",
                2,
                occupied=2,
                storage=Resources(3, 1),
                owner_id="north",
            ),
            "recruit",
            TRANSIENT_POPULATION,
        ),
        (
            "zero-balance-with-positive-storage",
            Settlement(
                "Home",
                2,
                occupied=2,
                storage=Resources(2, 1),
                owner_id="north",
            ),
            "recruit",
            PERMANENT_POPULATION,
        ),
        (
            "negative-balance",
            Settlement(
                "Home",
                5,
                occupied=5,
                active_buildings=(FARM,),
                storage=Resources(1, 1),
                owner_id="north",
            ),
            "develop",
            PERMANENT_POPULATION,
        ),
        (
            "capacity-threshold",
            Settlement(
                "Home",
                2,
                occupied=2,
                storage=Resources(3, 1),
                capacity=2,
                owner_id="north",
            ),
            "develop",
            PERMANENT_POPULATION,
        ),
    ),
)
def test_economic_order_reason_uses_post_economy_balance_and_capacity_gate(
    name, settlement, order, expected
):
    """AC2: zero is not growth, and capacity blocks positive balance."""
    world, duchy = _single_settlement_world(settlement)

    assert _economic_order_reason(world, duchy, order) == expected, name


def test_eight_recruits_leave_development_temporarily_population_blocked():
    """AC4: recruit x8 fills both starting settlements without exhausting wheat."""
    session = new_session(seed=73, player_duchy_id="player")
    for _ in range(8):
        session = apply_command(session, {"type": "order", "order": "recruit"})

    player_settlements = tuple(
        session.world.settlement_at(region)
        for region in session.world.regions
        if session.world.settlement_at(region) is not None
        and session.world.settlement_at(region).owner_id == "player"
    )
    assert tuple(
        (settlement.free, settlement.storage.wheat)
        for settlement in player_settlements
    ) == ((0, 10), (0, 10))

    player = next(d for d in session.game.duchies if d.duchy_id == "player")
    assert _economic_order_reason(session.world, player, "develop") == TRANSIENT_POPULATION


def _drain_order(session, order):
    """Reproduce the measured player path up to the first unchanged order."""
    while True:
        before = session.world
        session = apply_command(session, {"type": "order", "order": order})
        if session.world is before:
            return session


def test_seed73_turn_three_positive_storage_is_already_permanent_hunger():
    """AC3: the measured threshold defeats a ``storage.wheat > 0`` oracle."""
    session = new_session(seed=73, player_duchy_id="player")
    for turn in range(3):
        session = _drain_order(session, "develop")
        session = _drain_order(session, "recruit")
        if turn < 2:
            session = apply_command(session, {"type": "next_turn"})

    player_settlements = {
        region.name: session.world.settlement_at(region)
        for region in session.world.regions
        if session.world.settlement_at(region) is not None
        and session.world.settlement_at(region).owner_id == "player"
    }
    assert {
        name: (settlement.free, settlement.storage.wheat)
        for name, settlement in player_settlements.items()
    } == {
        "player lands": (0, 5),
        "player outpost": (0, 4),
    }
    assert all(settlement.storage.wheat > 0 for settlement in player_settlements.values())

    player = next(d for d in session.game.duchies if d.duchy_id == "player")
    assert _economic_order_reason(
        session.world, player, "recruit"
    ) == PERMANENT_POPULATION

    for _ in range(2):
        session = apply_command(session, {"type": "next_turn"})
        session = _drain_order(session, "develop")
        session = _drain_order(session, "recruit")

    assert {
        name: (settlement.population, settlement.storage.wheat)
        for name, settlement in {
            region.name: session.world.settlement_at(region)
            for region in session.world.regions
            if session.world.settlement_at(region) is not None
            and session.world.settlement_at(region).owner_id == "player"
        }.items()
    } == {
        "player lands": (8, 0),
        "player outpost": (9, 0),
    }
    player = next(d for d in session.game.duchies if d.duchy_id == "player")
    assert _economic_order_reason(
        session.world, player, "recruit"
    ) == PERMANENT_POPULATION
