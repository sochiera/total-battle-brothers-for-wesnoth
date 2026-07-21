"""Tests for the settlement resource panel presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.building import FARM, MARKET
from tbb.resources import Resources
from tbb.settlement import Settlement
from tbb.unit import Unit
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


def test_render_settlement_panel_rows_carry_population_and_garrison():
    """Each row also carries data-population/-free/-garrison, and the visible
    text appends ``· populacja P (wolne F), garnizon N`` after the K22.1a
    resource text, leaving owner/wheat/gold attributes and text unchanged.
    """
    a = Region("A")
    world = WorldMap(
        [a],
        [],
        settlements={
            a: Settlement(
                "Keep A",
                population=5,
                occupied=2,
                owner_id="north",
                storage=Resources(wheat=5, gold=3),
                garrison=(Unit(), Unit()),
            ),
        },
    )

    xml = render_settlement_panel(world)
    root = ET.fromstring(xml)

    row_a = root.findall("div")[0]
    assert row_a.attrib["data-owner"] == "north"
    assert row_a.attrib["data-wheat"] == "5"
    assert row_a.attrib["data-gold"] == "3"
    assert row_a.attrib["data-population"] == "5"
    assert row_a.attrib["data-free"] == "3"
    assert row_a.attrib["data-garrison"] == "2"

    text = "".join(row_a.itertext())
    assert text.startswith(
        "Keep A (north): pszenica 5, złoto 3 · populacja 5 (wolne 3), garnizon 2"
    )


def test_render_settlement_panel_rows_carry_garrison_hp():
    """Each row also carries data-garrison-hp = sum of Unit.hp across the
    garrison, and the visible text appends `` · siła garnizonu: HP H`` after
    the K25.1a text, leaving the other attributes/text unchanged. Empty
    garrison yields data-garrison-hp="0".
    """
    a = Region("A")
    b = Region("B")
    world = WorldMap(
        [a, b],
        [(a, b)],
        settlements={
            a: Settlement(
                "Keep A",
                population=5,
                occupied=2,
                owner_id="north",
                storage=Resources(wheat=5, gold=3),
                garrison=(Unit(), Unit()),
            ),
            b: Settlement(
                "Keep B",
                population=1,
                owner_id=None,
                storage=Resources(wheat=0, gold=0),
            ),
        },
    )

    xml = render_settlement_panel(world)
    root = ET.fromstring(xml)

    row_a, row_b = root.findall("div")
    default_units = (Unit(), Unit())
    expected_hp = sum(u.hp for u in default_units)
    expected_attack = sum(u.damage for u in default_units)
    expected_defense = sum(u.defense for u in default_units)
    assert row_a.attrib["data-garrison-hp"] == str(expected_hp)
    text_a = "".join(row_a.itertext())
    assert text_a == (
        f"Keep A (north): pszenica 5, złoto 3 · populacja 5 (wolne 3), garnizon 2"
        f" · siła garnizonu: HP {expected_hp}"
        f", atak {expected_attack}, obrona {expected_defense}"
        f" · budynki: 0"
    )

    assert row_b.attrib["data-garrison-hp"] == "0"
    text_b = "".join(row_b.itertext())
    assert text_b == (
        "Keep B (—): pszenica 0, złoto 0 · populacja 1 (wolne 1), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 0"
    )


def test_render_settlement_panel_rows_carry_garrison_attack_and_defense():
    """Each row also carries data-garrison-attack = sum of Unit.damage and
    data-garrison-defense = sum of Unit.defense across the garrison, and the
    visible text appends `` , atak A, obrona D`` after the K25.2a
    `` · siła garnizonu: HP H`` text. Empty garrison yields "0" for both.
    """
    a = Region("A")
    b = Region("B")
    units = (Unit(equipment=3, experience=1), Unit(equipment=2))
    world = WorldMap(
        [a, b],
        [(a, b)],
        settlements={
            a: Settlement(
                "Keep A",
                population=5,
                occupied=2,
                owner_id="north",
                storage=Resources(wheat=5, gold=3),
                garrison=units,
            ),
            b: Settlement(
                "Keep B",
                population=1,
                owner_id=None,
                storage=Resources(wheat=0, gold=0),
            ),
        },
    )

    xml = render_settlement_panel(world)
    root = ET.fromstring(xml)

    row_a, row_b = root.findall("div")
    expected_attack = sum(u.damage for u in units)
    expected_defense = sum(u.defense for u in units)
    expected_hp = sum(u.hp for u in units)
    assert row_a.attrib["data-garrison-attack"] == str(expected_attack)
    assert row_a.attrib["data-garrison-defense"] == str(expected_defense)
    text_a = "".join(row_a.itertext())
    assert text_a == (
        f"Keep A (north): pszenica 5, złoto 3 · populacja 5 (wolne 3), garnizon 2"
        f" · siła garnizonu: HP {expected_hp}"
        f", atak {expected_attack}, obrona {expected_defense}"
        f" · budynki: 0"
    )

    assert row_b.attrib["data-garrison-attack"] == "0"
    assert row_b.attrib["data-garrison-defense"] == "0"
    text_b = "".join(row_b.itertext())
    assert text_b == (
        "Keep B (—): pszenica 0, złoto 0 · populacja 1 (wolne 1), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 0"
    )


def test_render_settlement_panel_marks_player_owned_row_when_duchy_id_given():
    """When ``player_duchy_id`` is given, rows whose ``owner_id`` matches it get
    ``data-player-owned=""``; other rows do not carry the attribute at all.
    """
    a = Region("A")
    b = Region("B")
    world = WorldMap(
        [a, b],
        [(a, b)],
        settlements={
            a: Settlement(
                "Keep A",
                population=1,
                owner_id="north",
                storage=Resources(wheat=5, gold=3),
            ),
            b: Settlement(
                "Keep B",
                population=1,
                owner_id="south",
                storage=Resources(wheat=0, gold=0),
            ),
        },
    )

    xml = render_settlement_panel(world, player_duchy_id="north")
    root = ET.fromstring(xml)

    row_a, row_b = root.findall("div")
    assert row_a.attrib["data-player-owned"] == ""
    assert "data-player-owned" not in row_b.attrib


def test_render_settlement_panel_rows_carry_active_buildings_count():
    """Each row also carries data-buildings = len(settlement.active_buildings),
    and the visible text appends `` · budynki: N`` after the K25.2b garrison
    strength text, leaving the other attributes/text unchanged. A settlement
    without buildings yields data-buildings="0".
    """
    a = Region("A")
    b = Region("B")
    world = WorldMap(
        [a, b],
        [(a, b)],
        settlements={
            a: Settlement(
                "Keep A",
                population=5,
                occupied=2,
                owner_id="north",
                storage=Resources(wheat=5, gold=3),
                garrison=(Unit(), Unit()),
                active_buildings=(FARM, MARKET),
            ),
            b: Settlement(
                "Keep B",
                population=1,
                owner_id=None,
                storage=Resources(wheat=0, gold=0),
            ),
        },
    )

    xml = render_settlement_panel(world)
    root = ET.fromstring(xml)

    row_a, row_b = root.findall("div")
    default_units = (Unit(), Unit())
    expected_hp = sum(u.hp for u in default_units)
    expected_attack = sum(u.damage for u in default_units)
    expected_defense = sum(u.defense for u in default_units)

    assert row_a.attrib["data-buildings"] == "2"
    text_a = "".join(row_a.itertext())
    assert text_a == (
        f"Keep A (north): pszenica 5, złoto 3 · populacja 5 (wolne 3), garnizon 2"
        f" · siła garnizonu: HP {expected_hp}"
        f", atak {expected_attack}, obrona {expected_defense}"
        f" · budynki: 2"
    )

    assert row_b.attrib["data-buildings"] == "0"
    text_b = "".join(row_b.itertext())
    assert text_b == (
        "Keep B (—): pszenica 0, złoto 0 · populacja 1 (wolne 1), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 0"
    )


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
