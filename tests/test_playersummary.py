"""Tests for the player duchy economy summary presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.building import FARM, MARKET
from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.resources import Resources
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbbui.playersummary import render_player_summary
from tbbui.unitstrength import combat_totals


def test_render_player_summary_aggregates_duchy_economy_and_is_pure():
    """When ``player_duchy_id`` matches a duchy in ``game.duchies``, the root is
    ``<div data-player-summary="">`` with ``data-settlements`` / ``data-parties``
    / ``data-gold`` / ``data-wheat`` (counts and storage sums over that duchy),
    combat attrs from ``combat_totals`` over parties, and matching visible text.
    Pure: does not mutate ``game``.
    """
    s1 = Settlement(
        "Keep A",
        population=1,
        owner_id="north",
        storage=Resources(wheat=5, gold=3),
    )
    s2 = Settlement(
        "Keep B",
        population=1,
        owner_id="north",
        storage=Resources(wheat=2, gold=7),
    )
    hero = Unit()
    party = Party(hero=hero, units=(), owner_id="north")
    other = Settlement(
        "South Keep",
        population=1,
        owner_id="south",
        storage=Resources(wheat=99, gold=99),
    )
    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(s1, s2),
                parties=(party,),
            ),
            Duchy(
                "south",
                Unit(),
                settlements=(other,),
                parties=(),
            ),
        )
    )
    duchies_before = game.duchies
    expected_hp, expected_attack, expected_defense = combat_totals((hero,))

    xml = render_player_summary(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-player-summary") == ""
    assert root.attrib["data-settlements"] == "2"
    assert root.attrib["data-parties"] == "1"
    assert root.attrib["data-gold"] == "10"
    assert root.attrib["data-wheat"] == "7"
    assert root.attrib["data-hp"] == str(expected_hp)
    assert root.attrib["data-attack"] == str(expected_attack)
    assert root.attrib["data-defense"] == str(expected_defense)
    assert "".join(root.itertext()) == (
        "Twoje księstwo: osady 2, oddziały 1 · pszenica 7, złoto 10"
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}"
        f" · produkcja/mies.: +0 pszenicy · konsumpcja: 2 pszenicy"
    )

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before


def test_render_player_summary_empty_root_when_none_or_unknown_duchy():
    """When ``player_duchy_id`` is ``None`` or not in ``game.duchies``, return
    a bare empty root ``<div data-player-summary=""></div>`` with no numeric
    attributes and no visible text.
    """
    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(
                    Settlement(
                        "Keep",
                        population=1,
                        owner_id="north",
                        storage=Resources(wheat=1, gold=1),
                    ),
                ),
                parties=(),
            ),
        )
    )

    for player_duchy_id in (None, "missing"):
        xml = render_player_summary(game, player_duchy_id=player_duchy_id)
        root = ET.fromstring(xml)

        assert root.tag == "div"
        assert root.attrib == {"data-player-summary": ""}
        assert "".join(root.itertext()) == ""
        assert "data-settlements" not in root.attrib
        assert "data-parties" not in root.attrib
        assert "data-gold" not in root.attrib
        assert "data-wheat" not in root.attrib


def test_render_player_summary_aggregates_party_combat_strength():
    """When ``player_duchy_id`` matches a duchy, root carries ``data-hp`` /
    ``data-attack`` / ``data-defense`` from ``combat_totals`` over every unit
    (hero + subordinates) of each party in ``duchy.parties``, and the visible
    text gains a matching `` · siła oddziałów: HP H, atak A, obrona D`` suffix
    after the economy line. Other duchies' parties are ignored.
    """
    hero_a = Unit(training=5, equipment=3, experience=1)
    u_a1 = Unit(training=2, equipment=2, experience=0)
    u_a2 = Unit(training=0, equipment=1, experience=4)
    party_a = Party(hero=hero_a, units=(u_a1, u_a2), owner_id="north")

    hero_b = Unit(training=1, equipment=0, experience=2)
    party_b = Party(hero=hero_b, units=(), owner_id="north")

    south_party = Party(
        hero=Unit(training=99, equipment=99, experience=99),
        units=(Unit(training=99),),
        owner_id="south",
    )

    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(
                    Settlement(
                        "Keep",
                        population=1,
                        owner_id="north",
                        storage=Resources(wheat=4, gold=6),
                    ),
                ),
                parties=(party_a, party_b),
            ),
            Duchy(
                "south",
                Unit(),
                settlements=(
                    Settlement(
                        "South Keep",
                        population=1,
                        owner_id="south",
                        storage=Resources(wheat=1, gold=1),
                    ),
                ),
                parties=(south_party,),
            ),
        )
    )

    expected_hp, expected_attack, expected_defense = combat_totals(
        (hero_a, u_a1, u_a2, hero_b)
    )

    xml = render_player_summary(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.attrib["data-hp"] == str(expected_hp)
    assert root.attrib["data-attack"] == str(expected_attack)
    assert root.attrib["data-defense"] == str(expected_defense)
    text = "".join(root.itertext())
    assert text == (
        "Twoje księstwo: osady 1, oddziały 2 · pszenica 4, złoto 6"
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}"
        f" · produkcja/mies.: +0 pszenicy · konsumpcja: 1 pszenicy"
    )


def test_render_player_summary_carries_aggregated_monthly_wheat_economy_attributes():
    """When ``player_duchy_id`` matches a duchy in ``game.duchies``, the root
    carries ``data-wheat-production`` / ``data-wheat-consumption`` as sums of
    ``settlement.production.wheat`` / ``settlement.consumption.wheat`` over
    ``duchy.settlements`` (other duchies ignored), immediately after
    ``data-wheat`` and before ``data-hp``. Visible text carries the matching
    monthly economy suffix (K58.1b). Pure: does not mutate ``game``. Duchy
    with no settlements yields both sums ``0``.
    """
    s1 = Settlement(
        "Keep A",
        population=5,
        occupied=2,
        owner_id="north",
        storage=Resources(wheat=5, gold=3),
        garrison=(Unit(), Unit()),
        active_buildings=(FARM, MARKET),
    )
    s2 = Settlement(
        "Keep B",
        population=2,
        owner_id="north",
        storage=Resources(wheat=2, gold=7),
    )
    other = Settlement(
        "South Keep",
        population=99,
        owner_id="south",
        storage=Resources(wheat=99, gold=99),
        active_buildings=(FARM,),
    )
    hero = Unit()
    party = Party(hero=hero, units=(), owner_id="north")
    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(s1, s2),
                parties=(party,),
            ),
            Duchy(
                "south",
                Unit(),
                settlements=(other,),
                parties=(),
            ),
            Duchy("empty", Unit(), settlements=(), parties=()),
        )
    )
    duchies_before = game.duchies
    storage_s1_before = s1.storage
    storage_s2_before = s2.storage

    assert s1.production == Resources(wheat=3, gold=2)
    assert s1.consumption == Resources(wheat=5, gold=0)
    assert s2.production == Resources(wheat=0, gold=0)
    assert s2.consumption == Resources(wheat=2, gold=0)
    expected_prod = s1.production.wheat + s2.production.wheat  # 3
    expected_cons = s1.consumption.wheat + s2.consumption.wheat  # 7
    expected_hp, expected_attack, expected_defense = combat_totals((hero,))

    xml = render_player_summary(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.attrib["data-wheat"] == "7"
    assert root.attrib["data-wheat-production"] == str(expected_prod)
    assert root.attrib["data-wheat-consumption"] == str(expected_cons)
    assert root.attrib["data-hp"] == str(expected_hp)

    # Attribute order: immediately after data-wheat, before data-hp.
    assert (
        f' data-wheat="7" data-wheat-production="{expected_prod}"'
        f' data-wheat-consumption="{expected_cons}" data-hp="{expected_hp}"'
    ) in xml

    # Visible text includes monthly economy suffix (K58.1b); attrs still match.
    assert "".join(root.itertext()) == (
        "Twoje księstwo: osady 2, oddziały 1 · pszenica 7, złoto 10"
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}"
        f" · produkcja/mies.: +{expected_prod} pszenicy"
        f" · konsumpcja: {expected_cons} pszenicy"
    )

    # Pure: no mutation of game / settlement storage.
    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert s1.storage == storage_s1_before
    assert s2.storage == storage_s2_before

    empty_xml = render_player_summary(game, player_duchy_id="empty")
    empty_root = ET.fromstring(empty_xml)
    assert empty_root.attrib["data-wheat-production"] == "0"
    assert empty_root.attrib["data-wheat-consumption"] == "0"
    assert (
        ' data-wheat="0" data-wheat-production="0"'
        ' data-wheat-consumption="0" data-hp='
    ) in empty_xml


def test_render_player_summary_appends_monthly_wheat_economy_text_suffix():
    """When ``player_duchy_id`` matches a duchy, visible text ends with
    `` · produkcja/mies.: +Pw pszenicy · konsumpcja: Cw pszenicy`` immediately
    after the existing `` · siła oddziałów: …`` segment, where ``Pw`` /
    ``Cw`` match ``data-wheat-production`` / ``data-wheat-consumption``
    (sums of ``settlement.production.wheat`` / ``settlement.consumption.wheat``
    over ``duchy.settlements``). Other duchies ignored. Pure: no mutation.
    """
    s1 = Settlement(
        "Keep A",
        population=5,
        occupied=2,
        owner_id="north",
        storage=Resources(wheat=5, gold=3),
        garrison=(Unit(), Unit()),
        active_buildings=(FARM, MARKET),
    )
    s2 = Settlement(
        "Keep B",
        population=2,
        owner_id="north",
        storage=Resources(wheat=2, gold=7),
    )
    other = Settlement(
        "South Keep",
        population=99,
        owner_id="south",
        storage=Resources(wheat=99, gold=99),
        active_buildings=(FARM,),
    )
    hero = Unit()
    party = Party(hero=hero, units=(), owner_id="north")
    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(s1, s2),
                parties=(party,),
            ),
            Duchy(
                "south",
                Unit(),
                settlements=(other,),
                parties=(),
            ),
        )
    )
    duchies_before = game.duchies
    storage_s1_before = s1.storage
    storage_s2_before = s2.storage

    assert s1.production == Resources(wheat=3, gold=2)
    assert s1.consumption == Resources(wheat=5, gold=0)
    assert s2.production == Resources(wheat=0, gold=0)
    assert s2.consumption == Resources(wheat=2, gold=0)
    expected_prod = s1.production.wheat + s2.production.wheat  # 3
    expected_cons = s1.consumption.wheat + s2.consumption.wheat  # 7
    expected_hp, expected_attack, expected_defense = combat_totals((hero,))

    xml = render_player_summary(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.attrib["data-wheat-production"] == str(expected_prod)
    assert root.attrib["data-wheat-consumption"] == str(expected_cons)

    text = "".join(root.itertext())
    economy_suffix = (
        f" · produkcja/mies.: +{expected_prod} pszenicy"
        f" · konsumpcja: {expected_cons} pszenicy"
    )
    assert text.endswith(economy_suffix)
    assert text == (
        "Twoje księstwo: osady 2, oddziały 1 · pszenica 7, złoto 10"
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}"
        f"{economy_suffix}"
    )
    # Suffix is after siła oddziałów and matches machine attrs.
    assert (
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}{economy_suffix}"
    ) in text
    assert (
        f"+{root.attrib['data-wheat-production']} pszenicy"
        f" · konsumpcja: {root.attrib['data-wheat-consumption']} pszenicy"
    ) in text

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert s1.storage == storage_s1_before
    assert s2.storage == storage_s2_before
