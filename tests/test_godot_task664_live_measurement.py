import json
import shlex
from pathlib import Path

import pytest

from godot_runner import DEFERRED_BATTLE_E2E_REASON, run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = GAME / "tests" / "task664_live_measurement_probe.gd"
PREFIX = "TASK664_LIVE_MEASUREMENT "
SEED = 73


def _run_measurement(tmp_path: Path) -> dict:
    assert PROBE.is_file(), "missing res://tests/task664_live_measurement_probe.gd"
    command = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    result = run_godot_script(
        GAME,
        "res://tests/task664_live_measurement_probe.gd",
        command,
        str(tmp_path / "task664-state"),
        str(tmp_path / "task664-request"),
        str(SEED),
        timeout=90,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


@pytest.mark.xfail(strict=True, reason=DEFERRED_BATTLE_E2E_REASON)
def test_k117_live_measurements_and_documentation_are_complete(tmp_path):
    """G117.1b AC1-6: live persisted measurements and their prose contract.

    Realistic defect missed by the existing gates: the core ``muster`` and
    short K116 resolution tests can pass while the client-facing save/resume
    sequence empties the source settlement on the following turn, or while
    the longer active path loses its victory after the added ``reinforce``.
    This gate observes the settlement snapshots and result winner from the
    actual persistent bridge rather than deriving them from a second session.
    """
    payload = _run_measurement(tmp_path)

    opening = payload["opening"]
    assert opening["after_muster"]["garrison"] >= 1, opening
    assert opening["after_turn"]["garrison"] >= 1, opening
    assert opening["after_turn_resume"] == opening["after_turn"], opening

    passive = payload["passive"]
    assert passive["player_result"] == "defeat", passive
    assert passive["winner"] == "ai", passive

    active = payload["active"]
    assert active["player_result"] == "victory", active
    assert active["winner"] == "player", active
    assert [
        command["kind"] + (":" + command["order"] if "order" in command else "")
        for command in active["commands"]
    ] == [
        "order:recruit",
        "order:recruit",
        "order:recruit",
        "order:recruit",
        "order:recruit",
        "order:muster",
        "order:march",
        "turn",
        "order:reinforce",
        "turn",
        "order:march",
        "turn",
        "order:assault",
        "turn",
        "order:assault",
        "turn",
        "order:assault",
    ]

    defensive = payload["defensive"]
    assert defensive["turns"] == 20, defensive
    assert defensive["player_result"] == "ongoing", defensive
    assert (defensive["date"]["year"], defensive["date"]["month"]) == (
        2,
        8,
    ), defensive
    assert [
        command["order"] if command["kind"] == "order" else "next_turn"
        for command in defensive["commands"]
    ] == [
        "develop",
        "develop",
        "recruit",
        "recruit",
        "recruit",
        "recruit",
    ] + ["next_turn"] * 20, defensive
    for settlement in defensive["settlements"].values():
        assert settlement["garrison"] == 3, defensive

    backlog = (ROOT / "BACKLOG.md").read_text(encoding="utf-8")
    k117_start = backlog.index("## Kamień milowy 117")
    k117_end = backlog.index("## Kamień milowy 118", k117_start)
    k117 = backlog[k117_start:k117_end]
    assert (
        "`recruit`×5 → `muster` → `march` → `next_turn` → `reinforce` → "
        "`next_turn` → `march` → `next_turn` → `assault` → `next_turn` → "
        "`assault` → `next_turn` → `assault`"
    ) in k117

    project = (ROOT / "docs" / "PROJECT.md").read_text(encoding="utf-8")
    passive_date = passive["date"]
    active_date = active["date"]
    defensive_date = defensive["date"]
    for document in (k117, project):
        compact_document = document.replace("`", "").replace(" ", "")
        assert "`garrison=1`" in document, document
        assert f"R{passive_date['year']}M{passive_date['month']}" in document, document
        assert f"R{active_date['year']}M{active_date['month']}" in document, document
        assert (
            "next_turn×20" in compact_document
            or "20×next_turn" in compact_document
        ), document
        assert f"R{defensive_date['year']}M{defensive_date['month']}" in document, document
        assert "R2M8" in document, document
        assert "`garrison=3`" in document, document
