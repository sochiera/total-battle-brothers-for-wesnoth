"""Visual target-intent gate for G120.1e (task-683)."""

from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess


PREFIX = "BATTLE_TARGET_VISIBILITY "
ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/battle_target_visibility_probe.gd"
VISUAL_PROOF = GAME / "screenshots" / "task-683-battle-target-visibility-1152x648.png"


def _load_probe() -> dict:
    # Pixel-level visual evidence needs a real canvas; the shared headless
    # runner intentionally uses Godot's dummy renderer and returns no image.
    result = subprocess.run(
        [
            "godot",
            "--display-driver",
            "x11",
            "--rendering-method",
            "gl_compatibility",
            "--path",
            str(GAME),
            "--script",
            PROBE,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _by_qr(rows: list[dict]) -> dict[tuple[int, int], dict]:
    return {(int(row["q"]), int(row["r"])): row for row in rows}


def _diff_by_qr(rows: list[dict]) -> dict[tuple[int, int], int]:
    return {(int(row["q"]), int(row["r"])): int(row["pixels"]) for row in rows}


def _hp_labels(tile: dict) -> list[dict]:
    return [label for label in tile.get("labels", []) if "PŻ" in label.get("text", "")]


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path
    return struct.unpack(">II", data[16:24])


def _rgb(record: dict) -> tuple[float, float, float]:
    rgb = record.get("rgb")
    assert isinstance(rgb, list) and len(rgb) == 3, record
    return tuple(float(component) for component in rgb)


def _color_distance(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    return sum(abs(left - right) for left, right in zip(first, second))


def test_battle_view_visibly_tracks_attack_targets_and_keeps_hp_readable():
    """G120.1e AC1-4: target pair is visible, refresh-safe, and legible.

    Realistic defect existing gates miss: SnapshotModel can carry attack_targets
    and task-682 can send them successfully while BattleView ignores the field,
    leaves a previous highlight after a fresh snapshot, or paints an opaque
    overlay over the PŻ labels. The probe compares rendered pixels for two
    public target states and an empty refresh, records a human-review frame,
    and checks visible Polish battle controls; it does not require a marker
    node, asset, or private implementation name.
    """
    payload = _load_probe()
    assert payload["battle_view_visible"] is True, payload
    assert payload["battle_result_text"] == "", payload
    hexes = payload["hexes"]
    assert len(hexes) == 4, payload
    assert {str(row["side"]) for row in hexes} == {"attacker", "defender"}, payload
    assert payload["first_targets"] == [
        {"attacker": {"q": 0, "r": 0}, "target": {"q": 2, "r": 0}}
    ], payload
    assert payload["second_targets"] == [
        {"attacker": {"q": 1, "r": 0}, "target": {"q": 3, "r": 0}}
    ], payload

    # AC4: the same in-progress pair used by the pixel probe is committed as
    # a human-review frame at the required viewport size and retains Polish UI.
    visual_proof = payload["visual_proof"]
    assert visual_proof == {
        "path": "res://screenshots/task-683-battle-target-visibility-1152x648.png",
        "width": 1152,
        "height": 648,
    }, payload
    assert VISUAL_PROOF.is_file(), f"missing human-review screenshot: {VISUAL_PROOF}"
    assert _png_dimensions(VISUAL_PROOF) == (1152, 648), VISUAL_PROOF
    assert VISUAL_PROOF.stat().st_size >= 100_000, VISUAL_PROOF
    assert payload["polish_ui"] == {
        "BattleHeaderLabel": {"text": "Bitwa", "visible": True},
        "BattleAdvanceButton": {"text": "Następna runda", "visible": True},
        "BattleAutoButton": {"text": "Rozstrzygnij od razu", "visible": True},
    }, payload["polish_ui"]

    baseline = _by_qr(payload["baseline_tiles"])
    first = _by_qr(payload["first_tiles"])
    empty = _by_qr(payload["empty_tiles"])
    second = _by_qr(payload["second_tiles"])
    first_diff = _diff_by_qr(payload["first_diff_by_hex"])
    empty_diff = _diff_by_qr(payload["empty_diff_by_hex"])
    second_diff = _diff_by_qr(payload["second_diff_by_hex"])

    assert set(baseline) == set(first) == set(empty) == set(second) == {
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 0),
    }, payload

    # AC1: both endpoints of the first public pair change the rendered board,
    # while the two other units remain visually untouched.
    assert first_diff[(0, 0)] > 12 and first_diff[(2, 0)] > 12, (
        f"attacker and target hexes must have visible first-pair markers, diff={first_diff}"
    )
    assert first_diff[(1, 0)] <= 2 and first_diff[(3, 0)] <= 2, (
        f"unselected units must not receive the first-pair marker, diff={first_diff}"
    )

    # AC1: attacker and target use visually distinguishable marker colors,
    # rather than merely receiving the same generic overlay.
    first_marker_colors = _by_qr(payload["first_marker_colors"])
    assert _color_distance(
        _rgb(first_marker_colors[(0, 0)]), _rgb(first_marker_colors[(2, 0)])
    ) > 0.25, (
        "attacker and target markers must be color-distinguishable, "
        f"colors={first_marker_colors}"
    )

    # AC2: a snapshot with no attack_targets removes the old visual state, and
    # a later public pair moves it to the new endpoints instead of accumulating.
    assert all(pixels <= 2 for pixels in empty_diff.values()), (
        f"clearing attack_targets must remove the old highlight, diff={empty_diff}"
    )
    assert second_diff[(1, 0)] > 12 and second_diff[(3, 0)] > 12, (
        f"new target pair must be visibly highlighted, diff={second_diff}"
    )
    assert second_diff[(0, 0)] <= 2 and second_diff[(2, 0)] <= 2, (
        f"old target pair must not leave a ghost highlight, diff={second_diff}"
    )

    # AC3: with two units per side, every PŻ marker remains visible and has
    # rendered dark text in the highlighted state; the marker cannot hide it.
    for qr, tile in first.items():
        labels = _hp_labels(tile)
        assert len(labels) == 1, f"hex {qr} must expose one PŻ label, tile={tile!r}"
        label = labels[0]
        assert label["visible"] is True and label["rect"]["w"] > 0 and label["rect"]["h"] > 0, (
            f"hex {qr} PŻ label must remain visible and sized, label={label!r}"
        )
        assert label["ink_pixels"] >= 3, (
            f"hex {qr} PŻ text must remain visually readable under target marking, label={label!r}"
        )
