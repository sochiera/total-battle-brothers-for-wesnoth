"""Immutable regions and the strategic world graph."""

from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Mapping, Sequence

from tbb.battle import BattleResult, BattleSide, HexBattle
from tbb.battlefield import Battlefield
from tbb.hex import Hex
from tbb.party import Party
from tbb.rng import Rng
from tbb.settlement import Settlement
from tbb.unit import Unit


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

    def with_settlement(
        self, region: Region, settlement: Settlement
    ) -> "WorldMap":
        """Return a new world with one settlement inserted or replaced."""
        settlements = dict(self.settlements)
        settlements[region] = settlement
        return self._with_maps(settlements=settlements)

    def _with_maps(
        self,
        *,
        settlements: Mapping[Region, Settlement] | None = None,
        parties: Mapping[Region, Party] | None = None,
    ) -> "WorldMap":
        """Return a copy with selected strategic maps replaced."""
        return WorldMap(
            self.regions,
            self.connections,
            self.settlements if settlements is None else settlements,
            self.parties if parties is None else parties,
        )

    def party_at(self, region: Region) -> Party | None:
        """Return the party occupying the region, if present."""
        if region not in self._neighbors:
            raise ValueError("region is outside the world map")
        return self.parties.get(region)

    def settlement_defenders(self, region: Region) -> tuple[Unit, ...]:
        """Return the units that defend the settlement at ``region``."""
        settlement = self.settlement_at(region)
        if settlement is None:
            return ()

        home_party = self.parties.get(region)
        if not self._party_defends_settlement(home_party, settlement):
            return settlement.garrison
        return settlement.garrison + (home_party.hero, *home_party.units)

    def tick_settlements(self) -> "WorldMap":
        """Return a new world after all settlements complete a monthly tick."""
        settlements = {
            region: self.settlements[region]
            .tick_economy()
            .tick_growth()
            .tick_immigration()
            .tick_training()
            .tick_equipment()
            .tick_healing()
            for region in self.regions
            if region in self.settlements
        }
        return WorldMap(
            self.regions,
            self.connections,
            settlements,
            self.parties,
        )

    def tick_parties(self) -> "WorldMap":
        """Return a new world after every party heals wounds and trains one month."""
        parties = {
            region: replace(
                self.parties[region].tick_wounds(1).tick_training(1),
                acted_this_month=False,
            )
            for region in self.regions
            if region in self.parties
        }
        return WorldMap(
            self.regions,
            self.connections,
            self.settlements,
            parties,
        )

    def muster_party(self, region: Region, hero: Unit) -> "WorldMap":
        """Muster a settlement's garrison and place it in the same region."""
        if region not in self._neighbors:
            raise ValueError("region is outside the world map")
        if region not in self.settlements:
            raise ValueError("region has no settlement")
        if region in self.parties:
            raise ValueError("region is already occupied by a party")

        party, settlement = self.settlements[region].muster(hero)
        return self.with_settlement(region, settlement).place_party(party, region)

    def reinforce_party(self, region: Region) -> "WorldMap":
        """Move a settlement's garrison into its party in the same region.

        This returns the unchanged world when the region has no party or
        settlement, the party is ownerless or belongs to another owner, the
        garrison is empty, the party has already acted this month, or the
        garrison would exceed ``Party.MAX_SUBORDINATES``.
        """
        if region not in self._neighbors:
            raise ValueError("region is outside the world map")

        party = self.parties.get(region)
        settlement = self.settlements.get(region)
        if party is None or settlement is None:
            return self
        if party.owner_id is None:
            return self
        if party.owner_id != settlement.owner_id:
            return self
        if not settlement.garrison:
            return self
        if not self._party_can_act(region):
            return self
        if len(party.units) + len(settlement.garrison) > Party.MAX_SUBORDINATES:
            return self

        garrison_party, settlement = settlement.muster(party.hero)
        parties = dict(self.parties)
        parties[region] = replace(
            party,
            units=party.units + garrison_party.units,
            acted_this_month=True,
        )
        return self.with_settlement(region, settlement)._with_maps(
            parties=parties
        )

    def place_party(self, party: Party, region: Region) -> "WorldMap":
        """Return a new world with a party placed in an empty region."""
        if region not in self._neighbors:
            raise ValueError("region is outside the world map")
        if region in self.parties:
            raise ValueError("region is already occupied by a party")

        parties = dict(self.parties)
        parties[region] = party
        return self._with_maps(parties=parties)

    def move_party(
        self, source: Region, destination: Region, move_points: int
    ) -> "WorldMap":
        """Return a new world after moving a party along one connection.

        A party may move only once per month.  An already acted party makes a
        legal movement request a world-identity-preserving no-op; a successful
        move carries the monthly action marker to the moved party.
        """
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
        if not self._party_can_act(source):
            return self

        parties = dict(self.parties)
        parties[destination] = replace(
            parties.pop(source), acted_this_month=True
        )
        return self._with_maps(parties=parties)

    def _party_can_act(self, source: Region) -> bool:
        """Return whether the party at ``source`` still has its action.

        Requires ``self.parties[source]`` to exist.
        """
        return not self.parties[source].acted_this_month

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
        result: BattleResult | None,
        battle: HexBattle | None = None,
    ) -> "WorldMap":
        """Return a new world with a party battle's result applied.

        This low-level transition does not enforce the monthly-action marker;
        callers are expected to validate through ``resolve_party_battle`` or
        ``resolve_party_battle_recorded``.
        """
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
        if result is not None and not isinstance(result, BattleResult):
            raise ValueError("unknown battle result")

        parties = dict(self.parties)
        attacker = replace(parties.pop(source), acted_this_month=True)
        if result is None:
            parties[source] = (
                attacker
                if battle is None
                else Party.reconstruct(
                    attacker, battle.side_survivors(BattleSide.ATTACKER)
                )
            )
            if battle is not None:
                defender = parties[destination]
                parties[destination] = Party.reconstruct(
                    defender, battle.side_survivors(BattleSide.DEFENDER)
                )
        elif result is BattleResult.ATTACKER_WIN:
            parties[destination] = (
                attacker
                if battle is None
                else Party.reconstruct(
                    attacker, battle.side_survivors(BattleSide.ATTACKER)
                )
            )
        elif result is BattleResult.DEFENDER_WIN:
            if battle is not None:
                defender = parties[destination]
                parties[destination] = Party.reconstruct(
                    defender, battle.side_survivors(BattleSide.DEFENDER)
                )
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

    def resolve_party_battle_recorded(
        self,
        source: Region,
        destination: Region,
        rng: Rng,
        move_points: int = 1,
        attacker_morale: int = 0,
        defender_morale: int = 0,
    ) -> tuple["WorldMap", HexBattle | None]:
        """Play an adjacent party battle; return map and resolved battle.

        An already acted attacker is a monthly-action no-op.  The battle is
        built first so invalid regions still raise before the ``_party_can_act``
        guard, but RNG is not touched on the no-op path.
        """
        battle = self.start_battle(source, destination)
        if not self._party_can_act(source):
            return self, None
        resolved = battle.auto_resolve(
            move_points,
            rng,
            attacker_morale=attacker_morale,
            defender_morale=defender_morale,
        )
        new_world = self.apply_party_battle_result(
            source, destination, resolved.result(), battle=resolved
        )
        return new_world, resolved

    def resolve_party_battle(
        self,
        source: Region,
        destination: Region,
        rng: Rng,
        move_points: int = 1,
        attacker_morale: int = 0,
        defender_morale: int = 0,
    ) -> "WorldMap":
        """Play an adjacent party battle and apply its result to the world."""
        new_world, _ = self.resolve_party_battle_recorded(
            source,
            destination,
            rng,
            move_points=move_points,
            attacker_morale=attacker_morale,
            defender_morale=defender_morale,
        )
        return new_world

    def start_settlement_battle(
        self, source: Region, destination: Region
    ) -> HexBattle:
        """Create a battle between a party and an adjacent settlement garrison, plus any party already standing in that region that has the same owner as the settlement."""
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
        home_party = self.parties.get(destination)
        defending_party = (
            home_party
            if self._party_defends_settlement(home_party, settlement)
            else None
        )
        return self._build_settlement_battle(
            party, settlement, defending_party=defending_party
        )

    def start_settlement_battle_at(self, region: Region) -> HexBattle:
        """Create a wall assault for a party occupying an enemy settlement."""
        if region not in self._neighbors:
            raise ValueError("region is outside the world map")
        if region not in self.parties:
            raise ValueError("source region has no party")
        if region not in self.settlements:
            raise ValueError("region has no settlement")

        party = self.parties[region]
        settlement = self.settlements[region]
        self._require_enemy_owners(party.owner_id, settlement.owner_id)
        return self._build_settlement_battle(party, settlement)

    @staticmethod
    def _build_settlement_battle(
        attacker: Party,
        settlement: Settlement,
        *,
        defending_party: Party | None = None,
    ) -> HexBattle:
        """Deploy a party and settlement defenders on the assault battlefield."""
        battle = HexBattle(Battlefield())
        for row, unit in enumerate((attacker.hero, *attacker.units)):
            battle = battle.deploy(unit, Hex(0, row), BattleSide.ATTACKER)
        for row, unit in enumerate(settlement.garrison):
            battle = battle.deploy(unit, Hex(2, row), BattleSide.DEFENDER)
        if defending_party is not None:
            for row, unit in enumerate(
                (defending_party.hero, *defending_party.units)
            ):
                battle = battle.deploy(unit, Hex(3, row), BattleSide.DEFENDER)
        return battle

    @staticmethod
    def _party_defends_settlement(
        party: Party | None, settlement: Settlement
    ) -> bool:
        """True when a party in the settlement region fights as DEFENDER.

        Same ``owner_id`` as the settlement (owner/ally under the current
        same-id alliance model). Hostile-to-attacker alone is not enough.
        Used by deploy, absorb, and the ATTACKER_WIN occupancy guard so a
        defending party may be cleared on conquest while any non-defending
        occupant is rejected.
        """
        return party is not None and party.owner_id == settlement.owner_id

    @staticmethod
    def _ensure_garrison_occupancy(settlement: Settlement) -> Settlement:
        """Keep enough occupied population reserved for every garrison slot."""
        if settlement.occupied >= len(settlement.garrison):
            return settlement
        return replace(settlement, occupied=len(settlement.garrison))

    @staticmethod
    def _absorb_settlement_defenders(
        settlement: Settlement,
        parties: dict[Region, Party],
        destination: Region,
        attacker: Party,
        battle: HexBattle,
        *,
        keep_home_party_survivors: bool = True,
    ) -> Settlement:
        """Split defender survivors between garrison and home party by deployment slot.

        start_settlement_battle deploys the attacker first, then the garrison,
        then (if it fights) the home party, each getting a contiguous block of
        stable slot ids. Falling units drop out of ``side_survivors`` but never
        change the surviving units' slot ids, so a slot-id boundary tells
        garrison-origin survivors from party-origin ones even when Unit value
        equality or post-damage identity (e.g. stunning) can't.

        When ``keep_home_party_survivors`` is false, home-party survivors are
        discarded after the garrison survivors are absorbed.
        """
        home_party = parties.get(destination)
        if not WorldMap._party_defends_settlement(home_party, settlement):
            return settlement.absorb_defenders(
                battle.side_survivors(BattleSide.DEFENDER)
            )
        garrison_count = len(settlement.garrison)
        garrison_slot_low = 1 + len(attacker.units)
        garrison_slot_high = garrison_slot_low + garrison_count
        defender_survivors = battle.side_survivors_with_slots(BattleSide.DEFENDER)
        garrison_survivors = tuple(
            unit
            for slot, unit in defender_survivors
            if garrison_slot_low <= slot < garrison_slot_high
        )
        party_survivors = tuple(
            unit for slot, unit in defender_survivors if slot >= garrison_slot_high
        )
        if len(garrison_survivors) + len(party_survivors) != len(
            defender_survivors
        ):
            raise ValueError(
                "defender survivor lost outside deployment slot window"
            )
        if party_survivors and keep_home_party_survivors:
            parties[destination] = Party.reconstruct(home_party, party_survivors)
        else:
            del parties[destination]
        return settlement.absorb_defenders(garrison_survivors)

    def apply_settlement_battle_result(
        self,
        source: Region,
        destination: Region,
        result: BattleResult | None,
        battle: HexBattle | None = None,
    ) -> "WorldMap":
        """Return a new world with a settlement battle's result applied.

        This low-level transition does not enforce the monthly-action marker;
        callers are expected to validate through ``resolve_settlement_battle``
        or ``resolve_settlement_battle_recorded``.
        """
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
        self._require_battle_result(result)
        attacker = replace(self.parties[source], acted_this_month=True)
        settlement = self.settlements[destination]
        destination_party = self.parties.get(destination)
        if (
            result is BattleResult.ATTACKER_WIN
            and destination_party is not None
            and not self._party_defends_settlement(destination_party, settlement)
        ):
            raise ValueError("destination is already occupied by a party")

        parties = dict(self.parties)
        parties.pop(source)
        if result is None:
            parties[source] = (
                attacker
                if battle is None
                else Party.reconstruct(
                    attacker, battle.side_survivors(BattleSide.ATTACKER)
                )
            )
            if battle is not None and destination in parties:
                settlement = self._absorb_settlement_defenders(
                    settlement, parties, destination, attacker, battle
                )
        elif result is BattleResult.ATTACKER_WIN:
            if battle is not None:
                settlement = self._ensure_garrison_occupancy(settlement)
                settlement = self._absorb_settlement_defenders(
                    settlement,
                    parties,
                    destination,
                    attacker,
                    battle,
                    keep_home_party_survivors=False,
                )
                occupying = Party.reconstruct(
                    attacker, battle.side_survivors(BattleSide.ATTACKER)
                )
            else:
                # Occupancy guard rejects non-defenders; assignment replaces
                # a defending occupant (if any).
                occupying = attacker
            parties[destination] = occupying
            settlement = replace(settlement, owner_id=attacker.owner_id)
        elif battle is not None:
            settlement = self._absorb_settlement_defenders(
                settlement, parties, destination, attacker, battle
            )

        world_with_updated_parties = WorldMap(
            self.regions,
            self.connections,
            self.settlements,
            parties,
        )
        return world_with_updated_parties.with_settlement(
            destination, settlement
        )

    def apply_settlement_battle_result_at(
        self,
        region: Region,
        result: BattleResult | None,
        battle: HexBattle | None = None,
    ) -> "WorldMap":
        """Apply a wall-assault result when party and settlement share a region.

        This transition is separate from ``apply_settlement_battle_result``:
        there is no source/destination movement for an assault already inside
        the settlement's region.  With a recorded battle, both the attacking
        party and the garrison are rebuilt from their surviving units.  A
        failed assault leaves attacking survivors in place, since they have no
        retreat destination.  This operation intentionally validates that the
        party and settlement have known, different owners, which is stricter
        than the lower-level reconstruction performed after a battle.  It does
        not validate ``acted_this_month``; callers are responsible for that
        higher-level action check.
        """
        if region not in self._neighbors:
            raise ValueError("region is outside the world map")
        if region not in self.parties:
            raise ValueError("region has no party")
        if region not in self.settlements:
            raise ValueError("region has no settlement")
        self._require_battle_result(result)

        attacker = replace(self.parties[region], acted_this_month=True)
        settlement = self.settlements[region]
        self._require_enemy_owners(attacker.owner_id, settlement.owner_id)

        parties = dict(self.parties)
        if battle is None:
            surviving_attacker = attacker
        else:
            attacker_survivors = battle.side_survivors(BattleSide.ATTACKER)
            surviving_attacker = (
                Party.reconstruct(attacker, attacker_survivors)
                if attacker_survivors
                else None
            )
            settlement = self._ensure_garrison_occupancy(settlement)
            settlement = settlement.absorb_defenders(
                battle.side_survivors(BattleSide.DEFENDER)
            )

        if result is BattleResult.ATTACKER_WIN:
            settlement = replace(settlement, owner_id=attacker.owner_id)

        if surviving_attacker is None:
            parties.pop(region)
        else:
            parties[region] = surviving_attacker

        return WorldMap(
            self.regions,
            self.connections,
            self.settlements,
            parties,
        ).with_settlement(region, settlement)

    def resolve_settlement_battle_recorded(
        self,
        source: Region,
        destination: Region,
        rng: Rng,
        move_points: int = 1,
        attacker_morale: int = 0,
        defender_morale: int = 0,
    ) -> tuple["WorldMap", HexBattle | None]:
        """Play an adjacent settlement battle; return map and resolved battle.

        The monthly-action no-op follows the same ``_party_can_act`` rule as
        ``resolve_party_battle_recorded``.
        """
        battle = self.start_settlement_battle(source, destination)
        if not self._party_can_act(source):
            return self, None
        resolved = self._auto_resolve_settlement_battle(
            battle,
            move_points,
            rng,
            attacker_morale=attacker_morale,
            defender_morale=defender_morale,
        )
        new_world = self.apply_settlement_battle_result(
            source, destination, resolved.result(), battle=resolved
        )
        return new_world, resolved

    def resolve_settlement_battle(
        self,
        source: Region,
        destination: Region,
        rng: Rng,
        move_points: int = 1,
        attacker_morale: int = 0,
        defender_morale: int = 0,
    ) -> "WorldMap":
        """Play an adjacent settlement battle and apply its result."""
        new_world, _ = self.resolve_settlement_battle_recorded(
            source,
            destination,
            rng,
            move_points=move_points,
            attacker_morale=attacker_morale,
            defender_morale=defender_morale,
        )
        return new_world

    def resolve_settlement_battle_at_recorded(
        self,
        region: Region,
        rng: Rng,
        move_points: int = 1,
        attacker_morale: int = 0,
        defender_morale: int = 0,
    ) -> tuple["WorldMap", HexBattle | None]:
        """Play a wall assault in place; return map and resolved battle.

        An already acted party is a monthly-action no-op.  The battle is
        built before the action guard so invalid regions and contacts still
        raise, while the no-op path leaves the RNG untouched.
        """
        battle = self.start_settlement_battle_at(region)
        if not self._party_can_act(region):
            return self, None
        resolved = self._auto_resolve_settlement_battle(
            battle,
            move_points,
            rng,
            attacker_morale=attacker_morale,
            defender_morale=defender_morale,
        )
        new_world = self.apply_settlement_battle_result_at(
            region, resolved.result(), battle=resolved
        )
        return new_world, resolved

    def resolve_settlement_battle_at(
        self,
        region: Region,
        rng: Rng,
        move_points: int = 1,
        attacker_morale: int = 0,
        defender_morale: int = 0,
    ) -> "WorldMap":
        """Play a wall assault in place and apply its result to the world."""
        new_world, _ = self.resolve_settlement_battle_at_recorded(
            region,
            rng,
            move_points=move_points,
            attacker_morale=attacker_morale,
            defender_morale=defender_morale,
        )
        return new_world

    @staticmethod
    def _auto_resolve_settlement_battle(
        battle: HexBattle,
        move_points: int,
        rng: Rng,
        *,
        attacker_morale: int,
        defender_morale: int,
    ) -> HexBattle:
        """Resolve a settlement battle with the strategic combat settings."""
        return battle.auto_resolve(
            move_points,
            rng,
            attacker_morale=attacker_morale,
            defender_morale=defender_morale,
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

    @staticmethod
    def _require_battle_result(result: BattleResult | None) -> None:
        """Reject values outside the public battle-result contract."""
        if result is not None and not isinstance(result, BattleResult):
            raise ValueError("unknown battle result")
