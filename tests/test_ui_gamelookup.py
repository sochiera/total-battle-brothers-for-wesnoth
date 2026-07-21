"""Unit tests for pure game-lookup helpers (tbbui.gamelookup)."""

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.unit import Unit
from tbbui.gamelookup import player_duchy


def test_player_duchy_returns_first_match_none_when_absent_or_none_id_no_mutation():
    """player_duchy(game, player_duchy_id) is None when id is None; else the
    first duchy in game.duchies with duchy_id == player_duchy_id; otherwise
    None. Pure: does not mutate game.
    """
    alpha = Duchy("alpha", Unit())
    beta = Duchy("beta", Unit())
    # second alpha-id cannot exist (GameState enforces unique ids); first match
    # is still the sole entry for that id in game.duchies order
    game = GameState((alpha, beta))
    duchies_before = game.duchies

    assert player_duchy(game, "alpha") is alpha
    assert player_duchy(game, "beta") is beta
    assert player_duchy(game, "missing") is None
    assert player_duchy(game, None) is None

    assert game.duchies is duchies_before
    assert game.duchies == duchies_before
