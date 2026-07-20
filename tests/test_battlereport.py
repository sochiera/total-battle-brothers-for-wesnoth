"""Tests for the battle report HTML primitive."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from tbb.battle import BattleResult, BattleSide, HexBattle
from tbb.battlefield import Battlefield
from tbb.hex import Hex
from tbb.unit import Unit
from tbbui.battlereport import render_battle_report


class ControlledRng:
    def __init__(self, result):
        self.result = result
        self.probabilities = []

    def chance(self, probability):
        self.probabilities.append(probability)
        return self.result


def _finished_attacker_win_battle() -> HexBattle:
    dead = Unit(training=3)
    dead_position = Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(
        Unit(), Hex(0, 0), BattleSide.ATTACKER
    ).deploy(dead, dead_position, BattleSide.DEFENDER)
    return battle.damage(dead_position, dead.hp).resolve_defeat(
        dead_position, ControlledRng(True)
    )


def _finished_defender_win_battle() -> HexBattle:
    dead = Unit(training=3)
    dead_position = Hex(0, 0)
    battle = HexBattle(Battlefield()).deploy(
        dead, dead_position, BattleSide.ATTACKER
    ).deploy(Unit(), Hex(1, 0), BattleSide.DEFENDER)
    return battle.damage(dead_position, dead.hp).resolve_defeat(
        dead_position, ControlledRng(True)
    )


def _finished_draw_battle() -> HexBattle:
    attacker = Unit(training=3)
    defender = Unit(training=2)
    attacker_pos = Hex(0, 0)
    defender_pos = Hex(1, 0)
    battle = (
        HexBattle(Battlefield())
        .deploy(attacker, attacker_pos, BattleSide.ATTACKER)
        .deploy(defender, defender_pos, BattleSide.DEFENDER)
    )
    battle = battle.damage(attacker_pos, attacker.hp).resolve_defeat(
        attacker_pos, ControlledRng(True)
    )
    return battle.damage(defender_pos, defender.hp).resolve_defeat(
        defender_pos, ControlledRng(True)
    )


def test_render_battle_report_contains_result_value_in_root_div():
    battle = _finished_attacker_win_battle()

    html = render_battle_report(battle)

    root = ET.fromstring(html)
    assert root.tag == "div"
    assert root.attrib.get("data-battle-report") == ""
    result_div = root.find(".//div[@data-battle-result]")
    assert result_div is not None
    assert (
        result_div.attrib["data-battle-result"]
        == battle.report().result.value
        == BattleResult.ATTACKER_WIN.value
    )


def test_render_battle_report_has_attacker_then_defender_side_counts():
    battle = _finished_attacker_win_battle()
    report = battle.report()

    html = render_battle_report(battle)

    root = ET.fromstring(html)
    side_divs = root.findall(".//div[@data-battle-side]")
    assert [div.attrib["data-battle-side"] for div in side_divs] == [
        "attacker",
        "defender",
    ]
    attacker_div, defender_div = side_divs
    assert attacker_div.attrib["data-fallen"] == str(len(report.attacker.fallen))
    assert attacker_div.attrib["data-stunned"] == str(len(report.attacker.stunned))
    assert attacker_div.attrib["data-active"] == str(len(report.attacker.active))
    assert defender_div.attrib["data-fallen"] == str(len(report.defender.fallen))
    assert defender_div.attrib["data-stunned"] == str(len(report.defender.stunned))
    assert defender_div.attrib["data-active"] == str(len(report.defender.active))


def test_render_battle_report_is_deterministic():
    battle = _finished_attacker_win_battle()

    assert render_battle_report(battle) == render_battle_report(battle)


def test_render_battle_report_shows_human_readable_result_text_for_attacker_win():
    battle = _finished_attacker_win_battle()

    html = render_battle_report(battle)

    root = ET.fromstring(html)
    result_div = root.find(".//div[@data-battle-result]")
    assert result_div.attrib["data-battle-result"] == BattleResult.ATTACKER_WIN.value
    assert result_div.text == "Zwycięstwo atakującego"


def test_render_battle_report_shows_human_readable_result_text_for_defender_win():
    battle = _finished_defender_win_battle()

    html = render_battle_report(battle)

    root = ET.fromstring(html)
    result_div = root.find(".//div[@data-battle-result]")
    assert result_div.attrib["data-battle-result"] == BattleResult.DEFENDER_WIN.value
    assert result_div.text == "Zwycięstwo broniącego"


def test_render_battle_report_shows_human_readable_casualty_text_per_side():
    battle = _finished_attacker_win_battle()
    report = battle.report()

    html = render_battle_report(battle)

    root = ET.fromstring(html)
    attacker_div, defender_div = root.findall(".//div[@data-battle-side]")
    assert attacker_div.text == (
        f"Atakujący: polegli {len(report.attacker.fallen)}, "
        f"ogłuszeni {len(report.attacker.stunned)}, "
        f"zdolni {len(report.attacker.active)}"
    )
    assert defender_div.text == (
        f"Broniący: polegli {len(report.defender.fallen)}, "
        f"ogłuszeni {len(report.defender.stunned)}, "
        f"zdolni {len(report.defender.active)}"
    )


def test_render_battle_report_shows_human_readable_result_text_for_draw():
    battle = _finished_draw_battle()

    html = render_battle_report(battle)

    root = ET.fromstring(html)
    result_div = root.find(".//div[@data-battle-result]")
    assert result_div.attrib["data-battle-result"] == BattleResult.DRAW.value
    assert result_div.text == "Remis"
