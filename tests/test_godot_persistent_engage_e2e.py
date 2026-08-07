"""G108.1b e2e: the Engage button resolves and persists a party battle."""

from __future__ import annotations

import json
import shlex
from pathlib import Path

import tbb.ai as ai
from godot_runner import run_godot_script
from tbbbridge.persist import read_session, save_session
from tbbbridge.session import Session, apply_command, new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/persistent_order_process_probe.gd"
PREFIX = "PERSISTENT_ORDER_PROCESS "
SEED = 73
EXHAUSTED_ACTION_STATUS = "Oddział już działał w tym miesiącu — zakończ turę."
NO_TARGET_STATUS = "Rozkaz starcia nie zmienił stanu."


def _run_process(command_prefix: str, state_path: Path, request_path: Path, phase: str) -> dict:
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        phase,
        timeout=45,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _adjacent_parties_session() -> Session:
    """Build the seed-73 state with both adjacent parties alive.

    The monthly movement marker is reset through ``next_turn`` before the
    fixture asks the AI to provide the opposing adjacent party. One recruited
    unit keeps the player party alive after the first engage, so the next AI
    turn can provide a fresh adjacent target for the cycle assertion.
    """
    session = new_session(seed=SEED, player_duchy_id="player")
    for command in (
        {"type": "order", "order": "recruit"},
        {"type": "order", "order": "muster"},
        {"type": "order", "order": "march"},
        {"type": "next_turn"},
    ):
        session = apply_command(session, command)

    ai_duchy = next(duchy for duchy in session.game.duchies if duchy.duchy_id == "ai")
    world = ai.muster_duchy_party(session.world, ai_duchy)
    return Session(
        world=world,
        game=session.game.sync_from_world(world),
        calendar=session.calendar,
        rng=session.rng,
        player_duchy_id=session.player_duchy_id,
        seed=session.seed,
        last_battle=session.last_battle,
    )


def _party_without_adjacent_enemy_session() -> Session:
    return apply_command(
        new_session(seed=SEED, player_duchy_id="player"),
        {"type": "order", "order": "muster"},
    )


def _march_then_engage_session() -> Session:
    """Build a player path whose effective march leaves an adjacent AI party."""
    session = new_session(seed=SEED, player_duchy_id="player")
    for command in (
        {"type": "order", "order": "recruit"},
        {"type": "order", "order": "muster"},
    ):
        session = apply_command(session, command)

    ai_duchy = next(duchy for duchy in session.game.duchies if duchy.duchy_id == "ai")
    world = ai.muster_duchy_party(session.world, ai_duchy)
    world = ai.march_duchy_party(world, ai_duchy)
    return Session(
        world=world,
        game=session.game.sync_from_world(world),
        calendar=session.calendar,
        rng=session.rng,
        player_duchy_id=session.player_duchy_id,
        seed=session.seed,
        last_battle=session.last_battle,
    )


def _polish_engage_result(text: str) -> bool:
    lowered = text.casefold()
    return (
        lowered.startswith("starcie:")
        and "straty:" in lowered
        and "wróg:" in lowered
        and any(outcome in lowered for outcome in ("porażka", "zwycięstwo", "remis"))
    )


def _polish_battle_outcome(text: str) -> bool:
    lowered = text.casefold()
    return any(outcome in lowered for outcome in ("porażka", "zwycięstwo", "remis"))


def test_engage_button_resolves_party_battle_and_persists_it_across_processes(tmp_path):
    """A live click must not be a dead control or leave the state before combat.

    Realistic defect: the scene can expose the correctly named Engage button and
    format an ``engage`` result while its pressed signal is never bound. Existing
    assault e2e and order-result tests then stay green, but an adjacent enemy
    party is untouchable and no post-battle state reaches the resumed process.
    """
    state_path = tmp_path / "persistent-engage-session.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    before_battle = _adjacent_parties_session()
    save_session(before_battle, state_path)

    battle = _run_process(command_prefix, state_path, request_path, "engage")
    persisted_after_battle = read_session(state_path)
    cycle = _run_process(
        command_prefix, state_path, request_path, "second_engage_next_turn"
    )

    assert battle["session_command"] == f"{command_prefix} serve --resume '{state_path}'"
    assert battle["battle_before_order"]["tile_count"] == 0
    assert battle["controls_before_order"]["party_position"] == "Położenie oddziału: Posterunek gracza"

    # Visible player effect: resolved result and tiles from both sides.
    after = battle["battle"]
    assert _polish_engage_result(battle["controls"]["order_status"])
    assert after["tile_count"] >= 2, after
    assert after["paint_groups"] >= 2, after
    assert _polish_battle_outcome(after["result_text"]), after

    assert persisted_after_battle.world != before_battle.world

    # A new bridge process reads the post-battle file, rather than pre-click state.
    assert cycle["session_command"] == f"{command_prefix} serve --resume '{state_path}'"
    assert cycle["controls_before_order"]["party_position"] == battle["controls"]["party_position"]
    assert cycle["controls_before_order"]["duchy_status"] == battle["controls"]["duchy_status"]
    assert cycle["battle_before_order"]["tile_count"] == after["tile_count"]
    assert cycle["battle_before_order"]["result_text"] == after["result_text"]

    # The live two-process sequence is: same action blocked, next month, then
    # the same action resolves again with a fresh visible battle result.
    sequence = cycle["sequence"]
    assert sequence["blocked"]["order_status"] == EXHAUSTED_ACTION_STATUS
    assert sequence["after_turn"]["date"] != sequence["blocked"]["date"]
    assert _polish_engage_result(sequence["effective"]["order_status"])
    assert cycle["battle"]["tile_count"] >= 2, cycle
    assert _polish_battle_outcome(cycle["battle"]["result_text"]), cycle

    persisted_after_cycle = read_session(state_path)
    assert persisted_after_cycle.calendar != persisted_after_battle.calendar

    # A third process sees the second battle and its consumed monthly action.
    resumed = _run_process(command_prefix, state_path, request_path, "second_engage")
    assert resumed["controls"]["order_status"] == EXHAUSTED_ACTION_STATUS
    assert resumed["battle_before_order"]["tile_count"] == cycle["battle"]["tile_count"]
    assert resumed["battle_before_order"]["result_text"] == cycle["battle"]["result_text"]
    assert resumed["battle"]["tile_count"] == 0
    assert resumed["battle"]["result_text"] == ""
    assert read_session(state_path).world == persisted_after_cycle.world

    # The same no-op is also useful while the player's party is still alive:
    # it proves the missing-target branch, rather than merely the no-party one.
    no_enemy_state_path = tmp_path / "persistent-engage-no-enemy-session.json"
    no_enemy_request_path = tmp_path / "bridge-no-enemy-request.jsonl"
    living_party_without_enemy = _party_without_adjacent_enemy_session()
    save_session(living_party_without_enemy, no_enemy_state_path)
    no_enemy = _run_process(
        command_prefix, no_enemy_state_path, no_enemy_request_path, "engage"
    )

    assert no_enemy["controls_before_order"]["party_position"] != "Położenie oddziału: brak"
    assert no_enemy["controls"]["party_position"] == no_enemy["controls_before_order"]["party_position"]
    assert no_enemy["controls"]["order_status"] == NO_TARGET_STATUS
    assert no_enemy["battle_before_order"]["tile_count"] == 0
    assert no_enemy["battle"]["tile_count"] == 0
    assert read_session(no_enemy_state_path).world == living_party_without_enemy.world


def test_march_then_engage_shows_exhausted_month_status_on_live_bridge(tmp_path):
    """An effective March must block the next same-month Engage visibly.

    Realistic defect: the core marks a successful march as acted for the month,
    but BridgeClient currently records the marker only after a battle snapshot.
    The existing Engage e2e starts after a turn reset, so it cannot catch the
    direct march → engage path and the client falls back to the generic no-op.
    """
    state_path = tmp_path / "persistent-march-engage-session.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    save_session(_march_then_engage_session(), state_path)

    result = _run_process(command_prefix, state_path, request_path, "march_then_engage")
    sequence = result["sequence"]

    assert sequence["march"]["order_status"] == "Oddział przemieścił się."
    assert sequence["march"]["party_position"] == "Położenie oddziału: Posterunek gracza"
    assert sequence["engage"]["party_position"] == sequence["march"]["party_position"]
    assert sequence["engage"]["order_status"] == EXHAUSTED_ACTION_STATUS
