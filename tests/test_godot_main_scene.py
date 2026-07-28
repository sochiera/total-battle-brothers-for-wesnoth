import json
from pathlib import Path

from godot_runner import PLAYER_RESULT_PL, run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "SCENE_TREE "
DEVELOP_PREFIX = "DEVELOP_BUTTON "
ORDER_STATUS_PREFIX = "ORDER_STATUS "
MUSTER_PREFIX = "MUSTER_BUTTON "
MARCH_PREFIX = "MARCH_BUTTON "
ASSAULT_PREFIX = "ASSAULT_BUTTON "
ASSAULT_BINDING_PREFIX = "ASSAULT_BUTTON_BINDING "
PARTY_POSITION_PREFIX = "PARTY_POSITION "


def test_scene_probe_reports_main_scene_root():
    result = run_godot_script(
        GAME, "res://tests/scene_probe.gd", timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload[0] == {"path": ".", "name": "Main", "class": "Control"}
    # Public contract is name + class, findable under root; nesting in layout
    # containers is allowed (K83.1) so exact paths are not pinned.
    by_name = {node["name"]: node for node in payload}
    expected_controls = {
        "DateLabel": "Label",
        "StartStatusLabel": "Label",
        "RegionList": "ItemList",
        "ResultLabel": "Label",
        "PlayerDuchyStatusLabel": "Label",
        "LastOrderStatusLabel": "Label",
        "PlayerPartyPositionLabel": "Label",
        "NextTurnButton": "Button",
        "DevelopButton": "Button",
        "RecruitButton": "Button",
        "MusterButton": "Button",
        "MarchButton": "Button",
        "AssaultButton": "Button",
    }
    for name, cls in expected_controls.items():
        assert name in by_name, f"missing public control {name}"
        node = by_name[name]
        assert node["class"] == cls, node
        assert node["path"] != "."
        assert node["path"] == name or node["path"].endswith("/" + name)


def test_player_party_position_renders_and_updates_through_bridge_paths():
    result = run_godot_script(
        GAME, "res://tests/party_position_probe.gd", timeout=30
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(PARTY_POSITION_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PARTY_POSITION_PREFIX) :])
    assert payload["available"] is True
    assert payload["present_first"] == payload["present_second"]
    assert "Stary Gród" in payload["present_first"]
    assert payload["missing"] != payload["present_first"]
    assert payload["missing"].strip()
    assert "brak" in payload["missing"].lower()
    assert payload["empty"] == payload["missing"]
    assert "Nowy Gród" in payload["moved"]
    assert "Stary Gród" not in payload["moved"]
    assert "Odświeżony Gród" in payload["refreshed"]
    assert "Gród po turze" in payload["advanced"]
    assert "Gród po rozkazie" in payload["ordered"]
    assert payload["date_after_order"] == "Rok 9, miesiąc 1"


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
        "pressed_connections": 0,
        "controls_unchanged": True,
    }


def test_assault_button_sends_the_assault_order_and_projects_a_battle_result():
    result = run_godot_script(
        GAME, "res://tests/assault_button_binding_probe.gd", timeout=30
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [
        line
        for line in result.stdout.splitlines()
        if line.startswith(ASSAULT_BINDING_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(ASSAULT_BINDING_PREFIX) :])
    assert payload == {
        "orders": ["assault"],
        "date": "Rok 1, miesiąc 1",
        "result": PLAYER_RESULT_PL["ongoing"],
        "regions": ["Północ"],
        "duchy_status": "Morale: 2, osady: 1, oddziały: 1",
        "order_status": "Szturm: porażka (straty: 0, wróg: 0).",
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
