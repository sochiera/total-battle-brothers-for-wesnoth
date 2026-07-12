"""Immutable regions and the strategic world graph."""

from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Mapping, Sequence

from tbb.battle import BattleResult, BattleSide, HexBattle
from tbb.battlefield import Battlefield
from tbb.hex import Hex
from tbb.party import Party
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
    parties: Mapping[Region, Party]
    _neighbors: Mapping[Region, tuple[Region, ...]] = field(repr=False)

    def __init__(
        self,
        regions: Sequence[Region],
        connections: Sequence[tuple[Region, Region]] = (),
        settlements: Mapping[Region, Settlement] | None = None,
        parties: Mapping[Region, Party] | None = None,
    ) -> None:
        region_tuple = tuple(regions)
        connection_tuple = tuple(connections)
        settlement_dict = dict(settlements or {})
        party_dict = dict(parties or {})
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
        if any(region not in region_set for region in party_dict):
            raise ValueError("party region is outside the world map")

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
        object.__setattr__(self, "parties", MappingProxyType(party_dict))
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

    def party_at(self, region: Region) -> Party | None:
        """Return the party occupying the region, if present."""
        if region not in self._neighbors:
            raise ValueError("region is outside the world map")
        return self.parties.get(region)

    def tick_settlements(self) -> "WorldMap":
        """Return a new world after all settlements complete a monthly tick."""
        settlements = {
            region: self.settlements[region]
            .tick_economy()
            .tick_growth()
            .tick_immigration()
            for region in self.regions
            if region in self.settlements
        }
        return WorldMap(
            self.regions,
            self.connections,
            settlements,
            self.parties,
        )

    def place_party(self, party: Party, region: Region) -> "WorldMap":
        """Return a new world with a party placed in an empty region."""
        if region not in self._neighbors:
            raise ValueError("region is outside the world map")
        if region in self.parties:
            raise ValueError("region is already occupied by a party")

        parties = dict(self.parties)
        parties[region] = party
        return WorldMap(
            self.regions,
            self.connections,
            self.settlements,
            parties,
        )

    def move_party(
        self, source: Region, destination: Region, move_points: int
    ) -> "WorldMap":
        """Return a new world after moving a party along one connection."""
        if source not in self._neighbors or destination not in self._neighbors:
            raise ValueError("region is outside the world map")
        if move_points < 1:
            raise ValueError("at least one movement point is required")
        if destination not in self._neighbors[source]:
            raise ValueError("destination is not adjacent to source")
        if source not in self.parties:
            raise ValueError("source region has no party")
        if destination in self.parties:
            raise ValueError("destination is already occupied by a party")

        parties = dict(self.parties)
        parties[destination] = parties.pop(source)
        return WorldMap(
            self.regions,
            self.connections,
            self.settlements,
            parties,
        )

    def start_battle(self, source: Region, destination: Region) -> HexBattle:
        """Create a battle for parties occupying two adjacent regions."""
        if source not in self._neighbors or destination not in self._neighbors:
            raise ValueError("region is outside the world map")
        if source == destination:
            raise ValueError("battle regions must be different")
        if destination not in self._neighbors[source]:
            raise ValueError("battle regions must be adjacent")
        if source not in self.parties:
            raise ValueError("source region has no party")
        if destination not in self.parties:
            raise ValueError("destination region has no party")

        attacker = self.parties[source]
        defender = self.parties[destination]
        self._require_enemy_owners(attacker.owner_id, defender.owner_id)

        battle = HexBattle(Battlefield())
        deployments = (
            (attacker, 0, BattleSide.ATTACKER),
            (defender, 2, BattleSide.DEFENDER),
        )
        for party, column, side in deployments:
            for row, unit in enumerate((party.hero, *party.units)):
                battle = battle.deploy(unit, Hex(column, row), side)
        return battle

    def apply_party_battle_result(
        self,
        source: Region,
        destination: Region,
        result: BattleResult,
    ) -> "WorldMap":
        """Return a new world with a party battle's result applied."""
        if source not in self._neighbors or destination not in self._neighbors:
            raise ValueError("region is outside the world map")
        if source == destination:
            raise ValueError("battle regions must be different")
        if destination not in self._neighbors[source]:
            raise ValueError("battle regions must be adjacent")
        if source not in self.parties:
            raise ValueError("source region has no party")
        if destination not in self.parties:
            raise ValueError("destination region has no party")

        parties = dict(self.parties)
        attacker = parties.pop(source)
        if result is BattleResult.ATTACKER_WIN:
            parties[destination] = attacker
        elif result is BattleResult.DEFENDER_WIN:
            pass
        elif result is BattleResult.DRAW:
            parties.pop(destination)
        else:
            raise ValueError("unknown battle result")

        return WorldMap(
            self.regions,
            self.connections,
            self.settlements,
            parties,
        )

    def start_settlement_battle(
        self, source: Region, destination: Region
    ) -> HexBattle:
        """Create a battle between a party and an adjacent settlement garrison."""
        if source not in self._neighbors or destination not in self._neighbors:
            raise ValueError("region is outside the world map")
        if source == destination:
            raise ValueError("battle regions must be different")
        if destination not in self._neighbors[source]:
            raise ValueError("battle regions must be adjacent")
        if source not in self.parties:
            raise ValueError("source region has no party")
        if destination not in self.settlements:
            raise ValueError("destination region has no settlement")

        party = self.parties[source]
        settlement = self.settlements[destination]
        self._require_enemy_owners(party.owner_id, settlement.owner_id)
        battle = HexBattle(Battlefield())
        for row, unit in enumerate((party.hero, *party.units)):
            battle = battle.deploy(unit, Hex(0, row), BattleSide.ATTACKER)
        for row, unit in enumerate(settlement.garrison):
            battle = battle.deploy(unit, Hex(2, row), BattleSide.DEFENDER)
        return battle

    def apply_settlement_battle_result(
        self,
        source: Region,
        destination: Region,
        result: BattleResult,
    ) -> "WorldMap":
        """Return a new world with a settlement battle's result applied."""
        if source not in self._neighbors or destination not in self._neighbors:
            raise ValueError("region is outside the world map")
        if source == destination:
            raise ValueError("battle regions must be different")
        if destination not in self._neighbors[source]:
            raise ValueError("battle regions must be adjacent")
        if source not in self.parties:
            raise ValueError("source region has no party")
        if destination not in self.settlements:
            raise ValueError("destination region has no settlement")
        if not isinstance(result, BattleResult):
            raise ValueError("unknown battle result")
        if (
            result is BattleResult.ATTACKER_WIN
            and destination in self.parties
        ):
            raise ValueError("destination is already occupied by a party")

        parties = dict(self.parties)
        settlements = dict(self.settlements)
        attacker = parties.pop(source)
        if result is BattleResult.ATTACKER_WIN:
            parties[destination] = attacker
            settlements[destination] = replace(
                settlements[destination], owner_id=attacker.owner_id
            )

        return WorldMap(
            self.regions,
            self.connections,
            settlements,
            parties,
        )

    @staticmethod
    def _require_enemy_owners(
        attacker_owner_id: str | None, defender_owner_id: str | None
    ) -> None:
        """Reject strategic contact unless both owners are known and different."""
        if attacker_owner_id is None or defender_owner_id is None:
            raise ValueError("battle participants must have owners")
        if attacker_owner_id == defender_owner_id:
            raise ValueError("battle participants must have different owners")
