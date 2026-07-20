"""Deterministic HTML fragment for settlement resource overview."""

from __future__ import annotations

from tbb.world import WorldMap


def render_settlement_panel(
    world: WorldMap, player_duchy_id: str | None = None
) -> str:
    """Return a parsable HTML fragment listing settlement resources.

    Root is ``<div data-settlement-panel="">`` with one
    ``data-settlement-row`` child per region that has a settlement, in
    ``world.regions`` order. Each row carries ``data-owner`` / ``data-wheat`` /
    ``data-gold`` / ``data-population`` / ``data-free`` / ``data-garrison`` and
    visible text matching those attributes. When ``player_duchy_id`` is not
    ``None``, rows whose ``owner_id`` matches get ``data-player-owned=""``.
    Pure and deterministic: no RNG/IO; ``world`` is not mutated.
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
        text = (
            f"{settlement.name} ({owner_text}): pszenica {wheat}, złoto {gold}"
            f" · populacja {population} (wolne {free}), garnizon {garrison}"
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
            f"{player_owned}"
            f">{text}</div>"
        )
    return f'<div data-settlement-panel="">{"".join(rows)}</div>'
