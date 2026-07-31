import json
from pathlib import Path

import pytest

from godot_runner import (
    MISSING_PLAYER_RESULT_PL,
    PLAYER_RESULT_PL,
    run_godot_script,
)


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
FIXTURE = GAME / "tests" / "fixtures" / "session_snapshot.json"
PREFIX = "SCENE_TEXT "


def _bind_payload(tmp_path, player_result) -> dict:
    """Bind fixture snapshot; player_result may be str or None (JSON null from bridge)."""
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response_fixture = fixture.copy()
    response_result = fixture["result"].copy()
    response_result["player_result"] = player_result
    response_fixture["result"] = response_result
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": response_fixture}), encoding="utf-8"
    )
    result = run_godot_script(
        GAME, "res://tests/scene_bind_probe.gd", str(response_path), timeout=30
    )
    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    return json.loads(lines[0][len(PREFIX) :])


def test_scene_bind_probe_applies_model_date_regions_and_result(tmp_path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": fixture}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://tests/scene_bind_probe.gd", str(response_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload["date"] == (
        f"Rok {fixture['calendar']['year']}, miesiąc {fixture['calendar']['month']}"
    )
    token = fixture["result"]["player_result"]
    assert payload["result"] == PLAYER_RESULT_PL[token]
    assert payload["result_visible"] == PLAYER_RESULT_PL[token].removeprefix("Wynik: ")
    assert payload["regions"] == len(fixture["map"]["regions"])
    assert payload["region_names"] == [
        region["name"] for region in fixture["map"]["regions"]
    ]


@pytest.mark.parametrize(
    "token,expected",
    list(PLAYER_RESULT_PL.items()),
    ids=list(PLAYER_RESULT_PL),
)
def test_scene_bind_probe_shows_polish_player_result_not_bridge_token(
    tmp_path, token, expected
):
    """G90.2b: ResultLabel maps bridge tokens to Polish; English token stays off-screen.

    Realistic defect: apply_model formats ``Wynik: %s`` with raw player_result
    (ongoing/victory/defeat/draw), so a Polish UI shows English status tokens.
    Existing binding probes asserted that same English format and never caught it.
    """
    payload = _bind_payload(tmp_path, token)
    assert payload["result"] == expected
    assert token not in payload["result"]
    assert payload["result_visible"] == expected.removeprefix("Wynik: ")
    assert not payload["result_visible"].startswith("Wynik:")


@pytest.mark.parametrize(
    "missing_value",
    ["", None],
    ids=["empty_string", "json_null"],
)
def test_scene_bind_probe_missing_player_result_is_readable_polish(
    tmp_path, missing_value
):
    """G90.2b AC2: missing result is readable Polish — empty string or bridge null.

    Realistic defect: tbbbridge emits player_result JSON null when there is no
    player duchy; SnapshotModel.from_response requires TYPE_STRING and rejects
    the whole model, so apply_model never runs and ResultLabel stays blank.
    The empty-string case alone did not catch null rejection.
    """
    payload = _bind_payload(tmp_path, missing_value)
    assert payload["result"] == MISSING_PLAYER_RESULT_PL
    assert payload["result_visible"] == MISSING_PLAYER_RESULT_PL.removeprefix("Wynik: ")
    assert not payload["result_visible"].startswith("Wynik:")
    assert payload["result"].strip() != ""
    assert payload["result"].strip() != "Wynik:"


def _result_visual(payload: dict) -> tuple:
    """Visual fingerprint of ResultLabel (modulate + font color)."""
    return (
        tuple(payload["result_modulate"]),
        tuple(payload["result_font_color"]),
    )


def test_status_card_uses_distinct_label_value_rows_and_separators(tmp_path):
    """G101.1c: strategic status is a hierarchy, not several text-wall labels.

    Realistic defect missed by existing binding/layout gates: all expected copy
    can remain present and fit the window while duchy statistics are still one
    comma-separated Label and date/result/position have no distinct label and
    value cells. That preserves text but does not provide the required hierarchy.
    """
    payload = _bind_payload(tmp_path, "ongoing")
    records = payload["status_card_labels"]
    by_parent = {}
    for record in records:
        by_parent.setdefault(record["parent"], []).append(record["text"].strip())

    expected_rows = {
        "Data": ("Rok", "miesiąc"),
        "Wynik": ("gra trwa",),
        "Morale": ("0",),
        "Osady": ("2",),
        "Oddziały": ("0",),
        "Położenie oddziału": ("brak",),
    }
    for label, value_fragments in expected_rows.items():
        matching_rows = [
            texts
            for texts in by_parent.values()
            if any(text.rstrip(":") == label for text in texts)
            and any(
                all(fragment in text for fragment in value_fragments)
                and text.rstrip(":") != label
                for text in texts
            )
        ]
        assert matching_rows, (
            f"{label!r} must have a separate value Label in the same visible "
            f"row container; got status_card_labels={records!r}"
        )
        value_texts = [
            text
            for text in matching_rows[0]
            if text.rstrip(":") != label
        ]
        assert all(
            not text.casefold().startswith(f"{label}:".casefold())
            for text in value_texts
        ), (
            f"{label!r} value cell must not repeat its row key; "
            f"got value_texts={value_texts!r}"
        )

    assert payload["status_card_separators"] >= 2, (
        "status hierarchy must use visible separators between its major groups; "
        f"got {payload['status_card_separators']}"
    )


@pytest.mark.parametrize("token", ["victory", "defeat", "draw"])
def test_scene_bind_probe_finished_party_is_visually_distinct_from_ongoing(
    tmp_path, token
):
    """G90.2b AC3: finished party must stand out without reading the result text.

    Realistic defect: apply_model only changes ResultLabel.text; modulate/font stay
    default for victory/defeat/draw and ongoing alike, so a ended game looks like
    an in-progress one until the player reads the line carefully.
    """
    ongoing = _bind_payload(tmp_path, "ongoing")
    finished = _bind_payload(tmp_path, token)
    assert _result_visual(finished) != _result_visual(ongoing), (
        f"finished token {token!r} must style ResultLabel differently from ongoing; "
        f"got finished={_result_visual(finished)} ongoing={_result_visual(ongoing)}"
    )


def test_scene_bind_probe_uses_result_from_model_not_constant(tmp_path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    # Unknown token still comes from the model (not a hardcoded ongoing),
    # but must render a readable Polish fallback — never the raw English token.
    payload = _bind_payload(tmp_path, "won")
    assert payload["date"] == (
        f"Rok {fixture['calendar']['year']}, miesiąc {fixture['calendar']['month']}"
    )
    assert payload["result"] == MISSING_PLAYER_RESULT_PL
    assert "won" not in payload["result"]
    assert payload["regions"] == len(fixture["map"]["regions"])


def test_scene_bind_probe_lists_only_valid_region_names_when_map_has_junk(tmp_path):
    """Scene shows names from the model filter: junk entries do not blank the list."""
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response_fixture = fixture.copy()
    response_map = fixture["map"].copy()
    response_regions = fixture["map"]["regions"].copy()
    response_regions.extend(["nie-region", {"col": 9}, {"name": ""}])
    response_map["regions"] = response_regions
    response_fixture["map"] = response_map
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": response_fixture}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://tests/scene_bind_probe.gd", str(response_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload["region_names"] == [
        region["name"] for region in fixture["map"]["regions"]
    ]


def test_scene_bind_probe_is_idempotent_for_repeated_model_application(tmp_path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": fixture}), encoding="utf-8"
    )

    single = run_godot_script(
        GAME, "res://tests/scene_bind_probe.gd", str(response_path), timeout=30
    )
    repeated = run_godot_script(
        GAME,
        "res://tests/scene_bind_probe.gd",
        str(response_path),
        "3",
        timeout=30,
    )

    assert repeated.returncode == 0, repeated.stderr
    lines = [line for line in repeated.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, repeated.stdout
    assert "SCRIPT ERROR" not in repeated.stderr, repeated.stderr

    single_lines = [line for line in single.stdout.splitlines() if line.startswith(PREFIX)]
    assert single.returncode == 0, single.stderr
    assert len(single_lines) == 1, single.stdout
    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload == json.loads(single_lines[0][len(PREFIX) :])
    assert payload["regions"] == len(fixture["map"]["regions"])
    assert payload["region_names"] == [
        region["name"] for region in fixture["map"]["regions"]
    ]


@pytest.mark.parametrize("applications", ["0", "nie-liczba"])
def test_scene_bind_probe_rejects_invalid_application_count(tmp_path, applications):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": fixture}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME,
        "res://tests/scene_bind_probe.gd",
        str(response_path),
        applications,
        timeout=30,
    )

    assert result.returncode == 2
    assert not any(line.startswith(PREFIX) for line in result.stdout.splitlines())
