"""G118.1d: the committed live refusal frame shows the new assault status."""

from __future__ import annotations

from pathlib import Path

from godot_png_assets import png_rgba8


ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "game" / "screenshots" / "task-669-military-refusal-1152x648.png"
LEGACY_CAPTURE = ROOT / "game" / "screenshots" / "task-613-blocked-military-order-1152x648.png"
VIEWPORT = (1152, 648)


def _ink_bbox(
    width: int, height: int, pixels: bytes, *, x0: int, y0: int, x1: int, y1: int
) -> tuple[int, int, int, int]:
    points = []
    for y in range(y0, min(y1, height)):
        for x in range(x0, min(x1, width)):
            pixel = (y * width + x) * 4
            red, green, blue = pixels[pixel : pixel + 3]
            if red < 80 and green < 70 and blue < 60:
                points.append((x, y))
    assert points, "status band contains no dark text pixels"
    return (
        min(x for x, _y in points),
        min(y for _x, y in points),
        max(x for x, _y in points),
        max(y for _x, y in points),
    )


def test_task669_capture_is_full_screen_and_contains_the_new_assault_status():
    """The evidence is the refusal scene, not only an unrelated old status frame."""
    assert CAPTURE.is_file(), f"missing committed task-669 capture: {CAPTURE}"
    width, height, pixels = png_rgba8(CAPTURE)
    assert (width, height) == VIEWPORT
    assert CAPTURE.stat().st_size >= 100_000

    # The exact status is guarded by capture_task669_military_refusal.gd. These
    # two line-shape checks tie the committed pixels to that long, newly wrapped
    # sentence: the old exhausted-action frame has a shorter first line and a
    # narrower second line in the same public status slot.
    first_line = _ink_bbox(width, height, pixels, x0=45, y0=235, x1=375, y1=278)
    second_line = _ink_bbox(width, height, pixels, x0=45, y0=278, x1=375, y1=305)
    assert first_line[0] <= 60 and first_line[2] >= 360, first_line
    assert second_line[0] <= 150 and second_line[2] >= 270, second_line

    legacy_width, legacy_height, legacy_pixels = png_rgba8(LEGACY_CAPTURE)
    assert (legacy_width, legacy_height) == VIEWPORT
    legacy_first = _ink_bbox(
        legacy_width, legacy_height, legacy_pixels, x0=45, y0=235, x1=375, y1=278
    )
    assert (first_line[0], first_line[2]) != (legacy_first[0], legacy_first[2])
