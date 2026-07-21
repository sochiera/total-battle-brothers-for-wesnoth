"""Deterministic HTML fragment for engagement strength preview (assault targets)."""

from __future__ import annotations

from tbb.game import GameState
from tbb.world import Region, WorldMap
from tbbui.unitstrength import combat_totals


def render_engagement_preview(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return a strength comparison of the player's party vs adjacent enemy settlements.

    Root is ``<div data-engagement-preview="">``. When ``player_duchy_id`` matches
    a duchy in ``game.duchies``:

    * no player party on the map → ``data-player-on-map="false"``, no rows,
      no ``data-own-*``;
    * player party present → ``data-player-on-map="true"`` plus
      ``data-own-hp`` / ``data-own-attack`` / ``data-own-defense`` from
      ``combat_totals((party.hero, *party.units))``, and one child row per
      neighbouring region (``world.neighbors`` order) whose settlement has an
      explicit ``owner_id != player_duchy_id``:
      ``data-target-kind="settlement"`` and enemy strength from
      ``combat_totals(settlement.garrison)``.

    When ``player_duchy_id`` is ``None`` or not in ``game.duchies``, returns a
    bare empty root. Pure and deterministic: no RNG/IO; does not mutate
    ``world`` or ``game``.
    """
    if player_duchy_id is None:
        return '<div data-engagement-preview=""></div>'

    player = next(
        (d for d in game.duchies if d.duchy_id == player_duchy_id),
        None,
    )
    if player is None:
        return '<div data-engagement-preview=""></div>'

    player_region = _first_party_region(world, player_duchy_id)
    if player_region is None:
        return (
            '<div data-engagement-preview=""'
            ' data-player-on-map="false"></div>'
        )

    party = world.party_at(player_region)
    assert party is not None
    own_hp, own_attack, own_defense = combat_totals((party.hero, *party.units))

    rows: list[str] = []
    for neighbor in world.neighbors(player_region):
        settlement = world.settlement_at(neighbor)
        if settlement is None:
            continue
        owner = settlement.owner_id
        if owner is None or owner == player_duchy_id:
            continue
        enemy_hp, enemy_attack, enemy_defense = combat_totals(settlement.garrison)
        text = (
            f"{neighbor.name} ({owner}): garnizon HP {enemy_hp},"
            f" atak {enemy_attack}, obrona {enemy_defense}"
        )
        rows.append(
            f'<div data-target-region="{neighbor.name}"'
            f' data-target-owner="{owner}"'
            f' data-target-kind="settlement"'
            f' data-enemy-hp="{enemy_hp}"'
            f' data-enemy-attack="{enemy_attack}"'
            f' data-enemy-defense="{enemy_defense}"'
            f">{text}</div>"
        )

    return (
        f'<div data-engagement-preview=""'
        f' data-player-on-map="true"'
        f' data-own-hp="{own_hp}"'
        f' data-own-attack="{own_attack}"'
        f' data-own-defense="{own_defense}"'
        f">{''.join(rows)}</div>"
    )


def _first_party_region(world: WorldMap, owner_id: str) -> Region | None:
    """Return the first region in ``world.regions`` whose party has *owner_id*."""
    for region in world.regions:
        party = world.party_at(region)
        if party is not None and party.owner_id == owner_id:
            return region
    return None
