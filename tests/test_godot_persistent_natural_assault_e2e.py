"""G89.1b-4 e2e: natural player sequence ends with a visible battle effect.

On seed 73 the path recruit×2 → muster → march → assault drives a settlement
battle across a live bridge process bound to the Godot client — the unique risk
named in task-504 / PROJECT.md conclusion 13. Slice tests (core, protocol,
order_result, assault e2e without the two recruits) already pass; this path
must still surface a readable battle outcome, not a failed-order message.

After G89.2a-1 (swap past own stunned ally) the seed-73 natural fight is no
longer a round-limit stalemate: the last active attacker can advance and the
strong garrison resolves the fight as porażka. After G90.1a the player keep
starts with a veteran garrison (symmetric with AI), so the mustered party on
this path is larger and seed-73 records attacker_losses=1 (still porażka,
0 enemy losses; remaining attackers stunned). Unresolved remains a legal
contract elsewhere (K89.1).
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/persistent_natural_assault_e2e_probe.gd"
PREFIX = "PERSISTENT_NATURAL_ASSAULT "
SEED = 73
# Matches G85 assault e2e status shape; natural path with recruits now resolves.
EXPECTED_ORDER_STATUS = "Szturm: porażka (straty: 1, wróg: 0)."
EXPECTED_PARTY_POSITION = "Położenie oddziału: brak"
EXPECTED_BATTLE_RESULT = {
    "kind": "battle",
    "order": "assault",
    "outcome": "porażka",
    "attacker_losses": 1,
    "defender_losses": 0,
}


def _run_process(
    command_prefix: str, state_path: Path, request_path: Path, phase: str
) -> dict:
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        phase,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _assert_successful_resolved_assault(play: dict) -> None:
    """Criteria 1–2: live order succeeds; client shows readable battle effect."""
    assert play["state_exists"] is True
    assert play["controls"]["order_status"] == EXPECTED_ORDER_STATUS, (
        "expected readable battle outcome status, not a failed-order message; "
        f"got {play['controls']['order_status']!r}"
    )
    assert play["controls"]["party_position"] == EXPECTED_PARTY_POSITION
    # Settlement ownership lives in duchy_status (regions list shows names only).
    # Defender win: party destroyed, player keep retained.
    assert "osady: 1" in play["controls"]["duchy_status"]
    assert "oddziały: 0" in play["controls"]["duchy_status"]

    # Machine result from the bridge response projected by the client (kryt-1).
    last = play["order_results"][-1]
    assert last == EXPECTED_BATTLE_RESULT, last


def test_natural_sequence_ends_with_visible_battle_effect_on_live_bridge(tmp_path):
    """Recruit×2 → muster → march → assault on seed 73 must not surface as a failed order.

    Realistic defect: G89.1a/b unit tests and the G85 assault e2e (muster→march→
    assault without recruits) stay green while the natural seed-73 sequence still
    returns ok:false / "unknown battle result" at the client↔live-bridge
    boundary, or resumes a corrupted campaign.
    """
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"

    # Two independent runs on the same seed → same battle effect (kryt-4).
    outcomes = []
    for run_id in (1, 2):
        state_path = tmp_path / f"natural-assault-{run_id}.json"
        request_path = tmp_path / f"bridge-request-{run_id}.jsonl"
        play = _run_process(command_prefix, state_path, request_path, "play")
        _assert_successful_resolved_assault(play)
        outcomes.append(play["order_results"][-1])

        # Kryt-3: resume the persisted campaign; world matches post-assault result.
        resumed = _run_process(
            command_prefix,
            state_path,
            tmp_path / f"bridge-request-{run_id}-resume.jsonl",
            "resume",
        )
        assert resumed["session_command"] == (
            f"{command_prefix} serve --resume '{state_path}'"
        )
        assert resumed["state_exists"] is True
        assert resumed["controls"]["party_position"] == EXPECTED_PARTY_POSITION
        assert resumed["controls"]["date"] == play["controls"]["date"]
        # Defender win: party gone; player still has 1 settlement.
        assert "osady: 1" in resumed["controls"]["duchy_status"]
        assert "oddziały: 0" in resumed["controls"]["duchy_status"]
        assert resumed["controls"]["regions"] == play["controls"]["regions"]

    assert outcomes[0] == outcomes[1] == EXPECTED_BATTLE_RESULT
