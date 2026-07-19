"""Immutable game-over state across duchies."""

from dataclasses import dataclass
from typing import Iterable

from tbb.duchy import Duchy
from tbb.party import Party
from tbb.resources import Resources
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.world import Region, WorldMap


def create_headless_game() -> tuple[WorldMap, "GameState"]:
    """Create the fixed two-duchy starting state for the headless game."""
    player_region = Region("player lands")
    border_region = Region("border")
    ai_region = Region("ai lands")
    player_reserve_region = Region("player reserve")

    player_settlement = Settlement(
        "Player Keep", 5, storage=Resources(10, 10), owner_id="player"
    )
    player_reserve_settlement = Settlement(
        "Player Reserve", 1, owner_id="player"
    )
    ai_settlement = Settlement(
        "AI Keep",
        5,
        occupied=1,
        storage=Resources(10, 10),
        garrison=(Unit(training=5, equipment=12, training_progress=5),),
        owner_id="ai",
    )
    world = WorldMap(
        (player_region, border_region, ai_region, player_reserve_region),
        (
            (player_region, border_region),
            (border_region, ai_region),
            (player_region, player_reserve_region),
        ),
        {
            player_region: player_settlement,
            ai_region: ai_settlement,
            player_reserve_region: player_reserve_settlement,
        },
    )
    game = GameState(
        (
            Duchy(
                "player",
                Unit(equipment=1),
                settlements=(player_settlement, player_reserve_settlement),
            ),
            Duchy("ai", Unit(equipment=1), settlements=(ai_settlement,)),
        )
    )
    return world, game


@dataclass(frozen=True)
class GameState:
    """Hold the duchies in a game and expose its victory state."""

    duchies: tuple[Duchy, ...]

    def __init__(self, duchies: Iterable[Duchy]) -> None:
        copied = tuple(duchies)
        if any(not isinstance(duchy, Duchy) for duchy in copied):
            raise TypeError("game duchies must be Duchies")
        duchy_ids = [duchy.duchy_id for duchy in copied]
        if len(duchy_ids) != len(set(duchy_ids)):
            raise ValueError("game duchy identifiers must be unique")
        object.__setattr__(self, "duchies", copied)

    @property
    def contenders(self) -> tuple[Duchy, ...]:
        """Return undefeated duchies in their original order."""
        return tuple(duchy for duchy in self.duchies if not duchy.is_defeated)

    @property
    def is_over(self) -> bool:
        """Report whether at most one undefeated duchy remains."""
        return len(self.contenders) <= 1

    @property
    def winner(self) -> Duchy | None:
        """Return the sole undefeated duchy, if there is exactly one."""
        contenders = self.contenders
        return contenders[0] if len(contenders) == 1 else None

    def sync_from_world(self, world: WorldMap) -> "GameState":
        """Rebuild each duchy's strategic collections from the world map."""
        if not isinstance(world, WorldMap):
            raise TypeError("world must be a WorldMap")

        settlements_by_owner: dict[str, list[Settlement]] = {}
        parties_by_owner: dict[str, list[Party]] = {}
        for region in world.regions:
            settlement = world.settlements.get(region)
            if settlement is not None and settlement.owner_id is not None:
                settlements_by_owner.setdefault(settlement.owner_id, []).append(
                    settlement
                )
            party = world.parties.get(region)
            if party is not None and party.owner_id is not None:
                parties_by_owner.setdefault(party.owner_id, []).append(party)

        return GameState(
            Duchy(
                duchy_id=duchy.duchy_id,
                hero=duchy.hero,
                morale=duchy.morale,
                heir=duchy.heir,
                settlements=settlements_by_owner.get(duchy.duchy_id, ()),
                parties=parties_by_owner.get(duchy.duchy_id, ()),
            )
            for duchy in self.duchies
        )
