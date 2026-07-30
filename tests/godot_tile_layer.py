"""Shared assertions helpers for Godot tile texture layers (map + battle views).

Keeps the R87.1 rule „layer fills parent tile + mouse ignore” in one place so
map and battle regression gates cannot drift apart.
"""

from __future__ import annotations

# Godot Control.MouseFilter: STOP=0, PASS=1, IGNORE=2.
# Only STOP/IGNORE are used by map/battle gates; PASS is not exported.
MOUSE_FILTER_STOP = 0
MOUSE_FILTER_IGNORE = 2


def layer_fills_tile(layer: dict, tile: dict, *, tol: float = 0.5) -> bool:
    """True when layer global size matches the parent tile (control bounds).

    Probe reports ``get_global_rect().size``. With PRESET_FULL_RECT that size
    stays full-tile regardless of TextureRect.stretch_mode — so this checks
    layout fill (FULL_RECT bounds), not STRETCH_SCALE drawing mode.
    """
    return (
        abs(float(layer["w"]) - float(tile["w"])) <= tol
        and abs(float(layer["h"]) - float(tile["h"])) <= tol
    )
