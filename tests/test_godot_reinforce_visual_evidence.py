"""G112.1d: committed full-screen before/after visual proof."""

from __future__ import annotations

from pathlib import Path

from godot_png_assets import png_rgba8

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
BEFORE = GAME / "screenshots" / "task-630-reinforce-before-1152x648.png"
AFTER = GAME / "screenshots" / "task-630-reinforce-after-1152x648.png"
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
