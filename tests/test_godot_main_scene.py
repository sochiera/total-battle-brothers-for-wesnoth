import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "SCENE_TREE "
DEVELOP_PREFIX = "DEVELOP_BUTTON "
ORDER_STATUS_PREFIX = "ORDER_STATUS "
MUSTER_PREFIX = "MUSTER_BUTTON "
MARCH_PREFIX = "MARCH_BUTTON "
ASSAULT_PREFIX = "ASSAULT_BUTTON "


def test_scene_probe_reports_main_scene_root():
    result = run_godot_script(
        GAME, "res://scripts/scene_probe.gd", timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload[0] == {"path": ".", "name": "Main", "class": "Control"}
    assert payload[1:] == [
        {"path": "DateLabel", "name": "DateLabel", "class": "Label"},
        {"path": "RegionList", "name": "RegionList", "class": "ItemList"},
        {"path": "ResultLabel", "name": "ResultLabel", "class": "Label"},
        {
            "path": "PlayerDuchyStatusLabel",
            "name": "PlayerDuchyStatusLabel",
            "class": "Label",
        },
        {
            "path": "LastOrderStatusLabel",
            "name": "LastOrderStatusLabel",
            "class": "Label",
        },
        {"path": "NextTurnButton", "name": "NextTurnButton", "class": "Button"},
        {"path": "DevelopButton", "name": "DevelopButton", "class": "Button"},
        {"path": "RecruitButton", "name": "RecruitButton", "class": "Button"},
        {"path": "MusterButton", "name": "MusterButton", "class": "Button"},
        {"path": "MarchButton", "name": "MarchButton", "class": "Button"},
        {"path": "AssaultButton", "name": "AssaultButton", "class": "Button"},
    ]


def test_develop_button_has_exact_text_and_no_behavior():
    result = run_godot_script(
        GAME, "res://tests/develop_button_probe.gd", timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(DEVELOP_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(DEVELOP_PREFIX) :])
    assert payload == {
        "text": "Rozwiń osadę",
        "pressed_connections": 0,
        "child_count_unchanged": True,
    }


def test_muster_button_has_exact_text_and_no_behavior():
    result = run_godot_script(
        GAME, "res://tests/muster_button_probe.gd", timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(MUSTER_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(MUSTER_PREFIX) :])
    assert payload == {
        "name": "MusterButton",
        "text": "Zbierz oddział",
        "direct_child": True,
        "pressed_connections": 0,
        "controls_unchanged": True,
    }


def test_march_button_has_exact_text_and_no_behavior():
    result = run_godot_script(
        GAME, "res://tests/march_button_probe.gd", timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(MARCH_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(MARCH_PREFIX) :])
    assert payload == {
        "name": "MarchButton",
        "text": "Wyrusz w pole",
        "direct_child": True,
        "pressed_connections": 0,
        "controls_unchanged": True,
    }


def test_assault_button_has_exact_text_and_no_behavior():
    result = run_godot_script(
        GAME, "res://tests/assault_button_probe.gd", timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(ASSAULT_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(ASSAULT_PREFIX) :])
    assert payload == {
        "name": "AssaultButton",
        "text": "Szturmuj osadę",
        "direct_child": True,
        "pressed_connections": 0,
        "controls_unchanged": True,
    }


def test_last_order_status_label_starts_empty_without_bridge_configuration():
    result = run_godot_script(
        GAME, "res://tests/order_status_probe.gd", timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(ORDER_STATUS_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(ORDER_STATUS_PREFIX) :])
    assert payload == {"text": ""}
