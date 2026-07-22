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
        f" · produkcja/mies.: +0 pszenicy, +0 złota · konsumpcja: 2 pszenicy"
        f" · bilans pszenicy: deficyt"
        f" · saldo pszenicy/mies.: -2"
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
        f" · produkcja/mies.: +0 pszenicy, +0 złota · konsumpcja: 1 pszenicy"
        f" · bilans pszenicy: deficyt"
        f" · saldo pszenicy/mies.: -1"
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

    # Attribute order: after data-wheat; wheat-surplus (K58.2a) before data-hp.
    assert (
        f' data-wheat="7" data-wheat-production="{expected_prod}"'
        f' data-gold-production="2"'
        f' data-wheat-consumption="{expected_cons}"'
        f' data-wheat-surplus="false"'
        f' data-wheat-net="{expected_prod - expected_cons}"'
        f' data-hp="{expected_hp}"'
    ) in xml

    # Visible text includes monthly economy + bilans + saldo; attrs still match.
    assert "".join(root.itertext()) == (
        "Twoje księstwo: osady 2, oddziały 1 · pszenica 7, złoto 10"
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}"
        f" · produkcja/mies.: +{expected_prod} pszenicy, +2 złota"
        f" · konsumpcja: {expected_cons} pszenicy"
        f" · bilans pszenicy: deficyt"
        f" · saldo pszenicy/mies.: {expected_prod - expected_cons:+d}"
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
        ' data-gold-production="0"'
        ' data-wheat-consumption="0" data-wheat-surplus="true"'
        ' data-wheat-net="0" data-hp='
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
        f" · produkcja/mies.: +{expected_prod} pszenicy, +2 złota"
        f" · konsumpcja: {expected_cons} pszenicy"
    )
    bilans_suffix = " · bilans pszenicy: deficyt"
    saldo_suffix = f" · saldo pszenicy/mies.: {expected_prod - expected_cons:+d}"
    assert economy_suffix in text
    assert text.endswith(economy_suffix + bilans_suffix + saldo_suffix)
    assert text == (
        "Twoje księstwo: osady 2, oddziały 1 · pszenica 7, złoto 10"
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}"
        f"{economy_suffix}{bilans_suffix}{saldo_suffix}"
    )
    # Economy suffix is after siła oddziałów and matches machine attrs.
    assert (
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}{economy_suffix}"
    ) in text
    assert (
        f"+{root.attrib['data-wheat-production']} pszenicy, +2 złota"
        f" · konsumpcja: {root.attrib['data-wheat-consumption']} pszenicy"
    ) in text

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert s1.storage == storage_s1_before
    assert s2.storage == storage_s2_before


def test_render_player_summary_carries_aggregated_wheat_surplus_flag():
    """When ``player_duchy_id`` matches a duchy in ``game.duchies``, the root
    carries ``data-wheat-surplus="true|false"`` where the flag is
    ``sum(settlement.production.wheat) >= sum(settlement.consumption.wheat)``
    over ``duchy.settlements`` — the same sums as ``data-wheat-production`` /
    ``data-wheat-consumption`` — placed immediately after
    ``data-wheat-consumption`` and before ``data-hp``. Visible text carries
    the matching bilans suffix (K58.2b). Pure: does not mutate ``game``.
    Duchy with no settlements yields ``data-wheat-surplus="true"`` (0 >= 0).
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
    surplus_only = Settlement(
        "Farm Keep",
        population=1,
        owner_id="surplus",
        storage=Resources(wheat=4, gold=1),
        active_buildings=(FARM,),
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
    surplus_hero = Unit()
    surplus_party = Party(hero=surplus_hero, units=(), owner_id="surplus")
    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(s1, s2),
                parties=(party,),
            ),
            Duchy(
                "surplus",
                Unit(),
                settlements=(surplus_only,),
                parties=(surplus_party,),
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
    storage_surplus_before = surplus_only.storage

    assert s1.production == Resources(wheat=3, gold=2)
    assert s1.consumption == Resources(wheat=5, gold=0)
    assert s2.production == Resources(wheat=0, gold=0)
    assert s2.consumption == Resources(wheat=2, gold=0)
    expected_prod = s1.production.wheat + s2.production.wheat  # 3
    expected_cons = s1.consumption.wheat + s2.consumption.wheat  # 7
    assert expected_prod < expected_cons
    expected_hp, expected_attack, expected_defense = combat_totals((hero,))

    assert surplus_only.production == Resources(wheat=3, gold=0)
    assert surplus_only.consumption == Resources(wheat=1, gold=0)
    assert surplus_only.production.wheat >= surplus_only.consumption.wheat
    surplus_hp, surplus_attack, surplus_defense = combat_totals((surplus_hero,))

    # Deficit duchy: production sum < consumption sum → "false".
    xml = render_player_summary(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.attrib["data-wheat-production"] == str(expected_prod)
    assert root.attrib["data-wheat-consumption"] == str(expected_cons)
    assert root.attrib["data-wheat-surplus"] == "false"
    assert root.attrib["data-hp"] == str(expected_hp)

    # Attribute order: immediately after data-wheat-consumption, before data-hp
    # (data-wheat-net sits between surplus and hp — K58.3a).
    assert (
        f' data-wheat-production="{expected_prod}"'
        f' data-gold-production="2"'
        f' data-wheat-consumption="{expected_cons}"'
        f' data-wheat-surplus="false"'
        f' data-wheat-net="{expected_prod - expected_cons}"'
        f' data-hp="{expected_hp}"'
    ) in xml

    # Visible text: monthly economy + bilans + saldo spójne z atr. (K58.2b/K58.3b).
    assert "".join(root.itertext()) == (
        "Twoje księstwo: osady 2, oddziały 1 · pszenica 7, złoto 10"
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}"
        f" · produkcja/mies.: +{expected_prod} pszenicy, +2 złota"
        f" · konsumpcja: {expected_cons} pszenicy"
        f" · bilans pszenicy: deficyt"
        f" · saldo pszenicy/mies.: {expected_prod - expected_cons:+d}"
    )

    # Pure: no mutation of game / settlement storage.
    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert s1.storage == storage_s1_before
    assert s2.storage == storage_s2_before

    # Surplus duchy: production >= consumption → "true".
    surplus_xml = render_player_summary(game, player_duchy_id="surplus")
    surplus_root = ET.fromstring(surplus_xml)
    assert surplus_root.attrib["data-wheat-production"] == "3"
    assert surplus_root.attrib["data-wheat-consumption"] == "1"
    assert surplus_root.attrib["data-wheat-surplus"] == "true"
    assert (
        ' data-wheat-production="3"'
        ' data-gold-production="0"'
        ' data-wheat-consumption="1"'
        ' data-wheat-surplus="true"'
        ' data-wheat-net="2"'
        f' data-hp="{surplus_hp}"'
    ) in surplus_xml
    assert "".join(surplus_root.itertext()) == (
        "Twoje księstwo: osady 1, oddziały 1 · pszenica 4, złoto 1"
        f" · siła oddziałów: HP {surplus_hp}, atak {surplus_attack},"
        f" obrona {surplus_defense}"
        " · produkcja/mies.: +3 pszenicy, +0 złota · konsumpcja: 1 pszenicy"
        " · bilans pszenicy: nadwyżka"
        " · saldo pszenicy/mies.: +2"
    )
    assert surplus_only.storage == storage_surplus_before

    # Empty duchy: 0 >= 0 → "true".
    empty_xml = render_player_summary(game, player_duchy_id="empty")
    empty_root = ET.fromstring(empty_xml)
    assert empty_root.attrib["data-wheat-production"] == "0"
    assert empty_root.attrib["data-wheat-consumption"] == "0"
    assert empty_root.attrib["data-wheat-surplus"] == "true"
    assert (
        ' data-wheat-production="0"'
        ' data-gold-production="0"'
        ' data-wheat-consumption="0"'
        ' data-wheat-surplus="true"'
        ' data-wheat-net="0"'
        " data-hp="
    ) in empty_xml


def test_render_player_summary_appends_wheat_surplus_text_suffix():
    """When ``player_duchy_id`` matches a duchy, visible text ends with
    `` · bilans pszenicy: nadwyżka`` when ``data-wheat-surplus="true"``, else
    `` · bilans pszenicy: deficyt`` when ``"false"``, immediately after the
    existing `` · produkcja/mies.: +Pw pszenicy · konsumpcja: Cw pszenicy``
    segment. Flag and label stay consistent; machine attrs unchanged.
    Pure: does not mutate ``game``.
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
    surplus_only = Settlement(
        "Farm Keep",
        population=1,
        owner_id="surplus",
        storage=Resources(wheat=4, gold=1),
        active_buildings=(FARM,),
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
    surplus_hero = Unit()
    surplus_party = Party(hero=surplus_hero, units=(), owner_id="surplus")
    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(s1, s2),
                parties=(party,),
            ),
            Duchy(
                "surplus",
                Unit(),
                settlements=(surplus_only,),
                parties=(surplus_party,),
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
    storage_surplus_before = surplus_only.storage

    assert s1.production == Resources(wheat=3, gold=2)
    assert s1.consumption == Resources(wheat=5, gold=0)
    assert s2.production == Resources(wheat=0, gold=0)
    assert s2.consumption == Resources(wheat=2, gold=0)
    expected_prod = s1.production.wheat + s2.production.wheat  # 3
    expected_cons = s1.consumption.wheat + s2.consumption.wheat  # 7
    assert expected_prod < expected_cons
    expected_hp, expected_attack, expected_defense = combat_totals((hero,))

    assert surplus_only.production == Resources(wheat=3, gold=0)
    assert surplus_only.consumption == Resources(wheat=1, gold=0)
    assert surplus_only.production.wheat >= surplus_only.consumption.wheat
    surplus_hp, surplus_attack, surplus_defense = combat_totals((surplus_hero,))

    # Deficit: data-wheat-surplus="false" → bilans: deficyt after economy suffix.
    xml = render_player_summary(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.attrib["data-wheat-production"] == str(expected_prod)
    assert root.attrib["data-wheat-consumption"] == str(expected_cons)
    assert root.attrib["data-wheat-surplus"] == "false"
    # Attrs order: surplus then net (K58.3a) then hp.
    assert (
        f' data-wheat-production="{expected_prod}"'
        f' data-gold-production="2"'
        f' data-wheat-consumption="{expected_cons}"'
        f' data-wheat-surplus="false"'
        f' data-wheat-net="{expected_prod - expected_cons}"'
        f' data-hp="{expected_hp}"'
    ) in xml

    economy_suffix = (
        f" · produkcja/mies.: +{expected_prod} pszenicy, +2 złota"
        f" · konsumpcja: {expected_cons} pszenicy"
    )
    bilans_deficit = " · bilans pszenicy: deficyt"
    saldo_deficit = f" · saldo pszenicy/mies.: {expected_prod - expected_cons:+d}"
    text = "".join(root.itertext())
    assert text.endswith(economy_suffix + bilans_deficit + saldo_deficit)
    assert text == (
        "Twoje księstwo: osady 2, oddziały 1 · pszenica 7, złoto 10"
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}"
        f"{economy_suffix}{bilans_deficit}{saldo_deficit}"
    )
    assert bilans_deficit in text
    assert " · bilans pszenicy: nadwyżka" not in text

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert s1.storage == storage_s1_before
    assert s2.storage == storage_s2_before

    # Surplus: data-wheat-surplus="true" → bilans: nadwyżka after economy suffix.
    surplus_xml = render_player_summary(game, player_duchy_id="surplus")
    surplus_root = ET.fromstring(surplus_xml)
    assert surplus_root.attrib["data-wheat-surplus"] == "true"
    assert (
        ' data-wheat-production="3"'
        ' data-gold-production="0"'
        ' data-wheat-consumption="1"'
        ' data-wheat-surplus="true"'
        ' data-wheat-net="2"'
        f' data-hp="{surplus_hp}"'
    ) in surplus_xml
    bilans_surplus = " · bilans pszenicy: nadwyżka"
    saldo_surplus = " · saldo pszenicy/mies.: +2"
    surplus_text = "".join(surplus_root.itertext())
    assert surplus_text.endswith(
        " · produkcja/mies.: +3 pszenicy, +0 złota · konsumpcja: 1 pszenicy"
        + bilans_surplus
        + saldo_surplus
    )
    assert surplus_text == (
        "Twoje księstwo: osady 1, oddziały 1 · pszenica 4, złoto 1"
        f" · siła oddziałów: HP {surplus_hp}, atak {surplus_attack},"
        f" obrona {surplus_defense}"
        " · produkcja/mies.: +3 pszenicy, +0 złota · konsumpcja: 1 pszenicy"
        f"{bilans_surplus}{saldo_surplus}"
    )
    assert bilans_surplus in surplus_text
    assert " · bilans pszenicy: deficyt" not in surplus_text
    assert surplus_only.storage == storage_surplus_before


def test_render_player_summary_carries_aggregated_wheat_net_attribute():
    """When ``player_duchy_id`` matches a duchy in ``game.duchies``, the root
    carries ``data-wheat-net`` as ``str(int)`` of
    ``sum(settlement.production.wheat) - sum(settlement.consumption.wheat)``
    over ``duchy.settlements`` — the same sums as ``data-wheat-production`` /
    ``data-wheat-consumption`` — placed immediately after
    ``data-wheat-surplus`` and before ``data-hp``. Value is consistent with
    the surplus flag (``net >= 0`` ⇔ ``surplus="true"``). Pure: does not
    mutate ``game``. Duchy with no settlements yields ``data-wheat-net="0"``.
    Visible text is unchanged (no saldo suffix in this step).
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
    surplus_only = Settlement(
        "Farm Keep",
        population=1,
        owner_id="surplus",
        storage=Resources(wheat=4, gold=1),
        active_buildings=(FARM,),
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
    surplus_hero = Unit()
    surplus_party = Party(hero=surplus_hero, units=(), owner_id="surplus")
    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(s1, s2),
                parties=(party,),
            ),
            Duchy(
                "surplus",
                Unit(),
                settlements=(surplus_only,),
                parties=(surplus_party,),
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
    storage_surplus_before = surplus_only.storage

    assert s1.production == Resources(wheat=3, gold=2)
    assert s1.consumption == Resources(wheat=5, gold=0)
    assert s2.production == Resources(wheat=0, gold=0)
    assert s2.consumption == Resources(wheat=2, gold=0)
    expected_prod = s1.production.wheat + s2.production.wheat  # 3
    expected_cons = s1.consumption.wheat + s2.consumption.wheat  # 7
    expected_net = expected_prod - expected_cons  # -4
    assert expected_net < 0
    expected_hp, expected_attack, expected_defense = combat_totals((hero,))

    assert surplus_only.production == Resources(wheat=3, gold=0)
    assert surplus_only.consumption == Resources(wheat=1, gold=0)
    surplus_net = (
        surplus_only.production.wheat - surplus_only.consumption.wheat
    )  # 2
    assert surplus_net > 0
    surplus_hp, surplus_attack, surplus_defense = combat_totals((surplus_hero,))

    # Deficit duchy: net = production − consumption < 0 → signed str.
    xml = render_player_summary(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.attrib["data-wheat-production"] == str(expected_prod)
    assert root.attrib["data-wheat-consumption"] == str(expected_cons)
    assert root.attrib["data-wheat-surplus"] == "false"
    assert root.attrib["data-wheat-net"] == str(expected_net)
    assert root.attrib["data-wheat-net"] == "-4"
    assert root.attrib["data-hp"] == str(expected_hp)
    # net >= 0 ⇔ surplus="true"
    assert (int(root.attrib["data-wheat-net"]) >= 0) == (
        root.attrib["data-wheat-surplus"] == "true"
    )

    # Attribute order: immediately after data-wheat-surplus, before data-hp.
    assert (
        f' data-wheat-production="{expected_prod}"'
        f' data-gold-production="2"'
        f' data-wheat-consumption="{expected_cons}"'
        f' data-wheat-surplus="false"'
        f' data-wheat-net="{expected_net}"'
        f' data-hp="{expected_hp}"'
    ) in xml

    # Visible text includes bilans + signed saldo (K58.3b) matching data-wheat-net.
    assert "".join(root.itertext()) == (
        "Twoje księstwo: osady 2, oddziały 1 · pszenica 7, złoto 10"
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}"
        f" · produkcja/mies.: +{expected_prod} pszenicy, +2 złota"
        f" · konsumpcja: {expected_cons} pszenicy"
        f" · bilans pszenicy: deficyt"
        f" · saldo pszenicy/mies.: {expected_net:+d}"
    )

    # Pure: no mutation of game / settlement storage.
    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert s1.storage == storage_s1_before
    assert s2.storage == storage_s2_before

    # Surplus duchy: net > 0 → positive str; consistent with surplus="true".
    surplus_xml = render_player_summary(game, player_duchy_id="surplus")
    surplus_root = ET.fromstring(surplus_xml)
    assert surplus_root.attrib["data-wheat-production"] == "3"
    assert surplus_root.attrib["data-wheat-consumption"] == "1"
    assert surplus_root.attrib["data-wheat-surplus"] == "true"
    assert surplus_root.attrib["data-wheat-net"] == str(surplus_net)
    assert surplus_root.attrib["data-wheat-net"] == "2"
    assert (int(surplus_root.attrib["data-wheat-net"]) >= 0) == (
        surplus_root.attrib["data-wheat-surplus"] == "true"
    )
    assert (
        ' data-wheat-production="3"'
        ' data-gold-production="0"'
        ' data-wheat-consumption="1"'
        ' data-wheat-surplus="true"'
        f' data-wheat-net="{surplus_net}"'
        f' data-hp="{surplus_hp}"'
    ) in surplus_xml
    assert "".join(surplus_root.itertext()) == (
        "Twoje księstwo: osady 1, oddziały 1 · pszenica 4, złoto 1"
        f" · siła oddziałów: HP {surplus_hp}, atak {surplus_attack},"
        f" obrona {surplus_defense}"
        " · produkcja/mies.: +3 pszenicy, +0 złota · konsumpcja: 1 pszenicy"
        " · bilans pszenicy: nadwyżka"
        f" · saldo pszenicy/mies.: {surplus_net:+d}"
    )
    assert surplus_only.storage == storage_surplus_before

    # Empty duchy: 0 − 0 → "0"; consistent with surplus="true".
    empty_xml = render_player_summary(game, player_duchy_id="empty")
    empty_root = ET.fromstring(empty_xml)
    assert empty_root.attrib["data-wheat-production"] == "0"
    assert empty_root.attrib["data-wheat-consumption"] == "0"
    assert empty_root.attrib["data-wheat-surplus"] == "true"
    assert empty_root.attrib["data-wheat-net"] == "0"
    assert (int(empty_root.attrib["data-wheat-net"]) >= 0) == (
        empty_root.attrib["data-wheat-surplus"] == "true"
    )
    assert (
        ' data-wheat-production="0"'
        ' data-gold-production="0"'
        ' data-wheat-consumption="0"'
        ' data-wheat-surplus="true"'
        ' data-wheat-net="0"'
        " data-hp="
    ) in empty_xml


def test_render_player_summary_appends_wheat_net_text_suffix():
    """When ``player_duchy_id`` matches a duchy, visible text ends with
    `` · saldo pszenicy/mies.: {net:+d}`` immediately after the existing
    `` · bilans pszenicy: nadwyżka|deficyt`` segment, where ``net`` equals
    ``int(data-wheat-net)`` and is always rendered with a sign (``+2``,
    ``+0``, ``-3``). Machine attrs (including ``data-wheat-net``) unchanged;
    empty root for ``None``/unknown duchy unchanged. Pure: no mutation.
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
    surplus_only = Settlement(
        "Farm Keep",
        population=1,
        owner_id="surplus",
        storage=Resources(wheat=4, gold=1),
        active_buildings=(FARM,),
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
    surplus_hero = Unit()
    surplus_party = Party(hero=surplus_hero, units=(), owner_id="surplus")
    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(s1, s2),
                parties=(party,),
            ),
            Duchy(
                "surplus",
                Unit(),
                settlements=(surplus_only,),
                parties=(surplus_party,),
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
    storage_surplus_before = surplus_only.storage

    assert s1.production == Resources(wheat=3, gold=2)
    assert s1.consumption == Resources(wheat=5, gold=0)
    assert s2.production == Resources(wheat=0, gold=0)
    assert s2.consumption == Resources(wheat=2, gold=0)
    expected_prod = s1.production.wheat + s2.production.wheat  # 3
    expected_cons = s1.consumption.wheat + s2.consumption.wheat  # 7
    expected_net = expected_prod - expected_cons  # -4
    assert expected_net < 0
    expected_hp, expected_attack, expected_defense = combat_totals((hero,))

    assert surplus_only.production == Resources(wheat=3, gold=0)
    assert surplus_only.consumption == Resources(wheat=1, gold=0)
    surplus_net = (
        surplus_only.production.wheat - surplus_only.consumption.wheat
    )  # 2
    assert surplus_net > 0
    surplus_hp, surplus_attack, surplus_defense = combat_totals((surplus_hero,))

    # Deficit: saldo after bilans; net always signed; attrs including net intact.
    xml = render_player_summary(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.attrib["data-wheat-production"] == str(expected_prod)
    assert root.attrib["data-wheat-consumption"] == str(expected_cons)
    assert root.attrib["data-wheat-surplus"] == "false"
    assert root.attrib["data-wheat-net"] == str(expected_net)
    assert root.attrib["data-wheat-net"] == "-4"
    assert (
        f' data-wheat-production="{expected_prod}"'
        f' data-gold-production="2"'
        f' data-wheat-consumption="{expected_cons}"'
        f' data-wheat-surplus="false"'
        f' data-wheat-net="{expected_net}"'
        f' data-hp="{expected_hp}"'
    ) in xml

    economy_suffix = (
        f" · produkcja/mies.: +{expected_prod} pszenicy, +2 złota"
        f" · konsumpcja: {expected_cons} pszenicy"
    )
    bilans_deficit = " · bilans pszenicy: deficyt"
    saldo_deficit = f" · saldo pszenicy/mies.: {expected_net:+d}"
    assert saldo_deficit == " · saldo pszenicy/mies.: -4"
    text = "".join(root.itertext())
    assert text.endswith(economy_suffix + bilans_deficit + saldo_deficit)
    assert text == (
        "Twoje księstwo: osady 2, oddziały 1 · pszenica 7, złoto 10"
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}"
        f"{economy_suffix}{bilans_deficit}{saldo_deficit}"
    )
    # Visible signed net matches int(data-wheat-net).
    assert f"saldo pszenicy/mies.: {int(root.attrib['data-wheat-net']):+d}" in text

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert s1.storage == storage_s1_before
    assert s2.storage == storage_s2_before

    # Surplus: +N after bilans nadwyżka; data-wheat-net unchanged.
    surplus_xml = render_player_summary(game, player_duchy_id="surplus")
    surplus_root = ET.fromstring(surplus_xml)
    assert surplus_root.attrib["data-wheat-surplus"] == "true"
    assert surplus_root.attrib["data-wheat-net"] == str(surplus_net)
    assert surplus_root.attrib["data-wheat-net"] == "2"
    assert (
        ' data-wheat-production="3"'
        ' data-gold-production="0"'
        ' data-wheat-consumption="1"'
        ' data-wheat-surplus="true"'
        f' data-wheat-net="{surplus_net}"'
        f' data-hp="{surplus_hp}"'
    ) in surplus_xml
    bilans_surplus = " · bilans pszenicy: nadwyżka"
    saldo_surplus = f" · saldo pszenicy/mies.: {surplus_net:+d}"
    assert saldo_surplus == " · saldo pszenicy/mies.: +2"
    surplus_text = "".join(surplus_root.itertext())
    assert surplus_text.endswith(
        " · produkcja/mies.: +3 pszenicy, +0 złota · konsumpcja: 1 pszenicy"
        + bilans_surplus
        + saldo_surplus
    )
    assert surplus_text == (
        "Twoje księstwo: osady 1, oddziały 1 · pszenica 4, złoto 1"
        f" · siła oddziałów: HP {surplus_hp}, atak {surplus_attack},"
        f" obrona {surplus_defense}"
        " · produkcja/mies.: +3 pszenicy, +0 złota · konsumpcja: 1 pszenicy"
        f"{bilans_surplus}{saldo_surplus}"
    )
    assert (
        f"saldo pszenicy/mies.: {int(surplus_root.attrib['data-wheat-net']):+d}"
        in surplus_text
    )
    assert surplus_only.storage == storage_surplus_before

    # Empty duchy: net 0 → visible ``+0`` after bilans nadwyżka.
    empty_xml = render_player_summary(game, player_duchy_id="empty")
    empty_root = ET.fromstring(empty_xml)
    assert empty_root.attrib["data-wheat-net"] == "0"
    assert empty_root.attrib["data-wheat-surplus"] == "true"
    empty_text = "".join(empty_root.itertext())
    assert empty_text.endswith(
        " · bilans pszenicy: nadwyżka · saldo pszenicy/mies.: +0"
    )
    assert " · saldo pszenicy/mies.: +0" in empty_text

    # Empty root for None / unknown: no saldo text, no economy attrs.
    for player_duchy_id in (None, "missing"):
        bare = ET.fromstring(
            render_player_summary(game, player_duchy_id=player_duchy_id)
        )
        assert bare.attrib == {"data-player-summary": ""}
        assert "".join(bare.itertext()) == ""
        assert "data-wheat-net" not in bare.attrib


def test_render_player_summary_carries_aggregated_monthly_gold_production_attribute():
    """When ``player_duchy_id`` matches a duchy in ``game.duchies``, the root
    carries ``data-gold-production`` as the sum of ``settlement.production.gold``
    over ``duchy.settlements`` (other duchies ignored), placed immediately after
    ``data-wheat-production`` and before ``data-wheat-consumption`` (mirror of
    settlement-panel order). Visible text and remaining attrs unchanged. Pure:
    does not mutate ``game``. Duchy with no settlements yields ``"0"``.
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
        active_buildings=(MARKET,),
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
    assert other.production.gold == 2  # south Market must not leak into north sum
    expected_wheat_prod = s1.production.wheat + s2.production.wheat  # 3
    expected_gold_prod = s1.production.gold + s2.production.gold  # 2
    expected_cons = s1.consumption.wheat + s2.consumption.wheat  # 7
    expected_net = expected_wheat_prod - expected_cons  # -4
    expected_hp, expected_attack, expected_defense = combat_totals((hero,))

    xml = render_player_summary(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.attrib["data-wheat-production"] == str(expected_wheat_prod)
    assert root.attrib["data-gold-production"] == str(expected_gold_prod)
    assert root.attrib["data-gold-production"] == "2"
    assert root.attrib["data-wheat-consumption"] == str(expected_cons)
    # Remaining attrs unchanged (wheat economy + combat + storage).
    assert root.attrib["data-wheat"] == "7"
    assert root.attrib["data-gold"] == "10"
    assert root.attrib["data-wheat-surplus"] == "false"
    assert root.attrib["data-wheat-net"] == str(expected_net)
    assert root.attrib["data-hp"] == str(expected_hp)
    assert root.attrib["data-attack"] == str(expected_attack)
    assert root.attrib["data-defense"] == str(expected_defense)

    # Attribute order: after data-wheat-production, before data-wheat-consumption.
    assert (
        f' data-wheat-production="{expected_wheat_prod}"'
        f' data-gold-production="{expected_gold_prod}"'
        f' data-wheat-consumption="{expected_cons}"'
    ) in xml

    # Visible text includes gold production in the production group (K59.1b).
    assert "".join(root.itertext()) == (
        "Twoje księstwo: osady 2, oddziały 1 · pszenica 7, złoto 10"
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}"
        f" · produkcja/mies.: +{expected_wheat_prod} pszenicy, +{expected_gold_prod} złota"
        f" · konsumpcja: {expected_cons} pszenicy"
        f" · bilans pszenicy: deficyt"
        f" · saldo pszenicy/mies.: {expected_net:+d}"
    )

    # Pure: no mutation of game / settlement storage.
    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert s1.storage == storage_s1_before
    assert s2.storage == storage_s2_before

    # Empty duchy: sum over zero settlements → "0".
    empty_xml = render_player_summary(game, player_duchy_id="empty")
    empty_root = ET.fromstring(empty_xml)
    assert empty_root.attrib["data-gold-production"] == "0"
    assert (
        ' data-wheat-production="0"'
        ' data-gold-production="0"'
        ' data-wheat-consumption="0"'
    ) in empty_xml


def test_render_player_summary_appends_monthly_gold_production_text_suffix():
    """When ``player_duchy_id`` matches a duchy, the production group in visible
    text is ``produkcja/mies.: +Pw pszenicy, +Pg złota`` (gold in the production
    group, before `` · konsumpcja: …``), where ``Pg`` equals
    ``data-gold-production`` (sum of ``settlement.production.gold`` over
    ``duchy.settlements``). Machine attrs (including ``data-gold-production``)
    unchanged; empty root for ``None``/unknown duchy unchanged. Pure: no
    mutation.
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
        active_buildings=(MARKET,),
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
    assert other.production.gold == 2  # south Market must not leak into north sum
    expected_wheat_prod = s1.production.wheat + s2.production.wheat  # 3
    expected_gold_prod = s1.production.gold + s2.production.gold  # 2
    expected_cons = s1.consumption.wheat + s2.consumption.wheat  # 7
    expected_net = expected_wheat_prod - expected_cons  # -4
    expected_hp, expected_attack, expected_defense = combat_totals((hero,))

    xml = render_player_summary(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    # Machine attrs unchanged (incl. data-gold-production and order).
    assert root.attrib["data-wheat-production"] == str(expected_wheat_prod)
    assert root.attrib["data-gold-production"] == str(expected_gold_prod)
    assert root.attrib["data-gold-production"] == "2"
    assert root.attrib["data-wheat-consumption"] == str(expected_cons)
    assert root.attrib["data-wheat-surplus"] == "false"
    assert root.attrib["data-wheat-net"] == str(expected_net)
    assert root.attrib["data-hp"] == str(expected_hp)
    assert (
        f' data-wheat-production="{expected_wheat_prod}"'
        f' data-gold-production="{expected_gold_prod}"'
        f' data-wheat-consumption="{expected_cons}"'
    ) in xml

    production_group = (
        f"produkcja/mies.: +{expected_wheat_prod} pszenicy,"
        f" +{expected_gold_prod} złota"
    )
    economy_suffix = (
        f" · {production_group}"
        f" · konsumpcja: {expected_cons} pszenicy"
    )
    bilans_suffix = " · bilans pszenicy: deficyt"
    saldo_suffix = f" · saldo pszenicy/mies.: {expected_net:+d}"
    text = "".join(root.itertext())

    # Gold sits in the production group, before konsumpcja; matches attr.
    assert production_group in text
    assert (
        f"+{root.attrib['data-wheat-production']} pszenicy,"
        f" +{root.attrib['data-gold-production']} złota"
        f" · konsumpcja:"
    ) in text
    assert economy_suffix in text
    assert text.endswith(economy_suffix + bilans_suffix + saldo_suffix)
    assert text == (
        "Twoje księstwo: osady 2, oddziały 1 · pszenica 7, złoto 10"
        f" · siła oddziałów: HP {expected_hp}, atak {expected_attack},"
        f" obrona {expected_defense}"
        f"{economy_suffix}{bilans_suffix}{saldo_suffix}"
    )

    # Pure: no mutation of game / settlement storage.
    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert s1.storage == storage_s1_before
    assert s2.storage == storage_s2_before

    # Empty duchy: production group shows +0 złota; attrs still "0".
    empty_xml = render_player_summary(game, player_duchy_id="empty")
    empty_root = ET.fromstring(empty_xml)
    assert empty_root.attrib["data-gold-production"] == "0"
    empty_text = "".join(empty_root.itertext())
    assert "produkcja/mies.: +0 pszenicy, +0 złota" in empty_text
    assert (
        ' data-wheat-production="0"'
        ' data-gold-production="0"'
        ' data-wheat-consumption="0"'
    ) in empty_xml

    # None / unknown: bare empty root unchanged (no numeric attrs, no text).
    for player_duchy_id in (None, "missing"):
        bare = ET.fromstring(
            render_player_summary(game, player_duchy_id=player_duchy_id)
        )
        assert bare.attrib == {"data-player-summary": ""}
        assert "".join(bare.itertext()) == ""
        assert "data-gold-production" not in bare.attrib
