"""G116.1e: economic buttons (Develop/Recruit/Muster) follow MapView selection.

Covers acceptance criteria 1 and 2 of task-645 and prepares the visual setup
for criterion 5 (1152x648 viewport, panel of the second player settlement).
A narrow live-bridge check covers the selected settlement effect and foreign
region rejection without repeating core economic-order tests.
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/contextual_economic_button_probe.gd"
BRIDGE_PROBE = "res://tests/contextual_economic_button_bridge_probe.gd"
PREFIX = "CONTEXTUAL_ECONOMIC_BUTTON "
BRIDGE_PREFIX = "CONTEXTUAL_ECONOMIC_BUTTON_BRIDGE "
SEED = 73


def _load() -> dict:
    result = run_godot_script(GAME, PROBE, timeout=45)
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX):])


def _assert_calls_match(
    calls: list[dict],
    expected_by_button: dict[str, str],
    region_name: str,
    payload: dict,
    *,
    expected_target: str | None = None,
) -> None:
    """Every configured button must emit exactly one call with the expected target.

    ``expected_by_button`` maps button node name to its declared order name
    (DevelopButton→develop, RecruitButton→recruit, MusterButton→muster).
    """
    target = region_name if expected_target is None else expected_target
    assert isinstance(calls, list), payload
    assert len(calls) == len(expected_by_button), (
        f"with {region_name!r} selected expected "
        f"{len(expected_by_button)} economic order calls, got {calls!r}"
    )
    seen: list[dict] = []
    for button_name, order_name in expected_by_button.items():
        seen.append({"order": order_name, "target": target, "_button": button_name})
    by_signature: dict[tuple, list[dict]] = {}
    for call in calls:
        key = (call.get("order"), call.get("target"))
        by_signature.setdefault(key, []).append(call)
    for expected in seen:
        key = (expected["order"], expected["target"])
        matches = by_signature.get(key, [])
        assert matches, (
            f"{expected['_button']}: with {region_name!r} selected expected call "
            f"order={expected['order']!r} target={expected['target']!r}, "
            f"got {calls!r}"
        )
        by_signature[key] = matches[1:]


def test_economic_buttons_forward_selected_region_as_target():
    """Realistic defect existing gates miss: DevelopButton, RecruitButton and
    MusterButton are wired through ``_on_declared_order_button_pressed`` which
    calls ``_send_bound_order(order_name)`` without reading
    ``%MapView.selected_region_name``. Existing binding probes use a stub
    client whose ``send_order(order_name, _target="")`` discards the target
    argument, so a player selecting their second settlement and pressing
    "Rozwiń osadę" still hits the first. This gate records the target each
    button forwards to the bridge for every selection state.
    """
    payload = _load()
    region_a = payload["region_a"]
    region_b = payload["region_b"]
    region_c = payload["region_c"]

    expected_by_button = {
        "DevelopButton": "develop",
        "RecruitButton": "recruit",
        "MusterButton": "muster",
    }

    # Criterion 5 setup: viewport is the visual-evidence size and the panel of
    # the selected region shows garrison/free (so a screenshot can prove the
    # order went to the indicated settlement). Polish labels hide canonical
    # settlement names, so assert on the metric leaves that criterion 1 names.
    assert payload["viewport"] == [1152, 648], payload
    assert payload["no_selection_panel"] == "Nie wybrano regionu", payload
    assert "garnizon" in payload["select_a_panel"], payload
    assert "wolni mieszkańcy" in payload["select_a_panel"], payload
    assert "garnizon" in payload["select_b_panel"], payload
    assert payload["select_c_panel"] != "Nie wybrano regionu", payload

    # Criterion 2: without a selected region the buttons keep today's contract
    # (no target key forwarded → bridge auto-selects the settlement).
    _assert_calls_match(
        payload["no_selection_calls"],
        {name: order for name, order in expected_by_button.items()},
        "",
        payload,
    )
    _assert_calls_match(
        payload["no_selection_military_calls"],
        {"ReinforceButton": "reinforce", "AssaultButton": "assault", "EngageButton": "engage"},
        "",
        payload,
    )

    # Criterion 1: with a player region selected, the order carries that target.
    _assert_calls_match(payload["select_a_calls"], expected_by_button, region_a, payload)
    # Military orders remain automatic even while a map region is selected.
    _assert_calls_match(
        payload["select_a_military_calls"],
        {"ReinforceButton": "reinforce", "AssaultButton": "assault", "EngageButton": "engage"},
        region_a,
        payload,
        expected_target="",
    )
    # Second player settlement (criterion 5's framed region) is reachable too.
    _assert_calls_match(payload["select_b_calls"], expected_by_button, region_b, payload)
    # Foreign region without a player settlement: the client still forwards
    # the selection; the bridge decides it is a no-op (criterion 3 setup).
    _assert_calls_match(payload["select_c_calls"], expected_by_button, region_c, payload)


def test_economic_button_with_real_bridge_updates_panel_and_reports_foreign_rejection(
    tmp_path,
):
    """The selected settlement changes through the real bridge, not only in a stub log."""
    state_path = tmp_path / "contextual-economic-button-session.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    result = run_godot_script(
        GAME,
        BRIDGE_PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(BRIDGE_PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(BRIDGE_PREFIX) :])

    assert payload["target_region"] == "player outpost"
    assert payload["targeted_result"] == {"order": "develop", "changed": True}
    assert payload["targeted_status"] == "Rozkaz rozwoju zmienił stan."
    assert payload["targeted_panel_before"] != payload["targeted_panel_after"]
    assert "wolni mieszkańcy: 3" in payload["targeted_panel_after"]

    assert payload["foreign_region"] == "ai outpost"
    assert payload["foreign_result"] == {
        "order": "develop",
        "changed": False,
        "reason": "brak własnej osady w tym regionie",
    }
    assert payload["foreign_panel_before"] == payload["foreign_panel_after"]
    assert payload["foreign_status"] == "Rozkaz rozwoju nie zmienił stanu."
    assert "wolnych mieszkańców" not in payload["foreign_status"]
    assert "nie wyżywi" not in payload["foreign_status"]
