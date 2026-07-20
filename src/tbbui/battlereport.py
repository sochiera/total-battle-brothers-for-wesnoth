"""Deterministic HTML fragment for a finished hex-battle report."""

from __future__ import annotations

from tbb.battle import BattleResult, BattleSideReport, HexBattle

_RESULT_TEXT = {
    BattleResult.ATTACKER_WIN: "Zwycięstwo atakującego",
    BattleResult.DEFENDER_WIN: "Zwycięstwo broniącego",
    BattleResult.DRAW: "Remis",
}

_SIDE_LABEL = {
    "attacker": "Atakujący",
    "defender": "Broniący",
}


def _side_div(side: str, report: BattleSideReport) -> str:
    fallen = len(report.fallen)
    stunned = len(report.stunned)
    active = len(report.active)
    label = _SIDE_LABEL[side]
    text = f"{label}: polegli {fallen}, ogłuszeni {stunned}, zdolni {active}"
    return (
        f'<div data-battle-side="{side}"'
        f' data-fallen="{fallen}"'
        f' data-stunned="{stunned}"'
        f' data-active="{active}"'
        f">{text}</div>"
    )


def render_battle_report(battle: HexBattle) -> str:
    """Return a parsable HTML fragment for ``battle.report()``.

    Root is ``<div data-battle-report="">`` with a ``data-battle-result`` child
    (value = ``report.result.value`` plus visible text matching that result)
    and one ``data-battle-side`` child per side (attacker then defender)
    carrying ``data-fallen`` / ``data-stunned`` / ``data-active`` counts plus
    a human-readable casualty line matching those counts.
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
