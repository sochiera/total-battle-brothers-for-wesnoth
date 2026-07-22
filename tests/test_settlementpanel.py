"""Tests for the settlement resource panel presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb import BARRACKS, SMITH
from tbb.building import FARM, MARKET
from tbb.resources import Resources
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.wound import BRUISE, MAIMED
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
        f" · ranni: 0"
        f" · trening: wstrzymany (brak Koszar)"
        f" · uzbrojenie: wstrzymane (brak Kuźni)"
        f" · produkcja/mies.: +0 pszenicy, +0 złota · konsumpcja: 5 pszenicy"
    )

    assert row_b.attrib["data-garrison-hp"] == "0"
    text_b = "".join(row_b.itertext())
    assert text_b == (
        "Keep B (—): pszenica 0, złoto 0 · populacja 1 (wolne 1), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 0"
        " · ranni: 0"
        " · trening: wstrzymany (brak Koszar)"
        " · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +0 pszenicy, +0 złota · konsumpcja: 1 pszenicy"
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
        f" · ranni: 0"
        f" · trening: wstrzymany (brak Koszar)"
        f" · uzbrojenie: wstrzymane (brak Kuźni)"
        f" · produkcja/mies.: +0 pszenicy, +0 złota · konsumpcja: 5 pszenicy"
    )

    assert row_b.attrib["data-garrison-attack"] == "0"
    assert row_b.attrib["data-garrison-defense"] == "0"
    text_b = "".join(row_b.itertext())
    assert text_b == (
        "Keep B (—): pszenica 0, złoto 0 · populacja 1 (wolne 1), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 0"
        " · ranni: 0"
        " · trening: wstrzymany (brak Koszar)"
        " · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +0 pszenicy, +0 złota · konsumpcja: 1 pszenicy"
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
        f" · budynki: 2 (Farm, Market)"
        f" · ranni: 0"
        f" · trening: wstrzymany (brak Koszar)"
        f" · uzbrojenie: wstrzymane (brak Kuźni)"
        f" · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 5 pszenicy"
    )

    assert row_b.attrib["data-buildings"] == "0"
    text_b = "".join(row_b.itertext())
    assert text_b == (
        "Keep B (—): pszenica 0, złoto 0 · populacja 1 (wolne 1), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 0"
        " · ranni: 0"
        " · trening: wstrzymany (brak Koszar)"
        " · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +0 pszenicy, +0 złota · konsumpcja: 1 pszenicy"
    )


def test_render_settlement_panel_rows_carry_active_building_names():
    """Each row also carries data-building-names = names of
    settlement.active_buildings joined by ", " in active_buildings order
    (empty -> ""), and the visible text appends `` (name1, name2)`` right
    after the K26.1a `` · budynki: N`` text when N>0, with no parens when
    N=0. Other attributes/text stay unchanged.
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

    assert row_a.attrib["data-building-names"] == "Farm, Market"
    text_a = "".join(row_a.itertext())
    assert text_a == (
        f"Keep A (north): pszenica 5, złoto 3 · populacja 5 (wolne 3), garnizon 2"
        f" · siła garnizonu: HP {expected_hp}"
        f", atak {expected_attack}, obrona {expected_defense}"
        f" · budynki: 2 (Farm, Market)"
        f" · ranni: 0"
        f" · trening: wstrzymany (brak Koszar)"
        f" · uzbrojenie: wstrzymane (brak Kuźni)"
        f" · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 5 pszenicy"
    )

    assert row_b.attrib["data-building-names"] == ""
    text_b = "".join(row_b.itertext())
    assert text_b == (
        "Keep B (—): pszenica 0, złoto 0 · populacja 1 (wolne 1), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 0"
        " · ranni: 0"
        " · trening: wstrzymany (brak Koszar)"
        " · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +0 pszenicy, +0 złota · konsumpcja: 1 pszenicy"
    )


def test_render_settlement_panel_rows_carry_garrison_wounded_count():
    """Each row also carries data-garrison-wounded = count of garrison units
    with a non-empty ``wounds`` tuple, and the visible text appends
    `` · ranni: W`` at the very end, after the K26.1b buildings suffix. Empty
    garrison yields data-garrison-wounded="0".
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
                garrison=(Unit(wounds=(BRUISE,)), Unit(wounds=(MAIMED,)), Unit()),
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
    garrison_units = (Unit(wounds=(BRUISE,)), Unit(wounds=(MAIMED,)), Unit())
    expected_hp = sum(u.hp for u in garrison_units)
    expected_attack = sum(u.damage for u in garrison_units)
    expected_defense = sum(u.defense for u in garrison_units)

    assert row_a.attrib["data-garrison-wounded"] == "2"
    text_a = "".join(row_a.itertext())
    assert text_a == (
        f"Keep A (north): pszenica 5, złoto 3 · populacja 5 (wolne 3), garnizon 3"
        f" · siła garnizonu: HP {expected_hp}"
        f", atak {expected_attack}, obrona {expected_defense}"
        f" · budynki: 2 (Farm, Market)"
        f" · ranni: 2"
        f" · trening: wstrzymany (brak Koszar)"
        f" · uzbrojenie: wstrzymane (brak Kuźni)"
        f" · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 5 pszenicy"
    )

    assert row_b.attrib["data-garrison-wounded"] == "0"
    text_b = "".join(row_b.itertext())
    assert text_b == (
        "Keep B (—): pszenica 0, złoto 0 · populacja 1 (wolne 1), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 0"
        " · ranni: 0"
        " · trening: wstrzymany (brak Koszar)"
        " · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +0 pszenicy, +0 złota · konsumpcja: 1 pszenicy"
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


def test_render_settlement_panel_rows_carry_training_ready_flag():
    """Each row carries data-training-ready="true" when BARRACKS is in
    active_buildings, else "false", placed immediately after
    data-garrison-wounded (before optional data-player-owned). Visible text is
    unchanged. Flag depends only on BARRACKS presence, not population/garrison.
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
                active_buildings=(FARM, BARRACKS, MARKET),
            ),
            b: Settlement(
                "Keep B",
                population=10,
                occupied=0,
                owner_id="south",
                storage=Resources(wheat=0, gold=0),
                garrison=(Unit(), Unit(), Unit()),
                active_buildings=(FARM, MARKET),
            ),
        },
    )

    xml = render_settlement_panel(world, player_duchy_id="north")
    root = ET.fromstring(xml)

    row_a, row_b = root.findall("div")
    assert row_a.attrib["data-training-ready"] == "true"
    assert row_b.attrib["data-training-ready"] == "false"

    # Attribute order: immediately after data-garrison-wounded; equip-ready
    # (K56.1a) then monthly economy attrs (K57.1a) + wheat-surplus (K57.2a)
    # before optional player-owned.
    assert (
        ' data-garrison-wounded="0" data-training-ready="true"'
        ' data-equip-ready="false" data-wheat-production="3"'
        ' data-gold-production="2" data-wheat-consumption="5"'
        ' data-wheat-surplus="false" data-player-owned=""'
    ) in xml
    assert (
        ' data-garrison-wounded="0" data-training-ready="false"'
        ' data-equip-ready="false" data-wheat-production="3"'
        ' data-gold-production="2" data-wheat-consumption="10"'
        ' data-wheat-surplus="false"'
    ) in xml
    # No-barracks row must not get true merely from larger garrison/population.
    assert 'data-settlement-row="B"' in xml
    assert row_b.attrib["data-garrison"] == "3"
    assert row_b.attrib["data-population"] == "10"

    garrison_a = (Unit(), Unit())
    expected_hp_a = sum(u.hp for u in garrison_a)
    expected_attack_a = sum(u.damage for u in garrison_a)
    expected_defense_a = sum(u.defense for u in garrison_a)
    text_a = "".join(row_a.itertext())
    assert text_a == (
        f"Keep A (north): pszenica 5, złoto 3 · populacja 5 (wolne 3), garnizon 2"
        f" · siła garnizonu: HP {expected_hp_a}"
        f", atak {expected_attack_a}, obrona {expected_defense_a}"
        f" · budynki: 3 (Farm, Barracks, Market)"
        f" · ranni: 0"
        f" · trening: gotowy"
        f" · uzbrojenie: wstrzymane (brak Kuźni)"
        f" · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 5 pszenicy"
    )

    garrison_b = (Unit(), Unit(), Unit())
    expected_hp_b = sum(u.hp for u in garrison_b)
    expected_attack_b = sum(u.damage for u in garrison_b)
    expected_defense_b = sum(u.defense for u in garrison_b)
    text_b = "".join(row_b.itertext())
    assert text_b == (
        f"Keep B (south): pszenica 0, złoto 0 · populacja 10 (wolne 10), garnizon 3"
        f" · siła garnizonu: HP {expected_hp_b}"
        f", atak {expected_attack_b}, obrona {expected_defense_b}"
        f" · budynki: 2 (Farm, Market)"
        f" · ranni: 0"
        f" · trening: wstrzymany (brak Koszar)"
        f" · uzbrojenie: wstrzymane (brak Kuźni)"
        f" · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 10 pszenicy"
    )


def test_render_settlement_panel_rows_append_training_ready_text_suffix():
    """Visible row text includes `` · trening: gotowy`` when BARRACKS is in
    active_buildings, else `` · trening: wstrzymany (brak Koszar)``, appended
    after the existing `` · ranni: W`` suffix (before equip readiness). The
    suffix matches data-training-ready on the same row (true ↔ gotowy,
    false ↔ wstrzymany).
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
                garrison=(Unit(wounds=(BRUISE,)), Unit()),
                active_buildings=(FARM, BARRACKS, MARKET),
            ),
            b: Settlement(
                "Keep B",
                population=1,
                owner_id="south",
                storage=Resources(wheat=0, gold=0),
                active_buildings=(FARM, MARKET),
            ),
        },
    )

    xml = render_settlement_panel(world)
    root = ET.fromstring(xml)

    row_a, row_b = root.findall("div")
    garrison_a = (Unit(wounds=(BRUISE,)), Unit())
    expected_hp_a = sum(u.hp for u in garrison_a)
    expected_attack_a = sum(u.damage for u in garrison_a)
    expected_defense_a = sum(u.defense for u in garrison_a)

    assert row_a.attrib["data-training-ready"] == "true"
    text_a = "".join(row_a.itertext())
    assert text_a == (
        f"Keep A (north): pszenica 5, złoto 3 · populacja 5 (wolne 3), garnizon 2"
        f" · siła garnizonu: HP {expected_hp_a}"
        f", atak {expected_attack_a}, obrona {expected_defense_a}"
        f" · budynki: 3 (Farm, Barracks, Market)"
        f" · ranni: 1"
        f" · trening: gotowy"
        f" · uzbrojenie: wstrzymane (brak Kuźni)"
        f" · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 5 pszenicy"
    )
    assert " · ranni: 1 · trening: gotowy" in text_a

    assert row_b.attrib["data-training-ready"] == "false"
    text_b = "".join(row_b.itertext())
    assert text_b == (
        "Keep B (south): pszenica 0, złoto 0 · populacja 1 (wolne 1), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 2 (Farm, Market)"
        " · ranni: 0"
        " · trening: wstrzymany (brak Koszar)"
        " · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 1 pszenicy"
    )
    assert " · ranni: 0 · trening: wstrzymany (brak Koszar)" in text_b


def test_render_settlement_panel_rows_carry_equip_ready_flag():
    """Each row carries data-equip-ready="true" when SMITH is in
    active_buildings, else "false", placed immediately after
    data-training-ready (before optional data-player-owned). Visible text
    includes the equip readiness suffix (K56.1b). Flag depends only on
    SMITH presence, not population/garrison/gold.
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
                active_buildings=(FARM, SMITH, MARKET),
            ),
            b: Settlement(
                "Keep B",
                population=10,
                occupied=0,
                owner_id="south",
                storage=Resources(wheat=0, gold=99),
                garrison=(Unit(), Unit(), Unit()),
                active_buildings=(FARM, BARRACKS, MARKET),
            ),
        },
    )

    xml = render_settlement_panel(world, player_duchy_id="north")
    root = ET.fromstring(xml)

    row_a, row_b = root.findall("div")
    assert row_a.attrib["data-equip-ready"] == "true"
    assert row_b.attrib["data-equip-ready"] == "false"

    # Attribute order: immediately after data-training-ready; monthly economy
    # attrs (K57.1a) + wheat-surplus (K57.2a) sit between equip-ready and
    # optional player-owned.
    assert (
        ' data-training-ready="false" data-equip-ready="true"'
        ' data-wheat-production="3" data-gold-production="2"'
        ' data-wheat-consumption="5" data-wheat-surplus="false"'
        ' data-player-owned=""'
        in xml
    )
    assert (
        ' data-training-ready="true" data-equip-ready="false"'
        ' data-wheat-production="3" data-gold-production="2"'
        ' data-wheat-consumption="10" data-wheat-surplus="false"'
        in xml
    )
    # No-smith row must not get true merely from larger garrison/population/gold.
    assert 'data-settlement-row="B"' in xml
    assert row_b.attrib["data-garrison"] == "3"
    assert row_b.attrib["data-population"] == "10"
    assert row_b.attrib["data-gold"] == "99"

    garrison_a = (Unit(), Unit())
    expected_hp_a = sum(u.hp for u in garrison_a)
    expected_attack_a = sum(u.damage for u in garrison_a)
    expected_defense_a = sum(u.defense for u in garrison_a)
    text_a = "".join(row_a.itertext())
    assert text_a == (
        f"Keep A (north): pszenica 5, złoto 3 · populacja 5 (wolne 3), garnizon 2"
        f" · siła garnizonu: HP {expected_hp_a}"
        f", atak {expected_attack_a}, obrona {expected_defense_a}"
        f" · budynki: 3 (Farm, Smith, Market)"
        f" · ranni: 0"
        f" · trening: wstrzymany (brak Koszar)"
        f" · uzbrojenie: gotowe"
        f" · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 5 pszenicy"
    )
    assert text_a.endswith(
        " · trening: wstrzymany (brak Koszar) · uzbrojenie: gotowe"
        " · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 5 pszenicy"
    )

    garrison_b = (Unit(), Unit(), Unit())
    expected_hp_b = sum(u.hp for u in garrison_b)
    expected_attack_b = sum(u.damage for u in garrison_b)
    expected_defense_b = sum(u.defense for u in garrison_b)
    text_b = "".join(row_b.itertext())
    assert text_b == (
        f"Keep B (south): pszenica 0, złoto 99 · populacja 10 (wolne 10), garnizon 3"
        f" · siła garnizonu: HP {expected_hp_b}"
        f", atak {expected_attack_b}, obrona {expected_defense_b}"
        f" · budynki: 3 (Farm, Barracks, Market)"
        f" · ranni: 0"
        f" · trening: gotowy"
        f" · uzbrojenie: wstrzymane (brak Kuźni)"
        f" · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 10 pszenicy"
    )
    assert text_b.endswith(
        " · trening: gotowy · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 10 pszenicy"
    )


def test_render_settlement_panel_rows_append_equip_ready_text_suffix():
    """Visible row text ends with `` · uzbrojenie: gotowe`` when SMITH is in
    active_buildings, else `` · uzbrojenie: wstrzymane (brak Kuźni)``, appended
    after the existing `` · trening: …`` suffix. The suffix matches
    data-equip-ready on the same row (true ↔ gotowe, false ↔ wstrzymane).
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
                garrison=(Unit(wounds=(BRUISE,)), Unit()),
                active_buildings=(FARM, SMITH, MARKET),
            ),
            b: Settlement(
                "Keep B",
                population=1,
                owner_id="south",
                storage=Resources(wheat=0, gold=0),
                active_buildings=(FARM, BARRACKS, MARKET),
            ),
        },
    )

    xml = render_settlement_panel(world)
    root = ET.fromstring(xml)

    row_a, row_b = root.findall("div")
    garrison_a = (Unit(wounds=(BRUISE,)), Unit())
    expected_hp_a = sum(u.hp for u in garrison_a)
    expected_attack_a = sum(u.damage for u in garrison_a)
    expected_defense_a = sum(u.defense for u in garrison_a)

    assert row_a.attrib["data-equip-ready"] == "true"
    text_a = "".join(row_a.itertext())
    assert text_a == (
        f"Keep A (north): pszenica 5, złoto 3 · populacja 5 (wolne 3), garnizon 2"
        f" · siła garnizonu: HP {expected_hp_a}"
        f", atak {expected_attack_a}, obrona {expected_defense_a}"
        f" · budynki: 3 (Farm, Smith, Market)"
        f" · ranni: 1"
        f" · trening: wstrzymany (brak Koszar)"
        f" · uzbrojenie: gotowe"
        f" · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 5 pszenicy"
    )
    assert text_a.endswith(
        " · trening: wstrzymany (brak Koszar) · uzbrojenie: gotowe"
        " · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 5 pszenicy"
    )

    assert row_b.attrib["data-equip-ready"] == "false"
    text_b = "".join(row_b.itertext())
    assert text_b == (
        "Keep B (south): pszenica 0, złoto 0 · populacja 1 (wolne 1), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 3 (Farm, Barracks, Market)"
        " · ranni: 0"
        " · trening: gotowy"
        " · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 1 pszenicy"
    )
    assert text_b.endswith(
        " · trening: gotowy · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 1 pszenicy"
    )


def test_render_settlement_panel_rows_carry_monthly_economy_attributes():
    """Each row carries data-wheat-production / data-gold-production /
    data-wheat-consumption from settlement.production / .consumption (no world
    mutation, no tick_economy), immediately after data-equip-ready and before
    optional data-player-owned. Settlement without active buildings has
    production 0/0 and consumption equal to population. Visible text includes
    the K57.1b economy suffix consistent with the attributes.
    """
    a = Region("A")
    b = Region("B")
    settlement_a = Settlement(
        "Keep A",
        population=5,
        occupied=2,
        owner_id="north",
        storage=Resources(wheat=5, gold=3),
        garrison=(Unit(), Unit()),
        active_buildings=(FARM, MARKET),
    )
    settlement_b = Settlement(
        "Keep B",
        population=4,
        owner_id="south",
        storage=Resources(wheat=10, gold=7),
    )
    world = WorldMap(
        [a, b],
        [(a, b)],
        settlements={a: settlement_a, b: settlement_b},
    )
    settlements_before = world.settlements
    storage_a_before = settlement_a.storage
    storage_b_before = settlement_b.storage

    assert settlement_a.production == Resources(wheat=3, gold=2)
    assert settlement_a.consumption == Resources(wheat=5, gold=0)
    assert settlement_b.production == Resources(wheat=0, gold=0)
    assert settlement_b.consumption == Resources(wheat=4, gold=0)

    xml = render_settlement_panel(world, player_duchy_id="north")
    root = ET.fromstring(xml)

    row_a, row_b = root.findall("div")
    assert row_a.attrib["data-wheat-production"] == "3"
    assert row_a.attrib["data-gold-production"] == "2"
    assert row_a.attrib["data-wheat-consumption"] == "5"

    assert row_b.attrib["data-wheat-production"] == "0"
    assert row_b.attrib["data-gold-production"] == "0"
    assert row_b.attrib["data-wheat-consumption"] == "4"

    # Attribute order: after data-equip-ready; wheat-surplus (K57.2a) before
    # optional data-player-owned.
    assert (
        ' data-equip-ready="false" data-wheat-production="3"'
        ' data-gold-production="2" data-wheat-consumption="5"'
        ' data-wheat-surplus="false" data-player-owned=""'
    ) in xml
    assert (
        ' data-equip-ready="false" data-wheat-production="0"'
        ' data-gold-production="0" data-wheat-consumption="4"'
        ' data-wheat-surplus="false"'
    ) in xml
    assert 'data-settlement-row="B" data-owner="south"' in xml
    assert 'data-player-owned' not in row_b.attrib

    # Pure: no mutation of world / storage (no tick_economy side effects).
    assert world.settlements == settlements_before
    assert settlement_a.storage == storage_a_before
    assert settlement_b.storage == storage_b_before

    garrison_a = (Unit(), Unit())
    expected_hp_a = sum(u.hp for u in garrison_a)
    expected_attack_a = sum(u.damage for u in garrison_a)
    expected_defense_a = sum(u.defense for u in garrison_a)
    text_a = "".join(row_a.itertext())
    assert text_a == (
        f"Keep A (north): pszenica 5, złoto 3 · populacja 5 (wolne 3), garnizon 2"
        f" · siła garnizonu: HP {expected_hp_a}"
        f", atak {expected_attack_a}, obrona {expected_defense_a}"
        f" · budynki: 2 (Farm, Market)"
        f" · ranni: 0"
        f" · trening: wstrzymany (brak Koszar)"
        f" · uzbrojenie: wstrzymane (brak Kuźni)"
        f" · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 5 pszenicy"
    )

    text_b = "".join(row_b.itertext())
    assert text_b == (
        "Keep B (south): pszenica 10, złoto 7 · populacja 4 (wolne 4), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 0"
        " · ranni: 0"
        " · trening: wstrzymany (brak Koszar)"
        " · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +0 pszenicy, +0 złota · konsumpcja: 4 pszenicy"
    )


def test_render_settlement_panel_rows_append_monthly_economy_text_suffix():
    """Visible row text appends
    `` · produkcja/mies.: +Pw pszenicy, +Pg złota · konsumpcja: Cw pszenicy``
    immediately after the equip-readiness suffix (`` · uzbrojenie: …``). Numbers
    match ``data-wheat-production`` / ``data-gold-production`` /
    ``data-wheat-consumption`` on the same row (and settlement.production /
    .consumption). Machine attributes and their order stay as in K57.1a.
    """
    a = Region("A")
    b = Region("B")
    settlement_a = Settlement(
        "Keep A",
        population=5,
        occupied=2,
        owner_id="north",
        storage=Resources(wheat=5, gold=3),
        garrison=(Unit(), Unit()),
        active_buildings=(FARM, MARKET),
    )
    settlement_b = Settlement(
        "Keep B",
        population=4,
        owner_id="south",
        storage=Resources(wheat=10, gold=7),
    )
    world = WorldMap(
        [a, b],
        [(a, b)],
        settlements={a: settlement_a, b: settlement_b},
    )

    assert settlement_a.production == Resources(wheat=3, gold=2)
    assert settlement_a.consumption == Resources(wheat=5, gold=0)
    assert settlement_b.production == Resources(wheat=0, gold=0)
    assert settlement_b.consumption == Resources(wheat=4, gold=0)

    xml = render_settlement_panel(world)
    root = ET.fromstring(xml)

    row_a, row_b = root.findall("div")
    assert row_a.attrib["data-wheat-production"] == "3"
    assert row_a.attrib["data-gold-production"] == "2"
    assert row_a.attrib["data-wheat-consumption"] == "5"
    assert row_b.attrib["data-wheat-production"] == "0"
    assert row_b.attrib["data-gold-production"] == "0"
    assert row_b.attrib["data-wheat-consumption"] == "4"

    # Attribute order unchanged vs K57.1a.
    assert (
        ' data-equip-ready="false" data-wheat-production="3"'
        ' data-gold-production="2" data-wheat-consumption="5"'
    ) in xml
    assert (
        ' data-equip-ready="false" data-wheat-production="0"'
        ' data-gold-production="0" data-wheat-consumption="4"'
    ) in xml

    garrison_a = (Unit(), Unit())
    expected_hp_a = sum(u.hp for u in garrison_a)
    expected_attack_a = sum(u.damage for u in garrison_a)
    expected_defense_a = sum(u.defense for u in garrison_a)
    text_a = "".join(row_a.itertext())
    assert text_a == (
        f"Keep A (north): pszenica 5, złoto 3 · populacja 5 (wolne 3), garnizon 2"
        f" · siła garnizonu: HP {expected_hp_a}"
        f", atak {expected_attack_a}, obrona {expected_defense_a}"
        f" · budynki: 2 (Farm, Market)"
        f" · ranni: 0"
        f" · trening: wstrzymany (brak Koszar)"
        f" · uzbrojenie: wstrzymane (brak Kuźni)"
        f" · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 5 pszenicy"
    )
    assert text_a.endswith(
        " · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +3 pszenicy, +2 złota · konsumpcja: 5 pszenicy"
    )

    text_b = "".join(row_b.itertext())
    assert text_b == (
        "Keep B (south): pszenica 10, złoto 7 · populacja 4 (wolne 4), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 0"
        " · ranni: 0"
        " · trening: wstrzymany (brak Koszar)"
        " · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +0 pszenicy, +0 złota · konsumpcja: 4 pszenicy"
    )
    assert text_b.endswith(
        " · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +0 pszenicy, +0 złota · konsumpcja: 4 pszenicy"
    )


def test_render_settlement_panel_rows_carry_wheat_surplus_flag():
    """Each row carries data-wheat-surplus="true" when
    settlement.production.wheat >= settlement.consumption.wheat, else "false",
    placed immediately after data-wheat-consumption (before optional
    data-player-owned). Settlement without Farm and with positive population
    yields "false". Visible text is byte-for-byte the K57.1b economy row (no
    new surplus/deficit suffix).
    """
    a = Region("A")
    b = Region("B")
    settlement_a = Settlement(
        "Keep A",
        population=1,
        owner_id="north",
        storage=Resources(wheat=5, gold=3),
        active_buildings=(FARM,),
    )
    settlement_b = Settlement(
        "Keep B",
        population=4,
        owner_id="south",
        storage=Resources(wheat=10, gold=7),
    )
    world = WorldMap(
        [a, b],
        [(a, b)],
        settlements={a: settlement_a, b: settlement_b},
    )

    assert settlement_a.production.wheat >= settlement_a.consumption.wheat
    assert settlement_a.production == Resources(wheat=3, gold=0)
    assert settlement_a.consumption == Resources(wheat=1, gold=0)
    assert settlement_b.production.wheat < settlement_b.consumption.wheat
    assert settlement_b.production == Resources(wheat=0, gold=0)
    assert settlement_b.consumption == Resources(wheat=4, gold=0)

    xml = render_settlement_panel(world, player_duchy_id="north")
    root = ET.fromstring(xml)

    row_a, row_b = root.findall("div")
    assert row_a.attrib["data-wheat-surplus"] == "true"
    assert row_b.attrib["data-wheat-surplus"] == "false"

    # Attribute order: immediately after data-wheat-consumption, before optional
    # data-player-owned.
    assert (
        ' data-wheat-production="3" data-gold-production="0"'
        ' data-wheat-consumption="1" data-wheat-surplus="true"'
        ' data-player-owned=""'
    ) in xml
    assert (
        ' data-wheat-production="0" data-gold-production="0"'
        ' data-wheat-consumption="4" data-wheat-surplus="false"'
    ) in xml
    assert "data-player-owned" not in row_b.attrib

    text_a = "".join(row_a.itertext())
    assert text_a == (
        "Keep A (north): pszenica 5, złoto 3 · populacja 1 (wolne 1), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 1 (Farm)"
        " · ranni: 0"
        " · trening: wstrzymany (brak Koszar)"
        " · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +3 pszenicy, +0 złota · konsumpcja: 1 pszenicy"
    )
    assert "bilans" not in text_a
    assert "nadwyżka" not in text_a
    assert "deficyt" not in text_a

    text_b = "".join(row_b.itertext())
    assert text_b == (
        "Keep B (south): pszenica 10, złoto 7 · populacja 4 (wolne 4), garnizon 0"
        " · siła garnizonu: HP 0, atak 0, obrona 0"
        " · budynki: 0"
        " · ranni: 0"
        " · trening: wstrzymany (brak Koszar)"
        " · uzbrojenie: wstrzymane (brak Kuźni)"
        " · produkcja/mies.: +0 pszenicy, +0 złota · konsumpcja: 4 pszenicy"
    )
    assert "bilans" not in text_b
    assert "nadwyżka" not in text_b
    assert "deficyt" not in text_b
