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
    ``data-wheat-consumption`` (sums of ``settlement.production.wheat`` /
    ``settlement.consumption.wheat`` over ``duchy.settlements``; empty duchy
    → ``0``/``0``), immediately after ``data-wheat`` and before ``data-hp`` /
    ``data-attack`` / ``data-defense`` from ``combat_totals`` over every unit
    (hero + subordinates) of each party in ``duchy.parties``, and visible text
    ``Twoje księstwo: osady N, oddziały M · pszenica W, złoto G · siła
    oddziałów: HP H, atak A, obrona D · produkcja/mies.: +Pw pszenicy ·
    konsumpcja: Cw pszenicy`` (Pw/Cw match the production/consumption
    attributes). When ``player_duchy_id`` is ``None`` or not present in
    ``game.duchies``, returns a bare empty root. Pure and deterministic: no
    RNG/IO; ``game`` is not mutated.
    """
    duchy = player_duchy(game, player_duchy_id)
    if duchy is None:
        return '<div data-player-summary=""></div>'

    n_settlements = len(duchy.settlements)
    n_parties = len(duchy.parties)
    gold = sum(s.storage.gold for s in duchy.settlements)
    wheat = sum(s.storage.wheat for s in duchy.settlements)
    wheat_production = sum(s.production.wheat for s in duchy.settlements)
    wheat_consumption = sum(s.consumption.wheat for s in duchy.settlements)
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
    )
    return (
        f'<div data-player-summary=""'
        f' data-settlements="{n_settlements}"'
        f' data-parties="{n_parties}"'
        f' data-gold="{gold}"'
        f' data-wheat="{wheat}"'
        f' data-wheat-production="{wheat_production}"'
        f' data-wheat-consumption="{wheat_consumption}"'
        f' data-hp="{total_hp}"'
        f' data-attack="{total_attack}"'
        f' data-defense="{total_defense}"'
        f">{text}</div>"
    )
