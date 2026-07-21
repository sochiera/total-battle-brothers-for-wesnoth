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

_OUTCOME_FROM_ATTACKER = {
    BattleResult.ATTACKER_WIN: "zwycięstwo",
    BattleResult.DEFENDER_WIN: "porażka",
    BattleResult.DRAW: "remis",
}


def battle_outcome_text(battle: HexBattle) -> str:
    """Map a finished battle's result to a short word from the attacker's view.

    ``ATTACKER_WIN`` → ``"zwycięstwo"``, ``DEFENDER_WIN`` → ``"porażka"``,
    ``DRAW`` → ``"remis"``. Raises ``ValueError`` if the battle is unfinished
    (``battle.result() is None``). Pure: reads only ``battle.result()``;
    does not mutate ``battle``.
    """
    result = battle.result()
    if result is None:
        raise ValueError("battle is not finished")
    return _OUTCOME_FROM_ATTACKER[result]


def attacker_losses(battle: HexBattle) -> int:
    """Return the number of fallen attacker units for a finished battle.

    Equals ``len(battle.report().attacker.fallen)``. Raises ``ValueError`` if
    the battle is unfinished (via ``battle.report()``). Pure: reads only
    ``battle.report()``; does not mutate ``battle``.
    """
    return len(battle.report().attacker.fallen)


def defender_losses(battle: HexBattle) -> int:
    """Return the number of fallen defender units for a finished battle.

    Equals ``len(battle.report().defender.fallen)``. Raises ``ValueError`` if
    the battle is unfinished (via ``battle.report()``). Pure: reads only
    ``battle.report()``; does not mutate ``battle``.
    """
    return len(battle.report().defender.fallen)


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
