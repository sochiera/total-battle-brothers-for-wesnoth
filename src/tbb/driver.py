"""Pure transitions used by the headless game driver."""

import tbb.ai as ai
from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.rng import Rng
from tbb.world import WorldMap


def _has_owned_party(world: WorldMap, owner_id: str) -> bool:
    return any(party.owner_id == owner_id for party in world.parties.values())


def _owned_population(world: WorldMap, owner_id: str) -> int:
    return sum(
        settlement.population
        for settlement in world.settlements.values()
        if settlement.owner_id == owner_id
    )


def resolve_hero_survival(
    duchy: Duchy, world_before: WorldMap, world_after: WorldMap
) -> Duchy:
    """Resolve succession when a duchy's deployed party disappears."""
    had_party = _has_owned_party(world_before, duchy.duchy_id)
    has_party = _has_owned_party(world_after, duchy.duchy_id)
    mustered_during_action = _owned_population(
        world_after, duchy.duchy_id
    ) < _owned_population(world_before, duchy.duchy_id)
    if not has_party and (had_party or mustered_during_action):
        return duchy.succeed()
    return duchy


def _replace_duchy(game: GameState, replacement: Duchy) -> GameState:
    """Return a game with the matching duchy replaced in place."""
    return GameState(
        replacement if duchy.duchy_id == replacement.duchy_id else duchy
        for duchy in game.duchies
    )


def run_headless_game(
    world: WorldMap,
    game: GameState,
    rng: Rng,
    max_turns: int = 1000,
) -> tuple[WorldMap, GameState]:
    """Run AI turns until the game ends or the turn budget is exhausted."""
    current_world = world
    current_game = game
    for _ in range(max_turns):
        if current_game.is_over:
            break
        duchy_ids = tuple(
            duchy.duchy_id
            for duchy in current_game.duchies
            if not duchy.is_defeated
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
            world_before = current_world
            current_world = ai.take_duchy_turn(world_before, duchy, rng)
            resolved = resolve_hero_survival(duchy, world_before, current_world)
            current_game = _replace_duchy(current_game, resolved)
            current_game = current_game.sync_from_world(current_world)
            if current_game.is_over:
                break
    return current_world, current_game
