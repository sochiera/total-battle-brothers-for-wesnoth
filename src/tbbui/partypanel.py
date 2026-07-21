"""Deterministic HTML fragment for party strength overview."""

from __future__ import annotations

from tbb.world import WorldMap
from tbbui.unitstrength import combat_totals, wounded_count


def render_party_panel(
    world: WorldMap, player_duchy_id: str | None = None
) -> str:
    """Return a parsable HTML fragment listing parties on the map.

    Root is ``<div data-party-panel="">`` with one ``data-party-row`` child
    per region that has a party, in ``world.regions`` order. Each row carries
    ``data-owner`` / ``data-size`` / ``data-hp`` / ``data-attack`` /
    ``data-defense`` (sums of ``Unit.hp`` / ``Unit.damage`` / ``Unit.defense``
    over hero and subordinates), ``data-wounded`` (count of units among
    ``(hero, *units)`` with a non-empty ``wounds`` tuple) and visible text
    matching those attributes, including the
    `` · siła: HP H, atak A, obrona D · ranni: W`` suffix. When
    ``player_duchy_id`` is not ``None``, rows whose ``owner_id`` matches get
    ``data-player-owned=""``. Pure and deterministic: no RNG/IO; ``world`` is
    not mutated.
    """
    rows: list[str] = []
    for region in world.regions:
        party = world.party_at(region)
        if party is None:
            continue
        owner = party.owner_id or ""
        owner_text = party.owner_id if party.owner_id is not None else "—"
        size = len(party.units)
        roster = (party.hero, *party.units)
        total_hp, total_attack, total_defense = combat_totals(roster)
        wounded = wounded_count(roster)
        text = (
            f"{region.name} ({owner_text}): bohater + {size} podkomendnych"
            f" · siła: HP {total_hp}, atak {total_attack}, obrona {total_defense}"
            f" · ranni: {wounded}"
        )
        player_owned = (
            ' data-player-owned=""'
            if player_duchy_id is not None and party.owner_id == player_duchy_id
            else ""
        )
        rows.append(
            f'<div data-party-row="{region.name}"'
            f' data-owner="{owner}"'
            f' data-size="{size}"'
            f' data-hp="{total_hp}"'
            f' data-attack="{total_attack}"'
            f' data-defense="{total_defense}"'
            f' data-wounded="{wounded}"'
            f"{player_owned}"
            f">{text}</div>"
        )
    return f'<div data-party-panel="">{"".join(rows)}</div>'
