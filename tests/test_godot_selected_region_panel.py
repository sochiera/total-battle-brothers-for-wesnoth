"""G97.1e: strategic panel „Wybrany region” presents snapshot selection in Polish."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from godot_png_assets import assert_asset_credited
from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "SELECTED_REGION_PANEL "

# Public Polish presentation contract (panel title + empty state).
TITLE = "Wybrany region"
EMPTY_STATE = "Nie wybrano regionu"
PANEL_BACKGROUND = "selected_region_panel.png"
PANEL_BACKGROUND_RES = f"res://assets/{PANEL_BACKGROUND}"
EMPTY_ORNAMENT = "selected_region_empty_ornament.png"
EMPTY_ORNAMENT_RES = f"res://assets/{EMPTY_ORNAMENT}"

# Owner / side tokens the panel must use (readable Polish, not bridge ids alone).
OWNER_PLAYER_RE = re.compile(r"gracz|własn", re.IGNORECASE)
OWNER_AI_RE = re.compile(r"\bai\b|wr[oó]g", re.IGNORECASE)
OWNER_NEUTRAL_RE = re.compile(r"neutraln|brak właścic", re.IGNORECASE)
SETTLEMENT_ABSENT_RE = re.compile(r"brak osady|bez osady|osada:\s*brak", re.IGNORECASE)
PARTY_ABSENT_RE = re.compile(r"brak armii|bez armii|armia:\s*brak|brak oddziału", re.IGNORECASE)
DETAIL_ROW_PREFIXES = ("Nazwa:", "Właściciel:", "Osada:", "Armia:")


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


def _assert_distinct_detail_rows(step: dict, *, phase: str) -> None:
    labels = [str(text) for text in (step or {}).get("label_texts") or []]
    matched = [
        text
        for text in labels
        if any(prefix in text for prefix in DETAIL_ROW_PREFIXES)
    ]
    assert len(matched) == len(DETAIL_ROW_PREFIXES), (
        f"{phase}: name, owner, settlement and army must be four distinct "
        f"visible rows, got label_texts={labels!r}"
    )
    assert all(
        sum(prefix in text for prefix in DETAIL_ROW_PREFIXES) == 1
        for text in matched
    ), (
        f"{phase}: a single multiline label is still an undifferentiated text "
        f"wall, got detail rows={matched!r}"
    )
    assert [
        next(prefix for prefix in DETAIL_ROW_PREFIXES if prefix in text)
        for text in matched
    ] == list(DETAIL_ROW_PREFIXES), (
        f"{phase}: detail rows must keep name → owner → settlement → army order, "
        f"got detail rows={matched!r}"
    )
    assert EMPTY_STATE not in labels and EMPTY_STATE not in _text(step), (
        f"{phase}: selected state must hide {EMPTY_STATE!r}, "
        f"got label_texts={labels!r}"
    )


def _assert_empty_detail_rows_hidden(step: dict, *, phase: str) -> None:
    labels = [str(text) for text in (step or {}).get("label_texts") or []]
    visible_details = [
        text
        for text in labels
        if any(text.startswith(prefix) for prefix in DETAIL_ROW_PREFIXES)
    ]
    assert not visible_details, (
        f"{phase}: empty state must hide all detail rows, "
        f"got detail rows={visible_details!r}"
    )


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
    _assert_empty_detail_rows_hidden(empty_step, phase="empty_before")

    player_step = payload.get("after_player") or {}
    _assert_panel_visible(player_step, phase="after_player")
    after_player = _text(player_step)
    _assert_titled(after_player, phase="after_player")
    assert player in after_player, (
        f"player selection must show region name {player!r}, got {after_player!r}"
    )
    _assert_distinct_detail_rows(player_step, phase="after_player")
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
    _assert_distinct_detail_rows(neutral_step, phase="after_neutral")
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
    _assert_distinct_detail_rows(ai_step, phase="after_ai")
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
    _assert_distinct_detail_rows(refresh_step, phase="after_refresh")
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
    _assert_empty_detail_rows_hidden(gone_step, phase="after_gone")


def test_selected_region_panel_uses_credited_textured_frame():
    """G102.1c: the selection readout is framed by its named artwork.

    Realistic defect existing gates miss: all selection text and click/refresh
    behavior can remain correct while SelectedRegionPanel still renders its
    flat, single-color StyleBoxFlat. Observe the resolved runtime theme style
    so an unused PNG on disk cannot satisfy the visual carrier contract.
    """
    assets_dir = GAME / "assets"
    frame_path = assets_dir / PANEL_BACKGROUND
    assert frame_path.is_file(), (
        f"required selected-region panel artwork missing: {frame_path}"
    )
    assert_asset_credited(
        assets_dir / "CREDITS.md",
        PANEL_BACKGROUND,
        source_re=re.compile(r"https?://\S+|PNG/"),
    )

    payload = _load_panel()
    empty_step = payload.get("empty_before") or {}
    assert empty_step.get("carrier") == "SelectedRegionPanel", empty_step
    assert empty_step.get("background_path") == PANEL_BACKGROUND_RES, (
        "SelectedRegionPanel must resolve a StyleBoxTexture backed by "
        f"{PANEL_BACKGROUND_RES}, got {empty_step!r}"
    )


def test_empty_selected_region_panel_has_credited_visual_content():
    """G105.1d: empty selection is more than text on a parchment plate.

    Realistic defect existing gates miss: the panel can keep its textured
    frame and correct Polish message while its body remains visually empty.
    """
    payload = _load_panel()
    empty_step = payload.get("empty_before") or {}
    visual_paths = [
        str(path)
        for path in empty_step.get("visible_visual_paths") or []
        if str(path).startswith("res://assets/")
    ]
    assert EMPTY_ORNAMENT_RES in visual_paths, (
        "empty SelectedRegionPanel must render its visible credited ornament "
        f"inside the parchment carrier, got {empty_step!r}"
    )
    assets_dir = GAME / "assets"
    for resource_path in visual_paths:
        asset_name = Path(resource_path).name
        assert (assets_dir / asset_name).is_file(), resource_path
        assert_asset_credited(
            assets_dir / "CREDITS.md",
            asset_name,
            source_re=re.compile(r"https?://\S+|PNG/"),
        )

    selected_step = payload.get("after_player") or {}
    selected_visual_paths = [
        str(path) for path in selected_step.get("visible_visual_paths") or []
    ]
    assert EMPTY_ORNAMENT_RES not in selected_visual_paths, (
        "empty-state ornament must be hidden after selecting a region, "
        f"got {selected_step!r}"
    )


def _detail_row(step: dict, prefix: str, *, phase: str) -> str:
    """The single visible panel row carrying `prefix` (e.g. „Armia:")."""
    labels = [str(text) for text in (step or {}).get("label_texts") or []]
    matched = [text for text in labels if text.startswith(prefix)]
    assert len(matched) == 1, (
        f"{phase}: expected exactly one {prefix!r} row, got label_texts={labels!r}"
    )
    return matched[0]


def test_selected_region_panel_shows_party_and_garrison_strength():
    """G113.1b: the region panel carries the numbers behind „bić czy nie".

    Realistic defect existing gates miss: task-625 landed
    WorldPresentation.party_strength_text / settlement_strength_text, but
    Main still formats the „Osada:" / „Armia:" rows with its own private
    _settlement_text / _party_text, which drop size, hp and garrison. Every
    existing panel assertion (name, owner, side wording, absence clearing,
    empty state) stays green while both measured runs — a 4-unit army and a
    hero-only army — render identically as „Armia: własny (gracz)". The player
    still picks fights by icon.
    """
    payload = _load_panel()
    strengths = payload.get("strengths") or {}

    player_army = _detail_row(payload.get("after_player") or {}, "Armia:",
                              phase="after_player")
    size = strengths["player_party_size"]
    hp = strengths["player_party_hp"]
    assert re.search(rf"(?<!\d){size}(?!\d)", player_army), (
        f"own party row must show its unit count {size!r}, got {player_army!r}"
    )
    assert re.search(rf"(?<!\d){hp}(?!\d)", player_army), (
        f"own party row must show its hit points {hp!r}, got {player_army!r}"
    )

    player_settlement = _detail_row(payload.get("after_player") or {}, "Osada:",
                                    phase="after_player")
    player_garrison = strengths["settlement_player_garrison"]
    assert re.search(rf"(?<!\d){player_garrison}(?!\d)", player_settlement), (
        f"own settlement row must show garrison {player_garrison!r} — a zero "
        f"that must not vanish as a falsy value, got {player_settlement!r}"
    )

    # Enemy side: both an enemy party and an enemy settlement garrison.
    ai_step = payload.get("after_ai") or {}
    ai_army = _detail_row(ai_step, "Armia:", phase="after_ai")
    ai_size = strengths["ai_party_size"]
    ai_hp = strengths["ai_party_hp"]
    assert re.search(rf"(?<!\d){ai_size}(?!\d)", ai_army), (
        f"enemy party row must show its unit count {ai_size!r}, got {ai_army!r}"
    )
    assert re.search(rf"(?<!\d){ai_hp}(?!\d)", ai_army), (
        f"enemy party row must show its hit points {ai_hp!r}, got {ai_army!r}"
    )

    ai_settlement = _detail_row(ai_step, "Osada:", phase="after_ai")
    ai_garrison = strengths["settlement_ai_garrison"]
    assert re.search(rf"(?<!\d){ai_garrison}(?!\d)", ai_settlement), (
        f"enemy settlement row must show garrison {ai_garrison!r}, "
        f"got {ai_settlement!r}"
    )


def test_selected_region_panel_strength_refreshes_without_reselecting():
    """G113.1b: numbers follow the snapshot, not the click.

    Realistic defect existing gates miss: a panel can read strength once on
    selection and cache it, so after an order or a turn the still-selected
    region keeps yesterday's garrison. Existing refresh coverage only watches
    the settlement *name* change, which a cached-numbers panel survives.
    """
    payload = _load_panel()
    strengths = payload.get("strengths") or {}
    before = strengths["settlement_ai_garrison"]
    after = strengths["settlement_ai_garrison_refreshed"]
    assert before != after, "fixture must move the garrison to prove refresh"

    refreshed = _detail_row(payload.get("after_refresh") or {}, "Osada:",
                            phase="after_refresh")
    assert re.search(rf"(?<!\d){after}(?!\d)", refreshed), (
        f"refresh must show the new garrison {after!r} for the still-selected "
        f"region, got {refreshed!r}"
    )
    assert not re.search(rf"(?<!\d){before}(?!\d)", refreshed), (
        f"stale garrison {before!r} must not survive the refresh, "
        f"got {refreshed!r}"
    )


def test_selected_region_panel_invents_no_strength_without_party_or_settlement():
    """G113.1b: a bare region shows placeholders, never a made-up 0.

    Realistic defect existing gates miss: wiring strength into the rows
    invites a `int(party.get("size"))` default that renders „0 jednostek" for
    a region with no army at all — numbers taken from thin air, which is
    exactly what makes the readout untrustworthy.
    """
    payload = _load_panel()
    neutral_step = payload.get("after_neutral") or {}

    army = _detail_row(neutral_step, "Armia:", phase="after_neutral")
    assert PARTY_ABSENT_RE.search(army), (
        f"bare region must keep the army placeholder, got {army!r}"
    )
    assert not re.search(r"\d", army), (
        f"bare region must not show any army number, got {army!r}"
    )

    settlement = _detail_row(neutral_step, "Osada:", phase="after_neutral")
    assert SETTLEMENT_ABSENT_RE.search(settlement), (
        f"bare region must keep the settlement placeholder, got {settlement!r}"
    )
    assert not re.search(r"\d", settlement), (
        f"bare region must not show any garrison number, got {settlement!r}"
    )


def test_reinforce_button_refreshes_selected_region_strength_without_manual_refresh():
    """G112.1d crit-3: clicking reinforce redraws the selected panel.

    Realistic defect existing gates miss: Main can render snapshot numbers and
    can dispatch other order buttons, yet a reinforce handler can omit the
    post-order model application or leave the selected-region panel cached.
    """
    payload = _load_panel()
    reinforce = payload.get("reinforce") or {}
    assert reinforce.get("button_found") is True, payload
    assert reinforce.get("pressed") is True, reinforce
    assert reinforce.get("orders") == ["reinforce"], reinforce

    before = reinforce.get("before") or {}
    after = reinforce.get("after") or {}
    before_army = _detail_row(before, "Armia:", phase="reinforce_before")
    after_army = _detail_row(after, "Armia:", phase="reinforce_after")
    before_settlement = _detail_row(before, "Osada:", phase="reinforce_before")
    after_settlement = _detail_row(after, "Osada:", phase="reinforce_after")

    assert re.search(r"(?<!\d)5(?!\d)", before_army), before_army
    assert re.search(r"(?<!\d)5(?!\d)", before_settlement), before_settlement
    assert re.search(r"(?<!\d)10(?!\d)", after_army), after_army
    assert re.search(r"(?<!\d)0(?!\d)", after_settlement), after_settlement
    assert not re.search(r"(?<!\d)5(?!\d)", after_army), after_army
    assert not re.search(r"(?<!\d)5(?!\d)", after_settlement), after_settlement


def test_ineffective_reinforce_shows_a_reason_in_the_real_ui():
    """G112.1d crit-2: changed:false must explain an empty garrison.

    Realistic defect existing gates miss: the live button can send an
    ineffective order and leave the panel rendered with a valid party/garrison
    snapshot, while the status still reports only a generic no-op. The fixture
    deliberately has a party of five and a zero garrison, so the client can
    identify the reason without guessing at the core result.
    """
    payload = _load_panel()
    reinforce = payload.get("reinforce_ineffective") or {}
    assert reinforce.get("button_found") is True, payload
    assert reinforce.get("pressed") is True, reinforce
    assert reinforce.get("orders") == ["reinforce"], reinforce

    status = reinforce.get("status") or {}
    status_text = str(status.get("text") or "")
    assert status.get("visible") is True, status
    assert status_text, "an ineffective reinforce must not leave the status empty"
    assert "garnizon" in status_text.lower(), status_text
    assert status_text != "Wzmocnienie nie zmieniło stanu oddziału.", status_text

    after = reinforce.get("after") or {}
    army = _detail_row(after, "Armia:", phase="reinforce_ineffective_after")
    settlement = _detail_row(after, "Osada:", phase="reinforce_ineffective_after")
    assert re.search(r"(?<!\d)5(?!\d)", army), army
    assert re.search(r"(?<!\d)0(?!\d)", settlement), settlement


def test_ineffective_reinforce_explains_a_foreign_settlement():
    """G112.1d review regression: foreign ownership is a distinct cause.

    Realistic defect existing gates miss: a failed reinforce at a foreign
    settlement with zero garrison is indistinguishable from an own settlement
    with no garrison unless the client compares the party and settlement
    owners from the snapshot before checking the garrison count.
    """
    payload = _load_panel()
    foreign = payload.get("reinforce_foreign_settlement") or {}
    assert foreign.get("button_found") is True, foreign
    assert foreign.get("pressed") is True, foreign
    assert foreign.get("orders") == ["reinforce"], foreign
    status = foreign.get("status") or {}
    assert status.get("visible") is True, status
    assert status.get("text") == "Oddział stoi w obcej osadzie.", status


def test_reinforce_game_over_status_precedes_contextual_cause():
    """G112.1d review regression: game-over status keeps its priority.

    Realistic defect existing gates miss: changed:false with game_over:true
    and a zero-garrison snapshot can be replaced by the contextual
    reinforcement explanation, hiding the existing terminal-game contract.
    """
    payload = _load_panel()
    game_over = payload.get("reinforce_game_over") or {}
    assert game_over.get("orders") == ["reinforce"], game_over
    status = game_over.get("status") or {}
    assert status.get("visible") is True, status
    assert status.get("text") == "Partia jest zakończona.", status


def test_reinforce_status_uses_actual_party_position():
    """G112.1d review regression: contextual status follows actual party.

    Realistic defect existing gates miss: selecting another settlement with a
    zero garrison can make a failed reinforce claim the wrong cause.
    """
    payload = _load_panel()

    mismatch = payload.get("reinforce_selection_mismatch") or {}
    assert mismatch.get("button_found") is True, mismatch
    assert mismatch.get("orders") == ["reinforce"], mismatch
    assert mismatch.get("actual_party_region") != mismatch.get("selected_region"), mismatch
    mismatch_status = mismatch.get("status") or {}
    assert mismatch_status.get("visible") is True, mismatch_status
    assert mismatch_status.get("text") == "Wzmocnienie nie zmieniło stanu oddziału.", (
        "reinforce status must use the actual party settlement, not the selected "
        f"region's garrison, got {mismatch_status!r}"
    )


def test_reinforce_exhausted_status_has_priority_over_garrison_context():
    """G112.1d review regression: exhausted action reason wins.

    Realistic defect existing gates miss: a second failed click can hide the
    bridge's monthly-action-exhausted reason after a successful reinforce.
    """
    payload = _load_panel()
    exhausted = payload.get("reinforce_exhausted") or {}
    assert exhausted.get("orders") == ["reinforce"], exhausted
    exhausted_status = exhausted.get("status") or {}
    assert exhausted_status.get("visible") is True, exhausted_status
    assert exhausted_status.get("text") == "Oddział już działał w tym miesiącu — zakończ turę.", (
        "monthly_action_exhausted must take priority over the selected party's "
        f"zero-garrison context, got {exhausted_status!r}"
    )


@pytest.mark.parametrize(
    ("case_name", "expected_status"),
    [
        ("reinforce_no_party", "Brak oddziału do wzmocnienia."),
        ("reinforce_no_settlement", "Oddział nie stoi w osadzie."),
    ],
)
def test_ineffective_reinforce_explains_missing_party_or_settlement(
    case_name: str, expected_status: str
):
    """G112.1d review regression: snapshot context explains both no-op causes.

    Realistic defect existing gates miss: the generic contextual status handles
    a zero garrison, but falls through to the generic no-op when the snapshot
    has no player party or has a party outside any settlement.
    """
    payload = _load_panel()

    case = payload.get(case_name) or {}
    assert case.get("button_found") is True, case
    assert case.get("pressed") is True, case
    assert case.get("orders") == ["reinforce"], case
    status = case.get("status") or {}
    assert status.get("visible") is True, status
    assert status.get("text") == expected_status, (
        f"{case_name} must explain the snapshot cause in Polish, got {status!r}"
    )


def test_ineffective_reinforce_explains_party_capacity_limit():
    """G112.1d review regression: capacity no-op gets its own explanation.

    Realistic defect existing gates miss: the client can explain an empty
    garrison and missing context, yet still show the generic no-op when an
    eight-unit party tries to absorb a five-unit garrison and would exceed the
    core's maximum party size of twelve.
    """
    payload = _load_panel()

    capacity = payload.get("reinforce_capacity_limit") or {}
    assert capacity.get("button_found") is True, capacity
    assert capacity.get("pressed") is True, capacity
    assert capacity.get("orders") == ["reinforce"], capacity

    status = capacity.get("status") or {}
    status_text = str(status.get("text") or "")
    assert status.get("visible") is True, status
    assert status_text, "a capacity-limited reinforce must not leave the status empty"
    assert status_text == (
        "Wzmocnienie przekroczyłoby limit liczebności oddziału: 12 jednostek."
    ), status_text
