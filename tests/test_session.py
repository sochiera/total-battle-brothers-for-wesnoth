"""Tests for the tbbbridge session handle (G65.1a)."""

import copy
import json

from tbb.game import create_headless_game
from tbb.rng import Rng
from tbb.turn import Calendar
from tbbbridge.session import Session, new_session
from tbbbridge.snapshot import game_state


def test_new_session_builds_session_with_headless_game_calendar_rng_defaults_and_fields():
    """G65.1a-1: new_session() builds a Session from core public APIs.

    We assert behaviour, not implementation details: the returned object is a
    Session, carries a world built by create_headless_game(), a fresh Calendar,
    a seeded Rng, and exposes seed/player_duchy_id read-only fields with their
    default values.
    """
    s = new_session()

    assert type(s) is Session
    assert type(s.world).__name__ == "WorldMap"
    assert type(s.game).__name__ == "GameState"
    assert type(s.calendar).__name__ == "Calendar"
    assert type(s.rng).__name__ == "Rng"
    assert s.seed == 73
    assert s.player_duchy_id == "player"

    # The game inside the session must come from create_headless_game.
    expected_world, expected_game = create_headless_game()
    assert s.game == expected_game
    assert s.world == expected_world
    # Calendar and RNG are freshly constructed public objects.
    assert s.calendar == Calendar()
    assert s.rng is not Rng(73)  # different instances...
    # ...but reproducible: same seed behaves identically on the first draw.
    assert s.rng.randint(0, 1000) == Rng(73).randint(0, 1000)


def test_new_session_honours_explicit_seed_and_player_duchy_id_arguments():
    """G65.1a-2: new_session propagates seed and player_duchy_id arguments."""
    s = new_session(seed=99, player_duchy_id=None)

    assert s.seed == 99
    assert s.player_duchy_id is None
    assert s.rng.randint(0, 1000) == Rng(99).randint(0, 1000)


def test_snapshot_returns_game_state_contract_json_serializable_without_mutation():
    """G65.1a-3: Session.snapshot() delegates to game_state without mutation.

    The result equals game_state(session.world, session.game, session.calendar,
    session.player_duchy_id), passes json.dumps, and leaves the session state
    unchanged (repeated snapshots are byte-identical).
    """
    s = new_session(73, "player")
    snap = s.snapshot()
    expected = game_state(
        s.world,
        s.game,
        s.calendar,
        s.player_duchy_id,
    )
    assert snap == expected
    # The snapshot is json-serializable (no TypeError).
    json.dumps(snap)

    # No mutation of the session: compare snapshots before/after a second call.
    snap2 = s.snapshot()
    assert snap2 == snap
    assert json.dumps(snap2) == json.dumps(snap)
    # The RNG underlying the session must not have been consumed.
    assert s.rng.randint(0, 1000) == Rng(73).randint(0, 1000)


def test_fresh_new_session_snapshot_has_expected_starting_state():
    """G65.1a-4: fresh new_session(73, 'player') snapshot reflects a new game.

    The calendar starts at year 1 / month 1, the headless setup creates two
    duchies, and the player's result is "ongoing".
    """
    s = new_session(73, "player")
    snap = s.snapshot()

    assert snap["calendar"] == {"year": 1, "month": 1}
    assert len(snap["duchies"]) == 2
    assert snap["result"]["player_result"] == "ongoing"
    assert snap["result"]["winner"] is None
    assert snap["result"]["is_over"] is False


def test_next_turn_advances_calendar_by_one_month():
    """G65.1b-1: next_turn() runs exactly one headless turn.

    For a fresh new_session(73, 'player') the calendar advances from
    {year: 1, month: 1} to {year: 1, month: 2}.
    """
    s = new_session(73, "player")
    after = s.next_turn()
    assert after.snapshot()["calendar"] == {"year": 1, "month": 2}


def test_next_turn_returns_new_session_with_shared_advanced_rng_and_preserved_fields():
    """G65.1b-2: next_turn() returns a new session with deterministic state.

    The returned session is a distinct object, preserves ``player_duchy_id``
    and ``seed``, and shares the same (advanced) RNG instance by reference.
    The original session remains unchanged.
    """
    s = new_session(73, "player")
    rng_before = s.rng
    before_state = s.snapshot()

    after = s.next_turn()

    assert after is not s
    assert after.player_duchy_id == "player"
    assert after.seed == 73
    assert after.rng is rng_before
    assert after.rng is s.rng
    assert after.snapshot()["calendar"] == {"year": 1, "month": 2}
    # Original session not mutated.
    assert s.snapshot() == before_state


def test_next_turn_is_noop_when_game_is_over():
    """G65.1b-3: next_turn() is a no-op and returns an equivalent session
    sharing the same world/game/calendar objects when the game is already over.
    """
    from tbb.game import GameState

    s = new_session(73, "player")
    ended_game = GameState([s.game.duchies[0]])
    assert ended_game.is_over is True
    ended_session = Session(
        world=s.world,
        game=ended_game,
        calendar=s.calendar,
        rng=s.rng,
        player_duchy_id=s.player_duchy_id,
        seed=s.seed,
    )

    after = ended_session.next_turn()

    assert after is not ended_session
    assert after.world is ended_session.world
    assert after.game is ended_session.game
    assert after.calendar is ended_session.calendar
    assert after.rng is ended_session.rng
    assert after.player_duchy_id == "player"
    assert after.seed == 73
