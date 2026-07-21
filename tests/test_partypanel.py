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


def test_render_party_panel_row_carries_hp_sum_and_text_suffix():
    """``data-hp`` is the sum of ``Unit.hp`` over hero and all party units, and
    the visible text gains a matching `` · siła: HP H`` suffix.
    """
    a = Region("A")
    world = WorldMap(
        [a],
        [],
        parties={
            a: Party(
                hero=Unit(training=5),
                units=(Unit(training=2), Unit(training=0)),
                owner_id="north",
            ),
        },
    )

    xml = render_party_panel(world)
    root = ET.fromstring(xml)

    row_a = root.findall("div")[0]
    expected_hp = (10 + 5) + (10 + 2) + (10 + 0)
    assert row_a.attrib["data-hp"] == str(expected_hp)
    assert (
        f"A (north): bohater + 2 podkomendnych · siła: HP {expected_hp}"
        in "".join(row_a.itertext())
    )


def test_render_party_panel_row_carries_attack_and_defense_sums_and_text_suffix():
    """``data-attack`` is the sum of ``Unit.damage`` and ``data-defense`` the sum
    of ``Unit.defense`` over hero and all party units, and the visible text
    gains a matching ``, atak A, obrona D`` suffix after the HP suffix.
    """
    a = Region("A")
    world = WorldMap(
        [a],
        [],
        parties={
            a: Party(
                hero=Unit(equipment=3, experience=1),
                units=(Unit(equipment=2, experience=0), Unit(equipment=1, experience=4)),
                owner_id="north",
            ),
        },
    )

    xml = render_party_panel(world)
    root = ET.fromstring(xml)

    row_a = root.findall("div")[0]
    hero = Unit(equipment=3, experience=1)
    u1 = Unit(equipment=2, experience=0)
    u2 = Unit(equipment=1, experience=4)
    expected_attack = hero.damage + u1.damage + u2.damage
    expected_defense = hero.defense + u1.defense + u2.defense
    expected_hp = hero.hp + u1.hp + u2.hp
    assert row_a.attrib["data-attack"] == str(expected_attack)
    assert row_a.attrib["data-defense"] == str(expected_defense)
    assert (
        f"A (north): bohater + 2 podkomendnych · siła: HP {expected_hp}"
        f", atak {expected_attack}, obrona {expected_defense}"
        in "".join(row_a.itertext())
    )


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
