"""Deterministic owner-color palette for strategic map markers (tbbui)."""

from __future__ import annotations

from tbb.world import WorldMap

# Fixed cyclic list of owner fills (hex). More owners than colors wrap around.
OWNER_COLORS: tuple[str, ...] = (
    "#e41a1c",
    "#377eb8",
    "#4daf4a",
    "#984ea3",
    "#ff7f00",
    "#a65628",
    "#f781bf",
    "#66c2a5",
)

# Markers with no owner_id (None) use this neutral fill.
NEUTRAL_OWNER_COLOR = "#888888"


def owner_palette(world: WorldMap) -> dict[str, str]:
    """Map each distinct non-empty owner_id to a color by first-occurrence order.

    Scan order: ``world.regions``; within a region settlement before party.
    Only the first sighting of each owner_id enters the map. Colors are taken
    from ``OWNER_COLORS`` cyclically (index ``i % len(OWNER_COLORS)``).

    Pure and deterministic: no RNG, input map is not mutated. Key order of the
    returned dict matches first-occurrence order.
    """
    owners: list[str] = []
    seen: set[str] = set()
    for region in world.regions:
        settlement = world.settlement_at(region)
        if settlement is not None and settlement.owner_id is not None:
            owner_id = settlement.owner_id
            if owner_id not in seen:
                seen.add(owner_id)
                owners.append(owner_id)
        party = world.party_at(region)
        if party is not None and party.owner_id is not None:
            owner_id = party.owner_id
            if owner_id not in seen:
                seen.add(owner_id)
                owners.append(owner_id)

    n = len(OWNER_COLORS)
    return {owner_id: OWNER_COLORS[i % n] for i, owner_id in enumerate(owners)}
