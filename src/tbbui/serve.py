"""Interactive preview: request routing + thin http.server adapter (V13.5)."""

from __future__ import annotations

import http.server
from urllib.parse import parse_qs, quote, unquote_plus

from tbb import ai
from tbb.driver import run_headless_game
from tbb.game import GameState
from tbb.rng import Rng
from tbb.turn import Calendar
from tbb.world import Region, WorldMap
from tbbui.gamepage import render_game_page

_TURN_FORM = (
    '<form method="post" action="/turn">'
    '<button type="submit">Next turn</button>'
    "</form>"
)

_RECRUIT_FORM = (
    '<form method="post" action="/order/recruit">'
    '<button type="submit">Recruit</button>'
    "</form>"
)

_MUSTER_FORM = (
    '<form method="post" action="/order/muster">'
    '<button type="submit">Muster</button>'
    "</form>"
)

_DEVELOP_FORM = (
    '<form method="post" action="/order/develop">'
    '<button type="submit">Develop settlement</button>'
    "</form>"
)

_MARCH_FORM = (
    '<form method="post" action="/order/march">'
    '<button type="submit">March</button>'
    "</form>"
)

_ASSAULT_FORM = (
    '<form method="post" action="/order/assault">'
    '<button type="submit">Assault</button>'
    "</form>"
)


def _march_targets(world: WorldMap, player_duchy_id: str) -> tuple[Region, ...]:
    """Regions with a foreign-owned settlement, in ``world.regions`` order."""
    return tuple(
        region
        for region in world.regions
        if (settlement := world.settlement_at(region)) is not None
        and settlement.owner_id != player_duchy_id
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
    ) -> None:
        self.world = world
        self.game = game
        self.calendar = calendar
        self.rng = rng
        self.player_duchy_id = player_duchy_id
        self.last_battle = None

    def handle(self, method: str, path: str) -> tuple[int, str]:
        """Route one request; return ``(http_status, body)`` without sockets."""
        route, _, query = path.partition("?")
        if method == "GET" and route == "/":
            return 200, self._render()
        if method == "POST" and route == "/turn":
            self.last_battle = None
            if not self.game.is_over:
                self.world, self.game, self.calendar = run_headless_game(
                    self.world,
                    self.game,
                    self.rng,
                    max_turns=1,
                    calendar=self.calendar,
                    player_duchy_id=self.player_duchy_id,
                )
            return 200, self._render()
        if method == "POST" and route == "/order/recruit":
            self.last_battle = None
            self._apply_player_order(ai.recruit_duchy_unit)
            return 200, self._render()
        if method == "POST" and route == "/order/muster":
            self.last_battle = None
            self._apply_player_order(ai.muster_duchy_party)
            return 200, self._render()
        if method == "POST" and route == "/order/develop":
            self.last_battle = None
            self._apply_player_order(ai.develop_duchy_settlement)
            return 200, self._render()
        if method == "POST" and route == "/order/march":
            self.last_battle = None
            target_region = self._order_target_region(query)
            if target_region is not None:
                self._apply_player_order(
                    lambda world, duchy: ai.march_duchy_party_to(
                        world, duchy, target_region
                    )
                )
            else:
                self._apply_player_order(ai.march_duchy_party)
            return 200, self._render()
        if method == "POST" and route == "/order/assault":
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
                    )
                )
            else:
                self._apply_player_assault_order(
                    lambda world, duchy: ai.assault_duchy_party_recorded(
                        world,
                        duchy,
                        self.rng,
                        morale_by_owner=morale_by_owner,
                    )
                )
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

    def _apply_player_order(self, transition) -> None:
        """Apply ``transition(world, player_duchy)`` when a player order is legal.

        No-op when the game is over, there is no player duchy id, or that
        duchy is absent from ``game.duchies``. On success replaces ``world``
        and re-syncs ``game`` from the new map.
        """
        if self.game.is_over or self.player_duchy_id is None:
            return
        player_duchy = next(
            (d for d in self.game.duchies if d.duchy_id == self.player_duchy_id),
            None,
        )
        if player_duchy is None:
            return
        self.world = transition(self.world, player_duchy)
        self.game = self.game.sync_from_world(self.world)

    def _apply_player_assault_order(self, transition) -> None:
        """Apply recorded assault ``transition(world, duchy) -> (world, battle)``.

        Same guards as ``_apply_player_order``. On success replaces ``world``,
        re-syncs ``game``, and when ``battle`` is not ``None`` sets
        ``self.last_battle``. No-op paths leave ``last_battle`` unchanged.
        """
        if self.game.is_over or self.player_duchy_id is None:
            return
        player_duchy = next(
            (d for d in self.game.duchies if d.duchy_id == self.player_duchy_id),
            None,
        )
        if player_duchy is None:
            return
        self.world, battle = transition(self.world, player_duchy)
        if battle is not None:
            self.last_battle = battle
        self.game = self.game.sync_from_world(self.world)

    def _march_forms(self) -> str:
        """Per-target march forms when the player has a party; bare fallback otherwise."""
        if (
            self.player_duchy_id is not None
            and not self.game.is_over
            and _duchy_has_party(self.world, self.player_duchy_id)
        ):
            forms: list[str] = []
            for region in _march_targets(self.world, self.player_duchy_id):
                action = f"/order/march?target={quote(region.name)}"
                forms.append(
                    f'<form method="post" action="{action}">'
                    f'<button type="submit">{region.name}</button>'
                    "</form>"
                )
            return "".join(forms)
        return _MARCH_FORM

    def _assault_forms(self) -> str:
        """Per-target assault forms when the player has a party; bare fallback otherwise."""
        if (
            self.player_duchy_id is not None
            and not self.game.is_over
            and _duchy_has_party(self.world, self.player_duchy_id)
        ):
            forms: list[str] = []
            for region in _march_targets(self.world, self.player_duchy_id):
                action = f"/order/assault?target={quote(region.name)}"
                forms.append(
                    f'<form method="post" action="{action}">'
                    f'<button type="submit">{region.name}</button>'
                    "</form>"
                )
            return "".join(forms)
        return _ASSAULT_FORM

    def _render(self) -> str:
        html = render_game_page(
            self.world, self.game, self.calendar, battle=self.last_battle
        )
        player_value = self.player_duchy_id if self.player_duchy_id is not None else ""
        extras = (
            f'<span data-player="{player_value}"></span>'
            f"{_TURN_FORM}{_RECRUIT_FORM}{_MUSTER_FORM}"
            f"{_DEVELOP_FORM}{self._march_forms()}{self._assault_forms()}"
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
