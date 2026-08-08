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
    # G114.1c (task-637): the bridge diagnostic ``reason`` (task-636) must be
    # projected through so status_text can name what was lacking. Projection is
    # a faithful carrier (wzorzec K111 / blocked_region): any string reason is
    # carried, including ones status_text will later map to a fallback.
    assert payload["recruit_reason_transient"] == {
        "order": "recruit",
        "changed": False,
        "reason": "brak wolnej ludności",
    }
    assert payload["recruit_reason_permanent"] == {
        "order": "recruit",
        "changed": False,
        "reason": "brak wolnej ludności — osada nie wyżywi przyrostu",
    }
    assert payload["recruit_reason_unknown"] == {
        "order": "recruit",
        "changed": False,
        "reason": "nieznany defekt xyz",
    }
    # G114.1c: the bridge carries ``reason`` for develop and muster too
    # (test_protocol.py); projection must treat all economic orders alike.
    assert payload["develop_reason_transient"] == {
        "order": "develop",
        "changed": False,
        "reason": "brak wolnej ludności",
    }
    assert payload["muster_reason_transient"] == {
        "order": "muster",
        "changed": False,
        "reason": "brak wolnej ludności",
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
    assert payload["engage_battle"] == {
        "kind": "battle",
        "order": "engage",
        "outcome": "porażka",
        "attacker_losses": 1,
        "defender_losses": 0,
    }
    assert payload["engage_unchanged"] == {"order": "engage", "changed": False}
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
        "reinforce_changed": "Oddział został wzmocniony.",
        "reinforce_unchanged": "Wzmocnienie nie zmieniło stanu oddziału.",
        "reinforce_exhausted": "Oddział już działał w tym miesiącu — zakończ turę.",
        "assault_unchanged": "Oddział już działał w tym miesiącu — zakończ turę.",
        "assault_unchanged_default": "Rozkaz szturmu nie zmienił stanu.",
        # G97.1f: targeted move has dedicated PL (not the generic order template).
        # Blocked move (changed=false), e.g. enemy settlement: exact AC wording.
        "move_changed": "Oddział przemieścił się.",
        "move_unchanged": "Ruch nie nastąpił.",
        # G91.2b: odpowiedź mostu z game_over:true nie może wyglądać jak no-op w trwającej partii.
        "game_over_order": "Partia jest zakończona.",
        "assault_battle": "Szturm: porażka (straty: 0, wróg: 0).",
        "assault_battle_from_wire": "Szturm: zwycięstwo (straty: 0, wróg: 2).",
        # Ten sam szablon co zwycięstwo/porażka/remis; outcome mostu wprost w tekście.
        "assault_battle_unresolved": "Szturm: nierozstrzygnięta (straty: 0, wróg: 0).",
        "engage_unchanged": "Oddział już działał w tym miesiącu — zakończ turę.",
        "march_blocked": "Droga zablokowana w regionie Pogranicze: stoi tam wojsko wroga. Uderz na wojsko wroga.",
        "move_blocked": "Droga zablokowana w regionie Pogranicze: stoi tam wojsko wroga. Uderz na wojsko wroga.",
        "move_changed_with_blocker": "Oddział przemieścił się.",
        "move_blocked_missing_region": "Ruch nie nastąpił.",
        "move_blocked_invalid_region": "Ruch nie nastąpił.",
        "move_blocked_unknown_region": "Ruch nie nastąpił.",
        "engage_unchanged_default": "Rozkaz starcia nie zmienił stanu.",
        "engage_battle": "Starcie: porażka (straty: 1, wróg: 0).",
        # G114.1c (task-637): the refusal reason (task-636 field) surfaces in
        # Polish. Transient hunger may advise waiting; permanent hunger names
        # the state. An unrecognized reason falls back to the generic no-op
        # text (never empty), so a future core reason does not show a blank.
        "recruit_reason_transient": "Brak wolnych mieszkańców — ludność przybędzie w kolejnej turze.",
        "recruit_reason_permanent": "Osada nie wyżywi więcej ludzi — ludność nie przybywa.",
        "recruit_reason_unknown": "Rozkaz rekrutacji nie zmienił stanu.",
        "develop_reason_transient": "Brak wolnych mieszkańców — ludność przybędzie w kolejnej turze.",
        "muster_reason_transient": "Brak wolnych mieszkańców — ludność przybędzie w kolejnej turze.",
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

    # G114.1c AC2: permanent refusal names the state and MUST NOT advise
    # waiting, promise a way out, refer to an empty granary, or push a second
    # settlement — on the measured threshold the wheat store is still positive
    # and neither settlement recovers, so any such advice would be a lie.
    transient = payload["recruit_reason_transient"]
    permanent = payload["recruit_reason_permanent"]
    unknown = payload["recruit_reason_unknown"]
    assert transient != permanent, "transient and permanent reasons must read differently"
    assert "kolejnej turze" in transient.lower(), "transient reason should advise waiting"
    for forbidden in ("kolejnej turze", "poczekaj", "czekaj", "spichlerz", "pusty", "druga osada", "w drugiej"):
        assert forbidden.lower() not in permanent.lower(), (
            f"permanent refusal must not say {forbidden!r}: {permanent!r}"
        )
    # Never an empty status, and an unrecognized reason keeps the generic no-op text.
    assert permanent.strip() != ""
    assert unknown == "Rozkaz rekrutacji nie zmienił stanu."
