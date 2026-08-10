"""Acceptance gate for task-678's measured regressions and product docs."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "docs" / "PROJECT.md"
BACKLOG = ROOT / "BACKLOG.md"


def _project_section(source: str, heading: str, next_heading: str) -> str:
    start = source.index(heading)
    return source[start : source.index(next_heading, start)]


def test_task678_measured_regressions_and_product_status_are_consistent():
    """AC6-7: measured public pins and delivered battle stories agree.

    Realistic defect missed by the existing gates: live K112/K115-K118
    measurements can remain green while the product record still says that
    battle is an open, auto-only feature and the backlog leaves delivered
    stories marked as new.
    """
    project = PROJECT.read_text(encoding="utf-8")
    backlog = BACKLOG.read_text(encoding="utf-8")

    # AC6: keep the measured K112/K115-K118 records that the live regression
    # gates exercise, including their outcome and state pins.
    k112 = _project_section(project, "- **K112 — DOMKNIĘTY", "- **K114 — DOMKNIĘTY")
    assert "`develop`×10 → `recruit`×10 → `muster`" in k112, k112
    assert "8 turach" in k112 and "garrison: 1" in k112, k112

    k115 = _project_section(project, "- **K115 — DOMKNIĘTY", "- **K116 — DOMKNIĘTY")
    assert "R1M7" in k115 and "R1M4" in k115, k115
    assert "population 5→8" in k115 and "free` 2→5" in k115, k115

    k116 = _project_section(project, "- **K116 — DOMKNIĘTY", "- **K117 — DOMKNIĘTY")
    assert "wskazanego regionu (`target`)" in k116, k116

    k117 = _project_section(project, "- **K117 — DOMKNIĘTY", "- **K118 — DOMKNIĘTY")
    assert all(marker in k117 for marker in ("garrison=1", "R1M7", "R1M5", "R2M8", "garrison=3")), k117

    k118 = _project_section(project, "- **K118 — DOMKNIĘTY", "  Trwałe piny pomiarowe bramek live:")
    assert all(marker in k118 for marker in ("recruit`×3", "R1M4", "R1M7")), k118

    # AC7: PROJECT must describe the delivered paused-battle slice, and all
    # five public stories must no longer be left in the new state.
    assert "bitwa jest w całości rozstrzygana automatycznie" not in project
    stages = project[project.index("## Kolejne prawdopodobne etapy") :]
    assert "dostarczona pauzowana bitwa" in stages, stages
    for story_id in ("US-001", "US-002", "US-003", "US-004", "US-005"):
        heading = next(
            line for line in backlog.splitlines() if line.startswith(f"## {story_id} ")
        )
        assert "[nowa]" not in heading, heading
