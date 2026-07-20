"""Interactive preview routing: GameApp.handle without a real HTTP socket (V13.5a)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import tbb.ai as ai
from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.resources import Resources
from tbb.rng import Rng
from tbb.settlement import Settlement
from tbb.turn import Calendar
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.serve import GameApp


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find_by_attr(root: ET.Element, attr: str) -> list[ET.Element]:
    return [el for el in root.iter() if el.get(attr) is not None]


def _calendar_stamp(html: str) -> tuple[int, int]:
    root = ET.fromstring(html)
    calendars = _find_by_attr(root, "data-calendar")
    assert len(calendars) == 1
    return int(calendars[0].get("data-year")), int(calendars[0].get("data-month"))


def _has_post_turn_form(html: str) -> bool:
    """True when body contains a form that POSTs to /turn (contract V13.5a)."""
    return _has_post_form(html, "/turn")


def _has_post_recruit_form(html: str) -> bool:
    """True when body contains a form that POSTs to /order/recruit (K14.2a)."""
    return _has_post_form(html, "/order/recruit")


def _has_post_form(html: str, action_path: str) -> bool:
    """True when body contains a form that POSTs to ``action_path``."""
    root = ET.fromstring(html)
    for el in root.iter():
        if _local(el.tag) != "form":
            continue
        method = (el.get("method") or "").lower()
        action = el.get("action") or ""
        if method == "post" and action == action_path:
            return True
    # Fallback: tolerate attribute order / spacing in raw HTML.
    escaped = re.escape(action_path)
    return bool(
        re.search(
            rf'<form\b[^>]*\bmethod=["\']post["\'][^>]*\baction=["\']{escaped}["\']',
            html,
            flags=re.IGNORECASE,
        )
        or re.search(
            rf'<form\b[^>]*\baction=["\']{escaped}["\'][^>]*\bmethod=["\']post["\']',
            html,
            flags=re.IGNORECASE,
        )
    )


def _ongoing_world_game() -> tuple[WorldMap, GameState]:
    north, south = map(Region, ("North", "South"))
    north_keep = Settlement("North Keep", 2, owner_id="north")
    south_keep = Settlement("South Keep", 2, owner_id="south")
    world = WorldMap(
        (north, south), settlements={north: north_keep, south: south_keep}
    )
    game = GameState(
        (
            Duchy("north", Unit(), settlements=(north_keep,)),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )
    return world, game


def _finished_world_game() -> tuple[WorldMap, GameState]:
    """Game already over: sole undefeated duchy remains."""
    north = Region("North")
    keep = Settlement("North Keep", 2, owner_id="north")
    world = WorldMap((north,), settlements={north: keep})
    game = GameState(
        (
            Duchy("north", Unit(), settlements=(keep,)),
            Duchy("south", None, morale=0, settlements=()),
        )
    )
    assert game.is_over
    return world, game


def test_game_app_handle_get_turn_404_noop_and_determinism():
    """GameApp.handle: GET form, POST one turn, is_over no-op, 404, seed det.

    Contract (task-074 / V13.5a):
    - GET / → (200, page) with form method=post action=/turn
    - POST /turn → exactly one headless turn; calendar/state advance; 200
    - when game.is_over before request, POST /turn is no-op (200, same state)
    - other path/method → 404
    - same seed + same handle sequence → identical bodies and state
    """
    world, game = _ongoing_world_game()
    calendar = Calendar(year=4, month=9)
    app = GameApp(world, game, calendar, Rng(17))

    code, body = app.handle("GET", "/")
    assert code == 200
    assert isinstance(body, str)
    assert body.strip() != ""
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"
    assert _has_post_turn_form(body)
    assert _calendar_stamp(body) == (4, 9)
    results = _find_by_attr(root, "data-result")
    assert len(results) == 1
    assert results[0].get("data-result") == "ongoing"

    code_turn, body_after = app.handle("POST", "/turn")
    assert code_turn == 200
    assert isinstance(body_after, str)
    # One strategic turn advances the calendar by exactly one month.
    assert _calendar_stamp(body_after) == (4, 10)
    assert body_after != body
    assert _has_post_turn_form(body_after)

    code404, body404 = app.handle("GET", "/nope")
    assert code404 == 404
    assert isinstance(body404, str)

    code_bad_method, _ = app.handle("PUT", "/")
    assert code_bad_method == 404

    # Finished game: POST /turn must not advance calendar or change page body.
    fin_world, fin_game = _finished_world_game()
    fin_cal = Calendar(year=3, month=7)
    finished = GameApp(fin_world, fin_game, fin_cal, Rng(5))
    code_g, page_before = finished.handle("GET", "/")
    assert code_g == 200
    assert _calendar_stamp(page_before) == (3, 7)
    code_n, page_after = finished.handle("POST", "/turn")
    assert code_n == 200
    assert page_after == page_before
    assert _calendar_stamp(page_after) == (3, 7)

    # Determinism: two apps, same seed and request sequence → same bodies.
    w1, g1 = _ongoing_world_game()
    w2, g2 = _ongoing_world_game()
    a = GameApp(w1, g1, Calendar(year=1, month=1), Rng(73))
    b = GameApp(w2, g2, Calendar(year=1, month=1), Rng(73))
    seq = (("GET", "/"), ("POST", "/turn"), ("GET", "/"), ("POST", "/turn"))
    bodies_a = []
    bodies_b = []
    for method, path in seq:
        ca, ba = a.handle(method, path)
        cb, bb = b.handle(method, path)
        assert ca == cb
        assert ba == bb
        bodies_a.append(ba)
        bodies_b.append(bb)
    assert bodies_a == bodies_b
    assert _calendar_stamp(bodies_a[-1]) == (1, 3)


def test_game_app_player_duchy_id_data_player_and_turn_skips_player_ai(monkeypatch):
    """GameApp stores player_duchy_id; GET embeds data-player; POST /turn skips player AI.

    Contract (task-077 / K14.1b):
    - GameApp(..., player_duchy_id=None) accepts optional id at end of signature
      and stores it as self.player_duchy_id
    - GET / includes an element with data-player equal to that id (or "" when None)
    - POST /turn forwards player_duchy_id into run_headless_game so take_duchy_turn
      is not called for the player duchy (other duchies still act); still one
      strategic month (max_turns=1), returns 200 with updated page
    - player_duchy_id=None keeps previous behaviour: both duchies under AI
    """
    world, game = _ongoing_world_game()
    calendar = Calendar(year=4, month=9)
    app = GameApp(world, game, calendar, Rng(17), player_duchy_id="north")
    assert app.player_duchy_id == "north"

    code, body = app.handle("GET", "/")
    assert code == 200
    root = ET.fromstring(body)
    markers = _find_by_attr(root, "data-player")
    assert len(markers) >= 1
    assert markers[0].get("data-player") == "north"

    take_calls: list[str] = []
    real_take = ai.take_duchy_turn

    def recording_take(current_world, duchy, rng, morale_by_owner=None):
        take_calls.append(duchy.duchy_id)
        return real_take(
            current_world, duchy, rng, morale_by_owner=morale_by_owner
        )

    monkeypatch.setattr(ai, "take_duchy_turn", recording_take)

    code_turn, body_after = app.handle("POST", "/turn")
    assert code_turn == 200
    assert _calendar_stamp(body_after) == (4, 10)
    assert take_calls == ["south"]

    # Default / explicit None: no player, data-player empty, both sides AI.
    take_calls.clear()
    w2, g2 = _ongoing_world_game()
    none_app = GameApp(w2, g2, Calendar(year=1, month=1), Rng(5))
    assert none_app.player_duchy_id is None
    code_n, body_n = none_app.handle("GET", "/")
    assert code_n == 200
    root_n = ET.fromstring(body_n)
    markers_n = _find_by_attr(root_n, "data-player")
    assert len(markers_n) >= 1
    assert markers_n[0].get("data-player") == ""
    code_tn, _ = none_app.handle("POST", "/turn")
    assert code_tn == 200
    assert set(take_calls) == {"north", "south"}


def test_tbbui_serve_builds_game_app_with_player_duchy_id(monkeypatch):
    """python -m tbbui serve creates GameApp with player_duchy_id='player'.

    Contract (task-077 / K14.1b): serve branch builds GameApp with
    player_duchy_id='player' (duchy id from create_headless_game); remaining
    server construction unchanged (make_server + serve_forever lifecycle).
    """
    from tbb.game import create_headless_game
    from tbbui.__main__ import main

    captured: dict = {}

    class _FakeServer:
        server_address = ("127.0.0.1", 8765)

        def serve_forever(self) -> None:
            raise KeyboardInterrupt

        def server_close(self) -> None:
            captured["closed"] = True

    def fake_make_server(app, host="127.0.0.1", port=0):
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port
        return _FakeServer()

    monkeypatch.setattr("tbbui.__main__.make_server", fake_make_server)

    code = main(["serve"])
    assert code == 0
    app = captured["app"]
    assert isinstance(app, GameApp)
    assert app.player_duchy_id == "player"
    # player id matches the headless starting duchy from create_headless_game
    _, headless_game = create_headless_game()
    assert "player" in {d.duchy_id for d in headless_game.duchies}
    assert captured["closed"] is True
    assert captured["host"] == "127.0.0.1"


def test_game_app_post_order_recruit_applies_recruit_and_resyncs():
    """POST /order/recruit applies ai.recruit_duchy_unit + re-syncs game.

    Contract (task-078 / K14.2a):
    - when player_duchy_id is set, game is not is_over, and the player duchy
      exists in game.duchies: applies ai.recruit_duchy_unit(self.world,
      player_duchy), replaces self.world, re-syncs
      self.game = self.game.sync_from_world(self.world); returns (200, page)
    - player duchy looked up by duchy_id == player_duchy_id
    """
    north, south = map(Region, ("North", "South"))
    north_keep = Settlement(
        "North Keep",
        3,
        storage=Resources(0, 2),
        garrison=(Unit(training=1),),
        occupied=1,
        owner_id="north",
    )
    south_keep = Settlement("South Keep", 2, owner_id="south")
    world = WorldMap(
        (north, south), settlements={north: north_keep, south: south_keep}
    )
    game = GameState(
        (
            Duchy("north", Unit(), settlements=(north_keep,)),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )
    assert not game.is_over
    calendar = Calendar(year=2, month=3)
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")

    world_before = app.world
    game_before = app.game
    north_before = world_before.settlement_at(north)
    assert north_before.storage.gold == 2
    assert len(north_before.garrison) == 1
    assert north_before.occupied == 1

    expected_world = ai.recruit_duchy_unit(world_before, game_before.duchies[0])
    expected_game = game_before.sync_from_world(expected_world)
    expected_settlement = expected_world.settlement_at(north)
    assert expected_settlement is not north_before
    assert len(expected_settlement.garrison) == 2
    assert expected_settlement.occupied == 2
    assert expected_settlement.storage.gold == 1

    code, body = app.handle("POST", "/order/recruit")
    assert code == 200
    assert isinstance(body, str)
    assert body.strip() != ""
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"
    assert _calendar_stamp(body) == (2, 3)

    # World replaced with recruit result; game re-synced from that world.
    assert app.world is not world_before
    assert app.world.settlement_at(north).garrison == expected_settlement.garrison
    assert app.world.settlement_at(north).occupied == expected_settlement.occupied
    assert app.world.settlement_at(north).storage == expected_settlement.storage
    assert app.game is not game_before
    player = next(d for d in app.game.duchies if d.duchy_id == "north")
    expected_player = next(
        d for d in expected_game.duchies if d.duchy_id == "north"
    )
    assert player.settlements == expected_player.settlements
    # South and calendar untouched.
    assert app.world.settlement_at(south) is south_keep
    assert app.calendar == calendar
    # Inputs to the call must not have been mutated in place.
    assert world_before.settlement_at(north) is north_before
    assert north_before.garrison == (Unit(training=1),)
    assert north_before.storage.gold == 2


def test_game_app_order_recruit_form_noop_and_determinism():
    """GET form /order/recruit; no-op guards; recruit sequence determinism.

    Contract (task-078 / K14.2a):
    - GET / contains <form method="post" action="/order/recruit"> with a submit
    - when player_duchy_id is None, game is is_over, or player duchy is absent
      from game.duchies: POST /order/recruit is a no-op (state unchanged), still
      (200, page)
    - fixed GameApp seed + same handle sequence → identical bodies and state
    """
    def _recruit_ready_world_game() -> tuple[WorldMap, GameState, Region]:
        """World where north can actually recruit (gold + free slots)."""
        n, s = map(Region, ("North", "South"))
        nk = Settlement(
            "North Keep",
            3,
            storage=Resources(0, 2),
            garrison=(Unit(training=1),),
            occupied=1,
            owner_id="north",
        )
        sk = Settlement("South Keep", 2, owner_id="south")
        w = WorldMap((n, s), settlements={n: nk, s: sk})
        g = GameState(
            (
                Duchy("north", Unit(), settlements=(nk,)),
                Duchy("south", Unit(), settlements=(sk,)),
            )
        )
        return w, g, n

    world, game, north = _recruit_ready_world_game()
    calendar = Calendar(year=2, month=3)

    # GET / embeds the recruit form (and a button).
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")
    code_get, body_get = app.handle("GET", "/")
    assert code_get == 200
    assert _has_post_recruit_form(body_get)
    assert re.search(
        r"<button\b[^>]*>\s*Recruit\s*</button>", body_get, flags=re.IGNORECASE
    )

    # No-op: player_duchy_id is None — state frozen, still 200 + page.
    none_app = GameApp(world, game, calendar, Rng(11), player_duchy_id=None)
    world_n, game_n = none_app.world, none_app.game
    code_n, body_n = none_app.handle("POST", "/order/recruit")
    assert code_n == 200
    assert isinstance(body_n, str)
    assert none_app.world is world_n
    assert none_app.game is game_n
    assert none_app.calendar == calendar
    assert _calendar_stamp(body_n) == (2, 3)
    assert _has_post_recruit_form(body_n)
    # Would-be recruit target unchanged (gold still 2, garrison still 1).
    assert none_app.world.settlement_at(north).storage.gold == 2
    assert len(none_app.world.settlement_at(north).garrison) == 1

    # No-op: game is_over — finished sole-duchy world.
    fin_world, fin_game = _finished_world_game()
    fin_cal = Calendar(year=5, month=1)
    fin_app = GameApp(
        fin_world, fin_game, fin_cal, Rng(3), player_duchy_id="north"
    )
    w_f, g_f = fin_app.world, fin_app.game
    code_f, body_f = fin_app.handle("POST", "/order/recruit")
    assert code_f == 200
    assert fin_app.world is w_f
    assert fin_app.game is g_f
    assert fin_app.calendar == fin_cal
    assert _calendar_stamp(body_f) == (5, 1)

    # No-op: player duchy id not present in game.duchies.
    missing = GameApp(
        world, game, calendar, Rng(11), player_duchy_id="ghost"
    )
    w_m, g_m = missing.world, missing.game
    code_m, _body_m = missing.handle("POST", "/order/recruit")
    assert code_m == 200
    assert missing.world is w_m
    assert missing.game is g_m
    assert missing.calendar == calendar
    assert missing.world.settlement_at(north).storage.gold == 2
    assert len(missing.world.settlement_at(north).garrison) == 1

    # Determinism: two apps, same seed, same recruit sequence → same bodies/state.
    wa, ga, _ = _recruit_ready_world_game()
    wb, gb, _ = _recruit_ready_world_game()
    a = GameApp(wa, ga, Calendar(year=2, month=3), Rng(11), player_duchy_id="north")
    b = GameApp(wb, gb, Calendar(year=2, month=3), Rng(11), player_duchy_id="north")
    seq = (
        ("GET", "/"),
        ("POST", "/order/recruit"),
        ("GET", "/"),
        ("POST", "/order/recruit"),
    )
    bodies_a: list[str] = []
    bodies_b: list[str] = []
    for method, path in seq:
        ca, ba = a.handle(method, path)
        cb, bb = b.handle(method, path)
        assert ca == cb == 200
        assert ba == bb
        bodies_a.append(ba)
        bodies_b.append(bb)
    assert bodies_a == bodies_b
    north_a = a.world.settlement_at(a.world.regions[0])
    north_b = b.world.settlement_at(b.world.regions[0])
    assert north_a.garrison == north_b.garrison
    assert north_a.storage == north_b.storage
    # Two successful recruits on north: garrison grew, gold spent.
    assert len(north_a.garrison) == 3
    assert north_a.storage.gold == 0


def test_game_app_post_order_muster_applies_muster_and_resyncs():
    """POST /order/muster applies ai.muster_duchy_party + re-syncs game.

    Contract (task-079 / K14.2b):
    - when player_duchy_id is set, game is not is_over, and the player duchy
      exists in game.duchies: applies ai.muster_duchy_party(self.world,
      player_duchy), replaces self.world, re-syncs
      self.game = self.game.sync_from_world(self.world); returns (200, page)
    - player duchy looked up by duchy_id == player_duchy_id
    """
    north, south = map(Region, ("North", "South"))
    hero = Unit(training=4)
    garrison = (Unit(equipment=1), Unit(experience=2))
    north_keep = Settlement(
        "North Keep",
        3,
        occupied=2,
        garrison=garrison,
        owner_id="north",
    )
    south_keep = Settlement("South Keep", 2, owner_id="south")
    world = WorldMap(
        (north, south), settlements={north: north_keep, south: south_keep}
    )
    game = GameState(
        (
            Duchy("north", hero, settlements=(north_keep,)),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )
    assert not game.is_over
    calendar = Calendar(year=2, month=3)
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")

    world_before = app.world
    game_before = app.game
    assert world_before.party_at(north) is None
    assert world_before.settlement_at(north).garrison == garrison

    expected_world = ai.muster_duchy_party(world_before, game_before.duchies[0])
    expected_game = game_before.sync_from_world(expected_world)
    assert expected_world.party_at(north) == Party(hero, garrison, owner_id="north")
    assert expected_world.settlement_at(north).garrison == ()
    assert expected_world is not world_before

    code, body = app.handle("POST", "/order/muster")
    assert code == 200
    assert isinstance(body, str)
    assert body.strip() != ""
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"
    assert _calendar_stamp(body) == (2, 3)

    # World replaced with muster result; game re-synced from that world.
    assert app.world is not world_before
    assert app.world.party_at(north) == expected_world.party_at(north)
    assert app.world.settlement_at(north).garrison == ()
    assert app.game is not game_before
    player = next(d for d in app.game.duchies if d.duchy_id == "north")
    expected_player = next(
        d for d in expected_game.duchies if d.duchy_id == "north"
    )
    assert player.settlements == expected_player.settlements
    # South and calendar untouched.
    assert app.world.settlement_at(south) is south_keep
    assert app.world.party_at(south) is None
    assert app.calendar == calendar
    # Inputs to the call must not have been mutated in place.
    assert world_before.settlement_at(north) is north_keep
    assert world_before.party_at(north) is None
    assert north_keep.garrison == garrison

