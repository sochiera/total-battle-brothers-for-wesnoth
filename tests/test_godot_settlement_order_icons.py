"""Settlement order buttons: distinct credited icons with Polish labels (G95.1b)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from godot_png_assets import assert_asset_credited
from godot_runner import run_godot_script
from test_godot_assets import _import_game_assets

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
CREDITS = GAME / "assets" / "CREDITS.md"
PROBE = "res://tests/settlement_order_icons_probe.gd"
PREFIX = "SETTLEMENT_ORDER_ICONS "

# Public presentation paths for settlement order icons (G95.1b).
# Names mirror icon_next_turn.png and the three Polish settlement commands.
ORDERS: tuple[dict[str, str], ...] = (
    {
        "name": "DevelopButton",
        "text": "Rozwiń osadę",
        "icon_rel": "assets/icon_develop.png",
    },
    {
        "name": "RecruitButton",
        "text": "Rekrutuj jednostkę",
        "icon_rel": "assets/icon_recruit.png",
    },
    {
        "name": "MusterButton",
        "text": "Zbierz oddział",
        "icon_rel": "assets/icon_muster.png",
    },
)
# Icon must be large enough to read beside the label on a 40px-tall control.
MIN_ICON_EDGE = 16


def _run_probe(*script_args: str) -> subprocess.CompletedProcess[str]:
    return run_godot_script(GAME, PROBE, *script_args, timeout=30)


def _payload_from(result: subprocess.CompletedProcess[str]) -> dict:
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_settlement_order_buttons_show_distinct_credited_icons_with_polish_labels():
    """Develop / Recruit / Muster must each show a distinct Texture2D icon.

    Realistic defect existing gates miss: the three settlement order buttons
    remain plain ``Button`` nodes with only Polish ``text``. Existing probes
    (develop/recruit/muster unbound + binding) and layout/e2e gates assert
    names, labels, connections, and geometry — so a purely textual order bar
    stays green while G95.1b requires three mutually distinct, credited
    graphics under public ``res://assets/icon_{develop,recruit,muster}.png``
    paths that do not replace the Polish labels.
    """
    digests: list[str] = []
    for order in ORDERS:
        icon_on_disk = GAME / order["icon_rel"]
        assert icon_on_disk.is_file(), (
            f"committed settlement-order icon missing on disk: {icon_on_disk}"
        )
        digests.append(hashlib.sha256(icon_on_disk.read_bytes()).hexdigest())
        assert_asset_credited(CREDITS, Path(order["icon_rel"]).name)
    assert len(set(digests)) == len(digests), (
        "settlement order icon files must be pairwise distinct bytes "
        f"(not three copies of one placeholder), digests={digests!r}"
    )

    imported = _import_game_assets()
    assert imported.returncode == 0, (
        f"godot --import failed rc={imported.returncode} "
        f"stderr={imported.stderr!r} stdout={imported.stdout!r}"
    )

    result = _run_probe()
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    payload = _payload_from(result)
    orders = payload.get("orders")
    assert isinstance(orders, list) and len(orders) == len(ORDERS), payload
    by_name = {row["name"]: row for row in orders}

    icon_paths: list[str] = []
    for expected in ORDERS:
        row = by_name.get(expected["name"])
        assert row is not None, f"probe omitted {expected['name']}: {payload!r}"
        assert row["text"] == expected["text"], (
            f"Polish label must remain on {expected['name']}; icon is presentation only"
        )
        icon_res = f"res://{expected['icon_rel']}"
        assert row.get("icon_path") == icon_res, (
            f"{expected['name']} icon must use public path {icon_res}, "
            f"got {row.get('icon_path')!r}"
        )
        assert int(row.get("icon_w") or 0) >= MIN_ICON_EDGE, row
        assert int(row.get("icon_h") or 0) >= MIN_ICON_EDGE, row
        icon_paths.append(row["icon_path"])

    assert len(set(icon_paths)) == len(icon_paths), (
        "settlement order icons must be pairwise distinct "
        f"(develop ≠ recruit ≠ muster), got {icon_paths!r}"
    )
