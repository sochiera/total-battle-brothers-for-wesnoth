"""Tests for the player duchy economy summary presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.resources import Resources
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbbui.playersummary import render_player_summary


def test_render_player_summary_aggregates_duchy_economy_and_is_pure():
    """When ``player_duchy_id`` matches a duchy in ``game.duchies``, the root is
    ``<div data-player-summary="">`` with ``data-settlements`` / ``data-parties``
    / ``data-gold`` / ``data-wheat`` (counts and storage sums over that duchy)
    and matching visible text. Pure: does not mutate ``game``.
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
    party = Party(hero=Unit(), units=(), owner_id="north")
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

    xml = render_player_summary(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-player-summary") == ""
    assert root.attrib["data-settlements"] == "2"
    assert root.attrib["data-parties"] == "1"
    assert root.attrib["data-gold"] == "10"
    assert root.attrib["data-wheat"] == "7"
    assert "".join(root.itertext()) == (
        "Twoje księstwo: osady 2, oddziały 1 · pszenica 7, złoto 10"
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
