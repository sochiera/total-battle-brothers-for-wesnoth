"""Contract checks for task-676's three live measurement gates."""

from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "docs" / "PROJECT.md"


MEASUREMENT_GATES = (
    pytest.param(
        ROOT / "tests" / "test_godot_targeted_economic_measurement.py",
        ("population", "free", "changed:true", "R1M4", "R1M7"),
        "  Trwałe piny pomiarowe bramek live:",
        "\n\n## Ograniczenia",
        id="targeted-economic-k115",
    ),
    pytest.param(
        ROOT / "tests" / "test_godot_task664_live_measurement.py",
        ("garrison=1", "garrison=3", "next_turn", "R2M8", "R1M7", "R1M5"),
        "- **K117 — DOMKNIĘTY",
        "\n- **K118 — DOMKNIĘTY",
        id="task664-k117",
    ),
    pytest.param(
        ROOT / "tests" / "test_godot_persistent_engage_e2e.py",
        ("recruit`×3", "R1M4", "R1M7"),
        "- **K118 — DOMKNIĘTY",
        "\n\n  Trwałe piny pomiarowe bramek live:",
        id="persistent-engage-k118",
    ),
)


@pytest.mark.parametrize(
    "gate_path, gate_markers, project_start, project_end", MEASUREMENT_GATES
)
def test_measurement_gate_is_live_and_pins_product_record(
    gate_path: Path,
    gate_markers: tuple[str, ...],
    project_start: str,
    project_end: str,
):
    """The live gates must survive backlog migration and battle pausing.

    Realistic defect missed by the existing tests: the product record can be
    complete while the three measurement gates remain hidden behind a stale
    xfail and still parse removed BACKLOG headings.  The existing gates cannot
    expose that contract failure because pytest reports their body as xfailed.
    """
    gate_source = gate_path.read_text(encoding="utf-8")
    project_source = PROJECT.read_text(encoding="utf-8")
    project_start_index = project_source.index(project_start)
    project_block = project_source[
        project_start_index : project_source.index(project_end, project_start_index)
    ]

    # AC1: the gate is independent of removed milestone headings.
    assert "BACKLOG.md" not in gate_source, gate_path
    assert "Kamień milowy 11" not in gate_source, gate_path

    # AC2: the measured product record remains durable and the gate keeps its
    # former values as required markers rather than dropping them.
    assert "PROJECT.md" in gate_source, gate_path
    for marker in gate_markers:
        assert marker in project_block, f"{gate_path.name} pin missing: {marker}"

    # AC3: these gates are live now rather than hidden behind the stale
    # deferral marker. Their end-to-end bodies cover pending battle resolution,
    # so this contract test stays independent of helper names.
    assert "DEFERRED_BATTLE_E2E_REASON" not in gate_source, gate_path
