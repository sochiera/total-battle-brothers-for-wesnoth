"""Persistent next-turn e2e on a live bridge (two processes).

Includes G90.1b: after one „Następna tura” on a fresh seed-73 party the player
still sees ``player lands`` as a player MapView tile and ≥1 settlement, and a
resumed process reloads that same state — absolute contract, not session oracle.
"""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

from godot_runner import map_player_result, run_godot_script
from tbbbridge.session import new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/persistent_next_turn_e2e_probe.gd"
PREFIX = "PERSISTENT_NEXT_TURN "
SEED = 73
ONGOING_AFTER_MUSTER_SEED = 1  # Seed 73 legally ends the game on turn 1.
PLAYER_LANDS = "player lands"
AI_LANDS = "ai lands"
_SETTLEMENTS_RE = re.compile(r"osady:\s*(\d+)")


def _expected_snapshot(turns: int) -> dict:
    session = new_session(SEED)
    for _ in range(turns):
        session = session.next_turn()
    return session.snapshot()


def _controls(snapshot: dict) -> dict:
    player_status = next(
        duchy
        for duchy in snapshot["duchies"]
        if duchy["id"] == snapshot["player_duchy"]
    )
    return {
        "date": (
            f"Rok {snapshot['calendar']['year']}, "
            f"miesiąc {snapshot['calendar']['month']}"
        ),
        "result": map_player_result(snapshot['result']['player_result']),
        "duchy_status": (
            f"Morale: {player_status['morale']}, "
            f"osady: {player_status['settlements']}, "
            f"oddziały: {player_status['parties']}"
        ),
        "regions": [region["name"] for region in snapshot["map"]["regions"]],
    }


def _settlement_count(duchy_status: str) -> int:
    match = _SETTLEMENTS_RE.search(duchy_status)
    assert match is not None, f"duchy status must report osady: N, got {duchy_status!r}"
    return int(match.group(1))


def _run_probe(*script_args: str, timeout: float = 30) -> dict:
    result = run_godot_script(GAME, PROBE, *script_args, timeout=timeout)
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_next_turn_button_persists_the_game_across_two_bridge_processes(tmp_path):
    state_path = tmp_path / "persistent-session.json"
    command_prefix = (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    )
    payload = _run_probe(
        command_prefix,
        str(state_path),
        str(tmp_path / "bridge-request.jsonl"),
        str(SEED),
    )

    assert payload == {
        "state_exists_after_first_press": True,
        "first": _controls(_expected_snapshot(1)),
        "second": _controls(_expected_snapshot(2)),
    }


def test_next_turn_button_keeps_controls_empty_when_persistent_bridge_fails(tmp_path):
    payload = _run_probe(
        "false",
        str(tmp_path / "persistent-session.json"),
        str(tmp_path / "bridge-request.jsonl"),
        str(SEED),
    )
    assert payload == {
        "state_exists_after_first_press": False,
        "first": {"date": "", "result": "", "duchy_status": "", "regions": []},
        "second": {"date": "", "result": "", "duchy_status": "", "regions": []},
    }


def test_muster_then_two_turns_advance_visible_persistent_game(tmp_path):
    """G92.1b: the defensive player path stays playable on a live bridge.

    Existing gates exercise muster and persistent next-turn separately, so they
    miss the sequence-dependent lock where a mustered party occupies the
    destination selected during the AI turn.
    """
    state_path = tmp_path / "muster-then-turn.json"
    command_prefix = (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    )
    payload = _run_probe(
        command_prefix,
        str(state_path),
        str(tmp_path / "bridge-request.jsonl"),
        str(ONGOING_AFTER_MUSTER_SEED),
        "muster_then_two_turns",
        timeout=45,
    )

    assert payload["phase"] == "muster_then_two_turns"
    assert payload["state_exists_after_first_turn"] is True
    assert payload["before_turn"]["date"] == "Rok 1, miesiąc 1"
    assert payload["after_muster"]["order_status"] == "Rozkaz zbiórki zmienił stan."

    first = payload["after_first_turn"]
    resumed = payload["after_resume"]
    second = payload["after_second_turn"]
    assert first["date"] == "Rok 1, miesiąc 2"
    assert resumed["date"] == first["date"]
    assert resumed["duchy_status"] == first["duchy_status"]
    assert second["date"] == "Rok 1, miesiąc 3"


def test_player_sees_survival_after_first_turn_on_live_bridge(tmp_path):
    """G90.1b: one NextTurn keeps player lands paint and ≥1 settlement on screen.

    Realistic defect existing gates miss: ``test_next_turn_button_persists_…``
    builds expected labels from ``session.snapshot()``, so if passive turn 1
    hands ``player lands`` to the AI both sides agree and stay green; it also
    never looks at MapView ownership paint. A client that advances the date
    while painting the keep as enemy (or showing osady: 0) would pass the
    oracle e2e and still fail this absolute survival contract.
    """
    state_path = tmp_path / "survive-first-turn.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    )
    payload = _run_probe(
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        "survive_first_turn",
        timeout=45,
    )

    assert payload["phase"] == "survive_first_turn"
    assert payload["state_exists_after_first_press"] is True
    assert payload["session_command_after_resume"] == (
        f"{command_prefix} serve --resume '{state_path}'"
    )

    start = payload["after_start"]
    after = payload["after_first_turn"]
    resumed = payload["after_resume"]

    # Fresh start is a living player keep (precondition for a fair first turn).
    assert start["map_view_found"] is True, start
    assert start["date"] == "Rok 1, miesiąc 1", start
    assert _settlement_count(start["duchy_status"]) >= 1, start
    start_visuals = start["tile_visuals"]
    assert PLAYER_LANDS in start_visuals and AI_LANDS in start_visuals, start
    assert start_visuals[PLAYER_LANDS] != start_visuals[AI_LANDS], (
        "start must paint player lands differently from AI lands; "
        f"got {start_visuals}"
    )
    player_paint = start_visuals[PLAYER_LANDS]

    # AC1–AC2: after one NextTurn the keep is still the player's on the map
    # and the duchy status still reports at least one settlement.
    assert after["map_view_found"] is True, after
    assert after["date"] == "Rok 1, miesiąc 2", after
    assert _settlement_count(after["duchy_status"]) >= 1, after
    after_visuals = after["tile_visuals"]
    assert after_visuals.get(PLAYER_LANDS) == player_paint, (
        "player lands tile must keep player ownership paint after first turn; "
        f"start={player_paint!r} after={after_visuals.get(PLAYER_LANDS)!r} "
        f"full={after_visuals}"
    )
    assert after_visuals.get(PLAYER_LANDS) != after_visuals.get(AI_LANDS), (
        "player lands must not share AI ownership paint after first turn; "
        f"got {after_visuals}"
    )

    # AC3: next bridge process resumes the same visible state (no extra turn).
    assert resumed["map_view_found"] is True, resumed
    assert resumed["date"] == after["date"], resumed
    assert resumed["duchy_status"] == after["duchy_status"], resumed
    assert resumed["tile_visuals"].get(PLAYER_LANDS) == after_visuals.get(
        PLAYER_LANDS
    ), resumed
    assert resumed["tile_visuals"].get(AI_LANDS) == after_visuals.get(AI_LANDS), (
        resumed
    )
