"""Live bridge measurement for G121.1f (task-690)."""

from __future__ import annotations

import json
import shlex
from pathlib import Path

import tbb.ai as ai
from godot_runner import run_godot_script
from tbbbridge.persist import save_session
from tbbbridge.session import Session, apply_command, new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/battle_move_live_effect_probe.gd"
PREFIX = "BATTLE_MOVE_LIVE_EFFECT "
SEED = 73
MOVER = {"q": 0, "r": 2}
DESTINATION = {"q": 0, "r": 3}
EXPECTED_MOVE = {"mover": MOVER, "destination": DESTINATION}


def _prepared_session() -> Session:
    """Seed-73 party with an adjacent AI force ready for Engage."""
    session = new_session(seed=SEED, player_duchy_id="player")
    for command in (
        {"type": "order", "order": "recruit"},
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


def _run_phase(tmp_path: Path, phase: str) -> dict:
    state_path = tmp_path / "battle-move-live.json"
    request_path = tmp_path / f"battle-move-live-{phase}.jsonl"
    if phase == "select":
        save_session(_prepared_session(), state_path)
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        phase,
        str(SEED),
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _attacker_positions(hexes: list[dict]) -> list[tuple[int, int]]:
    return sorted(
        (int(hex_state["q"]), int(hex_state["r"]))
        for hex_state in hexes
        if hex_state.get("side") == "attacker" and int(hex_state.get("hp", 0)) > 0
    )


def _board_tile_positions(tiles: list[dict]) -> set[tuple[int, int]]:
    return {
        (int(tile["q"]), int(tile["r"]))
        for tile in tiles
        if tile.get("visible") and tile.get("hp_text")
    }


def test_live_move_occupies_indicated_hex_through_public_path_and_resume(tmp_path):
    """G121.1f AC1-3: live click move survives resume and lands after advance.

    Realistic defect existing gates miss: synthetic move-selection and bridge
    pause tests stay green while the persistent Godot path drops battle_move,
    fails to project move_targets onto the board before the round, or loses the
    intent across save/resume so battle_advance walks the default route instead
    of the indicated free neighbour.
    """
    selected = _run_phase(tmp_path, "select")
    resumed = _run_phase(tmp_path, "resume_advance")

    # AC1: Engage opens a live pending battle with the measured rear attacker.
    pending_hexes = selected["pending"]["hexes"]
    assert selected["pending"]["result"] is None, selected
    assert (MOVER["q"], MOVER["r"]) in {
        (int(hex_state["q"]), int(hex_state["r"]))
        for hex_state in pending_hexes
        if hex_state.get("side") == "attacker"
    }, selected
    assert f"HexTile_{DESTINATION['q']}_{DESTINATION['r']}" in selected[
        "destinations_after_select"
    ], selected

    # AC2: public scene clicks send battle_move over JSON Lines and the live
    # bridge snapshot keeps the intent visible before the round advances.
    assert selected["move_result"] == {
        "kind": "battle_move",
        "changed": True,
    }, selected
    assert selected["request_types"][:2] == ["battle_move", "save"], selected
    assert selected["after_move"]["move_targets"] == [EXPECTED_MOVE], selected
    assert selected["after_move"]["battle_visible"] is True, selected
    assert selected["after_move"]["model_result"] is None, selected
    assert (
        selected["after_move"]["mover_marked"]
        and selected["after_move"]["destination_marked"]
    ), selected

    # AC3: cold resume keeps the same public move intent before advance.
    assert "serve --resume" in resumed["session_command"], resumed
    assert resumed["before_advance"]["move_targets"] == [EXPECTED_MOVE], resumed
    assert resumed["before_advance"]["battle_visible"] is True, resumed
    assert resumed["before_advance"]["model_result"] is None, resumed

    # AC1: after one public battle_advance the indicated destination is occupied
    # on the model and still painted on the battle board.
    assert resumed["request_types"][:2] == ["battle_advance", "save"], resumed
    after = resumed["after_advance"]
    assert after["battle_visible"] is True, resumed
    assert after["move_targets"] in ([], None) or after["move_targets"] == [], resumed
    attacker_positions = _attacker_positions(after["model_hexes"])
    assert (DESTINATION["q"], DESTINATION["r"]) in attacker_positions, resumed
    assert (MOVER["q"], MOVER["r"]) not in attacker_positions, resumed
    board_positions = _board_tile_positions(after["tiles"])
    assert (DESTINATION["q"], DESTINATION["r"]) in board_positions, resumed
