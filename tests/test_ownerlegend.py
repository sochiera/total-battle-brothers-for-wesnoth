"""Tests for the owner-color legend presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.party import Party
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.ownerlegend import render_owner_legend
from tbbui.palette import owner_palette


def test_render_owner_legend_rows_match_owner_palette_order_and_colors():
    """One row per owner_palette(world) entry, in that order; each row carries
    data-owner/data-color matching the palette and visible text
    ``<owner_id>: <kolor>``. Pure: does not mutate ``world``.
    """
    a = Region("A")
    b = Region("B")
    c = Region("C")
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
        },
    )
    regions_before = world.regions
    settlements_before = world.settlements
    parties_before = world.parties

    palette = owner_palette(world)
    xml = render_owner_legend(world)
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-owner-legend") == ""

    rows = root.findall("div")
    assert len(rows) == len(palette) == 3

    for row, (owner_id, color) in zip(rows, palette.items()):
        assert row.attrib["data-owner-legend-row"] == owner_id
        assert row.attrib["data-owner"] == owner_id
        assert row.attrib["data-color"] == color
        assert "".join(row.itertext()) == f"{owner_id}: {color}"

    assert world.regions == regions_before
    assert world.settlements == settlements_before
    assert world.parties == parties_before


def test_render_owner_legend_marks_player_row_when_duchy_id_given():
    """When ``player_duchy_id`` is given, the row whose ``owner_id`` matches
    it gets ``data-player-owner=""`` and a visible ``» `` prefix; other rows
    are unaffected.
    """
    a = Region("A")
    b = Region("B")
    world = WorldMap(
        [a, b],
        [(a, b)],
        settlements={
            a: Settlement("Keep A", population=1, owner_id="north"),
            b: Settlement("Keep B", population=1, owner_id="south"),
        },
    )

    xml = render_owner_legend(world, player_duchy_id="south")
    root = ET.fromstring(xml)

    rows = root.findall("div")
    row_north = next(r for r in rows if r.attrib["data-owner"] == "north")
    row_south = next(r for r in rows if r.attrib["data-owner"] == "south")

    assert "data-player-owner" not in row_north.attrib
    assert "".join(row_north.itertext()) == "north: " + row_north.attrib["data-color"]

    assert row_south.attrib["data-player-owner"] == ""
    assert "".join(row_south.itertext()) == "» south: " + row_south.attrib["data-color"]


def test_render_owner_legend_empty_root_when_no_owners():
    """A world with no owned settlements/parties yields a bare, childless
    ``<div data-owner-legend="">`` root (no rows).
    """
    a = Region("A")
    world = WorldMap([a], [])

    xml = render_owner_legend(world)
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-owner-legend") == ""
    assert list(root) == []
