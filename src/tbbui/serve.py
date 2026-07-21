"""Interactive preview: request routing + thin http.server adapter (V13.5)."""

from __future__ import annotations

import http.server
from html import escape
from urllib.parse import parse_qs, quote, unquote_plus

from tbb import ai
from tbb.driver import run_headless_game
from tbb.duchy import Duchy
from tbb.game import GameState, create_headless_game
from tbb.rng import Rng
import tbb.settlement as settlement_module
from tbb.turn import Calendar
from tbb.world import Region, WorldMap
from tbbui.battlereport import attacker_losses, battle_outcome_text
from tbbui.gamepage import render_game_page
from tbbui.orderlog import format_log_entry, render_order_log
from tbbui.recommendedaction import recommended_order, recommended_order_text

ORDER_LOG_LIMIT = 10

_NEW_GAME_FORM = (
    '<form method="post" action="/new">'
    '<button type="submit">Nowa gra</button>'
    "</form>"
)

_TURN_FORM = (
    '<form method="post" action="/turn">'
    '<button type="submit">Następna tura</button>'
    "</form>"
)


def _recruit_form() -> str:
    """POST /order/recruit form; label cost from core ``RECRUIT_GOLD_COST`` (K30.2a)."""
    cost = settlement_module.RECRUIT_GOLD_COST
    return (
        '<form method="post" action="/order/recruit">'
        f'<button type="submit">Rekrutuj (koszt złota: {cost})</button>'
        "</form>"
    )

_MUSTER_FORM = (
    '<form method="post" action="/order/muster">'
    '<button type="submit">Zbierz oddział</button>'
    "</form>"
)

_DEVELOP_FORM = (
    '<form method="post" action="/order/develop">'
    '<button type="submit">Rozbuduj osadę</button>'
    "</form>"
)

_MARCH_FORM = (
    '<form method="post" action="/order/march">'
    '<button type="submit">Marsz</button>'
    "</form>"
)

_ASSAULT_FORM = (
    '<form method="post" action="/order/assault">'
    '<button type="submit">Szturm</button>'
    "</form>"
)

_ENGAGE_FORM = (
    '<form method="post" action="/order/engage">'
    '<button type="submit">Starcie</button>'
    "</form>"
)

_DEVELOP_SECTION_HEADER = '<h2 data-order-section="develop">Rozwój</h2>'
_MARCH_SECTION_HEADER = '<h2 data-order-section="march">Marsz</h2>'
_ASSAULT_SECTION_HEADER = '<h2 data-order-section="assault">Szturm</h2>'
_ENGAGE_SECTION_HEADER = '<h2 data-order-section="engage">Starcie</h2>'

_RECOMMENDED_ORDER_PATHS = {
    "assault": "/order/assault",
    "engage": "/order/engage",
    "defend": "/order/march",
    "develop": "/order/develop",
}


def recommended_order_path(action: str) -> str:
    """Map recommendation machine action to an existing POST order route (K42.1b).

    Pure and deterministic: ``assault``/``engage``/``develop`` keep their
    names; ``defend`` reuses ``/order/march`` (move the party to the threatened
    position). Unknown actions raise ``KeyError``.
    """
    return _RECOMMENDED_ORDER_PATHS[action]


def _march_targets(world: WorldMap, player_duchy_id: str) -> tuple[Region, ...]:
    """Regions with a foreign-owned settlement, in ``world.regions`` order."""
    return tuple(
        region
        for region in world.regions
        if (settlement := world.settlement_at(region)) is not None
        and settlement.owner_id != player_duchy_id
    )


def _engage_targets(world: WorldMap, player_duchy_id: str) -> tuple[Region, ...]:
    """Neighbor regions holding an enemy party, in ``world.neighbors`` order.

    Uses the first map region occupied by a party with ``owner_id ==
    player_duchy_id`` (same pick as ``ai._duchy_party_position``). Empty when
    the player has no party on the map. A neighbor is a target only when it
    holds a party with an explicit ``owner_id != player_duchy_id``.
    """
    position = next(
        (
            region
            for region in world.regions
            if (party := world.party_at(region)) is not None
            and party.owner_id == player_duchy_id
        ),
        None,
    )
    if position is None:
        return ()
    return tuple(
        neighbor
        for neighbor in world.neighbors(position)
        if (other := world.party_at(neighbor)) is not None
        and other.owner_id is not None
        and other.owner_id != player_duchy_id
    )


def _duchy_has_party(world: WorldMap, duchy_id: str) -> bool:
    """True when a party with ``owner_id == duchy_id`` is on the map."""
    return any(
        (party := world.party_at(region)) is not None and party.owner_id == duchy_id
        for region in world.regions
    )


class GameApp:
    """In-memory request router over one party snapshot (GET page / POST turn)."""

    def __init__(
        self,
        world: WorldMap,
        game: GameState,
        calendar: Calendar,
        rng: Rng,
        player_duchy_id: str | None = None,
        seed: int | None = None,
    ) -> None:
        self.world = world
        self.game = game
        self.calendar = calendar
        self.rng = rng
        self.player_duchy_id = player_duchy_id
        self.seed = seed
        self.last_battle = None
        self.previous_game: GameState | None = None
        self.last_notice = ""
        self.order_log: list[str] = []

    def _append_order_log(self, notice: str) -> None:
        """Append date-anchored notice; keep only last ``ORDER_LOG_LIMIT`` entries."""
        self.order_log.append(format_log_entry(notice, self.calendar))
        overflow = len(self.order_log) - ORDER_LOG_LIMIT
        if overflow > 0:
            del self.order_log[:overflow]

    def handle(self, method: str, path: str) -> tuple[int, str]:
        """Route one request; return ``(http_status, body)`` without sockets."""
        route, _, query = path.partition("?")
        if method == "GET" and route == "/":
            return 200, self._render()
        if method == "POST" and route == "/new":
            self.previous_game = None
            self.order_log.clear()
            if self.seed is not None:
                self.world, self.game = create_headless_game()
                self.calendar = Calendar()
                self.rng = Rng(self.seed)
                self.last_battle = None
                self.last_notice = "Nowa gra: rok 1, miesiąc 1"
            else:
                self.last_notice = "Nowa gra: brak zmian"
            self._append_order_log(self.last_notice)
            return 200, self._render()
        if method == "POST" and route == "/turn":
            self.last_battle = None
            if not self.game.is_over:
                game_before = self.game
                self.world, self.game, self.calendar = run_headless_game(
                    self.world,
                    self.game,
                    self.rng,
                    max_turns=1,
                    calendar=self.calendar,
                    player_duchy_id=self.player_duchy_id,
                )
                self.previous_game = game_before
                self.last_notice = (
                    f"Następna tura: rok {self.calendar.year}, "
                    f"miesiąc {self.calendar.month}"
                )
            else:
                self.previous_game = None
                self.last_notice = "Następna tura: gra zakończona"
            self._append_order_log(self.last_notice)
            return 200, self._render()
        if method == "POST" and route == "/order/recruit":
            self.last_battle = None
            self.previous_game = None
            self._apply_player_order(ai.recruit_duchy_unit, "Rekrutacja")
            self._append_order_log(self.last_notice)
            return 200, self._render()
        if method == "POST" and route == "/order/muster":
            self.last_battle = None
            self.previous_game = None
            self._apply_player_order(ai.muster_duchy_party, "Zebranie oddziału")
            self._append_order_log(self.last_notice)
            return 200, self._render()
        if method == "POST" and route == "/order/develop":
            self.last_battle = None
            self.previous_game = None
            self._apply_player_order(ai.develop_duchy_settlement, "Rozbudowa")
            self._append_order_log(self.last_notice)
            return 200, self._render()
        if method == "POST" and route == "/order/march":
            self.last_battle = None
            self.previous_game = None
            target_region = self._order_target_region(query)
            if target_region is not None:
                self._apply_player_order(
                    lambda world, duchy: ai.march_duchy_party_to(
                        world, duchy, target_region
                    ),
                    f"Marsz do {target_region.name}",
                )
            else:
                self._apply_player_order(ai.march_duchy_party, "Marsz")
            self._append_order_log(self.last_notice)
            return 200, self._render()
        if method == "POST" and route == "/order/assault":
            self.previous_game = None
            morale_by_owner = {d.duchy_id: d.morale for d in self.game.duchies}
            target_region = self._order_target_region(query)
            if target_region is not None:
                self._apply_player_assault_order(
                    lambda world, duchy: ai.assault_duchy_party_to_recorded(
                        world,
                        duchy,
                        target_region,
                        self.rng,
                        morale_by_owner=morale_by_owner,
                    ),
                    f"Szturm na {target_region.name}",
                )
            else:
                self._apply_player_assault_order(
                    lambda world, duchy: ai.assault_duchy_party_recorded(
                        world,
                        duchy,
                        self.rng,
                        morale_by_owner=morale_by_owner,
                    ),
                    "Szturm",
                )
            self._append_order_log(self.last_notice)
            return 200, self._render()
        if method == "POST" and route == "/order/engage":
            self.previous_game = None
            morale_by_owner = {d.duchy_id: d.morale for d in self.game.duchies}
            target_region = self._order_target_region(query)
            if target_region is not None:
                self._apply_player_assault_order(
                    lambda world, duchy: ai.engage_duchy_party_to_recorded(
                        world,
                        duchy,
                        target_region,
                        self.rng,
                        morale_by_owner=morale_by_owner,
                    ),
                    f"Starcie z {target_region.name}",
                )
            else:
                self._apply_player_assault_order(
                    lambda world, duchy: ai.engage_duchy_party_recorded(
                        world,
                        duchy,
                        self.rng,
                        morale_by_owner=morale_by_owner,
                    ),
                    "Starcie",
                )
            self._append_order_log(self.last_notice)
            return 200, self._render()
        return 404, "Not Found"

    def _order_target_region(self, query: str):
        """Resolve non-empty ``target`` query to a known ``Region``, else ``None``."""
        if not query:
            return None
        values = parse_qs(query, keep_blank_values=True).get("target", [])
        if not values:
            return None
        name = unquote_plus(values[0]).strip()
        if not name:
            return None
        for region in self.world.regions:
            if region.name == name:
                return region
        return None

    def _resolve_player_duchy(self) -> Duchy | None:
        """Return the player duchy when a player order is legal, else ``None``.

        ``None`` when the game is over, there is no ``player_duchy_id``, or that
        duchy is absent from ``game.duchies``. Shared by ``_apply_player_order``
        and ``_apply_player_assault_order`` (R29.1).
        """
        if self.game.is_over or self.player_duchy_id is None:
            return None
        return next(
            (d for d in self.game.duchies if d.duchy_id == self.player_duchy_id),
            None,
        )

    def _apply_player_order(self, transition, label: str | None = None) -> None:
        """Apply ``transition(world, player_duchy)`` when a player order is legal.

        No-op when the game is over, there is no player duchy id, or that
        duchy is absent from ``game.duchies``. On success replaces ``world``
        and re-syncs ``game`` from the new map. When ``label`` is set, updates
        ``last_notice`` to ``"{label}: wykonano"`` if ``world`` changed, else
        ``"{label}: brak zmian"`` (including guard rejections). When ``label``
        is ``None``, leaves ``last_notice`` unchanged.
        """
        player_duchy = self._resolve_player_duchy()
        if player_duchy is None:
            if label is not None:
                self.last_notice = f"{label}: brak zmian"
            return
        previous_world = self.world
        self.world = transition(self.world, player_duchy)
        self.game = self.game.sync_from_world(self.world)
        if label is not None:
            if self.world != previous_world:
                self.last_notice = f"{label}: wykonano"
            else:
                self.last_notice = f"{label}: brak zmian"

    def _apply_player_assault_order(self, transition, label: str) -> None:
        """Apply recorded assault ``transition(world, duchy) -> (world, battle)``.

        Same guards as ``_apply_player_order`` via ``_resolve_player_duchy``.
        On success replaces ``world``, re-syncs ``game``, and when ``battle``
        is not ``None`` sets ``self.last_battle``. No-op paths leave
        ``last_battle`` unchanged. Always sets ``last_notice`` to
        ``f"{label}: {battle_outcome_text(battle)} (straty: {attacker_losses(battle)})"``
        when a battle was recorded (K46.1b / K46.2b), else
        ``"{label}: brak zmian"`` (including guard rejections).
        """
        player_duchy = self._resolve_player_duchy()
        if player_duchy is None:
            self.last_notice = f"{label}: brak zmian"
            return
        self.world, battle = transition(self.world, player_duchy)
        if battle is not None:
            self.last_battle = battle
            self.last_notice = (
                f"{label}: {battle_outcome_text(battle)} "
                f"(straty: {attacker_losses(battle)})"
            )
        else:
            self.last_notice = f"{label}: brak zmian"
        self.game = self.game.sync_from_world(self.world)

    @staticmethod
    def _emit_target_forms(order_path: str, targets) -> str:
        """Emit per-target POST forms: ``{order_path}?target=quote(name)`` + button.

        Shared HTML shape for march, assault, and engage (R21.1). Callers supply
        ``order_path`` and the target region sequence; empty ``targets`` yields ``""``.
        """
        forms: list[str] = []
        for region in targets:
            action = f"{order_path}?target={quote(region.name)}"
            forms.append(
                f'<form method="post" action="{action}">'
                f'<button type="submit">{region.name}</button>'
                "</form>"
            )
        return "".join(forms)

    def _target_forms(self, order_path: str, bare_form: str) -> str:
        """Per-target order forms when the player has a party; bare fallback otherwise.

        Shared by march and assault (same guard and ``_march_targets``); only
        ``order_path`` and ``bare_form`` differ. Forms via ``_emit_target_forms``.
        """
        if (
            self.player_duchy_id is not None
            and not self.game.is_over
            and _duchy_has_party(self.world, self.player_duchy_id)
        ):
            return self._emit_target_forms(
                order_path, _march_targets(self.world, self.player_duchy_id)
            )
        return bare_form

    def _march_forms(self) -> str:
        """Per-target march forms when the player has a party; bare fallback otherwise."""
        return self._target_forms("/order/march", _MARCH_FORM)

    def _assault_forms(self) -> str:
        """Per-target assault forms when the player has a party; bare fallback otherwise."""
        return self._target_forms("/order/assault", _ASSAULT_FORM)

    def _engage_forms(self) -> str:
        """Per-target engage forms for adjacent enemy parties; bare fallback otherwise.

        Unlike march/assault (foreign settlements anywhere), engage targets are
        neighbors of the player party only. Bare ``_ENGAGE_FORM`` when there is
        no player id, the game is over, or ``_engage_targets`` is empty.
        Forms via ``_emit_target_forms`` (same HTML shape as march/assault).
        """
        if (
            self.player_duchy_id is not None
            and not self.game.is_over
        ):
            targets = _engage_targets(self.world, self.player_duchy_id)
            if targets:
                return self._emit_target_forms("/order/engage", targets)
        return _ENGAGE_FORM

    def _recommended_order_form(self) -> str:
        """One-click form for the K41 recommendation when player/advice allow (K42.1c/K42.2a).

        Empty string when ``player_duchy_id`` is missing, the game is over, or
        ``recommended_order`` returns ``None``. Otherwise a single POST form
        with ``data-recommended-order=""``; ``action`` is
        ``recommended_order_path(action)`` plus ``?target=quote(region)`` when
        the recommendation names a region (no target suffix for ``develop``).
        Button label is ``Wykonaj zalecenie: {recommended_order_text(...)}``
        (html-escaped).
        """
        if self.player_duchy_id is None or self.game.is_over:
            return ""
        order = recommended_order(self.world, self.game, self.player_duchy_id)
        if order is None:
            return ""
        action, region = order
        path = recommended_order_path(action)
        if region is not None:
            path = f"{path}?target={quote(region)}"
        label = escape(f"Wykonaj zalecenie: {recommended_order_text(action, region)}")
        return (
            f'<form method="post" action="{path}" data-recommended-order="">'
            f'<button type="submit">{label}</button>'
            "</form>"
        )

    def _render(self) -> str:
        html = render_game_page(
            self.world,
            self.game,
            self.calendar,
            battle=self.last_battle,
            player_duchy_id=self.player_duchy_id,
            previous_game=self.previous_game,
        )
        player_value = self.player_duchy_id if self.player_duchy_id is not None else ""
        notice_value = escape(self.last_notice, quote=True)
        extras = (
            f'<span data-player="{player_value}"></span>'
            f'<p data-notice="{notice_value}">{notice_value}</p>'
            f"{render_order_log(self.order_log, at_limit=len(self.order_log) >= ORDER_LOG_LIMIT)}"
            f"{_NEW_GAME_FORM}"
        )
        # K32.2a: when finished, omit turn and all order sections.
        if not self.game.is_over:
            extras += (
                f"{_TURN_FORM}"
                f"{self._recommended_order_form()}"
                f"{_DEVELOP_SECTION_HEADER}{_recruit_form()}{_MUSTER_FORM}"
                f"{_DEVELOP_FORM}"
                f"{_MARCH_SECTION_HEADER}{self._march_forms()}"
                f"{_ASSAULT_SECTION_HEADER}{self._assault_forms()}"
                f"{_ENGAGE_SECTION_HEADER}{self._engage_forms()}"
            )
        if "</body>" in html:
            return html.replace("</body>", f"{extras}</body>", 1)
        return f"{html}{extras}"


def handle_request(app: GameApp, method: str, path: str) -> tuple[int, bytes]:
    """Thin adapter: ``app.handle`` → ``(status, UTF-8 body bytes)`` (no socket)."""
    code, body = app.handle(method, path)
    return code, body.encode("utf-8")


def make_server(
    app: GameApp,
    host: str = "127.0.0.1",
    port: int = 0,
) -> http.server.HTTPServer:
    """Bind ``HTTPServer`` whose GET/POST handlers delegate to ``handle_request``.

    Does not call ``serve_forever``; the caller owns the lifecycle
    (``serve_forever`` / ``server_close``).
    """

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._dispatch("GET")

        def do_POST(self) -> None:
            self._dispatch("POST")

        def _dispatch(self, method: str) -> None:
            code, body = handle_request(app, method, self.path)
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            # Quiet by default — preview is local and tests bind real ports.
            return

    return http.server.HTTPServer((host, port), _Handler)
