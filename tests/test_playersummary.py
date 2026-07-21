"""Tests for the player duchy economy summary presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

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
    )
