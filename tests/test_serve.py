"""Interactive preview routing: GameApp.handle without a real HTTP socket (V13.5a)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import tbb.ai as ai
from tbb.duchy import Duchy
from tbb.game import GameState
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
    root = ET.fromstring(html)
    for el in root.iter():
        if _local(el.tag) != "form":
            continue
        method = (el.get("method") or "").lower()
        action = el.get("action") or ""
        if method == "post" and action == "/turn":
            return True
    # Fallback: tolerate attribute order / spacing in raw HTML.
    return bool(
        re.search(
            r'<form\b[^>]*\bmethod=["\']post["\'][^>]*\baction=["\']/turn["\']',
            html,
            flags=re.IGNORECASE,
        )
        or re.search(
            r'<form\b[^>]*\baction=["\']/turn["\'][^>]*\bmethod=["\']post["\']',
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

