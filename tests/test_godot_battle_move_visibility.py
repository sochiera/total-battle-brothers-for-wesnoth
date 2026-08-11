"""Visual move-intent gate for G121.1e (task-689)."""

from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess


PREFIX = "BATTLE_MOVE_VISIBILITY "
ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/battle_move_visibility_probe.gd"
VISUAL_PROOF = GAME / "screenshots" / "task-689-battle-move-visibility-1152x648.png"


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


def _present_by_qr(rows: list[dict]) -> dict[tuple[int, int], bool]:
    return {
        (int(row["q"]), int(row["r"])): bool(row.get("present", True)) for row in rows
    }


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


def _color_distance(
    first: tuple[float, float, float], second: tuple[float, float, float]
) -> float:
    return sum(abs(left - right) for left, right in zip(first, second))


def test_battle_view_visibly_tracks_move_targets_and_keeps_hp_readable():
    """G121.1e AC1-4: move pair is visible, refresh-safe, and legible.

    Realistic defect existing gates miss: SnapshotModel and BattleView already
    carry attack_targets markers and the move-selection path can send
    battle_move, while the board still ignores public battle.move_targets,
    leaves a previous move highlight after a fresh snapshot, paints the same
    colors as attack intent, or drops move_targets in from_response so the
    live bridge never reaches the view. The probe compares rendered pixels for
    two public move states, an empty refresh, a combined move+attack snapshot,
    and a bridge-projected move_targets field; it does not require a private
    marker class name.
    """
    payload = _load_probe()
    assert payload["battle_view_visible"] is True, payload
    assert payload["battle_result_text"] == "", payload
    hexes = payload["hexes"]
    assert len(hexes) == 4, payload
    assert {str(row["side"]) for row in hexes} == {"attacker", "defender"}, payload
    assert payload["first_moves"] == [
        {"mover": {"q": 0, "r": 0}, "destination": {"q": 0, "r": 1}}
    ], payload
    assert payload["second_moves"] == [
        {"mover": {"q": 1, "r": 0}, "destination": {"q": 1, "r": 1}}
    ], payload

    # Public adapter: live bridge snapshots must expose move_targets on the model.
    assert payload["projected_move_targets"] == payload["first_moves"], payload

    # AC4: the same in-progress move used by the pixel probe is committed as a
    # human-review frame at the required viewport size and retains Polish UI.
    visual_proof = payload["visual_proof"]
    assert visual_proof == {
        "path": "res://screenshots/task-689-battle-move-visibility-1152x648.png",
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
    first_present = _present_by_qr(payload["first_diff_by_hex"])
    empty_diff = _diff_by_qr(payload["empty_diff_by_hex"])
    second_diff = _diff_by_qr(payload["second_diff_by_hex"])
    second_present = _present_by_qr(payload["second_diff_by_hex"])
    second_old = _diff_by_qr(payload["second_old_pair_diff"])
    combined_move_diff = _diff_by_qr(payload["combined_move_diff"])
    combined_attack_diff = _diff_by_qr(payload["combined_attack_diff"])

    assert set(baseline) == set(first) == set(empty) == set(second) == {
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 0),
    }, payload

    # AC1: both endpoints of the first public move pair change the rendered
    # board (mover unit tile and free destination tile).
    assert first_present[(0, 0)] is True and first_present[(0, 1)] is True, (
        f"mover and destination tiles must exist for the first move, "
        f"present={first_present}"
    )
    assert first_diff[(0, 0)] > 12 and first_diff[(0, 1)] > 12, (
        f"mover and destination hexes must have visible first-pair markers, "
        f"diff={first_diff}"
    )

    # AC1: mover and destination use visually distinguishable marker colors.
    first_marker_colors = _by_qr(payload["first_marker_colors"])
    assert first_marker_colors[(0, 0)].get("present") is True, first_marker_colors
    assert first_marker_colors[(0, 1)].get("present") is True, first_marker_colors
    assert _color_distance(
        _rgb(first_marker_colors[(0, 0)]), _rgb(first_marker_colors[(0, 1)])
    ) > 0.25, (
        "mover and destination markers must be color-distinguishable, "
        f"colors={first_marker_colors}"
    )

    # AC2: a snapshot with no move_targets removes the old visual state, and a
    # later public pair moves it to the new endpoints instead of accumulating.
    assert all(pixels <= 2 for pixels in empty_diff.values()), (
        f"clearing move_targets must remove the old highlight, diff={empty_diff}"
    )
    assert second_present[(1, 0)] is True and second_present[(1, 1)] is True, (
        f"second move pair tiles must exist, present={second_present}"
    )
    assert second_diff[(1, 0)] > 12 and second_diff[(1, 1)] > 12, (
        f"new move pair must be visibly highlighted, diff={second_diff}"
    )
    assert second_old[(0, 0)] <= 2 and second_old[(0, 1)] <= 2, (
        f"old move pair must not leave a ghost highlight, diff={second_old}"
    )

    # AC1: every PŻ marker remains visible and has rendered dark text under the
    # move highlight; the marker cannot hide it.
    for qr, tile in first.items():
        labels = _hp_labels(tile)
        assert len(labels) == 1, f"hex {qr} must expose one PŻ label, tile={tile!r}"
        label = labels[0]
        assert label["visible"] is True and label["rect"]["w"] > 0 and label["rect"]["h"] > 0, (
            f"hex {qr} PŻ label must remain visible and sized, label={label!r}"
        )
        assert label["ink_pixels"] >= 3, (
            f"hex {qr} PŻ text must remain visually readable under move marking, "
            f"label={label!r}"
        )

    # AC3: independent move and attack intents stay visible together and use
    # distinguishable colors so the player does not confuse the two orders.
    assert combined_move_diff[(0, 0)] > 12 and combined_move_diff[(0, 1)] > 12, (
        f"move pair must remain visible beside attack markers, "
        f"diff={combined_move_diff}"
    )
    assert combined_attack_diff[(1, 0)] > 12 and combined_attack_diff[(3, 0)] > 12, (
        f"attack pair must remain visible beside move markers, "
        f"diff={combined_attack_diff}"
    )
    move_colors = _by_qr(payload["combined_move_colors"])
    attack_colors = _by_qr(payload["combined_attack_colors"])
    assert _color_distance(
        _rgb(move_colors[(0, 0)]), _rgb(attack_colors[(1, 0)])
    ) > 0.20, (
        "move mover marker must be color-distinguishable from attack attacker, "
        f"move={move_colors} attack={attack_colors}"
    )
