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
    """Build the documented seed-73 state with both adjacent parties alive."""
    session = new_session(seed=SEED, player_duchy_id="player")
    for order in ("muster", "march", "march"):
        session = apply_command(session, {"type": "order", "order": order})

    ai_duchy = next(duchy for duchy in session.game.duchies if duchy.duchy_id == "ai")
    world = ai.muster_duchy_party(session.world, ai_duchy)
    return session._derive(
        world,
        session.game.sync_from_world(world),
        session.calendar,
        last_battle=session.last_battle,
    )


def _party_without_adjacent_enemy_session() -> Session:
    return apply_command(
        new_session(seed=SEED, player_duchy_id="player"),
        {"type": "order", "order": "muster"},
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
    resumed = _run_process(command_prefix, state_path, request_path, "second_engage")

    assert battle["session_command"] == f"{command_prefix} serve --resume '{state_path}'"
    assert battle["battle_before_order"]["tile_count"] == 0
    assert battle["controls_before_order"]["party_position"] == "Położenie oddziału: Pogranicze"

    # Visible player effect: resolved result and tiles from both sides.
    after = battle["battle"]
    assert _polish_engage_result(battle["controls"]["order_status"])
    assert after["tile_count"] >= 2, after
    assert after["paint_groups"] >= 2, after
    assert _polish_battle_outcome(after["result_text"]), after

    persisted_after_battle = read_session(state_path)
    assert persisted_after_battle.world != before_battle.world

    # A new bridge process reads the post-battle file, rather than pre-click state.
    assert resumed["session_command"] == f"{command_prefix} serve --resume '{state_path}'"
    assert resumed["controls_before_order"]["party_position"] == battle["controls"]["party_position"]
    assert resumed["controls_before_order"]["duchy_status"] == battle["controls"]["duchy_status"]
    assert resumed["battle_before_order"]["tile_count"] == after["tile_count"]
    assert resumed["battle_before_order"]["result_text"] == after["result_text"]

    # With no adjacent enemy after the loss, another click gives a Polish no-op,
    # and the fresh no-battle snapshot removes the old battle panel.
    assert resumed["controls"]["order_status"] == "Rozkaz starcia nie zmienił stanu."
    assert resumed["battle"]["tile_count"] == 0
    assert resumed["battle"]["result_text"] == ""
    assert read_session(state_path).world == persisted_after_battle.world

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
    assert no_enemy["controls"]["order_status"] == "Rozkaz starcia nie zmienił stanu."
    assert no_enemy["battle_before_order"]["tile_count"] == 0
    assert no_enemy["battle"]["tile_count"] == 0
    assert read_session(no_enemy_state_path).world == living_party_without_enemy.world
