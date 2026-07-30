"""Field order buttons: distinct credited icons with Polish labels (G95.1c)."""

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
PROBE = "res://tests/field_order_icons_probe.gd"
PREFIX = "FIELD_ORDER_ICONS "

# Public presentation paths for field order icons (G95.1c).
# Names mirror icon_next_turn.png / settlement icons and the two field commands.
ORDERS: tuple[dict[str, str], ...] = (
    {
        "name": "MarchButton",
        "text": "Wyrusz w pole",
        "icon_rel": "assets/icon_march.png",
    },
    {
        "name": "AssaultButton",
        "text": "Szturmuj osadę",
        "icon_rel": "assets/icon_assault.png",
    },
)
# Icon must be large enough to read beside the label on a 40px-tall control.
MIN_ICON_EDGE = 16

# Whole order bar (next-turn + settlement + field). Field icons must not reuse
# any existing bar graphic as a renamed placeholder.
BAR_ICON_RELS: tuple[str, ...] = (
    "assets/icon_next_turn.png",
    "assets/icon_develop.png",
    "assets/icon_recruit.png",
    "assets/icon_muster.png",
    "assets/icon_march.png",
    "assets/icon_assault.png",
)


def _run_probe(*script_args: str) -> subprocess.CompletedProcess[str]:
    return run_godot_script(GAME, PROBE, *script_args, timeout=30)


def _payload_from(result: subprocess.CompletedProcess[str]) -> dict:
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_field_order_buttons_show_distinct_credited_icons_with_polish_labels():
    """March / Assault must each show a distinct Texture2D icon.

    Realistic defect existing gates miss: MarchButton and AssaultButton remain
    plain ``Button`` nodes with only Polish ``text``. Existing probes
    (march/assault unbound + binding, layout, e2e) and settlement/next-turn
    icon gates assert names, labels, connections, geometry, and the *other*
    order icons — so a purely textual field pair stays green while G95.1c
    requires two mutually distinct, credited graphics under public
    ``res://assets/icon_{march,assault}.png`` that do not replace the Polish
    labels and are not copies of each other or of any other order-bar icon
    (next-turn / develop / recruit / muster) used as a renamed placeholder.
    """
    digests: dict[str, str] = {}
    for rel in BAR_ICON_RELS:
        icon_on_disk = GAME / rel
        assert icon_on_disk.is_file(), (
            f"committed order-bar icon missing on disk: {icon_on_disk}"
        )
        digests[rel] = hashlib.sha256(icon_on_disk.read_bytes()).hexdigest()
    assert len(set(digests.values())) == len(digests), (
        "order-bar icon files must be unique bytes across the whole bar "
        f"(field ≠ settlement/next-turn placeholders), digests={digests!r}"
    )
    for order in ORDERS:
        assert_asset_credited(CREDITS, Path(order["icon_rel"]).name)

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
        "field order icons must be pairwise distinct "
        f"(march ≠ assault), got {icon_paths!r}"
    )
