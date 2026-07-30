"""G87.1a: committed CC0/CC-BY assets under game/assets/ load as Texture2D.

Public path contract for later MapView / BattleView work (task-486, G87.1c).
Headless Godot needs ``godot --import`` before ``load("res://assets/…")`` returns
a texture; ``game/.godot/`` must stay out of git so the tree stays clean.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from godot_png_assets import LICENSE_RE
from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/asset_load_probe.gd"
PREFIX = "ASSET_LOAD "

# Paths relative to game/; also the public res://assets/… contract.
REQUIRED_ASSETS: tuple[str, ...] = (
    "assets/map_ground_grass.png",
    "assets/map_ground_earth.png",
    "assets/map_ground_stone.png",
    "assets/settlement.png",
    "assets/party_player.png",
    "assets/terrain_plains.png",
    "assets/terrain_forest.png",
    "assets/terrain_hills.png",
    "assets/side_attacker.png",
    "assets/side_defender.png",
    # G94.1d: strategic screen panel background (task-539).
    "assets/strategic_map_background.png",
)

# Back-compat alias for callers that still import the private name.
_LICENSE_RE = LICENSE_RE


def _res_paths(rel_paths: tuple[str, ...] | list[str]) -> list[str]:
    return [f"res://{rel}" for rel in rel_paths]


def _import_game_assets() -> subprocess.CompletedProcess[str]:
    """Generate Godot import cache so PNG resources become Texture2D."""
    return subprocess.run(
        ["godot", "--headless", "--path", str(GAME), "--import"],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def _run_load_probe(*res_paths: str) -> subprocess.CompletedProcess[str]:
    return run_godot_script(GAME, PROBE, *res_paths, timeout=60)


def _probe_payload(result: subprocess.CompletedProcess[str]) -> list[dict]:
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, (
        f"expected one {PREFIX!r} line, got {result.stdout!r} stderr={result.stderr!r}"
    )
    payload = json.loads(lines[0][len(PREFIX) :])
    assert isinstance(payload, list), payload
    return payload


def test_required_assets_load_as_texture2d_after_godot_import():
    """Each declared asset must exist on disk and load as Texture2D after import.

    Realistic defect this catches: the client still has no committed graphics (or
    only raw PNGs without running ``godot --import``), so ``load("res://assets/…")``
    returns null. Existing MapView/BattleView gates only assert ColorRect geometry
    and stay green while the asset toolchain is missing.
    """
    missing = [rel for rel in REQUIRED_ASSETS if not (GAME / rel).is_file()]
    assert missing == [], (
        "committed graphics missing under game/: " + ", ".join(missing)
    )

    imported = _import_game_assets()
    assert imported.returncode == 0, (
        f"godot --import failed rc={imported.returncode} "
        f"stderr={imported.stderr!r} stdout={imported.stdout!r}"
    )

    result = _run_load_probe(*_res_paths(REQUIRED_ASSETS))
    assert result.returncode == 0, (
        f"asset load probe failed rc={result.returncode} "
        f"stderr={result.stderr!r} stdout={result.stdout!r}"
    )
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = _probe_payload(result)
    by_path = {row["path"]: row for row in payload}
    for res_path in _res_paths(REQUIRED_ASSETS):
        row = by_path.get(res_path)
        assert row is not None, f"probe omitted {res_path}: {payload!r}"
        assert row["ok"] is True, (
            f"{res_path} must load as Texture2D, got class={row.get('class')!r}"
        )


def test_missing_asset_path_makes_the_load_gate_red():
    """Same probe must fail for a path that is not a loadable Texture2D.

    Realistic defect: a green-only probe that always exits 0 after printing, so
    a typo or deleted file never fails the gate.
    """
    # Import is optional here; a missing path fails regardless of cache state.
    result = _run_load_probe("res://assets/__missing_not_in_pack.png")
    assert result.returncode != 0, (
        "probe must exit non-zero for a non-existent asset path; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    if PREFIX in result.stdout:
        payload = _probe_payload(result)
        assert payload and payload[0]["ok"] is False


def test_game_godot_import_cache_is_gitignored():
    """``game/.godot/`` must be ignored so import artifacts never enter git.

    Realistic defect: first ``godot --import`` creates ``game/.godot/`` and, with
    no ignore rule, pollutes ``git status`` after every headless gate run.
    """
    relative = "game/.godot/"
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--", relative],
        cwd=ROOT,
    )
    assert result.returncode == 0, (
        f"{relative} must be gitignored so asset import does not dirty the tree"
    )


def test_assets_credits_documents_each_file_with_cc0_or_cc_by():
    """``game/assets/CREDITS.md`` must attribute every required asset with license.

    Realistic defect: binary PNGs land in the tree without source/author/license,
    so a non-CC0 pack cannot be audited before MapView starts consuming paths.
    """
    credits = GAME / "assets" / "CREDITS.md"
    assert credits.is_file(), "game/assets/CREDITS.md is required for attribution"
    text = credits.read_text(encoding="utf-8")
    assert _LICENSE_RE.search(text), (
        "CREDITS.md must state a CC0 or CC-BY license for the pack"
    )
    for rel in REQUIRED_ASSETS:
        name = Path(rel).name
        assert name in text, f"CREDITS.md must mention asset file {name}"


# Battle-side silhouettes (G87.1c-1b / task-489): public res:// paths stay, content changes.
SIDE_SILHOUETTE_ASSETS: tuple[str, ...] = (
    "assets/side_attacker.png",
    "assets/side_defender.png",
)
TERRAIN_PLAINS_ASSET = "assets/terrain_plains.png"
# Source path inside Kenney RTS Pack: Medieval (Unit/ piechur, not Hexagon buildings).
_SIDE_SOURCE_UNIT_RE = re.compile(
    r"PNG/Default size/Unit/medievalUnit_\d+\.png",
    re.IGNORECASE,
)
_CREDITS_ROW_RE = re.compile(
    r"^\|\s*(?P<file>[^|]+?)\s*\|\s*(?P<source>[^|]+?)\s*\|",
    re.MULTILINE,
)


def test_side_silhouettes_are_distinct_unit_sized_alpha_textures_with_rts_credits():
    """Battle sides must be distinct human-unit silhouettes under the public paths.

    Realistic defect existing gates miss: ``side_attacker`` / ``side_defender`` still
    load as Texture2D and appear in CREDITS with a blanket CC0 line, but remain
    Hexagon *buildings* (castle/tower) — same footprint as a terrain tile, or even
    the same file twice — so a later BattleView looks "textured" while both sides
    are structures. Machine gate: Godot load + alpha + strictly smaller than
    ``terrain_plains`` in both axes + byte-distinct files; CREDITS rows must cite
    RTS Pack: Medieval unit paths (not Hexagon object tiles).
    """
    attacker_path = GAME / SIDE_SILHOUETTE_ASSETS[0]
    defender_path = GAME / SIDE_SILHOUETTE_ASSETS[1]
    assert attacker_path.is_file() and defender_path.is_file(), (
        "side silhouette PNGs must exist under game/assets/"
    )
    assert attacker_path.read_bytes() != defender_path.read_bytes(), (
        "side_attacker.png and side_defender.png must differ byte-wise "
        "(two sides, not one image under two names)"
    )

    imported = _import_game_assets()
    assert imported.returncode == 0, (
        f"godot --import failed rc={imported.returncode} "
        f"stderr={imported.stderr!r} stdout={imported.stdout!r}"
    )

    probe_rels = SIDE_SILHOUETTE_ASSETS + (TERRAIN_PLAINS_ASSET,)
    result = _run_load_probe(*_res_paths(probe_rels))
    assert result.returncode == 0, (
        f"asset load probe failed rc={result.returncode} "
        f"stderr={result.stderr!r} stdout={result.stdout!r}"
    )
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    by_path = {row["path"]: row for row in _probe_payload(result)}
    terrain = by_path.get(f"res://{TERRAIN_PLAINS_ASSET}")
    assert terrain is not None and terrain.get("ok") is True, (
        f"terrain_plains must load for size baseline, got {terrain!r}"
    )
    tw, th = int(terrain["width"]), int(terrain["height"])
    assert tw > 0 and th > 0, f"terrain_plains size unreadable: {terrain!r}"

    for rel in SIDE_SILHOUETTE_ASSETS:
        res_path = f"res://{rel}"
        row = by_path.get(res_path)
        assert row is not None and row.get("ok") is True, (
            f"{res_path} must load as Texture2D, got {row!r}"
        )
        # Image.ALPHA_NONE == 0; BIT/BLEND count as usable transparency.
        assert int(row.get("alpha", -1)) > 0, (
            f"{res_path} must have a detectable alpha channel "
            f"(detect_alpha > ALPHA_NONE), got {row!r}"
        )
        w, h = int(row["width"]), int(row["height"])
        assert w < tw and h < th, (
            f"{res_path} must be smaller than terrain_plains "
            f"({tw}x{th}) in both dimensions, got {w}x{h}"
        )

    credits_text = (GAME / "assets" / "CREDITS.md").read_text(encoding="utf-8")
    assert re.search(r"RTS\s*Pack\s*:\s*Medieval|Medieval\s*RTS", credits_text, re.I), (
        "CREDITS.md must name Kenney RTS Pack: Medieval for the side unit sources"
    )
    rows = {
        m.group("file").strip(): m.group("source").strip()
        for m in _CREDITS_ROW_RE.finditer(credits_text)
    }
    for rel in SIDE_SILHOUETTE_ASSETS:
        name = Path(rel).name
        source = rows.get(name)
        assert source is not None, (
            f"CREDITS.md must have a table row attributing {name}"
        )
        assert _SIDE_SOURCE_UNIT_RE.search(source), (
            f"CREDITS.md row for {name} must cite an RTS Medieval unit file "
            f"(PNG/Default size/Unit/medievalUnit_NN.png), got {source!r}"
        )
        assert "castle_small" not in source and "medieval_tower" not in source, (
            f"CREDITS.md row for {name} must not still point at Hexagon buildings, "
            f"got {source!r}"
        )
