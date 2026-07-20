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
