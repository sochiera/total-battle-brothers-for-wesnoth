"""Contract checks for task-677 live assault/engage gates."""

from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tests" / "godot_runner.py"

LIVE_BATTLE_GATES = (
    pytest.param(
        ROOT / "tests" / "test_godot_persistent_assault_e2e.py",
        id="persistent-assault",
    ),
    pytest.param(
        ROOT / "tests" / "test_godot_persistent_engage_e2e.py",
        id="persistent-engage",
    ),
    pytest.param(
        ROOT / "tests" / "test_godot_persistent_natural_assault_e2e.py",
        id="persistent-natural-assault",
    ),
)


@pytest.mark.parametrize("gate_path", LIVE_BATTLE_GATES)
def test_live_battle_gate_is_not_hidden_by_deferred_xfail(gate_path: Path):
    """Every production assault/engage path must execute as a live gate.

    Realistic defect missed by the existing contract gate: task-676 removed the
    stale marker from the assault and engage modules, but the natural assault
    gate could keep an identical strict xfail and continue hiding a live
    regression.  A skipped body cannot enforce the battle-pause contract.
    """
    source = gate_path.read_text(encoding="utf-8")

    assert "DEFERRED_BATTLE_E2E_REASON" not in source, gate_path
    assert "pytest.mark.xfail" not in source, gate_path


def test_deferred_battle_reason_is_not_a_closed_task_contract():
    """The shared reason must not claim that completed G119 work is deferred."""
    source = RUNNER.read_text(encoding="utf-8")

    assert "DEFERRED_BATTLE_E2E_REASON" not in source or "task-673+674+675" not in source
