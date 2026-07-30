"""G97.1f: MarchButton label and order follow MapView region selection."""

from __future__ import annotations

import json
from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/contextual_march_button_probe.gd"
PREFIX = "CONTEXTUAL_MARCH_BUTTON "


def _load() -> dict:
    result = run_godot_script(GAME, PROBE, timeout=45)
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _assert_icon_visible(icon: dict, *, phase: str, march_icon_res: str) -> None:
    assert (icon or {}).get("present") is True, (
        f"{phase}: march icon must stay visible on MarchButton, got {icon!r}"
    )
    path = str((icon or {}).get("path") or "")
    assert path == march_icon_res or path.endswith("icon_march.png"), (
        f"{phase}: expected march icon {march_icon_res!r}, got {path!r}"
    )
    assert int((icon or {}).get("w") or 0) >= 16, f"{phase}: icon too small: {icon!r}"
    assert int((icon or {}).get("h") or 0) >= 16, f"{phase}: icon too small: {icon!r}"


def test_march_button_label_and_order_follow_selected_region():
    """World labels are Polish while the selected move target stays canonical.

    Realistic defect existing gates miss: MapView already selects a region and
    its Polish plate, but Main formats party position, selected-region details
    and MarchButton from canonical snapshot names. Existing probes use custom
    names that need no translation, so that split presentation dictionary can
    stay green while a fresh party exposes English world tokens.
    """
    payload = _load()
    region_a = payload["region_a"]
    region_b = payload["region_b"]
    region_c = payload["region_c"]
    default_label = payload["default_label"]
    label_a = payload["expected_label_a"]
    label_b = payload["expected_label_b"]
    march_icon = payload["march_icon_res"]

    assert payload["party_position"] == (
        f"Położenie oddziału: {payload['region_a_pl']}"
    ), payload
    assert payload["unbound_label"] == default_label, payload
    _assert_icon_visible(payload["unbound_icon"], phase="unbound", march_icon_res=march_icon)

    # No selection: historical automatic march without target.
    assert payload["after_no_selection_label"] == default_label, payload
    _assert_icon_visible(
        payload["after_no_selection_icon"],
        phase="after_no_selection",
        march_icon_res=march_icon,
    )
    assert payload["after_no_selection_press"] == [
        {"order": "march", "target": ""},
    ], (
        "without selection MarchButton must send automatic march with empty "
        f"target once, got {payload['after_no_selection_press']!r}"
    )

    # Selection A → contextual label + single targeted move (no extra march).
    assert payload["after_select_a_label"] == label_a, (
        f"after selecting {region_a!r} button must show {label_a!r}, "
        f"got {payload['after_select_a_label']!r}"
    )
    assert payload["region_a_pl"] in payload["after_select_a_panel"], payload
    assert "Twierdza gracza" in payload["after_select_a_panel"], payload
    assert region_a not in payload["after_select_a_panel"], payload
    assert payload["settlement_a"] not in payload["after_select_a_panel"], payload
    _assert_icon_visible(
        payload["after_select_a_icon"],
        phase="after_select_a",
        march_icon_res=march_icon,
    )
    assert payload["after_select_a_press"] == [
        {"order": "move", "target": region_a},
    ], (
        f"with {region_a!r} selected press must send exactly one move with that "
        f"target (no automatic march), got {payload['after_select_a_press']!r}"
    )

    # Selection B → label and next order target update; still one press → one call.
    assert payload["after_select_b_label"] == label_b, (
        f"after selecting {region_b!r} button must show {label_b!r}, "
        f"got {payload['after_select_b_label']!r}"
    )
    assert payload["region_b_pl"] in payload["after_select_b_panel"], payload
    assert "Twierdza wroga" in payload["after_select_b_panel"], payload
    assert region_b not in payload["after_select_b_panel"], payload
    assert payload["settlement_b"] not in payload["after_select_b_panel"], payload
    _assert_icon_visible(
        payload["after_select_b_icon"],
        phase="after_select_b",
        march_icon_res=march_icon,
    )
    assert payload["after_select_b_press"] == [
        {"order": "move", "target": region_b},
    ], (
        f"with {region_b!r} selected press must send exactly one move with that "
        f"target, got {payload['after_select_b_press']!r}"
    )

    # Unknown names fall back through Main UI without changing the order contract.
    assert payload["after_select_c_label"] == f"Wyrusz: {region_c}", payload
    assert f"Nazwa: {region_c}" in payload["after_select_c_panel"], payload
    assert payload["after_select_c_press"] == [
        {"order": "move", "target": region_c},
    ], payload
