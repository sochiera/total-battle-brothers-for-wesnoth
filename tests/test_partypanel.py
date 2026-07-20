"""Tests for the party strength panel presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.party import Party
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.partypanel import render_party_panel


def test_render_party_panel_rows_match_parties_in_region_order():
    """One row per region with a party, in ``world.regions`` order; region
    without a party is skipped. Each row carries data-owner/-size attributes
    and matching visible text. Pure: does not mutate ``world``.
    """
    a = Region("A")
    b = Region("B")
    c = Region("C")
    world = WorldMap(
        [a, b, c],
        [(a, b), (b, c)],
        parties={
            a: Party(hero=Unit(), units=(Unit(), Unit()), owner_id="north"),
            c: Party(hero=Unit(), units=(), owner_id=None),
        },
    )
    parties_before = world.parties

    xml = render_party_panel(world)
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-party-panel") == ""

    rows = root.findall("div")
    assert len(rows) == 2

    row_a, row_c = rows
    assert row_a.attrib["data-party-row"] == "A"
    assert row_a.attrib["data-owner"] == "north"
    assert row_a.attrib["data-size"] == "2"
    assert "A (north): bohater + 2 podkomendnych" in "".join(row_a.itertext())

    assert row_c.attrib["data-party-row"] == "C"
    assert row_c.attrib["data-owner"] == ""
    assert row_c.attrib["data-size"] == "0"
    assert "C (—): bohater + 0 podkomendnych" in "".join(row_c.itertext())

    assert world.parties == parties_before


def test_render_party_panel_marks_player_owned_row_when_duchy_id_given():
    """When ``player_duchy_id`` is given, rows whose ``owner_id`` matches it get
    ``data-player-owned=""``; other rows do not carry the attribute at all.
    """
    a = Region("A")
    b = Region("B")
    world = WorldMap(
        [a, b],
        [(a, b)],
        parties={
            a: Party(hero=Unit(), units=(), owner_id="north"),
            b: Party(hero=Unit(), units=(), owner_id="south"),
        },
    )

    xml = render_party_panel(world, player_duchy_id="north")
    root = ET.fromstring(xml)

    row_a, row_b = root.findall("div")
    assert row_a.attrib["data-player-owned"] == ""
    assert "data-player-owned" not in row_b.attrib


def test_render_party_panel_empty_root_when_no_parties():
    """A world with regions but no parties at all yields a bare, childless
    ``<div data-party-panel="">`` root (no rows).
    """
    a = Region("A")
    b = Region("B")
    world = WorldMap([a, b], [(a, b)])

    xml = render_party_panel(world)
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-party-panel") == ""
    assert root.findall("div") == []
    assert list(root) == []
