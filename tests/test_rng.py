"""Tests for the deterministic, isolated random number generator."""

import random

from tbb import Rng


def test_same_seed_same_sequence():
    first = Rng(42)
    second = Rng(42)

    first_results = [first.randint(1, 100) for _ in range(5)] + [
        first.chance(0.4) for _ in range(5)
    ]
    second_results = [second.randint(1, 100) for _ in range(5)] + [
        second.chance(0.4) for _ in range(5)
    ]

    assert first_results == second_results


def test_different_seed_differs():
    first = Rng(1)
    second = Rng(2)

    assert [first.randint(1, 100) for _ in range(10)] != [
        second.randint(1, 100) for _ in range(10)
    ]


def test_randint_bounds():
    rng = Rng(42)
    results = [rng.randint(1, 6) for _ in range(200)]

    assert all(1 <= result <= 6 for result in results)
    assert 1 in results
    assert 6 in results
    assert rng.randint(5, 5) == 5


def test_chance_edges():
    rng = Rng(42)

    assert all(rng.chance(0.0) is False for _ in range(20))
    assert all(rng.chance(1.0) is True for _ in range(20))


def test_chance_deterministic():
    first = Rng(123)
    second = Rng(123)

    assert [first.chance(0.35) for _ in range(20)] == [
        second.chance(0.35) for _ in range(20)
    ]


def test_isolated_from_global_random():
    baseline = Rng(99)
    disturbed = Rng(99)
    baseline_results = []
    disturbed_results = []

    for _ in range(10):
        baseline_results.append((baseline.randint(1, 20), baseline.chance(0.5)))
        random.random()
        disturbed_results.append((disturbed.randint(1, 20), disturbed.chance(0.5)))
        random.random()

    assert disturbed_results == baseline_results


def test_state_does_not_mutate_generator():
    rng = Rng(7)
    for _ in range(3):
        rng.randint(1, 100)

    first = rng.state()
    second = rng.state()

    assert first == second


def test_from_state_reproduces_sequence_after_rolls():
    r = Rng(7)
    for _ in range(5):
        r.randint(1, 100)
    r.chance(0.4)

    restored = Rng.from_state(r.state())

    expected = [r.randint(1, 100) for _ in range(10)]
    actual = [restored.randint(1, 100) for _ in range(10)]

    assert actual == expected
