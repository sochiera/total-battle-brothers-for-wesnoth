"""Regression for a command button added to the live order-bar scene."""

from __future__ import annotations

import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/order_bar_dynamic_button_probe.gd"
PREFIX = "ORDER_BAR_DYNAMIC_BUTTON "


def test_order_bar_discovers_configured_commands_in_every_order_bar_row_for_style_and_binding():
    """A scene-added command must not become grey or inert.

    Realistic defect existing gates miss: both ``_order_action_buttons`` and
    ``_bind_order_buttons`` enumerate the ten current node names.  A designer
    can add a configured command button to any OrderBarContent row and it
    stays unstyled or does not dispatch its declared order, while every
    existing per-button binding and the fixed ten-button style probe remains
    green.
    """
    result = run_godot_script(GAME, PROBE, timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) == {
        "calls": ["recruit", "recruit"],
        "buttons": {
            "ProbeGridRecruitButton": {
                "normal": {"carrier": "StyleBoxTexture", "explicit": True},
                "hover": {"carrier": "StyleBoxTexture", "explicit": True},
                "pressed": {"carrier": "StyleBoxTexture", "explicit": True},
            },
            "ProbeOtherRowRecruitButton": {
                "normal": {"carrier": "StyleBoxTexture", "explicit": True},
                "hover": {"carrier": "StyleBoxTexture", "explicit": True},
                "pressed": {"carrier": "StyleBoxTexture", "explicit": True},
            },
        },
    }
