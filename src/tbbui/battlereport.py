"""Deterministic HTML fragment for a finished hex-battle report."""

from __future__ import annotations

from tbb.battle import BattleResult, BattleSideReport, HexBattle

_RESULT_TEXT = {
    BattleResult.ATTACKER_WIN: "Zwycięstwo atakującego",
    BattleResult.DEFENDER_WIN: "Zwycięstwo broniącego",
    BattleResult.DRAW: "Remis",
}


def _side_div(side: str, report: BattleSideReport) -> str:
    return (
        f'<div data-battle-side="{side}"'
        f' data-fallen="{len(report.fallen)}"'
        f' data-stunned="{len(report.stunned)}"'
        f' data-active="{len(report.active)}"'
        "></div>"
    )


def render_battle_report(battle: HexBattle) -> str:
    """Return a parsable HTML fragment for ``battle.report()``.

    Root is ``<div data-battle-report="">`` with a ``data-battle-result`` child
    (value = ``report.result.value`` plus visible text matching that result)
    and one ``data-battle-side`` child per side (attacker then defender)
    carrying ``data-fallen`` / ``data-stunned`` / ``data-active`` counts.
    Pure and deterministic: no RNG/IO; ``battle`` is not mutated.
    """
    report = battle.report()
    result_text = _RESULT_TEXT[report.result]
    return (
        '<div data-battle-report="">'
        f'<div data-battle-result="{report.result.value}">{result_text}</div>'
        f"{_side_div('attacker', report.attacker)}"
        f"{_side_div('defender', report.defender)}"
        "</div>"
    )
