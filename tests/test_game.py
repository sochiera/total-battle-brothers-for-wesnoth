"""Tests for immutable game-over state across duchies."""

from dataclasses import FrozenInstanceError

import pytest

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.unit import Unit


def test_two_contenders_keep_game_running_in_input_order():
    north = Duchy("north", Unit())
    south = Duchy("south", Unit())
    game = GameState([north, south])

    assert game.contenders == (north, south)
    assert game.is_over is False
    assert game.winner is None


def test_only_undefeated_duchy_wins():
    defeated_north = Duchy("north", None)
    south = Duchy("south", Unit())
    defeated_west = Duchy("west", None)
    game = GameState([defeated_north, south, defeated_west])

    assert game.contenders == (south,)
    assert game.is_over is True
    assert game.winner is south


def test_all_defeated_ends_without_winner():
    game = GameState([Duchy("north", None), Duchy("south", None)])

    assert game.contenders == ()
    assert game.is_over is True
    assert game.winner is None


def test_rejects_repeated_duchy_identifier():
    with pytest.raises(ValueError):
        GameState([Duchy("north", Unit()), Duchy("north", Unit())])


def test_rejects_non_duchy_member():
    with pytest.raises(TypeError):
        GameState([Duchy("north", Unit()), object()])


def test_copies_input_and_is_frozen():
    north = Duchy("north", Unit())
    source = [north]
    game = GameState(source)
    source.append(Duchy("south", Unit()))

    assert game.duchies == (north,)
    assert game.contenders == (north,)
    assert game.winner is north
    with pytest.raises((FrozenInstanceError, AttributeError)):
        game.duchies = ()


def test_equal_inputs_produce_deterministic_queries():
    duchies = [Duchy("north", Unit()), Duchy("south", None)]
    first = GameState(duchies)
    second = GameState(duchies)

    assert first.contenders == second.contenders
    assert first.is_over == second.is_over
    assert first.winner == second.winner
