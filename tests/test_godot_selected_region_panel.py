"""G97.1e: strategic panel „Wybrany region” presents snapshot selection in Polish."""

from __future__ import annotations

import json
import re
from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "SELECTED_REGION_PANEL "

# Public Polish presentation contract (panel title + empty state).
TITLE = "Wybrany region"
EMPTY_STATE = "Nie wybrano regionu"

# Owner / side tokens the panel must use (readable Polish, not bridge ids alone).
OWNER_PLAYER_RE = re.compile(r"gracz|własn", re.IGNORECASE)
OWNER_AI_RE = re.compile(r"\bai\b|wr[oó]g", re.IGNORECASE)
OWNER_NEUTRAL_RE = re.compile(r"neutraln|brak właścic", re.IGNORECASE)
SETTLEMENT_ABSENT_RE = re.compile(r"brak osady|bez osady|osada:\s*brak", re.IGNORECASE)
PARTY_ABSENT_RE = re.compile(r"brak armii|bez armii|armia:\s*brak|brak oddziału", re.IGNORECASE)


def _load_panel() -> dict:
    result = run_godot_script(
        GAME, "res://tests/selected_region_panel_probe.gd", timeout=45
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _text(step: dict) -> str:
    return str((step or {}).get("text") or "")


def _assert_panel_visible(step: dict, *, phase: str) -> None:
    assert (step or {}).get("found") is True, f"{phase}: panel missing, got {step!r}"
    assert (step or {}).get("visible") is True, (
        f"{phase}: panel must be visible in the tree, got {step!r}"
    )


def _assert_titled(text: str, *, phase: str) -> None:
    assert TITLE in text, f"{phase}: panel must keep title {TITLE!r}, got {text!r}"


def test_selected_region_panel_shows_polish_state_from_snapshot():
    """Click fills „Wybrany region”; bare/refresh/gone never leave stale fields.

    Realistic defect existing gates miss: MapView already emits region_selected
    and draws a durable frame (G97.1c/d), but Main never presents a named Polish
    panel of the selected region's name / owner / settlement / party from the
    current SnapshotModel.regions. Selection and hover stay green while the
    player has no side-panel readout, and a half-wired panel can keep the
    previous settlement or army after a bare or vanished target.
    """
    payload = _load_panel()
    assert payload.get("available") is True, payload
    assert payload.get("panel_found") is True, (
        "Main strategic composition must expose a „Wybrany region” panel "
        f"(SelectedRegionLabel, SelectedRegionPanel, or titled Label), got {payload!r}"
    )

    regions = payload.get("regions") or {}
    player = regions["player"]
    neutral = regions["neutral"]
    ai = regions["ai"]
    settlement_player = regions["settlement_player"]
    settlement_ai = regions["settlement_ai"]
    settlement_ai_refreshed = regions["settlement_ai_refreshed"]

    empty_step = payload.get("empty_before") or {}
    _assert_panel_visible(empty_step, phase="empty_before")
    empty = _text(empty_step)
    _assert_titled(empty, phase="empty_before")
    assert EMPTY_STATE in empty, (
        f"before selection panel must show exact empty Polish {EMPTY_STATE!r}, "
        f"got {empty!r}"
    )
    assert player not in empty and ai not in empty, (
        f"empty state must not show a region name, got {empty!r}"
    )

    player_step = payload.get("after_player") or {}
    _assert_panel_visible(player_step, phase="after_player")
    after_player = _text(player_step)
    _assert_titled(after_player, phase="after_player")
    assert player in after_player, (
        f"player selection must show region name {player!r}, got {after_player!r}"
    )
    assert OWNER_PLAYER_RE.search(after_player), (
        f"player-owned region must use Polish owner wording (gracz/własny), "
        f"got {after_player!r}"
    )
    assert settlement_player in after_player or re.search(
        r"keep|twierdz|zamek", after_player, re.IGNORECASE
    ), (
        f"player selection must present settlement name or type, got {after_player!r}"
    )
    # Army side for player party — same player wording is enough if name+owner
    # already match; require explicit party absence not present.
    assert not PARTY_ABSENT_RE.search(after_player), (
        f"player region has a party — panel must not claim army absent, "
        f"got {after_player!r}"
    )
    # One smoke check that a click path reached MapView → Main; full emission
    # policy belongs to G97.1c, not this panel gate.
    assert player in (payload.get("emitted_after_player") or []), (
        f"player click must reach region_selected so Main can bind the panel, "
        f"got {payload.get('emitted_after_player')!r}"
    )

    neutral_step = payload.get("after_neutral") or {}
    _assert_panel_visible(neutral_step, phase="after_neutral")
    after_neutral = _text(neutral_step)
    _assert_titled(after_neutral, phase="after_neutral")
    assert neutral in after_neutral, (
        f"neutral selection must show {neutral!r}, got {after_neutral!r}"
    )
    assert OWNER_NEUTRAL_RE.search(after_neutral), (
        f"null owner must read as neutral/brak właściciela in Polish, "
        f"got {after_neutral!r}"
    )
    assert SETTLEMENT_ABSENT_RE.search(after_neutral), (
        f"null settlement must clear to brak osady (no stale {settlement_player!r}), "
        f"got {after_neutral!r}"
    )
    assert settlement_player not in after_neutral, (
        f"switching to bare region must not keep previous settlement "
        f"{settlement_player!r}, got {after_neutral!r}"
    )
    assert PARTY_ABSENT_RE.search(after_neutral), (
        f"null party must clear to brak armii (no stale player army), "
        f"got {after_neutral!r}"
    )

    ai_step = payload.get("after_ai") or {}
    _assert_panel_visible(ai_step, phase="after_ai")
    after_ai = _text(ai_step)
    _assert_titled(after_ai, phase="after_ai")
    assert ai in after_ai, f"AI selection must show {ai!r}, got {after_ai!r}"
    assert OWNER_AI_RE.search(after_ai), (
        f"AI-owned region must use Polish/AI owner wording, got {after_ai!r}"
    )
    assert settlement_ai in after_ai or re.search(
        r"outpost|posterunek|wież", after_ai, re.IGNORECASE
    ), (
        f"AI selection must present settlement name or type, got {after_ai!r}"
    )
    assert not PARTY_ABSENT_RE.search(after_ai), (
        f"AI region has a party — panel must not claim army absent, got {after_ai!r}"
    )

    refresh_step = payload.get("after_refresh") or {}
    _assert_panel_visible(refresh_step, phase="after_refresh")
    after_refresh = _text(refresh_step)
    assert ai in after_refresh, (
        f"refresh must keep presenting selected {ai!r}, got {after_refresh!r}"
    )
    assert settlement_ai_refreshed in after_refresh or (
        settlement_ai not in after_refresh
        and re.search(r"keep|twierdz|zamek", after_refresh, re.IGNORECASE)
    ), (
        f"snapshot refresh must update settlement "
        f"({settlement_ai!r} → {settlement_ai_refreshed!r}), got {after_refresh!r}"
    )
    assert settlement_ai not in after_refresh or settlement_ai_refreshed in after_refresh, (
        f"stale settlement {settlement_ai!r} must not remain after refresh, "
        f"got {after_refresh!r}"
    )
    assert PARTY_ABSENT_RE.search(after_refresh), (
        f"refresh clears AI party — panel must show brak armii, got {after_refresh!r}"
    )

    gone_step = payload.get("after_gone") or {}
    _assert_panel_visible(gone_step, phase="after_gone")
    after_gone = _text(gone_step)
    _assert_titled(after_gone, phase="after_gone")
    assert EMPTY_STATE in after_gone, (
        f"when selected region vanishes from snapshot, panel must return to "
        f"{EMPTY_STATE!r}, got {after_gone!r}"
    )
    assert ai not in after_gone, (
        f"vanished selection must not keep region name {ai!r}, got {after_gone!r}"
    )
    assert settlement_ai_refreshed not in after_gone, (
        f"vanished selection must not keep settlement, got {after_gone!r}"
    )
