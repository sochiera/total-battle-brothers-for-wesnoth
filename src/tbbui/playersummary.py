"""Deterministic HTML fragment summarizing the player duchy economy and strength."""

from __future__ import annotations

from tbb.game import GameState
from tbbui.gamelookup import player_duchy
from tbbui.unitstrength import combat_totals


def render_player_summary(
    game: GameState, player_duchy_id: str | None = None
) -> str:
    """Return a parsable HTML fragment with the player duchy summary.

    Root is ``<div data-player-summary="">``. When ``player_duchy_id`` matches a
    duchy in ``game.duchies``, the root carries ``data-settlements`` /
    ``data-parties`` (counts), ``data-gold`` / ``data-wheat`` (sums of
    ``settlement.storage`` over that duchy), ``data-wheat-production`` /
    ``data-gold-production`` / ``data-wheat-consumption`` (sums of
    ``settlement.production.wheat`` / ``settlement.production.gold`` /
    ``settlement.consumption.wheat`` over ``duchy.settlements``; empty duchy
    → ``0``/``0``/``0``; gold-production immediately after wheat-production,
    before wheat-consumption), ``data-wheat-surplus`` (``"true"`` when
    production sum ``>=`` consumption sum, else ``"false"``; empty duchy →
    ``"true"``), ``data-wheat-net`` (``str(production − consumption)`` with
    sign; empty duchy → ``"0"``), immediately after ``data-wheat`` and before
    ``data-hp`` / ``data-attack`` / ``data-defense`` from ``combat_totals``
    over every unit (hero + subordinates) of each party in ``duchy.parties``,
    and visible text ``Twoje księstwo: osady N, oddziały M · pszenica W,
    złoto G · siła oddziałów: HP H, atak A, obrona D · produkcja/mies.: +Pw
    pszenicy · konsumpcja: Cw pszenicy · bilans pszenicy: nadwyżka|deficyt
    · saldo pszenicy/mies.: {net:+d}`` (Pw/Cw match the production/consumption
    attributes; bilans matches ``data-wheat-surplus``: ``true`` → nadwyżka,
    ``false`` → deficyt; saldo matches ``data-wheat-net``, always signed).
    When ``player_duchy_id`` is ``None`` or not present in ``game.duchies``,
    returns a bare empty root. Pure and deterministic: no RNG/IO; ``game``
    is not mutated.
    """
    duchy = player_duchy(game, player_duchy_id)
    if duchy is None:
        return '<div data-player-summary=""></div>'

    n_settlements = len(duchy.settlements)
    n_parties = len(duchy.parties)
    gold = sum(s.storage.gold for s in duchy.settlements)
    wheat = sum(s.storage.wheat for s in duchy.settlements)
    wheat_production = sum(s.production.wheat for s in duchy.settlements)
    gold_production = sum(s.production.gold for s in duchy.settlements)
    wheat_consumption = sum(s.consumption.wheat for s in duchy.settlements)
    wheat_net = wheat_production - wheat_consumption
    wheat_surplus = (
        "true" if wheat_production >= wheat_consumption else "false"
    )
    bilans_label = "nadwyżka" if wheat_surplus == "true" else "deficyt"
    units = tuple(
        unit
        for party in duchy.parties
        for unit in (party.hero, *party.units)
    )
    total_hp, total_attack, total_defense = combat_totals(units)
    text = (
        f"Twoje księstwo: osady {n_settlements}, oddziały {n_parties}"
        f" · pszenica {wheat}, złoto {gold}"
        f" · siła oddziałów: HP {total_hp}, atak {total_attack},"
        f" obrona {total_defense}"
        f" · produkcja/mies.: +{wheat_production} pszenicy"
        f" · konsumpcja: {wheat_consumption} pszenicy"
        f" · bilans pszenicy: {bilans_label}"
        f" · saldo pszenicy/mies.: {wheat_net:+d}"
    )
    return (
        f'<div data-player-summary=""'
        f' data-settlements="{n_settlements}"'
        f' data-parties="{n_parties}"'
        f' data-gold="{gold}"'
        f' data-wheat="{wheat}"'
        f' data-wheat-production="{wheat_production}"'
        f' data-gold-production="{gold_production}"'
        f' data-wheat-consumption="{wheat_consumption}"'
        f' data-wheat-surplus="{wheat_surplus}"'
        f' data-wheat-net="{wheat_net}"'
        f' data-hp="{total_hp}"'
        f' data-attack="{total_attack}"'
        f' data-defense="{total_defense}"'
        f">{text}</div>"
    )
