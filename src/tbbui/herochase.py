"""Deterministic HTML fragment for march distance to enemy heroes."""

from __future__ import annotations

from tbb.ai import region_distance
from tbb.game import GameState
from tbb.world import Region, WorldMap


def render_hero_chase(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return a chase-list of march distances to enemy heroes on the map.

    Root is ``<div data-hero-chase="">``. When ``player_duchy_id`` matches a
    duchy in ``game.duchies``, the root carries ``data-player-on-map="true"``
    or ``"false"`` (player party present on the map). With ``"false"``, no
    child rows. With ``"true"``, one child ``<div data-enemy-duchy>`` per other
    duchy with ``has_hero`` whose party occupies a region (``game.duchies``
    order). Distance is ``ai.region_distance`` from the player's first map
    region to the enemy's first map region; no path → empty ``data-distance``
    and „brak drogi” text. When ``player_duchy_id`` is ``None`` or not in
    ``game.duchies``, returns a bare empty root. Pure and deterministic: no
    RNG/IO; does not mutate ``world`` or ``game``.
    """
    if player_duchy_id is None:
        return '<div data-hero-chase=""></div>'

    player = next(
        (d for d in game.duchies if d.duchy_id == player_duchy_id),
        None,
    )
    if player is None:
        return '<div data-hero-chase=""></div>'

    def party_region(duchy_id: str) -> Region | None:
        for region in world.regions:
            party = world.party_at(region)
            if party is not None and party.owner_id == duchy_id:
                return region
        return None

    player_region = party_region(player_duchy_id)
    if player_region is None:
        return (
            '<div data-hero-chase="" data-player-on-map="false"></div>'
        )

    rows: list[str] = []
    for d in game.duchies:
        if d.duchy_id == player_duchy_id or not d.has_hero:
            continue
        enemy_region = party_region(d.duchy_id)
        if enemy_region is None:
            continue
        distance = region_distance(world, player_region, enemy_region)
        if distance is None:
            distance_attr = ""
            row_text = f"{d.duchy_id}: brak drogi"
        else:
            distance_attr = str(distance)
            row_text = f"{d.duchy_id}: {distance} pól marszu"
        rows.append(
            f'<div data-enemy-duchy="{d.duchy_id}"'
            f' data-distance="{distance_attr}"'
            f">{row_text}</div>"
        )
    return (
        f'<div data-hero-chase=""'
        f' data-player-on-map="true"'
        f">{"".join(rows)}</div>"
    )
