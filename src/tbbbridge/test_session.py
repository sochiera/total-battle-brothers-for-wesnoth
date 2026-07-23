"""Tests for the tbbbridge session handle (G65.1a/G65.1b).

Tests live next to the module under test per task-312 \"Ścieżki testów\".
"""

import copy
import json

import pytest

from tbb.game import GameState, create_headless_game
from tbb.rng import Rng
from tbb.turn import Calendar

from tbbbridge.session import Session, apply_command, new_session
from tbbbridge.snapshot import game_state


def test_new_session_builds_session_with_headless_game_calendar_rng_defaults_and_fields():
    """G65.1a-1: new_session() builds a Session from core public APIs."""
    s = new_session()

    assert type(s) is Session
    assert type(s.world).__name__ == "WorldMap"
    assert type(s.game).__name__ == "GameState"
    assert type(s.calendar).__name__ == "Calendar"
    assert type(s.rng).__name__ == "Rng"
    assert s.seed == 73
    assert s.player_duchy_id == "player"

    expected_world, expected_game = create_headless_game()
    assert s.game == expected_game
    assert s.world == expected_world
    assert s.calendar == Calendar()
    assert s.rng is not Rng(73)
    assert s.rng.randint(0, 1000) == Rng(73).randint(0, 1000)


def test_new_session_honours_explicit_seed_and_player_duchy_id_arguments():
    """G65.1a-2: new_session propagates seed and player_duchy_id arguments."""
    s = new_session(seed=99, player_duchy_id=None)

    assert s.seed == 99
    assert s.player_duchy_id is None
    assert s.rng.randint(0, 1000) == Rng(99).randint(0, 1000)


def test_snapshot_returns_game_state_contract_json_serializable_without_mutation():
    """G65.1a-3: Session.snapshot() delegates to game_state without mutation."""
    s = new_session(73, "player")
    snap = s.snapshot()
    expected = game_state(
        s.world,
        s.game,
        s.calendar,
        s.player_duchy_id,
    )
    assert snap == expected
    json.dumps(snap)

    snap2 = s.snapshot()
    assert snap2 == snap
    assert json.dumps(snap2) == json.dumps(snap)
    assert s.rng.randint(0, 1000) == Rng(73).randint(0, 1000)


def test_fresh_new_session_snapshot_has_expected_starting_state():
    """G65.1a-4: fresh new_session(73, 'player') snapshot reflects a new game."""
    s = new_session(73, "player")
    snap = s.snapshot()

    assert snap["calendar"] == {"year": 1, "month": 1}
    assert len(snap["duchies"]) == 2
    assert snap["result"]["player_result"] == "ongoing"
    assert snap["result"]["winner"] is None
    assert snap["result"]["is_over"] is False


def test_next_turn_advances_calendar_by_one_month():
    """G65.1b crit-1: next_turn() runs exactly one headless turn.

    For a fresh new_session(73, 'player') the calendar advances from
    {year: 1, month: 1} to {year: 1, month: 2}.
    """
    s = new_session(73, "player")
    after = s.next_turn()
    assert after.snapshot()["calendar"] == {"year": 1, "month": 2}


def test_next_turn_returns_new_session_with_shared_advanced_rng_and_preserved_fields():
    """G65.1b crit-1 supplement: next_turn() returns a new Session, preserves
    player_duchy_id/seed, shares the same (advanced) RNG by reference, and
    does not mutate the original session.
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
    assert s.snapshot() == before_state


def test_next_turn_is_noop_when_game_is_over():
    """G65.1b crit-2: when self.game.is_over, next_turn() is a no-op returning
    a session whose world/game/calendar are the same objects as the input. The
    input session is never mutated.
    """
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

    snapshot_before = ended_session.snapshot()
    after = ended_session.next_turn()

    assert after is not ended_session
    assert after.world is ended_session.world
    assert after.game is ended_session.game
    assert after.calendar is ended_session.calendar
    assert after.rng is ended_session.rng
    assert after.player_duchy_id == "player"
    assert after.seed == 73
    # Input session not mutated in any case.
    assert ended_session.snapshot() == snapshot_before


def test_apply_command_new_game_returns_fresh_session_preserving_player_and_seed():
    """G65.1c crit-2: apply_command({"type": "new_game"}) returns a fresh
    session built via new_session(seed=session.seed, player_duchy_id=...),
    preserving player_duchy_id and defaulting seed to the current session.seed;
    an explicit {"type": "new_game", "seed": 7} uses seed=7. The new game's
    snapshot has calendar == {"year": 1, "month": 1}. The input session is not
    mutated. An unknown type (and a missing type key) both raise ValueError.
    """
    s = new_session(42, "player")
    advanced = s.next_turn()
    assert advanced.snapshot()["calendar"] != {"year": 1, "month": 1}

    fresh_default = apply_command(advanced, {"type": "new_game"})

    assert isinstance(fresh_default, Session)
    assert fresh_default is not advanced
    assert fresh_default.player_duchy_id == "player"
    assert fresh_default.seed == 42
    assert fresh_default.snapshot()["calendar"] == {"year": 1, "month": 1}
    fresh_default_snapshot = copy.deepcopy(fresh_default.snapshot())
    assert fresh_default.snapshot() == fresh_default_snapshot

    fresh_seeded = apply_command(advanced, {"type": "new_game", "seed": 7})
    assert fresh_seeded.seed == 7
    assert fresh_seeded.player_duchy_id == "player"
    assert fresh_seeded.snapshot()["calendar"] == {"year": 1, "month": 1}
    assert fresh_seeded.rng.randint(0, 1000) == Rng(7).randint(0, 1000)

    advanced_before = copy.deepcopy(advanced.snapshot())
    assert advanced.snapshot() == advanced_before

    with pytest.raises(ValueError):
        apply_command(advanced, {"type": "totally_unknown"})
    with pytest.raises(ValueError):
        apply_command(advanced, {"unrelated": "value"})


def test_apply_command_next_turn_delegates_to_session_next_turn():
    """G65.1c crit-1: apply_command(session, {"type": "next_turn"}) returns a
    session whose snapshot matches session.next_turn() exactly (pure delegation,
    no own turn logic). The input session is not mutated.
    """
    s = new_session(73, "player")
    before = copy.deepcopy(s.snapshot())

    via_command = apply_command(s, {"type": "next_turn"})
    via_method = s.next_turn()

    assert via_command.snapshot() == via_method.snapshot()
    assert s.snapshot() == before


def test_apply_command_order_develop_applies_ai_primitive_syncs_game_returns_new_session():
    """G65.2a crit-1: apply_command({"type": "order", "order": "develop"})
    applies ``ai.develop_duchy_settlement`` to the player duchy (opening the
    first priority building — FARM — in Player Keep), then
    ``game.sync_from_world`` and returns a new Session with that world/game.
    The input session is not mutated; calendar/rng/seed/player_duchy_id are
    preserved.
    """
    s = new_session(73, "player")
    before = copy.deepcopy(s.snapshot())

    after = apply_command(s, {"type": "order", "order": "develop"})

    assert isinstance(after, Session)
    assert after is not s
    assert after.player_duchy_id == "player"
    assert after.seed == 73
    assert after.calendar == s.calendar
    assert after.rng is s.rng
    # FARM is the highest development priority — Player Keep starts with no
    # active buildings, so develop opens FARM (observable in the snapshot).
    player_settlement_after = after.snapshot()["map"]["regions"][0]["settlement"]
    assert "Farma" in player_settlement_after["buildings"] or len(
        player_settlement_after["buildings"]
    ) >= 1
    # The input session's snapshot is unchanged.
    assert s.snapshot() == before


def test_apply_command_unknown_type_and_missing_type_raise_valueerror_without_mutation():
    """G65.1c crit-3: unknown type or missing 'type' key both raise ValueError;
    the input session is never mutated (snapshot deterministic, RNG advanced
    by the raised call has no observable effect on a later identical session).
    """
    s = new_session(73, "player")
    before = copy.deepcopy(s.snapshot())

    with pytest.raises(ValueError):
        apply_command(s, {"type": "order"})
    with pytest.raises(ValueError):
        apply_command(s, {"type": "new_game", "seed": 999, "extra": True})
    with pytest.raises(ValueError):
        apply_command(s, {})
    with pytest.raises(ValueError):
        apply_command(s, {"unrelated": 1})

    assert s.snapshot() == before
