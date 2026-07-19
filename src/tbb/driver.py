"""Pure transitions used by the headless game driver."""

import tbb.ai as ai
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
    current_game = game
    duchy_ids = tuple(
        duchy.duchy_id for duchy in game.duchies if not duchy.is_defeated
    )
    for duchy_id in duchy_ids:
        duchy = next(
            (
                candidate
                for candidate in current_game.duchies
                if candidate.duchy_id == duchy_id
            ),
            None,
        )
        if duchy is None or duchy.is_defeated:
            continue
        current_world = ai.take_duchy_turn(current_world, duchy, rng)
        current_game = current_game.sync_from_world(current_world)
    return current_world, current_game
