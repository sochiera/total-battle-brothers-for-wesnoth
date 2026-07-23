"""Immutable deployment state for a hex battle."""

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
import heapq
from types import MappingProxyType

from tbb.battlefield import Battlefield
from tbb.combat import melee_hit_chance
from tbb.hex import Hex
from tbb.rng import Rng
from tbb.unit import Unit
from tbb.wound import BRUISE


class BattleSide(Enum):
    """One of the two opposing sides in a battle."""

    ATTACKER = "attacker"
    DEFENDER = "defender"


class BattleResult(Enum):
    """A resolved battle's winning side, or a draw."""

    ATTACKER_WIN = "attacker_win"
    DEFENDER_WIN = "defender_win"
    DRAW = "draw"


@dataclass(frozen=True)
class BattleSideReport:
    """Immutable final classification of one side's units."""

    fallen: tuple[Unit, ...] = ()
    stunned: tuple[Unit, ...] = ()
    active: tuple[Unit, ...] = ()


@dataclass(frozen=True)
class BattleReport:
    """Immutable result and final unit state for both battle sides."""

    result: BattleResult
    attacker: BattleSideReport
    defender: BattleSideReport


@dataclass(frozen=True)
class HexBattle:
    """Combine battlefield terrain with units deployed on hexes."""

    battlefield: Battlefield
    units: Mapping[Hex, Unit] = field(default_factory=dict)
    _current_hp: Mapping[Hex, int] = field(default_factory=dict, repr=False)
    sides: Mapping[Hex, BattleSide] = field(default_factory=dict)
    _fallen: tuple[tuple[BattleSide, Unit], ...] = field(
        default_factory=tuple, repr=False
    )
    _deployment_order: tuple[Hex, ...] = field(default_factory=tuple, repr=False)

    def __post_init__(self) -> None:
        """Protect deployment data from mutation through the public mapping."""
        battlefield = (
            self.battlefield
            if isinstance(self.battlefield, Battlefield)
            else Battlefield(self.battlefield)
        )
        units = dict(self.units)
        current_hp = dict(self._current_hp)
        sides = dict(self.sides)
        deployment_order = self._deployment_order or tuple(units)
        for position, unit in units.items():
            current_hp.setdefault(position, unit.hp)
        if sides.keys() != units.keys():
            raise ValueError("every deployed unit must have exactly one battle side")
        if len(deployment_order) != len(units) or set(deployment_order) != set(units):
            raise ValueError("deployment order must contain every deployed position")
        object.__setattr__(self, "battlefield", battlefield)
        object.__setattr__(self, "units", MappingProxyType(units))
        object.__setattr__(self, "_current_hp", MappingProxyType(current_hp))
        object.__setattr__(self, "sides", MappingProxyType(sides))
        object.__setattr__(self, "_fallen", tuple(self._fallen))
        object.__setattr__(self, "_deployment_order", tuple(deployment_order))

    def unit_at(self, position: Hex) -> Unit | None:
        """Return the unit at ``position``, if any."""
        return self.units.get(position)

    def is_occupied(self, position: Hex) -> bool:
        """Return whether a unit occupies ``position``."""
        return position in self.units

    def current_hp_at(self, position: Hex) -> int:
        """Return current HP of the unit at ``position``."""
        if not self.is_occupied(position):
            raise ValueError("cannot get HP from an empty hex")
        return self._current_hp[position]

    def side_at(self, position: Hex) -> BattleSide:
        """Return the side of the unit at ``position``."""
        if not self.is_occupied(position):
            raise ValueError("cannot get side from an empty hex")
        return self.sides[position]

    def side_survivors(self, side: BattleSide) -> tuple[Unit, ...]:
        """Return one side's deployed survivors in deployment order."""
        return tuple(
            self.units[position]
            for position in self._deployment_order
            if self.sides[position] is side
        )

    def nearest_enemy(self, position: Hex) -> Hex | None:
        """Return the nearest active enemy, breaking ties by deployment order."""
        if not self.is_occupied(position):
            raise ValueError("cannot select an enemy from an empty hex")
        source_side = self.sides[position]
        enemies = (
            enemy
            for enemy in self._deployment_order
            if self.sides[enemy] is not source_side
            and self._current_hp[enemy] > 0
            and not self.units[enemy].stunned
        )
        return min(enemies, key=position.distance, default=None)

    def take_unit_turn(
        self, position: Hex, move_points: int, morale: int, rng: Rng
    ) -> "HexBattle":
        """Move toward the nearest enemy or attack it when already adjacent."""
        unit = self.unit_at(position)
        if unit is None:
            raise ValueError("cannot take a turn from an empty hex")
        if self.current_hp_at(position) == 0 or unit.stunned:
            return self

        enemy = self.nearest_enemy(position)
        if enemy is None:
            return self
        if position.distance(enemy) == 1:
            attacked = self.melee_attack(position, enemy, morale, rng)
            if attacked.current_hp_at(enemy) == 0 and not attacked.units[enemy].stunned:
                return attacked.resolve_defeat(enemy, rng)
            return attacked

        reachable = self.reachable(position, move_points)
        if not reachable:
            return self
        destination = min(
            reachable, key=lambda candidate: (
                candidate.distance(enemy), candidate.q, candidate.r
            )
        )
        if destination.distance(enemy) >= position.distance(enemy):
            return self
        return self.move(position, destination, move_points)

    def auto_resolve(
        self,
        move_points: int,
        rng: Rng,
        attacker_morale: int = 0,
        defender_morale: int = 0,
        max_rounds: int = 1000,
    ) -> "HexBattle":
        """Play deployment-ordered rounds until resolution or the round limit.

        Each unit receives the morale of its battle side (attacker or defender).
        """
        battle = self
        rounds = 0
        while battle.result() is None and rounds < max_rounds:
            turn_positions = battle._deployment_order
            for position in turn_positions:
                if battle.result() is not None:
                    break
                unit = battle.unit_at(position)
                if (
                    unit is None
                    or battle.current_hp_at(position) == 0
                    or unit.stunned
                ):
                    continue
                side = battle.sides[position]
                morale = (
                    attacker_morale
                    if side is BattleSide.ATTACKER
                    else defender_morale
                )
                battle = battle.take_unit_turn(position, move_points, morale, rng)
            rounds += 1
        return battle

    def result(self) -> BattleResult | None:
        """Return the resolved result, or ``None`` while both sides are active."""
        active_sides = {
            self.sides[position]
            for position, unit in self.units.items()
            if self._current_hp[position] > 0 and not unit.stunned
        }
        if active_sides == {BattleSide.ATTACKER, BattleSide.DEFENDER}:
            return None
        if active_sides == {BattleSide.ATTACKER}:
            return BattleResult.ATTACKER_WIN
        if active_sides == {BattleSide.DEFENDER}:
            return BattleResult.DEFENDER_WIN
        return BattleResult.DRAW

    def report(self) -> BattleReport:
        """Return the immutable final report for a resolved battle."""
        result = self.result()
        if result is None:
            raise ValueError("cannot report an unfinished battle")
        if any(self._current_hp[position] == 0 and not unit.stunned
               for position, unit in self.units.items()):
            raise ValueError("cannot report an unresolved defeated unit")

        def for_side(side: BattleSide) -> BattleSideReport:
            return BattleSideReport(
                fallen=tuple(unit for fallen_side, unit in self._fallen
                             if fallen_side is side),
                stunned=tuple(self.units[position] for position in self._deployment_order
                              if self.sides[position] is side
                              and self.units[position].stunned),
                active=tuple(self.units[position] for position in self._deployment_order
                             if self.sides[position] is side
                             and self._current_hp[position] > 0
                             and not self.units[position].stunned),
            )

        return BattleReport(
            result=result,
            attacker=for_side(BattleSide.ATTACKER),
            defender=for_side(BattleSide.DEFENDER),
        )

    def award_experience(self) -> BattleReport:
        """Return a final report with one experience awarded to each survivor."""
        report = self.report()

        def reward(side: BattleSideReport) -> BattleSideReport:
            return BattleSideReport(
                fallen=side.fallen,
                stunned=tuple(
                    replace(unit, experience=unit.experience + 1)
                    for unit in side.stunned
                ),
                active=tuple(
                    replace(unit, experience=unit.experience + 1)
                    for unit in side.active
                ),
            )

        return BattleReport(
            result=report.result,
            attacker=reward(report.attacker),
            defender=reward(report.defender),
        )

    def deploy(self, unit: Unit, position: Hex, side: BattleSide) -> "HexBattle":
        """Return a new state with ``unit`` deployed at ``position``."""
        if self.is_occupied(position):
            raise ValueError("cannot deploy a unit on an occupied hex")
        if not isinstance(side, BattleSide):
            raise ValueError("unit must be deployed on a battle side")
        units = dict(self.units)
        units[position] = unit
        current_hp = dict(self._current_hp)
        current_hp[position] = unit.hp
        sides = dict(self.sides)
        sides[position] = side
        return HexBattle(
            self.battlefield, units, current_hp, sides, self._fallen,
            self._deployment_order + (position,),
        )

    def damage(self, position: Hex, amount: int) -> "HexBattle":
        """Return a new state after dealing non-negative damage at ``position``."""
        if amount < 0:
            raise ValueError("damage cannot be negative")
        if not self.is_occupied(position):
            raise ValueError("cannot damage an empty hex")
        current_hp = dict(self._current_hp)
        current_hp[position] = max(0, current_hp[position] - amount)
        return HexBattle(
            self.battlefield, self.units, current_hp, self.sides, self._fallen,
            self._deployment_order,
        )

    def melee_attack(
        self, attacker: Hex, target: Hex, morale: int, rng: Rng
    ) -> "HexBattle":
        """Resolve one melee attack and return the resulting immutable state."""
        attacking_unit = self.unit_at(attacker)
        target_unit = self.unit_at(target)
        if attacking_unit is None:
            raise ValueError("cannot attack from an empty hex")
        if attacking_unit.stunned:
            raise ValueError("a stunned unit cannot attack")
        if target_unit is None:
            raise ValueError("cannot attack an empty hex")
        if attacker.distance(target) != 1:
            raise ValueError("melee target must be adjacent")
        if self.side_at(attacker) is self.side_at(target):
            raise ValueError("cannot attack a unit on the same side")

        hit_chance = melee_hit_chance(
            attacking_unit,
            target_unit,
            self.battlefield.terrain_at(attacker),
            self.battlefield.terrain_at(target),
            morale,
        )
        if rng.chance(hit_chance / 100):
            return self.damage(target, attacking_unit.damage)
        return self

    def ranged_attack(
        self, attacker: Hex, target: Hex, morale: int, rng: Rng
    ) -> "HexBattle":
        """Resolve one ranged attack and return the resulting immutable state."""
        attacking_unit = self.unit_at(attacker)
        target_unit = self.unit_at(target)
        if attacking_unit is None:
            raise ValueError("cannot attack from an empty hex")
        if attacking_unit.stunned:
            raise ValueError("a stunned unit cannot attack")
        if target_unit is None:
            raise ValueError("cannot attack an empty hex")
        distance = attacker.distance(target)
        if not 2 <= distance <= attacking_unit.ranged_range:
            raise ValueError("target is outside ranged attack range")
        if self.side_at(attacker) is self.side_at(target):
            raise ValueError("cannot attack a unit on the same side")
        if any(self.is_occupied(position) for position in attacker.line_to(target)[1:-1]):
            raise ValueError("a unit blocks the ranged attack line")

        hit_chance = melee_hit_chance(
            attacking_unit,
            target_unit,
            self.battlefield.terrain_at(attacker),
            self.battlefield.terrain_at(target),
            morale,
        )
        if rng.chance(hit_chance / 100):
            return self.damage(target, attacking_unit.damage)
        return self

    def reachable(self, source: Hex, move_points: int) -> set[Hex]:
        """Return unoccupied hexes reachable within ``move_points``."""
        best_cost = {source: 0}
        frontier = [(0, source.q, source.r)]
        reachable: set[Hex] = set()

        while frontier:
            cost, q, r = heapq.heappop(frontier)
            position = Hex(q, r)
            if cost != best_cost[position]:
                continue

            for neighbor in position.neighbors():
                if self.is_occupied(neighbor):
                    continue
                next_cost = cost + self.battlefield.move_cost_at(neighbor)
                if next_cost > move_points or next_cost >= best_cost.get(
                    neighbor, next_cost + 1
                ):
                    continue
                best_cost[neighbor] = next_cost
                reachable.add(neighbor)
                heapq.heappush(frontier, (next_cost, neighbor.q, neighbor.r))

        return reachable

    def move(
        self, source: Hex, destination: Hex, move_points: int
    ) -> "HexBattle":
        """Return a new state with the source unit moved to a reachable hex."""
        unit = self.unit_at(source)
        if unit is None:
            raise ValueError("cannot move from an empty hex")
        if unit.stunned:
            raise ValueError("a stunned unit cannot move")
        if self.is_occupied(destination):
            raise ValueError("cannot move to an occupied hex")
        if destination not in self.reachable(source, move_points):
            raise ValueError("destination is outside the movement budget")

        units = dict(self.units)
        del units[source]
        units[destination] = unit
        current_hp = dict(self._current_hp)
        current_hp[destination] = current_hp.pop(source)
        sides = dict(self.sides)
        sides[destination] = sides.pop(source)
        deployment_order = tuple(
            destination if position == source else position
            for position in self._deployment_order
        )
        return HexBattle(
            self.battlefield, units, current_hp, sides, self._fallen,
            deployment_order,
        )

    def resolve_defeat(self, position: Hex, rng: Rng) -> "HexBattle":
        """Resolve death or stunned survival for a unit reduced to zero HP."""
        unit = self.unit_at(position)
        if unit is None:
            raise ValueError("cannot resolve defeat on an empty hex")
        if self.current_hp_at(position) != 0:
            raise ValueError("cannot resolve a unit with HP remaining")
        if unit.stunned:
            raise ValueError("cannot resolve an already stunned unit")

        units = dict(self.units)
        current_hp = dict(self._current_hp)
        sides = dict(self.sides)
        fallen = self._fallen
        deployment_order = self._deployment_order
        if rng.chance(0.5):
            fallen += ((sides[position], unit),)
            del units[position]
            del current_hp[position]
            del sides[position]
            deployment_order = tuple(
                deployed for deployed in deployment_order if deployed != position
            )
        else:
            units[position] = replace(
                unit, stunned=True, wounds=unit.wounds + (BRUISE,)
            )
        return HexBattle(
            self.battlefield, units, current_hp, sides, fallen, deployment_order
        )
