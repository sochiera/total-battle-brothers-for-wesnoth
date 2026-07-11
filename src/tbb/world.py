"""Immutable regions and the strategic world graph."""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Sequence

from tbb.settlement import Settlement


@dataclass(frozen=True)
class Region:
    """A world region identified by its name."""

    name: str


@dataclass(frozen=True, init=False)
class WorldMap:
    """A finite, immutable graph of regions and their settlements."""

    regions: tuple[Region, ...]
    connections: tuple[tuple[Region, Region], ...]
    settlements: Mapping[Region, Settlement]
    _neighbors: Mapping[Region, tuple[Region, ...]] = field(repr=False)

    def __init__(
        self,
        regions: Sequence[Region],
        connections: Sequence[tuple[Region, Region]] = (),
        settlements: Mapping[Region, Settlement] | None = None,
    ) -> None:
        region_tuple = tuple(regions)
        connection_tuple = tuple(connections)
        settlement_dict = dict(settlements or {})
        region_set = set(region_tuple)

        if len(region_set) != len(region_tuple):
            raise ValueError("regions must be unique")

        adjacency: dict[Region, set[Region]] = {
            region: set() for region in region_tuple
        }
        for first, second in connection_tuple:
            if first not in region_set or second not in region_set:
                raise ValueError("connection endpoint is outside the world map")
            if first == second:
                raise ValueError("self-loop connections are not allowed")
            adjacency[first].add(second)
            adjacency[second].add(first)

        if any(region not in region_set for region in settlement_dict):
            raise ValueError("settlement region is outside the world map")

        ordered_neighbors = {
            region: tuple(
                candidate
                for candidate in region_tuple
                if candidate in adjacency[region]
            )
            for region in region_tuple
        }
        object.__setattr__(self, "regions", region_tuple)
        object.__setattr__(self, "connections", connection_tuple)
        object.__setattr__(
            self, "settlements", MappingProxyType(settlement_dict)
        )
        object.__setattr__(self, "_neighbors", MappingProxyType(ordered_neighbors))

    def neighbors(self, region: Region) -> tuple[Region, ...]:
        """Return adjacent regions in the world's declared region order."""
        try:
            return self._neighbors[region]
        except KeyError as error:
            raise ValueError("region is outside the world map") from error

    def settlement_at(self, region: Region) -> Settlement | None:
        """Return the region's settlement, if present."""
        if region not in self._neighbors:
            raise ValueError("region is outside the world map")
        return self.settlements.get(region)
