"""Pure transitions used by the headless game driver."""

from tbb.ai import take_duchy_turn
from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.rng import Rng
from tbb.world import WorldMap


def _has_owned_party(world: WorldMap, owner_id: str) -> bool:
    return any(party.owner_id == owner_id for party in world.parties.values())


def resolve_hero_survival(
    duchy: Duchy, world_before: WorldMap, world_after: WorldMap
) -> Duchy:
    """Resolve succession when a duchy's deployed party disappears."""
    if _has_owned_party(world_before, duchy.duchy_id) and not _has_owned_party(
        world_after, duchy.duchy_id
    ):
        return duchy.succeed()
    return duchy


def run_headless_game(
    world: WorldMap,
    game: GameState,
    rng: Rng,
    max_turns: int = 1000,
) -> tuple[WorldMap, GameState]:
    """Run one AI turn unless the game or configured turn budget is over."""
    if game.is_over or max_turns == 0:
        return world, game

    current_world = world
    for duchy in game.duchies:
        if not duchy.is_defeated:
            current_world = take_duchy_turn(current_world, duchy, rng)
    return current_world, game
