"""Tests for deterministic owner color palette (tbbui presentation layer)."""

from tbb.party import Party
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.palette import OWNER_COLORS, owner_palette


def test_owner_palette_first_occurrence_order_distinct_colors_deterministic():
    """≥2 owners: first-occurrence order (settlement then party per region), distinct, pure.

    Scan order is ``world.regions``; within a region settlement is considered
    before party. Only distinct non-empty ``owner_id`` values enter the map.
    Fixture expected key order: north → south → east.
    """
    a = Region("A")
    b = Region("B")
    c = Region("C")
    # A: settlement "north" (1st), party "south" (2nd)
    # B: settlement "south" (seen), party "east" (3rd)
    # C: unowned settlement, party "north" (seen)
    world = WorldMap(
        [a, b, c],
        [(a, b), (b, c)],
        settlements={
            a: Settlement("Keep A", population=1, owner_id="north"),
            b: Settlement("Keep B", population=1, owner_id="south"),
            c: Settlement("Keep C", population=1, owner_id=None),
        },
        parties={
            a: Party(Unit(), owner_id="south"),
            b: Party(Unit(), owner_id="east"),
            c: Party(Unit(), owner_id="north"),
        },
    )
    regions_before = world.regions
    settlements_before = world.settlements
    parties_before = world.parties

    palette = owner_palette(world)

    assert isinstance(palette, dict)
    assert list(palette.keys()) == ["north", "south", "east"]
    assert len(set(palette.values())) == 3
    assert all(isinstance(color, str) and color for color in palette.values())

    again = owner_palette(world)
    assert again == palette
    assert list(again.keys()) == list(palette.keys())

    assert world.regions is regions_before
    assert world.settlements is settlements_before
    assert world.parties is parties_before
    assert world.regions == regions_before
    assert world.settlements == settlements_before
    assert world.parties == parties_before


def test_owner_palette_cycles_when_more_owners_than_colors():
    """More distinct owners than OWNER_COLORS wraps cyclically (index i % n)."""
    n = len(OWNER_COLORS)
    assert n >= 1
    # One region per owner so first-occurrence order is owner_0 … owner_{n}.
    regions = [Region(f"R{i}") for i in range(n + 1)]
    connections = [(regions[i], regions[i + 1]) for i in range(n)]
    settlements = {
        regions[i]: Settlement(f"Keep {i}", population=1, owner_id=f"owner_{i}")
        for i in range(n + 1)
    }
    world = WorldMap(regions, connections, settlements=settlements)

    palette = owner_palette(world)

    assert list(palette.keys()) == [f"owner_{i}" for i in range(n + 1)]
    for i in range(n + 1):
        assert palette[f"owner_{i}"] == OWNER_COLORS[i % n]
    # Wrap: last owner reuses first color; first n colors stay unique.
    assert palette[f"owner_{n}"] == OWNER_COLORS[0]
    assert palette["owner_0"] == OWNER_COLORS[0]
    assert len({palette[f"owner_{i}"] for i in range(n)}) == n
