"""G89.1b-4 / G91.1b e2e: natural sequence ends with battle effect and party win.

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
(defender_losses=1, no attacker losses; party holds the captured keep) and the
campaign ends with player_result victory.

G91.1b: ResultLabel shows Polish victory, AI lands paint as player-owned, and a
second process resumes that finished state. Unresolved battle remains legal
elsewhere (K89.1).
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from godot_runner import PLAYER_RESULT_PL, run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/persistent_natural_assault_e2e_probe.gd"
PREFIX = "PERSISTENT_NATURAL_ASSAULT "
SEED = 73
PLAYER_LANDS = "player lands"
AI_LANDS = "ai lands"
# Matches G85 assault e2e status shape; natural path with G91.1a recruits wins.
EXPECTED_ORDER_STATUS = "Szturm: zwycięstwo (straty: 0, wróg: 1)."
EXPECTED_PARTY_POSITION = "Położenie oddziału: ai lands"
EXPECTED_PARTY_RESULT = PLAYER_RESULT_PL["victory"]
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
    """Live order succeeds; client shows readable battle effect (G89.1b-4)."""
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

    # Machine result from the bridge response projected by the client.
    last = play["order_results"][-1]
    assert last == EXPECTED_BATTLE_RESULT, last


def _assert_player_party_victory_on_screen(play: dict, *, phase: str = "play") -> None:
    """G91.1b: finished party shows Polish victory and captured AI keep on map.

    Realistic defect existing gates miss: natural assault e2e and G90.2b binding
    stay green while the live path still leaves ResultLabel on „gra trwa” (or
    blank) and MapView keeps AI ownership paint on the taken keep — battle
    status says „Szturm: zwycięstwo” but the player never sees a won campaign.
    """
    assert play["controls"]["result"] == EXPECTED_PARTY_RESULT, (
        f"{phase}: expected game-level Polish victory on ResultLabel; "
        f"got {play['controls']['result']!r}"
    )

    map_view = play["map_view"]
    assert map_view["map_view_found"] is True, map_view
    visuals = map_view["tile_visuals"]
    assert PLAYER_LANDS in visuals and AI_LANDS in visuals, visuals
    assert visuals[PLAYER_LANDS] == visuals[AI_LANDS], (
        f"{phase}: captured ai lands must share player ownership paint; "
        f"got {visuals}"
    )

    if phase == "play":
        # after_start mirrors final payload shape: controls + map_view (probe).
        start = play["after_start"]
        start_visuals = start["map_view"]["tile_visuals"]
        assert start["controls"]["result"] == PLAYER_RESULT_PL["ongoing"], start
        assert start_visuals.get(PLAYER_LANDS) != start_visuals.get(AI_LANDS), (
            "precondition: start must paint player lands differently from AI lands; "
            f"got {start_visuals}"
        )
        assert visuals[AI_LANDS] == start_visuals[PLAYER_LANDS], (
            "ai lands after assault must adopt the start player ownership paint; "
            f"start_player={start_visuals.get(PLAYER_LANDS)!r} "
            f"after_ai={visuals.get(AI_LANDS)!r} full_after={visuals}"
        )
        assert visuals[AI_LANDS] != start_visuals[AI_LANDS], (
            "ai lands must change ownership paint after capture; "
            f"start_ai={start_visuals.get(AI_LANDS)!r} after={visuals.get(AI_LANDS)!r}"
        )


def test_natural_sequence_ends_with_player_party_victory_on_live_bridge(tmp_path):
    """Recruit×2 → muster → march → assault wins the party on a live bridge (G91.1b).

    Realistic defect: G89 battle-outcome e2e and G90.2b fixture binding stay
    green while the natural live path still shows „gra trwa”, leaves AI paint on
    the captured keep, or resumes a non-victory campaign — so pytest never
    proves the player can win looking at the screen.
    """
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"

    # Two independent runs on the same seed → same battle + party outcome (kryt-4).
    outcomes = []
    party_results = []
    for run_id in (1, 2):
        state_path = tmp_path / f"natural-assault-{run_id}.json"
        request_path = tmp_path / f"bridge-request-{run_id}.jsonl"
        play = _run_process(command_prefix, state_path, request_path, "play")
        _assert_successful_resolved_assault(play)
        _assert_player_party_victory_on_screen(play, phase="play")
        outcomes.append(play["order_results"][-1])
        party_results.append(play["controls"]["result"])

        # Kryt-3: resume the persisted finished campaign.
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
        _assert_player_party_victory_on_screen(resumed, phase="resume")
        assert resumed["controls"]["result"] == play["controls"]["result"]
        assert resumed["map_view"]["tile_visuals"] == play["map_view"]["tile_visuals"]

    assert outcomes[0] == outcomes[1] == EXPECTED_BATTLE_RESULT
    assert party_results[0] == party_results[1] == EXPECTED_PARTY_RESULT
