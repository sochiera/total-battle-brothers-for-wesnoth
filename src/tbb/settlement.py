"""Immutable settlement state and its population pool."""

from collections.abc import Sequence
from dataclasses import dataclass, replace

from tbb.building import Building, SMITH
from tbb.party import Party
from tbb.resources import Resources
from tbb.unit import Unit


TRAINING_MONTHS_PER_TURN: int = 1
RECRUIT_GOLD_COST: int = 1
EQUIP_GOLD_COST: int = 1
EQUIP_INVESTMENT_PER_TURN: int = 1


@dataclass(frozen=True)
class Settlement:
    """Represent a settlement with free and occupied population."""

    name: str
    population: int
    occupied: int = 0
    active_buildings: tuple[Building, ...] = ()
    storage: Resources = Resources(0, 0)
    capacity: int | None = None
    garrison: tuple[Unit, ...] = ()
    owner_id: str | None = None

    def __post_init__(self) -> None:
        """Reject an inconsistent population pool."""
        if self.population < 0:
            raise ValueError("population cannot be negative")
        if self.occupied < 0 or self.occupied > self.population:
            raise ValueError("occupied must be between zero and population")
        if self.capacity is not None and self.capacity < self.population:
            raise ValueError("capacity cannot be below population")
        if self.owner_id is not None and not isinstance(self.owner_id, str):
            raise TypeError("settlement owner_id must be text or None")
        if self.owner_id == "":
            raise ValueError("settlement owner_id cannot be empty")

    @property
    def free(self) -> int:
        """Return population currently available for assignment."""
        return self.population - self.occupied

    @property
    def production(self) -> Resources:
        """Return the combined output of all active buildings."""
        total = Resources(0, 0)
        for building in self.active_buildings:
            total = total.add(building.output)
        return total

    @property
    def consumption(self) -> Resources:
        """Return resources consumed by the total population each month."""
        return Resources(wheat=self.population, gold=0)

    def tick_economy(self) -> "Settlement":
        """Return the settlement state after one monthly economy tick."""
        storage = self.storage.add(self.production).subtract(
            self.consumption, allow_negative=True
        )
        return replace(self, storage=storage)

    def tick_growth(self) -> "Settlement":
        """Return the settlement state after deterministic monthly births."""
        below_capacity = self.capacity is None or self.population < self.capacity
        growth = 1 if self.storage.wheat > 0 and below_capacity else 0
        return replace(self, population=self.population + growth)

    def tick_immigration(self) -> "Settlement":
        """Return the settlement state after deterministic monthly immigration."""
        below_capacity = self.capacity is None or self.population < self.capacity
        immigration = (
            1
            if self.storage.gold > 0 and self.storage.wheat > 0 and below_capacity
            else 0
        )
        return replace(self, population=self.population + immigration)

    def tick_training(self) -> "Settlement":
        """Return the settlement after one monthly garrison training tick."""
        return replace(
            self,
            garrison=tuple(
                unit.train(TRAINING_MONTHS_PER_TURN) for unit in self.garrison
            ),
        )

    def tick_equipment(self) -> "Settlement":
        """Equip one least-equipped soldier when an active smith can be paid."""
        if (
            SMITH not in self.active_buildings
            or not self.garrison
            or self.storage.gold < EQUIP_GOLD_COST
        ):
            return replace(self)

        target = min(
            range(len(self.garrison)),
            key=lambda index: self.garrison[index].equipment,
        )
        garrison = list(self.garrison)
        garrison[target] = garrison[target].equip(EQUIP_INVESTMENT_PER_TURN)
        storage = self.storage.subtract(Resources(wheat=0, gold=EQUIP_GOLD_COST))
        return replace(self, garrison=tuple(garrison), storage=storage)

    def occupy(self, amount: int) -> "Settlement":
        """Return a new settlement with ``amount`` population assigned."""
        if amount < 0:
            raise ValueError("amount to occupy cannot be negative")
        if amount > self.free:
            raise ValueError("not enough free population")
        return replace(self, occupied=self.occupied + amount)

    def release(self, amount: int) -> "Settlement":
        """Return a new settlement with ``amount`` population released."""
        if amount < 0:
            raise ValueError("amount to release cannot be negative")
        if amount > self.occupied:
            raise ValueError("cannot release more than occupied population")
        return replace(self, occupied=self.occupied - amount)

    def recruit(self, unit: Unit | None = None) -> "Settlement":
        """Return a new state with one resident recruited into the garrison."""
        if self.storage.gold < RECRUIT_GOLD_COST:
            raise ValueError("not enough gold to recruit")
        staffed = self.occupy(1)
        storage = staffed.storage.subtract(
            Resources(wheat=0, gold=RECRUIT_GOLD_COST)
        )
        recruit = Unit() if unit is None else unit
        return replace(
            staffed,
            storage=storage,
            garrison=staffed.garrison + (recruit,),
        )

    def muster(self, hero: Unit) -> tuple[Party, "Settlement"]:
        """Move the whole garrison into a new party led by ``hero``."""
        party = Party(hero=hero, units=self.garrison, owner_id=self.owner_id)
        departing = len(self.garrison)
        settlement = replace(
            self,
            population=self.population - departing,
            occupied=self.occupied - departing,
            garrison=(),
        )
        return party, settlement

    def absorb_defenders(self, survivors: Sequence[Unit]) -> "Settlement":
        """Replace the garrison with survivors and remove fallen residents."""
        surviving_garrison = tuple(survivors)
        fallen = len(self.garrison) - len(surviving_garrison)
        if fallen < 0:
            raise ValueError("cannot have more survivors than defenders")
        return replace(
            self,
            population=self.population - fallen,
            occupied=self.occupied - fallen,
            garrison=surviving_garrison,
        )

    def open_building(self, building: Building) -> "Settlement":
        """Return a new state with ``building`` active and staffed."""
        staffed = self.occupy(building.staff)
        return replace(
            staffed,
            active_buildings=staffed.active_buildings + (building,),
        )

    def close_building(self, building: Building) -> "Settlement":
        """Return a new state with one matching building closed."""
        if building not in self.active_buildings:
            raise ValueError("building is not active")
        active = list(self.active_buildings)
        active.remove(building)
        released = self.release(building.staff)
        return replace(released, active_buildings=tuple(active))
