"""G85.1c e2e: assault click shows BattleView tiles via bridge across processes."""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script


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


def _polish_battle_result(text: str) -> bool:
    lowered = text.casefold()
    return any(
        keyword in lowered
        for keyword in ("porażka", "zwycięstwo", "remis", "bitwa")
    )


def test_assault_button_shows_battle_view_across_godot_processes(tmp_path):
    """Assault path must paint BattleView from live bridge state, not only status text.

    Realistic defect: BattleView is green with synthetic apply_model (G85.1b) and
    K80 e2e only asserts LastOrderStatusLabel after assault. If the order/resume
    path never feeds the live snapshot's battle into BattleView, the player still
    sees only one line of text while hex tiles stay empty — across process resume
    the fight remains invisible even though the state file holds last_battle.
    """
    state_path = tmp_path / "persistent-assault-session.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"

    prepared = _run_process(command_prefix, state_path, request_path, "prepare")
    battle = _run_process(command_prefix, state_path, request_path, "battle")
    resumed = _run_process(command_prefix, state_path, request_path, "second_engage_clear")

    assert prepared["state_exists"] is True
    assert battle["session_command"] == f"{command_prefix} serve --resume '{state_path}'"
    assert resumed["session_command"] == f"{command_prefix} serve --resume '{state_path}'"

    # The staging window is diagnostic only: the actual assault precondition
    # proves that the player is on border and frontier defenders are alive.
    precondition = prepared["assault_precondition"]
    assert precondition["ready"] is True, precondition
    assert precondition["player_party_at_border"] is True, precondition
    assert precondition["frontier_defenders_live"] is True, precondition
    assert precondition["frontier_defenders"] >= 1, precondition

    # K80/G109.1c regression: order status text carries battle outcome and the
    # second military action names the exhausted monthly action.
    assert prepared["controls_after_muster"]["party_position"] == "Położenie oddziału: Ziemie gracza"
    assert prepared["controls"]["party_position"] == "Położenie oddziału: Pogranicze"
    assert battle["controls_before_order"]["party_position"] == "Położenie oddziału: Pogranicze"
    assert battle["controls"]["party_position"] == "Położenie oddziału: Posterunek wroga"
    assert battle["controls"]["order_status"] == "Szturm: zwycięstwo (straty: 0, wróg: 2)."
    assert resumed["controls"]["order_status"] == (
        "Oddział już działał w tym miesiącu — zakończ turę."
    )
    assert prepared["controls"]["date"] != prepared["controls_before_order"]["date"]
    assert battle["controls_before_order"]["date"] == prepared["controls"]["date"]
    assert battle["controls"]["date"] == prepared["controls"]["date"]
    assert resumed["controls"]["date"] == battle["controls"]["date"]

    # Party start / bind_client: battle view empty before any order in prepare.
    prep_start = prepared["battle_before_order"]
    assert prep_start["tile_count"] == 0, prep_start
    assert prep_start["result_text"] == "", prep_start

    # Before first assault (prepare after march+one next_turn+engage): still empty.
    prep_battle = prepared["battle"]
    assert prep_battle["tile_count"] == 0, prep_battle
    assert prep_battle["result_text"] == "", prep_battle

    # Resume after prepare, before assault: still no battle on screen.
    assert battle["battle_before_order"]["tile_count"] == 0, battle["battle_before_order"]
    assert battle["battle_before_order"]["result_text"] == "", battle["battle_before_order"]

    # After assault: both resolved sides' tiles + Polish result are readable
    # on BattleView.  The third next_turn lets the AI keep a live garrison
    # while the engage clears its field party before the settlement assault.
    after = battle["battle"]
    assert after["tile_count"] >= 2, after
    assert after["paint_groups"] >= 2, (
        "attacker and defender tiles must differ visually "
        "(silhouette or paint groups), got one paint group: %r" % after
    )
    assert all(t.get("visible") for t in after["tiles"]), after
    assert _polish_battle_result(after["result_text"]), after
    assert "zwycięstwo" in after["result_text"].casefold(), after

    # Next process resumes from state file: battle still visible before re-order
    # (two-process persistence of last battle — the core K85.1c risk).
    resume_before = resumed["battle_before_order"]
    assert resume_before["tile_count"] >= 2, resume_before
    assert resume_before["paint_groups"] >= 2, (
        "resume must keep distinct side visuals (silhouette/paint groups): %r"
        % resume_before
    )
    assert resume_before["result_text"] == after["result_text"], (
        f"resume must restore same Polish battle result: after={after} resume={resume_before}"
    )
    assert resume_before["tile_count"] == after["tile_count"], (
        f"resume must restore same battle tiles: after={after} resume={resume_before}"
    )

    # Domain: second assault is a no-op and the bridge snapshot drops "battle".
    # View must not keep stale tiles when the model has no battle (K85.1c kryt-5).
    resume_after = resumed["battle"]
    assert resume_after["tile_count"] == 0, resume_after
    assert resume_after["result_text"] == "", resume_after
