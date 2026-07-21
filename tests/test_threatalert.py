"""Tests for the threat-alert presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.threatalert import render_threat_alert
from tbbui.unitstrength import combat_totals


def test_render_threat_alert_empty_root_when_none_or_unknown_duchy():
    """When ``player_duchy_id`` is ``None`` or not in ``game.duchies``
    (``player_duchy(...) is None``), return a bare empty root
    ``<div data-threat-alert=""></div>`` with no ``data-threats``, no
    visible text, and no children. Does not depend on world parties or
    settlements.
    """
    a = Region("A")
    b = Region("B")
    world = WorldMap(
        [a, b],
        [(a, b)],
        parties={
            a: Party(hero=Unit(), units=(), owner_id="south"),
        },
        settlements={},
    )
    game = GameState(
        (
            Duchy("north", Unit()),
            Duchy("south", Unit()),
        )
    )

    for player_duchy_id in (None, "missing"):
        xml = render_threat_alert(
            world, game, player_duchy_id=player_duchy_id
        )
        root = ET.fromstring(xml)

        assert root.tag == "div"
        assert root.attrib == {"data-threat-alert": ""}
        assert "data-threats" not in root.attrib
        assert list(root) == []
        assert "".join(root.itertext()) == ""


def test_render_threat_alert_data_threats_count_and_label():
    """Known player: root has ``data-threats="N"`` and visible text
    ``Zagrożone pozycje: N``. ``N`` counts own positions (player settlement
    and/or party, separately per region and kind) that have ≥1 neighbor
    with ``party_at(neighbor).owner_id`` set and ``!= player_duchy_id``.
    Pure (no world/game mutation).
    """
    home = Region("Home")
    keep = Region("Keep")
    fort = Region("Fort")
    safe = Region("Safe")
    enemy_camp = Region("EnemyCamp")
    neutral_camp = Region("NeutralCamp")
    ally_camp = Region("AllyCamp")

    # Topology (all of home/keep/fort adj. to enemy_camp; safe only to fort/ally):
    # home party only → 1; keep settlement only → 1; fort party+settlement → 2;
    # safe party (neighbors: player party / same-owner ally) → 0. Total N = 4.
    # neutral (owner_id=None) and same-owner ally do not count as threats.
    world = WorldMap(
        [home, keep, fort, safe, enemy_camp, neutral_camp, ally_camp],
        [
            (home, enemy_camp),
            (keep, enemy_camp),
            (fort, enemy_camp),
            (home, fort),
            (fort, safe),
            (enemy_camp, neutral_camp),
            (safe, ally_camp),
        ],
        parties={
            home: Party(hero=Unit(), units=(), owner_id="player"),
            fort: Party(hero=Unit(), units=(), owner_id="player"),
            safe: Party(hero=Unit(), units=(), owner_id="player"),
            enemy_camp: Party(hero=Unit(), units=(), owner_id="enemy"),
            # unowned / ally neighbors must not create threats for safe
            neutral_camp: Party(hero=Unit(), units=(), owner_id=None),
            ally_camp: Party(hero=Unit(), units=(), owner_id="player"),
        },
        settlements={
            keep: Settlement("KeepS", population=2, owner_id="player"),
            fort: Settlement("FortS", population=2, owner_id="player"),
            # enemy settlement next to home is irrelevant for threat count
            enemy_camp: Settlement(
                "EnemyS", population=2, owner_id="enemy"
            ),
        },
    )
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    # Threatened: home party, keep settlement, fort party, fort settlement → 4
    # safe party has only ally/unowned-adjacent via ally_camp (same owner) → 0
    expected_n = 4

    regions_before = world.regions
    parties_before = {r: world.party_at(r) for r in world.regions}
    settlements_before = {r: world.settlement_at(r) for r in world.regions}
    duchies_before = game.duchies

    xml = render_threat_alert(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-threat-alert") == ""
    assert root.attrib.get("data-threats") == str(expected_n)
    # Root text node carries the K39.1a counter; child rows (K39.1b) add more
    # descendant text, so check root.text rather than full itertext().
    assert root.text == f"Zagrożone pozycje: {expected_n}"
    assert len(root.findall("*[@data-threatened-region]")) == expected_n

    assert world.regions == regions_before
    assert {r: world.party_at(r) for r in world.regions} == parties_before
    assert {
        r: world.settlement_at(r) for r in world.regions
    } == settlements_before
    assert game.duchies == duchies_before


def test_render_threat_alert_rows_per_threatened_position():
    """Known player: one child row per threatened own position.

    Order follows ``world.regions``; within a region with both a player
    settlement and a player party the settlement row comes first. Each row is
    ``<div data-threatened-region data-threatened-kind data-enemy-region
    data-enemy-owner>`` where the enemy is the first neighbouring party with
    explicit ``owner_id != player_duchy_id`` in ``world.neighbors`` order
    (neutral/same-owner parties are skipped). Visible text is
    ``Osada <R>: zagrożenie od <owner> z <E>`` or
    ``Oddział <R>: zagrożenie od <owner> z <E>``. ``data-threats`` equals the
    number of emitted rows.
    """
    home = Region("Home")
    keep = Region("Keep")
    fort = Region("Fort")
    safe = Region("Safe")
    neutral_camp = Region("NeutralCamp")
    bandit_camp = Region("BanditCamp")
    enemy_camp = Region("EnemyCamp")
    ally_camp = Region("AllyCamp")

    # Topology / expected first hostile (neighbors order = world.regions order):
    # home party: neighbors NeutralCamp (unowned), BanditCamp (bandit),
    #   EnemyCamp (enemy) → first hostile BanditCamp / bandit
    # keep settlement: neighbors EnemyCamp → EnemyCamp / enemy
    # fort settlement+party: neighbors BanditCamp → BanditCamp / bandit
    # safe party: neighbors AllyCamp (same owner) → no threat
    world = WorldMap(
        [
            home,
            keep,
            fort,
            safe,
            neutral_camp,
            bandit_camp,
            enemy_camp,
            ally_camp,
        ],
        [
            (home, neutral_camp),
            (home, bandit_camp),
            (home, enemy_camp),
            (keep, enemy_camp),
            (fort, bandit_camp),
            (safe, ally_camp),
        ],
        parties={
            home: Party(hero=Unit(), units=(), owner_id="player"),
            fort: Party(hero=Unit(), units=(), owner_id="player"),
            safe: Party(hero=Unit(), units=(), owner_id="player"),
            bandit_camp: Party(hero=Unit(), units=(), owner_id="bandit"),
            enemy_camp: Party(hero=Unit(), units=(), owner_id="enemy"),
            neutral_camp: Party(hero=Unit(), units=(), owner_id=None),
            ally_camp: Party(hero=Unit(), units=(), owner_id="player"),
        },
        settlements={
            keep: Settlement("KeepS", population=2, owner_id="player"),
            fort: Settlement("FortS", population=2, owner_id="player"),
        },
    )
    assert [r.name for r in world.neighbors(home)] == [
        "NeutralCamp",
        "BanditCamp",
        "EnemyCamp",
    ]
    assert [r.name for r in world.neighbors(keep)] == ["EnemyCamp"]
    assert [r.name for r in world.neighbors(fort)] == ["BanditCamp"]
    assert [r.name for r in world.neighbors(safe)] == ["AllyCamp"]

    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("bandit", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    xml = render_threat_alert(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)

    rows = [
        el
        for el in root
        if el.get("data-threatened-region") is not None
    ]
    # world.regions order: Home party → Keep settlement → Fort settlement
    # then Fort party; Safe has no hostile neighbor.
    expected = [
        ("Home", "party", "BanditCamp", "bandit"),
        ("Keep", "settlement", "EnemyCamp", "enemy"),
        ("Fort", "settlement", "BanditCamp", "bandit"),
        ("Fort", "party", "BanditCamp", "bandit"),
    ]
    assert [
        (
            r.get("data-threatened-region"),
            r.get("data-threatened-kind"),
            r.get("data-enemy-region"),
            r.get("data-enemy-owner"),
        )
        for r in rows
    ] == expected
    assert root.attrib.get("data-threats") == str(len(expected))
    assert len(rows) == len(expected)

    kind_label = {"settlement": "Osada", "party": "Oddział"}
    for row, (region, kind, enemy_region, owner) in zip(
        rows, expected, strict=True
    ):
        assert row.tag == "div"
        # K39.2a: strength attrs + matching text suffix after the K39.1b prefix.
        prefix = (
            f"{kind_label[kind]} {region}: zagrożenie od {owner}"
            f" z {enemy_region}"
        )
        text = "".join(row.itertext())
        assert text.startswith(prefix)
        assert " · siła obronna: HP " in text
        assert " · siła wroga: HP " in text
        assert row.get("data-own-hp") is not None
        assert row.get("data-own-attack") is not None
        assert row.get("data-own-defense") is not None
        assert row.get("data-enemy-hp") is not None
        assert row.get("data-enemy-attack") is not None
        assert row.get("data-enemy-defense") is not None
        assert text == (
            f"{prefix}"
            f" · siła obronna: HP {row.get('data-own-hp')},"
            f" atak {row.get('data-own-attack')},"
            f" obrona {row.get('data-own-defense')}"
            f" · siła wroga: HP {row.get('data-enemy-hp')},"
            f" atak {row.get('data-enemy-attack')},"
            f" obrona {row.get('data-enemy-defense')}"
        )


def test_render_threat_alert_row_own_and_enemy_combat_totals():
    """Each ``data-threatened-region`` row carries own and enemy combat totals.

    Own strength: settlement → ``combat_totals(settlement.garrison)``; party →
    ``combat_totals((hero, *units))``. Enemy strength:
    ``combat_totals((enemy.hero, *enemy.units))`` of the first hostile adjacent
    party. Attributes ``data-own-hp`` / ``data-own-attack`` / ``data-own-defense``
    and ``data-enemy-hp`` / ``data-enemy-attack`` / ``data-enemy-defense`` match
    those totals. Visible text keeps the K39.1b prefix and appends
    `` · siła obronna: HP Ho, atak Ao, obrona Do · siła wroga: HP He, atak Ae,
    obrona De`` consistent with the attributes.
    """
    home = Region("Home")
    keep = Region("Keep")
    enemy_camp = Region("EnemyCamp")

    garrison = (Unit(training=2), Unit(equipment=1, experience=1))
    own_party_hero = Unit(training=4)
    own_party_units = (Unit(equipment=3),)
    enemy_hero = Unit(training=1, equipment=2)
    enemy_units = (Unit(training=5), Unit(experience=2))

    garrison_hp, garrison_atk, garrison_def = combat_totals(garrison)
    party_hp, party_atk, party_def = combat_totals(
        (own_party_hero, *own_party_units)
    )
    enemy_hp, enemy_atk, enemy_def = combat_totals(
        (enemy_hero, *enemy_units)
    )

    world = WorldMap(
        [home, keep, enemy_camp],
        [
            (home, enemy_camp),
            (keep, enemy_camp),
        ],
        parties={
            home: Party(
                hero=own_party_hero,
                units=own_party_units,
                owner_id="player",
            ),
            enemy_camp: Party(
                hero=enemy_hero,
                units=enemy_units,
                owner_id="enemy",
            ),
        },
        settlements={
            keep: Settlement(
                "KeepS",
                population=4,
                owner_id="player",
                garrison=garrison,
            ),
        },
    )
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    xml = render_threat_alert(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)
    rows = [
        el
        for el in root
        if el.get("data-threatened-region") is not None
    ]
    assert [
        (r.get("data-threatened-region"), r.get("data-threatened-kind"))
        for r in rows
    ] == [("Home", "party"), ("Keep", "settlement")]

    home_row, keep_row = rows

    assert home_row.get("data-own-hp") == str(party_hp)
    assert home_row.get("data-own-attack") == str(party_atk)
    assert home_row.get("data-own-defense") == str(party_def)
    assert home_row.get("data-enemy-hp") == str(enemy_hp)
    assert home_row.get("data-enemy-attack") == str(enemy_atk)
    assert home_row.get("data-enemy-defense") == str(enemy_def)
    assert "".join(home_row.itertext()) == (
        f"Oddział Home: zagrożenie od enemy z EnemyCamp"
        f" · siła obronna: HP {party_hp}, atak {party_atk},"
        f" obrona {party_def}"
        f" · siła wroga: HP {enemy_hp}, atak {enemy_atk},"
        f" obrona {enemy_def}"
    )

    assert keep_row.get("data-own-hp") == str(garrison_hp)
    assert keep_row.get("data-own-attack") == str(garrison_atk)
    assert keep_row.get("data-own-defense") == str(garrison_def)
    assert keep_row.get("data-enemy-hp") == str(enemy_hp)
    assert keep_row.get("data-enemy-attack") == str(enemy_atk)
    assert keep_row.get("data-enemy-defense") == str(enemy_def)
    assert "".join(keep_row.itertext()) == (
        f"Osada Keep: zagrożenie od enemy z EnemyCamp"
        f" · siła obronna: HP {garrison_hp}, atak {garrison_atk},"
        f" obrona {garrison_def}"
        f" · siła wroga: HP {enemy_hp}, atak {enemy_atk},"
        f" obrona {enemy_def}"
    )
