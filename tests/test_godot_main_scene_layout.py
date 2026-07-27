"""Layout contract for the Godot main scene: controls must not stack on one point."""

from __future__ import annotations

import json
from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "SCENE_LAYOUT "

# Public contract names from task-471 / main scene.
STATUS_CONTROLS = (
    "DateLabel",
    "StartStatusLabel",
    "RegionList",
    "ResultLabel",
    "PlayerDuchyStatusLabel",
    "LastOrderStatusLabel",
    "PlayerPartyPositionLabel",
)
ORDER_CONTROLS = (
    "NextTurnButton",
    "DevelopButton",
    "RecruitButton",
    "MusterButton",
    "MarchButton",
    "AssaultButton",
)
ALL_CONTROLS = STATUS_CONTROLS + ORDER_CONTROLS


def _load_layout() -> dict[str, dict[str, float] | None]:
    result = run_godot_script(GAME, "res://tests/scene_layout_probe.gd", timeout=30)
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])
    controls = payload["controls"]
    assert set(controls) == set(ALL_CONTROLS), controls
    return controls


def _rects_share_a_point(a: dict[str, float], b: dict[str, float]) -> bool:
    """Closed axis-aligned rects: true if any screen point lies in both."""
    a_right = a["x"] + a["w"]
    a_bottom = a["y"] + a["h"]
    b_right = b["x"] + b["w"]
    b_bottom = b["y"] + b["h"]
    # Strict separation on an axis ⇒ no shared point (edges may touch).
    if a_right <= b["x"] or b_right <= a["x"]:
        return False
    if a_bottom <= b["y"] or b_bottom <= a["y"]:
        return False
    return True


def _union_bbox(rects: list[dict[str, float]]) -> dict[str, float]:
    left = min(r["x"] for r in rects)
    top = min(r["y"] for r in rects)
    right = max(r["x"] + r["w"] for r in rects)
    bottom = max(r["y"] + r["h"] for r in rects)
    return {"x": left, "y": top, "w": right - left, "h": bottom - top}


def test_main_scene_controls_have_disjoint_layout_and_visible_region_list():
    """Controls must not share screen points; RegionList must be visible area.

    Realistic defect this catches: main.tscn still parents every control at the
    same origin with default zero sizes (empirically all global_position==(0,0),
    RegionList 0×0). Existing scene probes only assert names/classes/text and
    bridge behaviour, so a stacked, unreadable UI stays green.
    """
    controls = _load_layout()

    for name in ALL_CONTROLS:
        rect = controls[name]
        assert rect is not None, f"missing control {name}"
        assert rect["w"] > 0 and rect["h"] > 0, (
            f"{name} must have non-zero size after layout, got {rect}"
        )

    # Beyond ALL_CONTROLS non-zero size: list must be tall enough to show several rows.
    # Default ItemList row ~24px; main.tscn min height is 180 — require at least ~3 rows.
    region = controls["RegionList"]
    assert region["w"] >= 100, f"RegionList width too small for names: {region}"
    assert region["h"] >= 72, f"RegionList height must fit several items, got {region}"

    for i, left_name in enumerate(ALL_CONTROLS):
        for right_name in ALL_CONTROLS[i + 1 :]:
            left = controls[left_name]
            right = controls[right_name]
            assert not _rects_share_a_point(left, right), (
                f"{left_name} and {right_name} share screen area: "
                f"{left} vs {right}"
            )

    status_rects = [controls[name] for name in STATUS_CONTROLS]
    order_rects = [controls[name] for name in ORDER_CONTROLS]
    status_box = _union_bbox(status_rects)
    order_box = _union_bbox(order_rects)
    assert not _rects_share_a_point(status_box, order_box), (
        "status controls and order buttons must form separate groups, "
        f"got status={status_box} orders={order_box}"
    )
