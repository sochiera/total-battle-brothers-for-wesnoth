"""Deterministic HTML fragment for threatened-position alert."""

from __future__ import annotations

from tbb.game import GameState
from tbb.world import Region, WorldMap
from tbbui.gamelookup import player_duchy


def _first_hostile_neighbor(
    world: WorldMap, region: Region, player_duchy_id: str
) -> tuple[Region, str] | None:
    """Return (neighbor region, owner_id) of first hostile adjacent party.

    Walks ``world.neighbors(region)`` order; skips empty regions and parties
    without explicit ``owner_id`` or with ``owner_id == player_duchy_id``.
    """
    for neighbor in world.neighbors(region):
        party = world.party_at(neighbor)
        if party is None:
            continue
        owner = party.owner_id
        if owner is not None and owner != player_duchy_id:
            return neighbor, owner
    return None


def _threatened_rows(world: WorldMap, player_duchy_id: str) -> list[str]:
    """Build HTML row fragments for each threatened own position.

    Order follows ``world.regions``; within a region, settlement before party.
    """
    rows: list[str] = []
    for region in world.regions:
        hostile = _first_hostile_neighbor(world, region, player_duchy_id)
        if hostile is None:
            continue
        enemy_region, enemy_owner = hostile
        settlement = world.settlement_at(region)
        if settlement is not None and settlement.owner_id == player_duchy_id:
            rows.append(
                f'<div data-threatened-region="{region.name}"'
                f' data-threatened-kind="settlement"'
                f' data-enemy-region="{enemy_region.name}"'
                f' data-enemy-owner="{enemy_owner}">'
                f"Osada {region.name}: zagrożenie od {enemy_owner}"
                f" z {enemy_region.name}</div>"
            )
        party = world.party_at(region)
        if party is not None and party.owner_id == player_duchy_id:
            rows.append(
                f'<div data-threatened-region="{region.name}"'
                f' data-threatened-kind="party"'
                f' data-enemy-region="{enemy_region.name}"'
                f' data-enemy-owner="{enemy_owner}">'
                f"Oddział {region.name}: zagrożenie od {enemy_owner}"
                f" z {enemy_region.name}</div>"
            )
    return rows


def render_threat_alert(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return an alert root for own positions threatened by adjacent enemy parties.

    Root is ``<div data-threat-alert="">``. When ``player_duchy_id`` is ``None``
    or not in ``game.duchies`` (``player_duchy(...) is None``), returns a bare
    empty root with no ``data-threats``, no visible text, and no children.
    When the player is known, the root carries ``data-threats="N"`` and visible
    text ``Zagrożone pozycje: N``, plus one child row per threatened own
    position (settlement and/or party, counted separately; order of
    ``world.regions``, settlement before party in the same region). Each row is
    ``data-threatened-region`` / ``data-threatened-kind`` /
    ``data-enemy-region`` / ``data-enemy-owner`` for the first neighboring
    party with explicit ``owner_id != player_duchy_id`` in ``world.neighbors``
    order. ``N`` equals the number of emitted rows. Pure and deterministic:
    no RNG/IO; does not mutate ``world`` or ``game``.
    """
    if player_duchy(game, player_duchy_id) is None:
        return '<div data-threat-alert=""></div>'

    # player_duchy is not None ⇒ player_duchy_id is a known str
    assert player_duchy_id is not None
    rows = _threatened_rows(world, player_duchy_id)
    n = len(rows)
    return (
        f'<div data-threat-alert="" data-threats="{n}">'
        f"Zagrożone pozycje: {n}"
        f"{''.join(rows)}</div>"
    )
