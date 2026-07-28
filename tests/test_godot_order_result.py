import json
from pathlib import Path
import re

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
SCRIPT = GAME / "scripts" / "order_result.gd"
PROBE = GAME / "tests" / "order_result_probe.gd"
PREFIX = "ORDER_RESULT "
STATUS_TEXT_PREFIX = "ORDER_STATUS_TEXT "


def test_order_result_exposes_pure_status_text_function():
    source = SCRIPT.read_text(encoding="utf-8")

    assert re.search(
        r"^static func status_text\(order_result: Variant\) -> String:",
        source,
        flags=re.MULTILINE,
    ), "OrderResult must expose status_text for projected order results"


def test_order_result_exposes_a_pure_order_failure_status_function():
    source = SCRIPT.read_text(encoding="utf-8")

    assert re.search(
        r"^static func failure_status_text\(\) -> String:",
        source,
        flags=re.MULTILINE,
    ), "OrderResult must own the general status text for a failed order"


def test_godot_order_result_projects_only_complete_successful_order_results():
    assert SCRIPT.is_file(), "missing res://scripts/order_result.gd"
    assert PROBE.is_file(), "missing res://tests/order_result_probe.gd"

    result = run_godot_script(GAME, "res://tests/order_result_probe.gd", timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])

    assert payload["changed"] == {"order": "develop", "changed": True}
    assert payload["unchanged"] == {"order": "develop", "changed": False}
    # G91.2b: projected shape must keep game_over (not only status_text).
    assert payload["game_over_order"] == {
        "order": "recruit",
        "changed": False,
        "game_over": True,
    }
    assert payload["battle"] == {
        "kind": "battle",
        "order": "assault",
        "outcome": "porażka",
        "attacker_losses": 0,
        "defender_losses": 0,
    }
    assert payload["battle_from_wire"] == {
        "kind": "battle",
        "order": "assault",
        "outcome": "zwycięstwo",
        "attacker_losses": 0,
        "defender_losses": 2,
    }
    # Most (G89.1b-2) oddaje outcome "nierozstrzygnięta" — klient musi projektować
    # ten skutek jak każdy inny wynik bitwy, nie odrzucać go ani mapować na null.
    assert payload["battle_unresolved"] == {
        "kind": "battle",
        "order": "assault",
        "outcome": "nierozstrzygnięta",
        "attacker_losses": 0,
        "defender_losses": 0,
    }
    for case in (
        "missing_ok",
        "not_ok",
        "missing_result",
        "turn_result",
        "save_result",
        "snapshot_result",
        "new_game_result",
        "missing_order",
        "invalid_order",
        "missing_changed",
        "invalid_changed",
        "battle_missing_outcome",
        "battle_missing_order",
        "battle_invalid_order",
        "battle_invalid_outcome",
        "battle_missing_attacker_losses",
        "battle_missing_defender_losses",
        "battle_invalid_attacker_losses",
        "battle_invalid_defender_losses",
        "battle_fractional_losses_from_wire",
    ):
        assert payload[case] is None


def test_godot_order_result_returns_polish_status_text_for_projected_orders():
    result = run_godot_script(GAME, "res://tests/order_result_probe.gd", timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(STATUS_TEXT_PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(STATUS_TEXT_PREFIX) :])

    assert payload == {
        "develop_changed": "Rozkaz rozwoju zmienił stan.",
        "develop_unchanged": "Rozkaz rozwoju nie zmienił stanu.",
        "recruit_changed": "Rozkaz rekrutacji zmienił stan.",
        "recruit_unchanged": "Rozkaz rekrutacji nie zmienił stanu.",
        "muster_changed": "Rozkaz zbiórki zmienił stan.",
        "muster_unchanged": "Rozkaz zbiórki nie zmienił stanu.",
        "assault_unchanged": "Rozkaz szturmu nie zmienił stanu.",
        # G91.2b: odpowiedź mostu z game_over:true nie może wyglądać jak no-op w trwającej partii.
        "game_over_order": "Partia jest zakończona.",
        "assault_battle": "Szturm: porażka (straty: 0, wróg: 0).",
        "assault_battle_from_wire": "Szturm: zwycięstwo (straty: 0, wróg: 2).",
        # Ten sam szablon co zwycięstwo/porażka/remis; outcome mostu wprost w tekście.
        "assault_battle_unresolved": "Szturm: nierozstrzygnięta (straty: 0, wróg: 0).",
        "missing_result": "",
        "non_dictionary": "",
        "missing_order": "",
        "invalid_changed": "",
        "unknown_order": "",
        "unknown_kind": "",
        "deterministic": "Rozkaz rozwoju zmienił stan.",
        "deterministic_muster": "Rozkaz zbiórki zmienił stan.",
    }
    unresolved = payload["assault_battle_unresolved"]
    assert unresolved != payload["assault_battle"]
    assert unresolved != payload["assault_battle_from_wire"]
    assert unresolved != "Szturm: remis (straty: 0, wróg: 0)."
    assert unresolved != "Rozkaz nie powiódł się."
    assert "nierozstrzyg" in unresolved.lower()
