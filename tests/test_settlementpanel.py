"""Tests for the settlement resource panel presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.resources import Resources
from tbb.settlement import Settlement
from tbb.world import Region, WorldMap
from tbbui.settlementpanel import render_settlement_panel


def test_render_settlement_panel_rows_match_settlements_in_region_order():
    """One row per settlement region, in ``world.regions`` order; region without a
    settlement is skipped; each row carries data-owner/-wheat/-gold attributes
    and matching visible text. Pure: does not mutate ``world``.
    """
    a = Region("A")
    b = Region("B")
    c = Region("C")
    world = WorldMap(
        [a, b, c],
        [(a, b), (b, c)],
        settlements={
            a: Settlement(
                "Keep A",
                population=1,
                owner_id="north",
                storage=Resources(wheat=5, gold=3),
            ),
            c: Settlement(
                "Keep C",
                population=1,
                owner_id=None,
                storage=Resources(wheat=0, gold=0),
            ),
        },
    )
    settlements_before = world.settlements

    xml = render_settlement_panel(world)
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-settlement-panel") == ""

    rows = root.findall("div")
    assert len(rows) == 2

    row_a, row_c = rows
    assert row_a.attrib["data-settlement-row"] == "A"
    assert row_a.attrib["data-owner"] == "north"
    assert row_a.attrib["data-wheat"] == "5"
    assert row_a.attrib["data-gold"] == "3"
    assert "Keep A (north): pszenica 5, złoto 3" in "".join(row_a.itertext())

    assert row_c.attrib["data-settlement-row"] == "C"
    assert row_c.attrib["data-owner"] == ""
    assert row_c.attrib["data-wheat"] == "0"
    assert row_c.attrib["data-gold"] == "0"
    assert "Keep C (—): pszenica 0, złoto 0" in "".join(row_c.itertext())

    assert world.settlements == settlements_before


def test_render_settlement_panel_empty_root_when_no_settlements():
    """A world with regions but no settlements at all yields a bare, childless
    ``<div data-settlement-panel="">`` root (no rows).
    """
    a = Region("A")
    b = Region("B")
    world = WorldMap([a, b], [(a, b)])

    xml = render_settlement_panel(world)
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-settlement-panel") == ""
    assert root.findall("div") == []
    assert list(root) == []
