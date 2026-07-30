"""NextTurnButton: Polish label, enabled state, and time-passage icon (G95.1a)."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from godot_runner import run_godot_script
from test_godot_assets import _LICENSE_RE, _import_game_assets

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/next_turn_button_probe.gd"
PREFIX = "NEXT_TURN_BUTTON "

# Public presentation path for the Next Turn order icon (G95.1a).
ICON_REL = "assets/icon_next_turn.png"
ICON_RES = f"res://{ICON_REL}"
# Icon must be large enough to read beside the label on a 40px-tall control.
MIN_ICON_EDGE = 16


def _run_probe(*script_args: str) -> subprocess.CompletedProcess[str]:
    return run_godot_script(GAME, PROBE, *script_args, timeout=30)


def _payload_from(result: subprocess.CompletedProcess[str]) -> dict:
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_main_scene_exposes_an_enabled_next_turn_button():
    result = _run_probe()

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    payload = _payload_from(result)
    assert payload["name"] == "NextTurnButton"
    assert payload["text"] == "Następna tura"
    assert payload["disabled"] is False


def test_next_turn_button_probe_fails_for_an_incorrect_label_expectation():
    result = _run_probe("Zła etykieta")

    assert result.returncode != 0
    assert "SCRIPT ERROR" not in result.stderr, result.stderr


def test_next_turn_button_shows_credited_time_icon_with_polish_label():
    """NextTurnButton must show a committed Texture2D icon, not text alone.

    Realistic defect existing gates miss: NextTurnButton is still a plain
    ``Button`` with only ``text = "Następna tura"``. ``next_turn_button_probe``
    and layout/e2e gates only assert name, Polish label, enabled state, and
    geometry, so a purely textual order bar stays green while G95.1a requires a
    real time-passage graphic (CC0/CC-BY) under a public ``res://assets/`` path.
    """
    icon_on_disk = GAME / ICON_REL
    assert icon_on_disk.is_file(), (
        f"committed next-turn icon missing on disk: {icon_on_disk}"
    )

    credits = (GAME / "assets" / "CREDITS.md").read_text(encoding="utf-8")
    credit_lines = credits.splitlines()
    credit_idx = next(
        (i for i, line in enumerate(credit_lines) if Path(ICON_REL).name in line),
        None,
    )
    assert credit_idx is not None, (
        f"CREDITS.md must attribute {Path(ICON_REL).name} with source/author/license"
    )
    credit_window = "\n".join(
        credit_lines[max(0, credit_idx - 3) : credit_idx + 4]
    )
    assert _LICENSE_RE.search(credit_window), (
        f"CREDITS.md must state CC0 or CC-BY next to {Path(ICON_REL).name}"
    )
    assert re.search(r"https?://\S+|PNG/", credit_window), (
        f"CREDITS.md must give a source page or pack-relative path for "
        f"{Path(ICON_REL).name}"
    )

    # Headless import so scene-assigned Texture2D resources resolve after add.
    imported = _import_game_assets()
    assert imported.returncode == 0, (
        f"godot --import failed rc={imported.returncode} "
        f"stderr={imported.stderr!r} stdout={imported.stdout!r}"
    )

    result = _run_probe()
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    payload = _payload_from(result)

    assert payload["name"] == "NextTurnButton"
    assert payload["text"] == "Następna tura", (
        "Polish label must remain; icon is presentation only"
    )
    assert payload["disabled"] is False
    assert payload.get("has_icon") is True, (
        f"NextTurnButton.icon must be a Texture2D (time-passage asset), got {payload!r}"
    )
    assert payload.get("icon_path") == ICON_RES, (
        f"icon must use public path {ICON_RES}, got {payload.get('icon_path')!r}"
    )
    assert int(payload.get("icon_w") or 0) >= MIN_ICON_EDGE, payload
    assert int(payload.get("icon_h") or 0) >= MIN_ICON_EDGE, payload
