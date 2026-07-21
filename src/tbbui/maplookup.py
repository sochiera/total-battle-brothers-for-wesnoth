"""Pure map lookup helpers for owner parties on the strategic map."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tbb.world import Region, WorldMap


def first_party_region(world: WorldMap, owner_id: str) -> Region | None:
    """Return the first region in ``world.regions`` whose party has *owner_id*.

    Iterates ``world.regions`` in order; returns the first region where
    ``party_at(region)`` is not ``None`` and ``party.owner_id == owner_id``.
    If no such party exists, returns ``None``. Pure: does not mutate *world*.
    """
    for region in world.regions:
        party = world.party_at(region)
        if party is not None and party.owner_id == owner_id:
            return region
    return None
