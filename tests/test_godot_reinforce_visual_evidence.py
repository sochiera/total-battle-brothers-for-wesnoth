"""G112.1d/G117.1c: committed full-screen before/after visual proof."""

from __future__ import annotations

import subprocess
from pathlib import Path

from godot_png_assets import assert_asset_credited, png_rgba8

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
BEFORE = GAME / "screenshots" / "task-630-reinforce-before-1152x648.png"
AFTER = GAME / "screenshots" / "task-630-reinforce-after-1152x648.png"
MUSTER_BEFORE = GAME / "screenshots" / "task-665-muster-before-1152x648.png"
MUSTER_AFTER = GAME / "screenshots" / "task-665-muster-after-1152x648.png"
ASSET_CREDITS = GAME / "assets" / "CREDITS.md"
VIEWPORT = (1152, 648)


def _selected_region_panel_crop(rgba: bytes, width: int, height: int) -> bytes:
    """Return the selected-region panel area in the fixed 1152×648 evidence frame."""
    crop_x, crop_y = 10, 340
    crop_width = min(400, max(0, width - crop_x))
    crop_height = min(150, max(0, height - crop_y))
    return b"".join(
        rgba[(row + crop_y) * width * 4 + crop_x * 4 :
             (row + crop_y) * width * 4 + (crop_x + crop_width) * 4]
        for row in range(crop_height)
    )


def _map_crop(rgba: bytes, width: int, height: int) -> bytes:
    """Return the strategic-map strip where the new party mark must appear."""
    crop_x, crop_y = 480, 110
    crop_width = min(650, max(0, width - crop_x))
    crop_height = min(220, max(0, height - crop_y))
    return b"".join(
        rgba[(row + crop_y) * width * 4 + crop_x * 4 :
             (row + crop_y) * width * 4 + (crop_x + crop_width) * 4]
        for row in range(crop_height)
    )


def _changed_asset_names() -> list[str]:
    """Find added/changed raster/vector files under game/assets in this worktree."""
    names: set[str] = set()
    for command in (
        ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", "--", "game/assets"],
        ["git", "ls-files", "--others", "--exclude-standard", "--", "game/assets"],
    ):
        result = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
        names.update(
            Path(line).name
            for line in result.stdout.splitlines()
            if Path(line).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}
        )
    return sorted(names)


def test_reinforce_before_after_kadry_are_full_screen_and_change_panel_area():
    """The review pair must show the changed party/garrison panel at 1152×648.

    Realistic defect existing UI tests miss: runtime interaction can be green
    while the required visual evidence is absent, cropped, or two identical
    captures. A difference in the status-card crop keeps the proof tied to the
    selected-region panel rather than accepting an unrelated map-only change.
    """
    assert BEFORE.is_file(), f"missing committed before frame: {BEFORE}"
    assert AFTER.is_file(), f"missing committed after frame: {AFTER}"

    before_width, before_height, before_rgba = png_rgba8(BEFORE)
    after_width, after_height, after_rgba = png_rgba8(AFTER)
    assert (before_width, before_height) == VIEWPORT
    assert (after_width, after_height) == VIEWPORT
    assert before_rgba != after_rgba, "before/after frames must not be identical"
    assert _selected_region_panel_crop(
        before_rgba, before_width, before_height
    ) != _selected_region_panel_crop(
        after_rgba, after_width, after_height
    ), "before/after frames must differ in the selected-region panel area"


def test_muster_before_after_kadry_are_full_screen_and_show_panel_and_army():
    """G117.1c AC4-5: committed muster proof is complete and attributable.

    Realistic defect existing live gates miss: the client can pass its runtime
    assertions while the required before/after evidence is absent, cropped, or
    changes only an unrelated part of the map. The panel and map crops keep the
    proof tied to the visible garrison and newly placed party. Any newly added
    graphics under ``game/assets`` are checked against the public credits file.
    """
    assert MUSTER_BEFORE.is_file(), f"missing committed before frame: {MUSTER_BEFORE}"
    assert MUSTER_AFTER.is_file(), f"missing committed after frame: {MUSTER_AFTER}"

    before_width, before_height, before_rgba = png_rgba8(MUSTER_BEFORE)
    after_width, after_height, after_rgba = png_rgba8(MUSTER_AFTER)
    assert (before_width, before_height) == VIEWPORT
    assert (after_width, after_height) == VIEWPORT
    assert before_rgba != after_rgba, "before/after frames must not be identical"
    assert _selected_region_panel_crop(
        before_rgba, before_width, before_height
    ) != _selected_region_panel_crop(
        after_rgba, after_width, after_height
    ), "before/after frames must differ in the selected-region panel area"
    assert _map_crop(
        before_rgba, before_width, before_height
    ) != _map_crop(
        after_rgba, after_width, after_height
    ), "before/after frames must differ in the strategic-map party area"

    assert ASSET_CREDITS.is_file(), f"missing asset credits file: {ASSET_CREDITS}"
    for asset_name in _changed_asset_names():
        assert_asset_credited(ASSET_CREDITS, asset_name)
