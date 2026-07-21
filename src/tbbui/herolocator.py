"""Deterministic HTML fragment for enemy-hero locations on the map."""

from __future__ import annotations

from tbb.game import GameState
from tbb.world import WorldMap


def render_enemy_hero_locator(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return a chase-list of enemy heroes and their map regions.

    Root is ``<div data-hero-locator="">``. When ``player_duchy_id`` matches a
    duchy in ``game.duchies``, the root carries ``data-heroes-on-map="K"``
    (``K`` = enemy duchies with ``has_hero`` whose party occupies a region) and
    one child ``<div data-enemy-duchy>`` per other duchy with ``has_hero``
    (``game.duchies`` order). Region is the first in ``world.regions`` with
    ``party_at(region).owner_id == duchy_id``; missing party → empty region and
    „niewystawiony” text. When ``player_duchy_id`` is ``None`` or not in
    ``game.duchies``, returns a bare empty root. Pure and deterministic: no
    RNG/IO; does not mutate ``world`` or ``game``.
    """
    if player_duchy_id is None:
        return '<div data-hero-locator=""></div>'

    player = next(
        (d for d in game.duchies if d.duchy_id == player_duchy_id),
        None,
    )
    if player is None:
        return '<div data-hero-locator=""></div>'

    def hero_region(duchy_id: str) -> str | None:
        for region in world.regions:
            party = world.party_at(region)
            if party is not None and party.owner_id == duchy_id:
                return region.name
        return None

    rows: list[str] = []
    on_map = 0
    for d in game.duchies:
        if d.duchy_id == player_duchy_id or not d.has_hero:
            continue
        region_name = hero_region(d.duchy_id)
        if region_name is not None:
            on_map += 1
            region_attr = region_name
            row_text = f"{d.duchy_id}: bohater w {region_name}"
        else:
            region_attr = ""
            row_text = f"{d.duchy_id}: bohater niewystawiony"
        rows.append(
            f'<div data-enemy-duchy="{d.duchy_id}"'
            f' data-hero-region="{region_attr}"'
            f">{row_text}</div>"
        )
    return (
        f'<div data-hero-locator=""'
        f' data-heroes-on-map="{on_map}"'
        f">{"".join(rows)}</div>"
    )
