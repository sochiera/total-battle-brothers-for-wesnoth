"""Deterministic HTML fragment for settlement resource overview."""

from __future__ import annotations

from tbb import BARRACKS, SMITH
from tbb.world import WorldMap
from tbbui.unitstrength import combat_totals, wounded_count


def render_settlement_panel(
    world: WorldMap, player_duchy_id: str | None = None
) -> str:
    """Return a parsable HTML fragment listing settlement resources.

    Root is ``<div data-settlement-panel="">`` with one
    ``data-settlement-row`` child per region that has a settlement, in
    ``world.regions`` order. Each row carries ``data-owner`` / ``data-wheat`` /
    ``data-gold`` / ``data-population`` / ``data-free`` / ``data-garrison`` /
    ``data-garrison-hp`` / ``data-garrison-attack`` / ``data-garrison-defense``
    (sums of ``Unit.hp`` / ``Unit.damage`` / ``Unit.defense`` over the garrison;
    empty → 0) / ``data-buildings`` (``len(active_buildings)``; none → 0) /
    ``data-building-names`` (building names joined by ``", "`` in
    ``active_buildings`` order; empty → ``""``) /
    ``data-garrison-wounded`` (count of garrison units with a non-empty
    ``wounds`` tuple; empty garrison → 0) /
    ``data-training-ready`` (``"true"`` when ``BARRACKS`` is in
    ``active_buildings``, else ``"false"``; immediately after
    ``data-garrison-wounded``) /
    ``data-equip-ready`` (``"true"`` when ``SMITH`` is in ``active_buildings``,
    else ``"false"``; immediately after ``data-training-ready``) and visible
    text matching those attributes, including the
    `` · siła garnizonu: HP H, atak A, obrona D · budynki: N`` suffix and, when
    N>0, `` (name1, name2)`` after the count, then `` · ranni: W``, then
    `` · trening: gotowy`` when training is ready, else
    `` · trening: wstrzymany (brak Koszar)``, then
    `` · uzbrojenie: gotowe`` when equip is ready, else
    `` · uzbrojenie: wstrzymane (brak Kuźni)``. When
    ``player_duchy_id`` is not ``None``, rows whose ``owner_id`` matches get
    ``data-player-owned=""``. Pure and deterministic: no RNG/IO; ``world`` is
    not mutated.
    """
    rows: list[str] = []
    for region in world.regions:
        settlement = world.settlement_at(region)
        if settlement is None:
            continue
        owner = settlement.owner_id or ""
        owner_text = settlement.owner_id if settlement.owner_id is not None else "—"
        wheat = settlement.storage.wheat
        gold = settlement.storage.gold
        population = settlement.population
        free = settlement.free
        garrison = len(settlement.garrison)
        garrison_hp, garrison_attack, garrison_defense = combat_totals(
            settlement.garrison
        )
        garrison_wounded = wounded_count(settlement.garrison)
        has_barracks = BARRACKS in settlement.active_buildings
        training_ready = "true" if has_barracks else "false"
        training_suffix = (
            " · trening: gotowy"
            if has_barracks
            else " · trening: wstrzymany (brak Koszar)"
        )
        has_smith = SMITH in settlement.active_buildings
        equip_ready = "true" if has_smith else "false"
        equip_suffix = (
            " · uzbrojenie: gotowe"
            if has_smith
            else " · uzbrojenie: wstrzymane (brak Kuźni)"
        )
        buildings = len(settlement.active_buildings)
        building_names = ", ".join(b.name for b in settlement.active_buildings)
        buildings_suffix = (
            f" · budynki: {buildings} ({building_names})"
            if buildings
            else f" · budynki: {buildings}"
        )
        text = (
            f"{settlement.name} ({owner_text}): pszenica {wheat}, złoto {gold}"
            f" · populacja {population} (wolne {free}), garnizon {garrison}"
            f" · siła garnizonu: HP {garrison_hp}"
            f", atak {garrison_attack}, obrona {garrison_defense}"
            f"{buildings_suffix}"
            f" · ranni: {garrison_wounded}"
            f"{training_suffix}"
            f"{equip_suffix}"
        )
        player_owned = (
            ' data-player-owned=""'
            if player_duchy_id is not None and settlement.owner_id == player_duchy_id
            else ""
        )
        rows.append(
            f'<div data-settlement-row="{region.name}"'
            f' data-owner="{owner}"'
            f' data-wheat="{wheat}"'
            f' data-gold="{gold}"'
            f' data-population="{population}"'
            f' data-free="{free}"'
            f' data-garrison="{garrison}"'
            f' data-garrison-hp="{garrison_hp}"'
            f' data-garrison-attack="{garrison_attack}"'
            f' data-garrison-defense="{garrison_defense}"'
            f' data-buildings="{buildings}"'
            f' data-building-names="{building_names}"'
            f' data-garrison-wounded="{garrison_wounded}"'
            f' data-training-ready="{training_ready}"'
            f' data-equip-ready="{equip_ready}"'
            f"{player_owned}"
            f">{text}</div>"
        )
    return f'<div data-settlement-panel="">{"".join(rows)}</div>'
