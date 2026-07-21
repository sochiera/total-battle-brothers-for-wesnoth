"""Deterministic HTML fragment for engagement strength preview (assault/engage targets)."""

from __future__ import annotations

from tbb.game import GameState
from tbb.world import WorldMap
from tbbui.maplookup import first_party_region
from tbbui.unitstrength import combat_totals


def render_engagement_preview(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return a strength comparison of the player's party vs adjacent enemy targets.

    Root is ``<div data-engagement-preview="">``. When ``player_duchy_id`` matches
    a duchy in ``game.duchies``:

    * no player party on the map → ``data-player-on-map="false"``, no rows,
      no ``data-own-*``;
    * player party present → ``data-player-on-map="true"`` plus
      ``data-own-hp`` / ``data-own-attack`` / ``data-own-defense`` from
      ``combat_totals((party.hero, *party.units))``, and child rows per
      neighbouring region (``world.neighbors`` order) for hostile targets:
      settlement with explicit ``owner_id != player_duchy_id`` →
      ``data-target-kind="settlement"`` (strength from garrison, text
      „garnizon …"); party with ``owner_id != player_duchy_id`` →
      ``data-target-kind="party"`` (strength from hero+units, text
      „oddział …"). In a region with both, settlement precedes party.
      Each row carries ``data-advantage`` after ``data-enemy-defense``
      (``"true"`` / suffix „ — przewaga" when own hp+attack+defense ≥ enemy
      sum; else ``"false"`` / „ — niekorzystnie").

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

    player_region = first_party_region(world, player_duchy_id)
    if player_region is None:
        return (
            '<div data-engagement-preview=""'
            ' data-player-on-map="false"></div>'
        )

    party = world.party_at(player_region)
    assert party is not None
    own_hp, own_attack, own_defense = combat_totals((party.hero, *party.units))
    own_sum = own_hp + own_attack + own_defense

    rows: list[str] = []
    for neighbor in world.neighbors(player_region):
        settlement = world.settlement_at(neighbor)
        if settlement is not None:
            owner = settlement.owner_id
            if owner is not None and owner != player_duchy_id:
                enemy_hp, enemy_attack, enemy_defense = combat_totals(
                    settlement.garrison
                )
                rows.append(
                    _target_row(
                        neighbor.name,
                        owner,
                        "settlement",
                        "garnizon",
                        enemy_hp,
                        enemy_attack,
                        enemy_defense,
                        own_sum,
                    )
                )

        enemy_party = world.party_at(neighbor)
        if enemy_party is not None:
            owner = enemy_party.owner_id
            if owner is not None and owner != player_duchy_id:
                enemy_hp, enemy_attack, enemy_defense = combat_totals(
                    (enemy_party.hero, *enemy_party.units)
                )
                rows.append(
                    _target_row(
                        neighbor.name,
                        owner,
                        "party",
                        "oddział",
                        enemy_hp,
                        enemy_attack,
                        enemy_defense,
                        own_sum,
                    )
                )

    return (
        f'<div data-engagement-preview=""'
        f' data-player-on-map="true"'
        f' data-own-hp="{own_hp}"'
        f' data-own-attack="{own_attack}"'
        f' data-own-defense="{own_defense}"'
        f">{''.join(rows)}</div>"
    )


def _target_row(
    region_name: str,
    owner: str,
    kind: str,
    force_label: str,
    enemy_hp: int,
    enemy_attack: int,
    enemy_defense: int,
    own_sum: int,
) -> str:
    """One target row: attrs + text with advantage suffix."""
    advantage = own_sum >= enemy_hp + enemy_attack + enemy_defense
    advantage_attr = "true" if advantage else "false"
    suffix = " — przewaga" if advantage else " — niekorzystnie"
    text = (
        f"{region_name} ({owner}): {force_label} HP {enemy_hp},"
        f" atak {enemy_attack}, obrona {enemy_defense}{suffix}"
    )
    return (
        f'<div data-target-region="{region_name}"'
        f' data-target-owner="{owner}"'
        f' data-target-kind="{kind}"'
        f' data-enemy-hp="{enemy_hp}"'
        f' data-enemy-attack="{enemy_attack}"'
        f' data-enemy-defense="{enemy_defense}"'
        f' data-advantage="{advantage_attr}"'
        f">{text}</div>"
    )

