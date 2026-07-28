"""G89.1b-4 e2e: natural player sequence ends with a visible battle effect.

On seed 73 the path recruit×2 → muster → march → assault drives a settlement
battle across a live bridge process bound to the Godot client — the unique risk
named in task-504 / PROJECT.md conclusion 13. Slice tests (core, protocol,
order_result, assault e2e without the two recruits) already pass; this path
must still surface a readable battle outcome, not a failed-order message.

After G89.2a-1 (swap past own stunned ally) the seed-73 natural fight is no
longer a round-limit stalemate. After G90.1a the player keep starts with a
veteran garrison (symmetric with AI), so the mustered party on this path is
larger. After G91.1a default recruits enter with positive training/equipment,
so the same recruit×2 path on seed 73 resolves as attacker zwycięstwo
(defender_losses=1, no attacker losses; party holds the captured keep).
Unresolved remains a legal contract elsewhere (K89.1).
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
# Matches G85 assault e2e status shape; natural path with G91.1a recruits wins.
EXPECTED_ORDER_STATUS = "Szturm: zwycięstwo (straty: 0, wróg: 1)."
EXPECTED_PARTY_POSITION = "Położenie oddziału: ai lands"
EXPECTED_BATTLE_RESULT = {
    "kind": "battle",
    "order": "assault",
    "outcome": "zwycięstwo",
    "attacker_losses": 0,
    "defender_losses": 1,
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
    # Attacker win (G91.1a): enemy keep taken; party remains on captured region.
    assert "osady: 2" in play["controls"]["duchy_status"]
    assert "oddziały: 1" in play["controls"]["duchy_status"]

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
        # Attacker win: party holds captured keep; player has 2 settlements.
        assert "osady: 2" in resumed["controls"]["duchy_status"]
        assert "oddziały: 1" in resumed["controls"]["duchy_status"]
        assert resumed["controls"]["regions"] == play["controls"]["regions"]

    assert outcomes[0] == outcomes[1] == EXPECTED_BATTLE_RESULT
