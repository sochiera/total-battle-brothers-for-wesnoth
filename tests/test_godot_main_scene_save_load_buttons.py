"""G86.2a/G107.1b: main scene exposes party controls with Polish labels.

G95.1d/G107.1b: the party-action buttons show distinct credited icons.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from godot_png_assets import assert_asset_credited
from godot_runner import import_game_assets, run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
CREDITS = GAME / "assets" / "CREDITS.md"
PROBE = "res://tests/save_load_buttons_probe.gd"
PREFIX = "SAVE_LOAD_BUTTONS "

# Public presentation paths for save/load icons (G95.1d).
# Names mirror icon_next_turn.png / order-bar icons and the two Polish actions.
BUTTONS: tuple[dict[str, str], ...] = (
    {
        "key": "save",
        "name": "SaveGameButton",
        "text": "Zapisz partię",
        "icon_rel": "assets/icon_save.png",
        "author": "Delapouite",
    },
    {
        "key": "load",
        "name": "LoadGameButton",
        "text": "Wczytaj partię",
        "icon_rel": "assets/icon_load.png",
        "author": "Delapouite",
    },
    {
        "key": "new_game",
        "name": "NewGameButton",
        "text": "Nowa partia",
        "icon_rel": "assets/icon_new_game.png",
        "author": "Lorc",
    },
)
# Pin minimum source texture edge (pixels), not on-button rendered size.
MIN_ICON_EDGE = 16

# Order bar + save/load pair. Save/load icons must not reuse any existing
# bar graphic as a renamed placeholder, and must differ from each other.
CONTROL_ICON_RELS: tuple[str, ...] = (
    "assets/icon_next_turn.png",
    "assets/icon_develop.png",
    "assets/icon_recruit.png",
    "assets/icon_muster.png",
    "assets/icon_march.png",
    "assets/icon_assault.png",
    "assets/icon_save.png",
    "assets/icon_load.png",
    "assets/icon_new_game.png",
)


def _run_probe(*script_args: str) -> subprocess.CompletedProcess[str]:
    return run_godot_script(GAME, PROBE, *script_args, timeout=30)


def _payload_from(result: subprocess.CompletedProcess[str]) -> dict:
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_main_scene_exposes_party_controls():
    """Player-facing party controls must exist, be labeled and enabled.

    Realistic defect this catches: main.tscn still has no %NewGameButton, so
    the player has no visible entry point for starting a new party. Existing
    scene probes pin the old order/save/load control set and do not require
    %NewGameButton or its Polish label.

    Binding, status text and round-trip live in
    test_godot_main_scene_save_load_binding (G86.2b). This gate only pins
    presence/labels; pressed_connections may be 0 or more depending on session
    autostart. Visibility of the flag `visible` is asserted here. Non-zero
    laid-out size and pairwise-disjoint rects (K83) are pinned by
    test_godot_main_scene_layout.
    """
    result = _run_probe()

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    payload = _payload_from(result)
    for expected in BUTTONS:
        row = payload.get(expected["key"])
        assert isinstance(row, dict), f"probe omitted {expected['key']}: {payload!r}"
        assert row.get("name") == expected["name"], row
        assert row.get("text") == expected["text"], row
        assert row.get("unique_name_in_owner") is True, row
        assert row.get("disabled") is False, row
        assert row.get("visible") is True, row


def test_party_action_buttons_show_distinct_credited_icons_with_polish_labels():
    """Save / Load / New Game each show a distinct Texture2D icon.

    Realistic defect existing gates miss: a party-action button remains a
    plain ``Button`` with only Polish ``text``. Existing probes (presence,
    binding, layout, order-icon gates) pin names, labels, connections,
    geometry, and *older order-bar* icons — so a purely textual control stays
    green while this gate requires distinct, credited graphics under the
    public ``res://assets/`` paths that keep the Polish labels and are not
    renamed copies of another control-bar icon.
    """
    digests: dict[str, str] = {}
    for rel in CONTROL_ICON_RELS:
        icon_on_disk = GAME / rel
        assert icon_on_disk.is_file(), (
            f"committed control-bar icon missing on disk: {icon_on_disk}"
        )
        digests[rel] = hashlib.sha256(icon_on_disk.read_bytes()).hexdigest()
    assert len(set(digests.values())) == len(digests), (
        "control-bar icon files must be unique bytes across the whole bar "
        f"(save/load ≠ order-bar placeholders), digests={digests!r}"
    )
    for button in BUTTONS:
        assert_asset_credited(CREDITS, Path(button["icon_rel"]).name)
        credit_row = next(
            line
            for line in CREDITS.read_text(encoding="utf-8").splitlines()
            if Path(button["icon_rel"]).name in line
        )
        assert f"| {button['author']} |" in credit_row, credit_row

    imported = import_game_assets(GAME)
    assert imported.returncode == 0, (
        f"godot --import failed rc={imported.returncode} "
        f"stderr={imported.stderr!r} stdout={imported.stdout!r}"
    )

    result = _run_probe()
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    payload = _payload_from(result)

    icon_paths: list[str] = []
    for expected in BUTTONS:
        row = payload.get(expected["key"])
        assert isinstance(row, dict), f"probe omitted {expected['key']}: {payload!r}"
        assert row.get("name") == expected["name"], row
        assert row.get("text") == expected["text"], (
            f"Polish label must remain on {expected['name']}; icon is presentation only"
        )
        assert row.get("unique_name_in_owner") is True, row
        icon_res = f"res://{expected['icon_rel']}"
        assert row.get("icon_path") == icon_res, (
            f"{expected['name']} icon must use public path {icon_res}, "
            f"got {row.get('icon_path')!r}"
        )
        assert int(row.get("icon_w") or 0) >= MIN_ICON_EDGE, row
        assert int(row.get("icon_h") or 0) >= MIN_ICON_EDGE, row
        icon_paths.append(row["icon_path"])

    assert len(set(icon_paths)) == len(icon_paths), (
        "save/load icons must be pairwise distinct "
        f"(save ≠ load), got {icon_paths!r}"
    )
