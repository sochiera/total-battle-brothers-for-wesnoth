"""Interactive preview routing: GameApp.handle without a real HTTP socket (V13.5a)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

import tbb.ai as ai
from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.resources import Resources
from tbb.rng import Rng
import tbb.settlement as settlement_module
from tbb.settlement import Settlement
from tbb.turn import Calendar
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.battlesvg import render_battle_svg
from tbbui.serve import GameApp, recommended_order_path
from tbbui.turnsummary import render_turn_summary


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


def _has_post_muster_form(html: str) -> bool:
    """True when body contains a form that POSTs to /order/muster (K14.2b)."""
    return _has_post_form(html, "/order/muster")


def _has_post_develop_form(html: str) -> bool:
    """True when body contains a form that POSTs to /order/develop (K14.2c)."""
    return _has_post_form(html, "/order/develop")


def _has_post_march_form(html: str) -> bool:
    """True when body contains a form that POSTs to /order/march (K14.2d2)."""
    return _has_post_form(html, "/order/march")


def _has_post_assault_form(html: str) -> bool:
    """True when body contains a form that POSTs to /order/assault (K14.2e2)."""
    return _has_post_form(html, "/order/assault")


def _has_post_engage_form(html: str) -> bool:
    """True when body contains a form that POSTs to /order/engage (K18.1c)."""
    return _has_post_form(html, "/order/engage")


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


def _form_submit_button_text(html: str, action_path: str) -> str | None:
    """Text of the first submit button inside the POST form for ``action_path``."""
    root = ET.fromstring(html)
    for el in root.iter():
        if _local(el.tag) != "form":
            continue
        method = (el.get("method") or "").lower()
        action = el.get("action") or ""
        if method != "post" or action != action_path:
            continue
        for child in el.iter():
            if _local(child.tag) == "button":
                return "".join(child.itertext()).strip()
    return None


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


def test_game_app_get_polish_labels_turn_and_development_order_buttons():
    """GET /: turn + development-order forms use Polish button labels (K29.2a).

    Contract (task-149 / K29.2a; K30.2a extends recruit label with gold cost):
    - form action=/turn submit button text is ``Następna tura``
    - form action=/order/recruit → ``Rekrutuj (koszt złota: N)``
      (N = ``tbb.settlement.RECRUIT_GOLD_COST``)
    - form action=/order/muster → ``Zbierz oddział``
    - form action=/order/develop → ``Rozbuduj osadę``
    - form method/action paths unchanged (still POST to those actions)
    """
    world, game = _ongoing_world_game()
    app = GameApp(
        world, game, Calendar(year=1, month=1), Rng(1), player_duchy_id="north"
    )
    code, body = app.handle("GET", "/")
    assert code == 200
    assert _has_post_turn_form(body)
    assert _has_post_recruit_form(body)
    assert _has_post_muster_form(body)
    assert _has_post_develop_form(body)
    assert _form_submit_button_text(body, "/turn") == "Następna tura"
    cost = settlement_module.RECRUIT_GOLD_COST
    assert _form_submit_button_text(body, "/order/recruit") == (
        f"Rekrutuj (koszt złota: {cost})"
    )
    assert _form_submit_button_text(body, "/order/muster") == "Zbierz oddział"
    assert _form_submit_button_text(body, "/order/develop") == "Rozbuduj osadę"


def test_game_app_get_polish_labels_bare_march_assault_engage_buttons():
    """GET /: bare march/assault/engage forms use Polish button labels (K29.2b).

    Contract (task-150 / K29.2b):
    - bare form action=/order/march submit button text is ``Marsz``
    - bare form action=/order/assault → ``Szturm``
    - bare form action=/order/engage → ``Starcie``
    - form method/action paths unchanged (still POST to those bare actions)
    - when player has no party, bare forms are present (no per-target alternatives)
    """
    world, game = _ongoing_world_game()
    app = GameApp(
        world, game, Calendar(year=1, month=1), Rng(1), player_duchy_id="north"
    )
    code, body = app.handle("GET", "/")
    assert code == 200
    assert _has_post_march_form(body)
    assert _has_post_assault_form(body)
    assert _has_post_engage_form(body)
    assert _form_submit_button_text(body, "/order/march") == "Marsz"
    assert _form_submit_button_text(body, "/order/assault") == "Szturm"
    assert _form_submit_button_text(body, "/order/engage") == "Starcie"


def test_game_app_handle_get_turn_404_noop_and_determinism():
    """GameApp.handle: GET form, POST one turn, is_over no-op, 404, seed det.

    Contract (task-074 / V13.5a):
    - GET / → (200, page) with form method=post action=/turn
    - POST /turn → exactly one headless turn; calendar/state advance; 200
    - when game.is_over before request, POST /turn is no-op on party state
      (200, calendar/world/game unchanged; K28.1e still sets last_notice)
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

    # Finished game: POST /turn must not advance calendar; notice still set (K28.1e).
    fin_world, fin_game = _finished_world_game()
    fin_cal = Calendar(year=3, month=7)
    finished = GameApp(fin_world, fin_game, fin_cal, Rng(5))
    code_g, page_before = finished.handle("GET", "/")
    assert code_g == 200
    assert _calendar_stamp(page_before) == (3, 7)
    world_before = finished.world
    game_before = finished.game
    code_n, page_after = finished.handle("POST", "/turn")
    assert code_n == 200
    assert finished.world is world_before
    assert finished.game is game_before
    assert _calendar_stamp(page_after) == (3, 7)
    assert finished.last_notice == "Następna tura: gra zakończona"
    notices = _find_by_attr(ET.fromstring(page_after), "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == "Następna tura: gra zakończona"

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


def test_game_app_last_notice_empty_string_renders_empty_data_notice():
    """GameApp exposes last_notice, rendered as one <p data-notice> in extras.

    Contract (task-143 / K28.1a + task-148 / K29.1a empty body):
    - GameApp(...).last_notice == "" right after construction
    - fresh GET / (no prior order) embeds exactly one element with a
      data-notice attribute, and its value equals self.last_notice ("")
    - paragraph body is also empty: (el.text or "") == ""
    """
    world, game = _ongoing_world_game()
    calendar = Calendar(year=4, month=9)
    app = GameApp(world, game, calendar, Rng(17), player_duchy_id="north")
    assert app.last_notice == ""

    code, body = app.handle("GET", "/")
    assert code == 200
    root = ET.fromstring(body)
    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == app.last_notice == ""
    assert (notices[0].text or "") == ""


def test_game_app_render_data_notice_body_text_matches_last_notice_after_recruit():
    """_render puts last_notice in both data-notice attribute and paragraph body.

    Contract (task-148 / K29.1a):
    - after a recruit that changes world, last_notice == "Rekrutacja: wykonano"
    - rendered page has exactly one <p data-notice="…"> whose attribute equals
      that string (as before) and whose body text equals self.last_notice
      (entities decoded by the parser — visible confirmation in the browser)
    """
    north, south = map(Region, ("North", "South"))
    north_keep = Settlement(
        "North Keep",
        3,
        storage=Resources(0, 1),
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
    calendar = Calendar(year=2, month=3)
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")

    code, body = app.handle("POST", "/order/recruit")
    assert code == 200
    assert app.last_notice == "Rekrutacja: wykonano"
    root = ET.fromstring(body)
    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == "Rekrutacja: wykonano"
    assert notices[0].text == app.last_notice


def test_game_app_post_turn_sets_last_notice_with_calendar_date_after_turn():
    """POST /turn after an executed turn sets last_notice from post-turn calendar (K28.1e).

    Contract (task-147 / K28.1e):
    - when game is not is_over before the request, POST /turn runs one headless
      turn then sets last_notice to
      f"Następna tura: rok {calendar.year}, miesiąc {calendar.month}"
      using the calendar state *after* the turn
    - returns (200, page); rendered <p data-notice> carries that exact string
    """
    world, game = _ongoing_world_game()
    calendar = Calendar(year=4, month=9)
    app = GameApp(world, game, calendar, Rng(17))
    assert app.last_notice == ""
    assert not app.game.is_over

    code, body = app.handle("POST", "/turn")
    assert code == 200
    # One strategic turn advances calendar by one month (4,9 → 4,10).
    assert (app.calendar.year, app.calendar.month) == (4, 10)
    expected = f"Następna tura: rok {app.calendar.year}, miesiąc {app.calendar.month}"
    assert expected == "Następna tura: rok 4, miesiąc 10"
    assert app.last_notice == expected
    notices = _find_by_attr(ET.fromstring(body), "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == expected


def test_game_app_post_order_recruit_sets_last_notice_wykonano_then_brak_zmian():
    """POST /order/recruit sets last_notice via the "Rekrutacja" label.

    Contract (task-144 / K28.1b):
    - a recruit that changes world sets last_notice == "Rekrutacja: wykonano"
      and the rendered page carries <p data-notice="Rekrutacja: wykonano">
    - a subsequent recruit with insufficient gold (world unchanged) sets
      last_notice == "Rekrutacja: brak zmian"
    """
    north, south = map(Region, ("North", "South"))
    north_keep = Settlement(
        "North Keep",
        3,
        storage=Resources(0, 1),
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
    calendar = Calendar(year=2, month=3)
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")

    code, body = app.handle("POST", "/order/recruit")
    assert code == 200
    assert app.last_notice == "Rekrutacja: wykonano"
    assert app.world.settlement_at(north).storage.gold == 0
    root = ET.fromstring(body)
    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == "Rekrutacja: wykonano"

    code2, body2 = app.handle("POST", "/order/recruit")
    assert code2 == 200
    assert app.last_notice == "Rekrutacja: brak zmian"
    root2 = ET.fromstring(body2)
    notices2 = _find_by_attr(root2, "data-notice")
    assert len(notices2) == 1
    assert notices2[0].get("data-notice") == "Rekrutacja: brak zmian"


def test_game_app_post_order_muster_sets_last_notice_wykonano_then_brak_zmian():
    """POST /order/muster sets last_notice via the "Zebranie oddziału" label.

    Contract (task-144 / K28.1b):
    - a muster that changes world sets last_notice == "Zebranie oddziału: wykonano"
      and the rendered page carries that data-notice value
    - a subsequent muster with party already fielded (world unchanged) sets
      last_notice == "Zebranie oddziału: brak zmian"
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
    calendar = Calendar(year=2, month=3)
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")

    code, body = app.handle("POST", "/order/muster")
    assert code == 200
    assert app.last_notice == "Zebranie oddziału: wykonano"
    assert app.world.party_at(north) == Party(hero, garrison, owner_id="north")
    root = ET.fromstring(body)
    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == "Zebranie oddziału: wykonano"

    code2, body2 = app.handle("POST", "/order/muster")
    assert code2 == 200
    assert app.last_notice == "Zebranie oddziału: brak zmian"
    root2 = ET.fromstring(body2)
    notices2 = _find_by_attr(root2, "data-notice")
    assert len(notices2) == 1
    assert notices2[0].get("data-notice") == "Zebranie oddziału: brak zmian"


def test_game_app_post_order_develop_sets_last_notice_wykonano_then_brak_zmian():
    """POST /order/develop sets last_notice via the "Rozbudowa" label.

    Contract (task-144 / K28.1b):
    - a develop that changes world sets last_notice == "Rozbudowa: wykonano"
      and the rendered page carries that data-notice value
    - a subsequent develop with no free slots (world unchanged) sets
      last_notice == "Rozbudowa: brak zmian"
    """
    north, south = map(Region, ("North", "South"))
    # capacity=1 → first develop opens Farm (staff=1); second has free=0.
    north_keep = Settlement("North Keep", 1, owner_id="north")
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
    calendar = Calendar(year=2, month=3)
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")

    code, body = app.handle("POST", "/order/develop")
    assert code == 200
    assert app.last_notice == "Rozbudowa: wykonano"
    root = ET.fromstring(body)
    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == "Rozbudowa: wykonano"

    code2, body2 = app.handle("POST", "/order/develop")
    assert code2 == 200
    assert app.last_notice == "Rozbudowa: brak zmian"
    root2 = ET.fromstring(body2)
    notices2 = _find_by_attr(root2, "data-notice")
    assert len(notices2) == 1
    assert notices2[0].get("data-notice") == "Rozbudowa: brak zmian"


def test_game_app_post_order_march_without_target_sets_last_notice_marsz():
    """POST /order/march without a target uses the plain "Marsz" label (K28.1c).

    Contract: missing/empty/unknown target falls back to ai.march_duchy_party
    with label "Marsz", so a march that changes world sets
    last_notice == "Marsz: wykonano", and a subsequent no-op march (already
    adjacent to the enemy) sets last_notice == "Marsz: brak zmian".
    """
    start, step, target = map(Region, ("Start", "Step", "Target"))
    party = Party(Unit(training=4), (Unit(equipment=1),), owner_id="north")
    enemy_keep = Settlement("Enemy Keep", 2, owner_id="south")
    world = WorldMap(
        (start, step, target),
        ((start, step), (step, target)),
        settlements={target: enemy_keep},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,)),
            Duchy("south", Unit(), settlements=(enemy_keep,)),
        )
    )
    calendar = Calendar(year=2, month=3)
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")
    assert app.last_notice == ""

    code, body = app.handle("POST", "/order/march")
    assert code == 200
    assert app.last_notice == "Marsz: wykonano"
    root = ET.fromstring(body)
    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == "Marsz: wykonano"

    code2, body2 = app.handle("POST", "/order/march")
    assert code2 == 200
    assert app.last_notice == "Marsz: brak zmian"
    root2 = ET.fromstring(body2)
    notices2 = _find_by_attr(root2, "data-notice")
    assert len(notices2) == 1
    assert notices2[0].get("data-notice") == "Marsz: brak zmian"


def test_game_app_post_order_march_with_target_sets_last_notice_with_region_name():
    """POST /order/march?target=<region> sets last_notice with a target-named label (K28.1c).

    Contract: a known target uses label f"Marsz do {region.name}", so a march
    that changes world sets last_notice == "Marsz do Target: wykonano", and a
    subsequent no-op march to the same target sets "Marsz do Target: brak zmian".
    """
    start, step, target = map(Region, ("Start", "Step", "Target"))
    party = Party(Unit(training=4), (Unit(equipment=1),), owner_id="north")
    enemy_keep = Settlement("Enemy Keep", 2, owner_id="south")
    home_keep = Settlement("Home", 1, owner_id="north")
    world = WorldMap(
        (start, step, target),
        ((start, step), (step, target)),
        settlements={start: home_keep, target: enemy_keep},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, settlements=(home_keep,), parties=(party,)),
            Duchy("south", Unit(), settlements=(enemy_keep,)),
        )
    )
    calendar = Calendar(year=2, month=3)
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")
    assert app.last_notice == ""

    code, body = app.handle("POST", "/order/march?target=Target")
    assert code == 200
    assert app.last_notice == "Marsz do Target: wykonano"
    root = ET.fromstring(body)
    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == "Marsz do Target: wykonano"

    code2, body2 = app.handle("POST", "/order/march?target=Target")
    assert code2 == 200
    assert app.last_notice == "Marsz do Target: brak zmian"
    root2 = ET.fromstring(body2)
    notices2 = _find_by_attr(root2, "data-notice")
    assert len(notices2) == 1
    assert notices2[0].get("data-notice") == "Marsz do Target: brak zmian"


def test_game_app_post_order_assault_with_target_sets_last_notice_bitwa_then_brak_zmian():
    """POST /order/assault?target=<region> sets last_notice via target-named label (K28.1d).

    Contract: a known target uses label f"Szturm na {region.name}"; when the
    recorded assault returns a battle, last_notice == "Szturm na KeepB: bitwa"
    and the page carries matching data-notice; a subsequent assault that finds
    no enemy (battle is None) sets last_notice == "Szturm na KeepB: brak zmian".
    last_battle remains set after the hit assault (primitives / return code
    unchanged: 200 + page).
    """
    start, keep_a_region, keep_b_region = map(
        Region, ("Start", "KeepA", "KeepB")
    )
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    keep_a = Settlement(
        "Keep A", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    keep_b = Settlement(
        "Keep B", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        (start, keep_a_region, keep_b_region),
        ((start, keep_a_region), (start, keep_b_region)),
        settlements={keep_a_region: keep_a, keep_b_region: keep_b},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), morale=10),
            Duchy("south", Unit(), settlements=(keep_a, keep_b), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(world, game, calendar, Rng(seed), player_duchy_id="north")
    assert app.last_notice == ""
    assert app.last_battle is None

    code, body = app.handle("POST", "/order/assault?target=KeepB")
    assert code == 200
    assert app.last_battle is not None
    assert app.last_notice == "Szturm na KeepB: bitwa"
    root = ET.fromstring(body)
    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == "Szturm na KeepB: bitwa"

    # KeepB is now owned by the player — re-assaulting it is a no-op (no battle).
    code2, body2 = app.handle("POST", "/order/assault?target=KeepB")
    assert code2 == 200
    assert app.last_notice == "Szturm na KeepB: brak zmian"
    root2 = ET.fromstring(body2)
    notices2 = _find_by_attr(root2, "data-notice")
    assert len(notices2) == 1
    assert notices2[0].get("data-notice") == "Szturm na KeepB: brak zmian"


def test_game_app_post_order_engage_with_target_sets_last_notice_bitwa_then_brak_zmian():
    """POST /order/engage?target=<region> sets last_notice via target-named label (K28.1d).

    Contract: a known target uses label f"Starcie z {region.name}"; when the
    recorded engage returns a battle, last_notice == "Starcie z EnemyB: bitwa"
    and the page carries matching data-notice; a subsequent engage that finds
    no enemy (battle is None) sets last_notice == "Starcie z EnemyB: brak zmian".
    """
    start, enemy_a, enemy_b = map(Region, ("Start", "EnemyA", "EnemyB"))
    north_party = Party(Unit(training=5, equipment=6), owner_id="north")
    south_party_a = Party(Unit(training=1, equipment=1), owner_id="south")
    south_party_b = Party(Unit(training=1, equipment=1), owner_id="south")
    world = WorldMap(
        (start, enemy_a, enemy_b),
        ((start, enemy_a), (start, enemy_b)),
        parties={start: north_party, enemy_a: south_party_a, enemy_b: south_party_b},
    )
    game = GameState(
        (
            Duchy("north", north_party.hero, parties=(north_party,), morale=10),
            Duchy(
                "south",
                south_party_a.hero,
                parties=(south_party_a, south_party_b),
                morale=-5,
            ),
        )
    )
    calendar = Calendar(year=2, month=3)
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")
    assert app.last_notice == ""
    assert app.last_battle is None

    code, body = app.handle("POST", "/order/engage?target=EnemyB")
    assert code == 200
    assert app.last_battle is not None
    assert app.last_notice == "Starcie z EnemyB: bitwa"
    root = ET.fromstring(body)
    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == "Starcie z EnemyB: bitwa"

    # EnemyB now holds the player's party — re-engaging it is a no-op (no battle).
    code2, body2 = app.handle("POST", "/order/engage?target=EnemyB")
    assert code2 == 200
    assert app.last_notice == "Starcie z EnemyB: brak zmian"
    root2 = ET.fromstring(body2)
    notices2 = _find_by_attr(root2, "data-notice")
    assert len(notices2) == 1
    assert notices2[0].get("data-notice") == "Starcie z EnemyB: brak zmian"


def test_game_app_post_order_assault_without_target_sets_last_notice_szturm():
    """POST /order/assault (no/unknown target) uses bare label "Szturm" (K28.1d).

    Contract: missing or unknown ``target`` falls back to auto assault with
    label "Szturm"; a hit battle sets last_notice == "Szturm: bitwa" (and
    data-notice); a no-op (no adjacent enemy keep) sets "Szturm: brak zmian".
    """
    start, keep_region = map(Region, ("Start", "KeepB"))
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    keep = Settlement(
        "Keep B", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        (start, keep_region),
        ((start, keep_region),),
        settlements={keep_region: keep},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), morale=10),
            Duchy("south", Unit(), settlements=(keep,), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(world, game, calendar, Rng(seed), player_duchy_id="north")
    assert app.last_notice == ""

    code, body = app.handle("POST", "/order/assault")
    assert code == 200
    assert app.last_battle is not None
    assert app.last_notice == "Szturm: bitwa"
    root = ET.fromstring(body)
    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == "Szturm: bitwa"

    # Unknown target uses the same bare "Szturm" label (auto fallback; keep taken).
    code_u, body_u = app.handle("POST", "/order/assault?target=Nonexistent")
    assert code_u == 200
    assert app.last_notice == "Szturm: brak zmian"
    notices_u = _find_by_attr(ET.fromstring(body_u), "data-notice")
    assert len(notices_u) == 1
    assert notices_u[0].get("data-notice") == "Szturm: brak zmian"

    # Isolated party: auto assault finds nothing → "Szturm: brak zmian".
    isolated = Region("Isolated")
    lone_party = Party(Unit(training=5, equipment=6), owner_id="north")
    lone_world = WorldMap((isolated,), (), parties={isolated: lone_party})
    lone_game = GameState((Duchy("north", lone_party.hero, parties=(lone_party,)),))
    lone_app = GameApp(
        lone_world, lone_game, calendar, Rng(seed), player_duchy_id="north"
    )
    code_lone, body_lone = lone_app.handle("POST", "/order/assault")
    assert code_lone == 200
    assert lone_app.last_battle is None
    assert lone_app.last_notice == "Szturm: brak zmian"
    notices_lone = _find_by_attr(ET.fromstring(body_lone), "data-notice")
    assert len(notices_lone) == 1
    assert notices_lone[0].get("data-notice") == "Szturm: brak zmian"


def test_game_app_post_order_engage_without_target_sets_last_notice_starcie():
    """POST /order/engage (no/unknown target) uses bare label "Starcie" (K28.1d).

    Contract: missing or unknown ``target`` falls back to auto engage with
    label "Starcie"; a hit battle sets last_notice == "Starcie: bitwa"; a
    no-op (no adjacent enemy party) sets "Starcie: brak zmian".
    """
    start, target = map(Region, ("Start", "Target"))
    north_party = Party(Unit(training=5, equipment=6), owner_id="north")
    south_party = Party(Unit(training=1, equipment=1), owner_id="south")
    world = WorldMap(
        (start, target),
        ((start, target),),
        parties={start: north_party, target: south_party},
    )
    game = GameState(
        (
            Duchy("north", north_party.hero, parties=(north_party,), morale=10),
            Duchy("south", south_party.hero, parties=(south_party,), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(world, game, calendar, Rng(seed), player_duchy_id="north")
    assert app.last_notice == ""

    code, body = app.handle("POST", "/order/engage")
    assert code == 200
    assert app.last_battle is not None
    assert app.last_notice == "Starcie: bitwa"
    root = ET.fromstring(body)
    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == "Starcie: bitwa"

    # Unknown target uses the same bare "Starcie" label (auto fallback; no enemy left).
    code_u, body_u = app.handle("POST", "/order/engage?target=Nonexistent")
    assert code_u == 200
    assert app.last_notice == "Starcie: brak zmian"
    notices_u = _find_by_attr(ET.fromstring(body_u), "data-notice")
    assert len(notices_u) == 1
    assert notices_u[0].get("data-notice") == "Starcie: brak zmian"

    # Isolated party: auto engage finds nothing → "Starcie: brak zmian".
    isolated = Region("Isolated")
    lone_party = Party(Unit(training=5, equipment=6), owner_id="north")
    lone_world = WorldMap((isolated,), (), parties={isolated: lone_party})
    lone_game = GameState((Duchy("north", lone_party.hero, parties=(lone_party,)),))
    lone_app = GameApp(
        lone_world, lone_game, calendar, Rng(seed), player_duchy_id="north"
    )
    code_lone, body_lone = lone_app.handle("POST", "/order/engage")
    assert code_lone == 200
    assert lone_app.last_battle is None
    assert lone_app.last_notice == "Starcie: brak zmian"
    notices_lone = _find_by_attr(ET.fromstring(body_lone), "data-notice")
    assert len(notices_lone) == 1
    assert notices_lone[0].get("data-notice") == "Starcie: brak zmian"


def test_game_app_post_order_assault_and_engage_guard_rejection_sets_last_notice_brak_zmian():
    """Guard rejection on assault/engage still sets last_notice (K28.1d).

    Contract (analogous to recruit guards ~K28.1b): when player_duchy_id is
    None, game is_over, or player duchy is absent from game.duchies, POST
    /order/assault and POST /order/engage leave world/game/last_battle
    unchanged but set last_notice to "{label}: brak zmian" with bare labels
    "Szturm" / "Starcie" (no target), and data-notice matches.
    """
    start, target = map(Region, ("Start", "Target"))
    north_party = Party(Unit(training=5, equipment=6), owner_id="north")
    south_party = Party(Unit(training=1, equipment=1), owner_id="south")
    keep = Settlement(
        "Enemy Keep",
        population=1,
        garrison=(Unit(equipment=1),),
        owner_id="south",
    )
    world = WorldMap(
        (start, target),
        ((start, target),),
        settlements={target: keep},
        parties={start: north_party, target: south_party},
    )
    game = GameState(
        (
            Duchy("north", north_party.hero, parties=(north_party,), morale=10),
            Duchy(
                "south",
                south_party.hero,
                parties=(south_party,),
                settlements=(keep,),
                morale=-5,
            ),
        )
    )
    calendar = Calendar(year=2, month=3)

    for path, expected_notice in (
        ("/order/assault", "Szturm: brak zmian"),
        ("/order/engage", "Starcie: brak zmian"),
    ):
        # No-op: player_duchy_id is None.
        none_app = GameApp(world, game, calendar, Rng(11), player_duchy_id=None)
        world_n, game_n = none_app.world, none_app.game
        code_n, body_n = none_app.handle("POST", path)
        assert code_n == 200
        assert none_app.world is world_n
        assert none_app.game is game_n
        assert none_app.last_battle is None
        assert none_app.last_notice == expected_notice
        notices_n = _find_by_attr(ET.fromstring(body_n), "data-notice")
        assert len(notices_n) == 1
        assert notices_n[0].get("data-notice") == expected_notice

        # No-op: game is_over.
        fin_world, fin_game = _finished_world_game()
        fin_cal = Calendar(year=5, month=1)
        fin_app = GameApp(
            fin_world, fin_game, fin_cal, Rng(3), player_duchy_id="north"
        )
        w_f, g_f = fin_app.world, fin_app.game
        code_f, body_f = fin_app.handle("POST", path)
        assert code_f == 200
        assert fin_app.world is w_f
        assert fin_app.game is g_f
        assert fin_app.last_battle is None
        assert fin_app.last_notice == expected_notice
        notices_f = _find_by_attr(ET.fromstring(body_f), "data-notice")
        assert len(notices_f) == 1
        assert notices_f[0].get("data-notice") == expected_notice

        # No-op: player duchy id not present in game.duchies.
        missing = GameApp(world, game, calendar, Rng(11), player_duchy_id="ghost")
        w_m, g_m = missing.world, missing.game
        code_m, body_m = missing.handle("POST", path)
        assert code_m == 200
        assert missing.world is w_m
        assert missing.game is g_m
        assert missing.last_battle is None
        assert missing.last_notice == expected_notice
        notices_m = _find_by_attr(ET.fromstring(body_m), "data-notice")
        assert len(notices_m) == 1
        assert notices_m[0].get("data-notice") == expected_notice


def test_game_app_render_forwards_player_duchy_id_to_data_player_duchy():
    """GameApp._render passes self.player_duchy_id into render_game_page.

    Contract (task-122 / K23.2b): with player_duchy_id="north" set, GET /
    contains exactly one element carrying data-player-duchy (on the "north"
    duchy panel row); with player_duchy_id=None, no element carries it.
    """
    world, game = _ongoing_world_game()
    calendar = Calendar(year=4, month=9)
    app = GameApp(world, game, calendar, Rng(17), player_duchy_id="north")

    code, body = app.handle("GET", "/")
    assert code == 200
    root = ET.fromstring(body)
    marked = _find_by_attr(root, "data-player-duchy")
    assert len(marked) == 1
    assert marked[0].get("data-duchy") == "north"

    w2, g2 = _ongoing_world_game()
    none_app = GameApp(w2, g2, Calendar(year=1, month=1), Rng(5))
    code_n, body_n = none_app.handle("GET", "/")
    assert code_n == 200
    root_n = ET.fromstring(body_n)
    assert _find_by_attr(root_n, "data-player-duchy") == []


def test_game_app_accepts_optional_seed_default_none():
    """GameApp accepts optional seed; default None; constructions without seed work (K31.1a).

    Contract (task-157 / K31.1a):
    - GameApp(world, game, calendar, rng, player_duchy_id=None, seed=None)
      takes optional ``seed: int | None = None`` after player_duchy_id
    - constructing without the seed kwarg still works (existing call sites)
    - omitting seed or passing seed=None stores seed is None
    - passing seed=<int> stores that value on the app
    - player_duchy_id remains independently settable with seed present
    """
    world, game = _ongoing_world_game()
    calendar = Calendar(year=4, month=9)
    rng = Rng(17)

    bare = GameApp(world, game, calendar, rng)
    assert bare.seed is None
    assert bare.player_duchy_id is None

    none_seed = GameApp(world, game, calendar, rng, player_duchy_id="north", seed=None)
    assert none_seed.seed is None
    assert none_seed.player_duchy_id == "north"

    with_seed = GameApp(world, game, calendar, rng, player_duchy_id="north", seed=73)
    assert with_seed.seed == 73
    assert with_seed.player_duchy_id == "north"

    seed_only = GameApp(world, game, calendar, rng, seed=11)
    assert seed_only.seed == 11
    assert seed_only.player_duchy_id is None


def test_game_app_post_new_with_seed_resets_party_state():
    """POST /new with seed set rebuilds party from create_headless_game (K31.1a).

    Contract (task-157 / K31.1a):
    - POST /new with app.seed set → (200, page)
    - world/game replaced with fresh create_headless_game()
    - calendar replaced with new Calendar() (year 1, month 1)
    - rng replaced with Rng(seed)
    - player_duchy_id unchanged
    """
    from tbb.game import create_headless_game

    world, game = _ongoing_world_game()
    calendar = Calendar(year=4, month=9)
    seed = 73
    app = GameApp(
        world,
        game,
        calendar,
        Rng(999),
        player_duchy_id="north",
        seed=seed,
    )
    # Advance state so reset is observable (not already at headless defaults).
    code_turn, _ = app.handle("POST", "/turn")
    assert code_turn == 200
    assert app.calendar.year != 1 or app.calendar.month != 1
    assert [r.name for r in app.world.regions] == ["North", "South"]

    code, body = app.handle("POST", "/new")
    assert code == 200
    assert isinstance(body, str)
    assert body.strip() != ""
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"

    assert app.player_duchy_id == "north"
    assert app.seed == seed

    expected_world, expected_game = create_headless_game()
    assert [r.name for r in app.world.regions] == [
        r.name for r in expected_world.regions
    ]
    assert [d.duchy_id for d in app.game.duchies] == [
        d.duchy_id for d in expected_game.duchies
    ]
    assert app.calendar.year == 1
    assert app.calendar.month == 1
    assert _calendar_stamp(body) == (1, 1)

    # Fresh Rng(seed): first draw matches a brand-new Rng(seed).
    assert isinstance(app.rng, Rng)
    probe = Rng(seed)
    assert app.rng.randint(0, 10_000) == probe.randint(0, 10_000)


def test_game_app_post_new_with_seed_clears_last_battle_and_sets_notice():
    """POST /new with seed set zeros last_battle and sets last_notice (K31.1a).

    Contract (task-157 / K31.1a):
    - POST /new with app.seed set → last_battle is None
    - last_notice == "Nowa gra: rok 1, miesiąc 1"
    - returned page embeds that notice in <p data-notice>
    - returns (200, page)
    """
    start, keep_a_region, keep_b_region = map(
        Region, ("Start", "KeepA", "KeepB")
    )
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    keep_a = Settlement(
        "Keep A", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    keep_b = Settlement(
        "Keep B", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        (start, keep_a_region, keep_b_region),
        ((start, keep_a_region), (start, keep_b_region)),
        settlements={keep_a_region: keep_a, keep_b_region: keep_b},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), morale=10),
            Duchy("south", Unit(), settlements=(keep_a, keep_b), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(
        world, game, calendar, Rng(seed), player_duchy_id="north", seed=seed
    )

    code_assault, body_assault = app.handle("POST", "/order/assault?target=KeepB")
    assert code_assault == 200
    assert app.last_battle is not None
    prior_battle = app.last_battle
    assert render_battle_svg(prior_battle) in body_assault

    code, body = app.handle("POST", "/new")
    assert code == 200
    assert isinstance(body, str)
    assert body.strip() != ""
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"

    assert app.last_battle is None
    assert app.last_notice == "Nowa gra: rok 1, miesiąc 1"
    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == "Nowa gra: rok 1, miesiąc 1"
    assert notices[0].text == "Nowa gra: rok 1, miesiąc 1"
    assert render_battle_svg(prior_battle) not in body


def test_game_app_post_new_without_seed_is_noop_state():
    """POST /new when seed is None is a state no-op with notice (K31.1a).

    Contract (task-157 / K31.1a):
    - seed is None → world/game/calendar unchanged; last_battle unchanged
    - last_notice == "Nowa gra: brak zmian"
    - returns (200, page)
    """
    start, keep_a_region, keep_b_region = map(
        Region, ("Start", "KeepA", "KeepB")
    )
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    keep_a = Settlement(
        "Keep A", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    keep_b = Settlement(
        "Keep B", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        (start, keep_a_region, keep_b_region),
        ((start, keep_a_region), (start, keep_b_region)),
        settlements={keep_a_region: keep_a, keep_b_region: keep_b},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), morale=10),
            Duchy("south", Unit(), settlements=(keep_a, keep_b), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)
    app = GameApp(
        world, game, calendar, Rng(11), player_duchy_id="north", seed=None
    )

    # Real battle so last_battle is non-None and still renderable after no-op.
    code_assault, _ = app.handle("POST", "/order/assault?target=KeepB")
    assert code_assault == 200
    assert app.last_battle is not None
    world_after = app.world
    game_after = app.game
    calendar_after = app.calendar
    rng_after = app.rng
    battle_before = app.last_battle

    code, body = app.handle("POST", "/new")
    assert code == 200
    assert isinstance(body, str)
    assert body.strip() != ""
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"

    assert app.world is world_after
    assert app.game is game_after
    assert app.calendar is calendar_after
    assert app.rng is rng_after
    assert app.last_battle is battle_before
    assert app.player_duchy_id == "north"
    assert app.seed is None
    assert app.last_notice == "Nowa gra: brak zmian"
    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert notices[0].get("data-notice") == "Nowa gra: brak zmian"
    assert notices[0].text == "Nowa gra: brak zmian"
    assert render_battle_svg(battle_before) in body


def test_game_app_post_new_same_seed_converges_get_bodies():
    """Two GameApps with same seed after POST /new yield identical GET / (K31.1a).

    Contract (task-157 / K31.1a):
    - two apps constructed with the same seed, after arbitrary prior handle
      sequences, both POST /new then GET / → identical response bodies
    """
    seed = 73

    wa, ga = _ongoing_world_game()
    a = GameApp(
        wa, ga, Calendar(year=4, month=9), Rng(1), player_duchy_id="north", seed=seed
    )
    code_a_turn, _ = a.handle("POST", "/turn")
    assert code_a_turn == 200
    code_a_new, _ = a.handle("POST", "/new")
    assert code_a_new == 200

    wb, gb = _ongoing_world_game()
    b = GameApp(
        wb, gb, Calendar(year=2, month=3), Rng(999), player_duchy_id="north", seed=seed
    )
    # Different prior path than app a (recruit then turn).
    code_b_recruit, _ = b.handle("POST", "/order/recruit")
    assert code_b_recruit == 200
    code_b_turn, _ = b.handle("POST", "/turn")
    assert code_b_turn == 200
    code_b_new, _ = b.handle("POST", "/new")
    assert code_b_new == 200

    code_get_a, body_a = a.handle("GET", "/")
    code_get_b, body_b = b.handle("GET", "/")
    assert code_get_a == 200
    assert code_get_b == 200
    assert body_a == body_b


def test_game_app_get_embeds_exactly_one_new_game_form_with_button():
    """GET / contains exactly one POST /new form with button „Nowa gra" (K31.1b).

    Contract (task-158 / K31.1b):
    - GET / embeds exactly one ``<form method="post" action="/new">``
    - that form's submit button text is ``Nowa gra``
    """
    world, game = _ongoing_world_game()
    app = GameApp(
        world, game, Calendar(year=1, month=1), Rng(17), player_duchy_id="north"
    )

    code, body = app.handle("GET", "/")
    assert code == 200
    assert isinstance(body, str)
    assert body.strip() != ""
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"

    new_forms = [
        el
        for el in root.iter()
        if _local(el.tag) == "form"
        and (el.get("method") or "").lower() == "post"
        and (el.get("action") or "") == "/new"
    ]
    assert len(new_forms) == 1
    assert _has_post_form(body, "/new")
    assert _form_submit_button_text(body, "/new") == "Nowa gra"


def test_game_app_get_new_game_form_between_notice_and_turn():
    """GET / extras order: data-notice → POST /new → POST /turn (K31.1b).

    Contract (task-158 / K31.1b):
    - ``<p data-notice>`` appears before the ``/new`` form
    - the ``/new`` form appears before the ``/turn`` form
      (document order: data-notice → /new → /turn)
    """
    world, game = _ongoing_world_game()
    app = GameApp(
        world, game, Calendar(year=1, month=1), Rng(17), player_duchy_id="north"
    )

    code, body = app.handle("GET", "/")
    assert code == 200

    notice_marker = 'data-notice="'
    new_form_open = '<form method="post" action="/new">'
    turn_form_open = '<form method="post" action="/turn">'

    assert body.count(new_form_open) == 1
    assert body.count(turn_form_open) == 1
    notice_pos = body.index(notice_marker)
    new_pos = body.index(new_form_open)
    turn_pos = body.index(turn_form_open)
    assert notice_pos < new_pos < turn_pos


def test_game_app_get_new_game_form_present_when_over_and_without_player():
    """GET / embeds POST /new form when is_over and when player_duchy_id is None (K31.1b).

    Contract (task-158 / K31.1b):
    - finished game (``game.is_over``) still has exactly one POST /new form
      with submit button ``Nowa gra``
    - observer app (``player_duchy_id=None``) still has that form
    """
    finished_world, finished_game = _finished_world_game()
    assert finished_game.is_over
    finished_app = GameApp(
        finished_world,
        finished_game,
        Calendar(year=1, month=1),
        Rng(17),
        player_duchy_id="north",
    )
    code_f, body_f = finished_app.handle("GET", "/")
    assert code_f == 200
    root_f = ET.fromstring(body_f)
    new_forms_f = [
        el
        for el in root_f.iter()
        if _local(el.tag) == "form"
        and (el.get("method") or "").lower() == "post"
        and (el.get("action") or "") == "/new"
    ]
    assert len(new_forms_f) == 1
    assert _form_submit_button_text(body_f, "/new") == "Nowa gra"

    world, game = _ongoing_world_game()
    none_app = GameApp(
        world, game, Calendar(year=1, month=1), Rng(17), player_duchy_id=None
    )
    code_n, body_n = none_app.handle("GET", "/")
    assert code_n == 200
    root_n = ET.fromstring(body_n)
    new_forms_n = [
        el
        for el in root_n.iter()
        if _local(el.tag) == "form"
        and (el.get("method") or "").lower() == "post"
        and (el.get("action") or "") == "/new"
    ]
    assert len(new_forms_n) == 1
    assert _form_submit_button_text(body_n, "/new") == "Nowa gra"


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
    cost = settlement_module.RECRUIT_GOLD_COST
    assert _form_submit_button_text(body_get, "/order/recruit") == (
        f"Rekrutuj (koszt złota: {cost})"
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
    # K28.1b: guard rejection still sets last_notice / data-notice.
    assert none_app.last_notice == "Rekrutacja: brak zmian"
    notices_n = _find_by_attr(ET.fromstring(body_n), "data-notice")
    assert len(notices_n) == 1
    assert notices_n[0].get("data-notice") == "Rekrutacja: brak zmian"

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
    assert fin_app.last_notice == "Rekrutacja: brak zmian"
    notices_f = _find_by_attr(ET.fromstring(body_f), "data-notice")
    assert len(notices_f) == 1
    assert notices_f[0].get("data-notice") == "Rekrutacja: brak zmian"

    # No-op: player duchy id not present in game.duchies.
    missing = GameApp(
        world, game, calendar, Rng(11), player_duchy_id="ghost"
    )
    w_m, g_m = missing.world, missing.game
    code_m, body_m = missing.handle("POST", "/order/recruit")
    assert code_m == 200
    assert missing.world is w_m
    assert missing.game is g_m
    assert missing.calendar == calendar
    assert missing.world.settlement_at(north).storage.gold == 2
    assert len(missing.world.settlement_at(north).garrison) == 1
    assert missing.last_notice == "Rekrutacja: brak zmian"
    notices_m = _find_by_attr(ET.fromstring(body_m), "data-notice")
    assert len(notices_m) == 1
    assert notices_m[0].get("data-notice") == "Rekrutacja: brak zmian"

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


def test_game_app_order_muster_form_noop_and_determinism():
    """GET form /order/muster; no-op guards; muster sequence determinism.

    Contract (task-079 / K14.2b):
    - GET / contains <form method="post" action="/order/muster"> with a submit
    - when player_duchy_id is None, game is is_over, or player duchy is absent
      from game.duchies: POST /order/muster is a no-op (state unchanged), still
      (200, page)
    - fixed GameApp seed + same handle sequence → identical bodies and state
    """
    def _muster_ready_world_game() -> tuple[WorldMap, GameState, Region, Unit, tuple[Unit, ...]]:
        """World where north can muster (hero + owned garrison, no party yet)."""
        n, s = map(Region, ("North", "South"))
        hero = Unit(training=4)
        garrison = (Unit(equipment=1), Unit(experience=2))
        nk = Settlement(
            "North Keep",
            3,
            occupied=2,
            garrison=garrison,
            owner_id="north",
        )
        sk = Settlement("South Keep", 2, owner_id="south")
        w = WorldMap((n, s), settlements={n: nk, s: sk})
        g = GameState(
            (
                Duchy("north", hero, settlements=(nk,)),
                Duchy("south", Unit(), settlements=(sk,)),
            )
        )
        return w, g, n, hero, garrison

    world, game, north, hero, garrison = _muster_ready_world_game()
    calendar = Calendar(year=2, month=3)

    # GET / embeds the muster form (and a button).
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")
    code_get, body_get = app.handle("GET", "/")
    assert code_get == 200
    assert _has_post_muster_form(body_get)
    assert re.search(
        r"<button\b[^>]*>\s*Zbierz oddział\s*</button>", body_get, flags=re.IGNORECASE
    )

    # No-op: player_duchy_id is None — state frozen, still 200 + page.
    none_app = GameApp(world, game, calendar, Rng(11), player_duchy_id=None)
    world_n, game_n = none_app.world, none_app.game
    code_n, body_n = none_app.handle("POST", "/order/muster")
    assert code_n == 200
    assert isinstance(body_n, str)
    assert none_app.world is world_n
    assert none_app.game is game_n
    assert none_app.calendar == calendar
    assert _calendar_stamp(body_n) == (2, 3)
    assert _has_post_muster_form(body_n)
    # Would-be muster target unchanged (garrison intact, no party).
    assert none_app.world.settlement_at(north).garrison == garrison
    assert none_app.world.party_at(north) is None

    # No-op: game is_over — finished sole-duchy world.
    fin_world, fin_game = _finished_world_game()
    fin_cal = Calendar(year=5, month=1)
    fin_app = GameApp(
        fin_world, fin_game, fin_cal, Rng(3), player_duchy_id="north"
    )
    w_f, g_f = fin_app.world, fin_app.game
    code_f, body_f = fin_app.handle("POST", "/order/muster")
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
    code_m, _body_m = missing.handle("POST", "/order/muster")
    assert code_m == 200
    assert missing.world is w_m
    assert missing.game is g_m
    assert missing.calendar == calendar
    assert missing.world.settlement_at(north).garrison == garrison
    assert missing.world.party_at(north) is None

    # Determinism: two apps, same seed, same muster sequence → same bodies/state.
    wa, ga, _, hero_a, garrison_a = _muster_ready_world_game()
    wb, gb, _, hero_b, garrison_b = _muster_ready_world_game()
    a = GameApp(wa, ga, Calendar(year=2, month=3), Rng(11), player_duchy_id="north")
    b = GameApp(wb, gb, Calendar(year=2, month=3), Rng(11), player_duchy_id="north")
    seq = (
        ("GET", "/"),
        ("POST", "/order/muster"),
        ("GET", "/"),
        ("POST", "/order/muster"),
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
    north_a = a.world.regions[0]
    north_b = b.world.regions[0]
    assert a.world.party_at(north_a) == b.world.party_at(north_b)
    assert a.world.settlement_at(north_a).garrison == b.world.settlement_at(
        north_b
    ).garrison
    # First muster succeeds; second is a no-op (party already fielded).
    assert a.world.party_at(north_a) == Party(hero_a, garrison_a, owner_id="north")
    assert a.world.settlement_at(north_a).garrison == ()
    assert b.world.party_at(north_b) == Party(hero_b, garrison_b, owner_id="north")


def test_game_app_post_order_develop_applies_develop_and_resyncs():
    """POST /order/develop applies ai.develop_duchy_settlement + re-syncs game.

    Contract (task-080 / K14.2c):
    - when player_duchy_id is set, game is not is_over, and the player duchy
      exists in game.duchies: applies ai.develop_duchy_settlement(self.world,
      player_duchy), replaces self.world, re-syncs
      self.game = self.game.sync_from_world(self.world); returns (200, page)
    - player duchy looked up by duchy_id == player_duchy_id
    - opens at most one building by priority Farm→Smith→Market
    """
    from tbb.building import FARM

    north, south = map(Region, ("North", "South"))
    # Free slots + no buildings: develop opens Farm (staff=1) first.
    north_keep = Settlement("North Keep", 3, owner_id="north")
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
    assert north_before.active_buildings == ()
    assert north_before.occupied == 0

    expected_world = ai.develop_duchy_settlement(world_before, game_before.duchies[0])
    expected_game = game_before.sync_from_world(expected_world)
    expected_settlement = expected_world.settlement_at(north)
    assert expected_settlement is not north_before
    assert expected_settlement.active_buildings == (FARM,)
    assert expected_settlement.occupied == FARM.staff

    code, body = app.handle("POST", "/order/develop")
    assert code == 200
    assert isinstance(body, str)
    assert body.strip() != ""
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"
    assert _calendar_stamp(body) == (2, 3)

    # World replaced with develop result; game re-synced from that world.
    assert app.world is not world_before
    assert (
        app.world.settlement_at(north).active_buildings
        == expected_settlement.active_buildings
    )
    assert app.world.settlement_at(north).occupied == expected_settlement.occupied
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
    assert north_before.active_buildings == ()
    assert north_before.occupied == 0


def test_game_app_order_develop_form_noop_and_determinism():
    """GET form /order/develop; no-op guards; develop sequence determinism.

    Contract (task-080 / K14.2c):
    - GET / contains <form method="post" action="/order/develop"> with a submit
    - when player_duchy_id is None, game is is_over, or player duchy is absent
      from game.duchies: POST /order/develop is a no-op (state unchanged), still
      (200, page)
    - fixed GameApp seed + same handle sequence → identical bodies and state
    """
    from tbb.building import FARM, SMITH

    def _develop_ready_world_game() -> tuple[WorldMap, GameState, Region]:
        """World where north can develop (free slots, no buildings yet)."""
        n, s = map(Region, ("North", "South"))
        nk = Settlement("North Keep", 3, owner_id="north")
        sk = Settlement("South Keep", 2, owner_id="south")
        w = WorldMap((n, s), settlements={n: nk, s: sk})
        g = GameState(
            (
                Duchy("north", Unit(), settlements=(nk,)),
                Duchy("south", Unit(), settlements=(sk,)),
            )
        )
        return w, g, n

    world, game, north = _develop_ready_world_game()
    calendar = Calendar(year=2, month=3)

    # GET / embeds the develop form (and a button).
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")
    code_get, body_get = app.handle("GET", "/")
    assert code_get == 200
    assert _has_post_develop_form(body_get)
    assert re.search(
        r"<button\b[^>]*>\s*Rozbuduj osadę\s*</button>",
        body_get,
        flags=re.IGNORECASE,
    )

    # No-op: player_duchy_id is None — state frozen, still 200 + page.
    none_app = GameApp(world, game, calendar, Rng(11), player_duchy_id=None)
    world_n, game_n = none_app.world, none_app.game
    code_n, body_n = none_app.handle("POST", "/order/develop")
    assert code_n == 200
    assert isinstance(body_n, str)
    assert none_app.world is world_n
    assert none_app.game is game_n
    assert none_app.calendar == calendar
    assert _calendar_stamp(body_n) == (2, 3)
    assert _has_post_develop_form(body_n)
    # Would-be develop target unchanged (still no buildings).
    assert none_app.world.settlement_at(north).active_buildings == ()
    assert none_app.world.settlement_at(north).occupied == 0

    # No-op: game is_over — finished sole-duchy world.
    fin_world, fin_game = _finished_world_game()
    fin_cal = Calendar(year=5, month=1)
    fin_app = GameApp(
        fin_world, fin_game, fin_cal, Rng(3), player_duchy_id="north"
    )
    w_f, g_f = fin_app.world, fin_app.game
    code_f, body_f = fin_app.handle("POST", "/order/develop")
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
    code_m, _body_m = missing.handle("POST", "/order/develop")
    assert code_m == 200
    assert missing.world is w_m
    assert missing.game is g_m
    assert missing.calendar == calendar
    assert missing.world.settlement_at(north).active_buildings == ()
    assert missing.world.settlement_at(north).occupied == 0

    # Determinism: two apps, same seed, same develop sequence → same bodies/state.
    wa, ga, _ = _develop_ready_world_game()
    wb, gb, _ = _develop_ready_world_game()
    a = GameApp(wa, ga, Calendar(year=2, month=3), Rng(11), player_duchy_id="north")
    b = GameApp(wb, gb, Calendar(year=2, month=3), Rng(11), player_duchy_id="north")
    seq = (
        ("GET", "/"),
        ("POST", "/order/develop"),
        ("GET", "/"),
        ("POST", "/order/develop"),
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
    assert north_a.active_buildings == north_b.active_buildings
    assert north_a.occupied == north_b.occupied
    # Two successful develops: Farm then Smith (priority order).
    assert north_a.active_buildings == (FARM, SMITH)
    assert north_a.occupied == FARM.staff + SMITH.staff


def test_game_app_post_order_march_applies_march_and_resyncs():
    """POST /order/march applies ai.march_duchy_party + re-syncs game.

    Contract (task-082 / K14.2d2):
    - when player_duchy_id is set, game is not is_over, and the player duchy
      exists in game.duchies: applies ai.march_duchy_party(self.world,
      player_duchy) via shared _apply_player_order, replaces self.world,
      re-syncs self.game = self.game.sync_from_world(self.world);
      returns (200, page)
    - player duchy looked up by duchy_id == player_duchy_id
    - party moves one step toward the nearest enemy settlement
    """
    start, step, target = map(Region, ("Start", "Step", "Target"))
    party = Party(Unit(training=4), (Unit(equipment=1),), owner_id="north")
    enemy_keep = Settlement("Enemy Keep", 2, owner_id="south")
    world = WorldMap(
        (start, step, target),
        ((start, step), (step, target)),
        settlements={target: enemy_keep},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,)),
            Duchy("south", Unit(), settlements=(enemy_keep,)),
        )
    )
    assert not game.is_over
    calendar = Calendar(year=2, month=3)
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")

    world_before = app.world
    game_before = app.game
    assert world_before.party_at(start) is party
    assert world_before.party_at(step) is None

    expected_world = ai.march_duchy_party(world_before, game_before.duchies[0])
    expected_game = game_before.sync_from_world(expected_world)
    assert expected_world.party_at(step) is party
    assert expected_world.party_at(start) is None
    assert expected_world is not world_before

    code, body = app.handle("POST", "/order/march")
    assert code == 200
    assert isinstance(body, str)
    assert body.strip() != ""
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"
    assert _calendar_stamp(body) == (2, 3)

    # World replaced with march result; game re-synced from that world.
    assert app.world is not world_before
    assert app.world.party_at(step) is party
    assert app.world.party_at(start) is None
    assert app.world.party_at(step) == expected_world.party_at(step)
    assert app.game is not game_before
    player = next(d for d in app.game.duchies if d.duchy_id == "north")
    expected_player = next(
        d for d in expected_game.duchies if d.duchy_id == "north"
    )
    assert player.parties == expected_player.parties
    # Enemy settlement and calendar untouched.
    assert app.world.settlement_at(target) is enemy_keep
    assert app.calendar == calendar
    # Inputs to the call must not have been mutated in place.
    assert world_before.party_at(start) is party
    assert world_before.party_at(step) is None


def test_game_app_order_march_form_noop_and_determinism():
    """GET form /order/march; no-op guards; march sequence determinism.

    Contract (task-082 / K14.2d2):
    - GET / contains <form method="post" action="/order/march"> with a submit
    - when player_duchy_id is None, game is is_over, or player duchy is absent
      from game.duchies: POST /order/march is a no-op (state unchanged), still
      (200, page)
    - fixed GameApp seed + same handle sequence → identical bodies and state
    """
    def _march_ready_world_game() -> tuple[
        WorldMap, GameState, Region, Region, Region
    ]:
        """World where north can march two steps before standing next to enemy.

        Chain Start → Mid → Approach → Target (enemy keep). March stops when
        the enemy is adjacent (assault is a separate order), so two marches
        leave the party at Approach.
        """
        start, mid, approach, target = map(
            Region, ("Start", "Mid", "Approach", "Target")
        )
        party = Party(Unit(training=4), (Unit(equipment=1),), owner_id="north")
        enemy_keep = Settlement("Enemy Keep", 2, owner_id="south")
        w = WorldMap(
            (start, mid, approach, target),
            ((start, mid), (mid, approach), (approach, target)),
            settlements={target: enemy_keep},
            parties={start: party},
        )
        g = GameState(
            (
                Duchy("north", party.hero, parties=(party,)),
                Duchy("south", Unit(), settlements=(enemy_keep,)),
            )
        )
        return w, g, start, mid, approach

    world, game, start, mid, approach = _march_ready_world_game()
    calendar = Calendar(year=2, month=3)
    party = world.party_at(start)

    # GET / embeds per-target march forms when the player has a party (K15.1c).
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")
    code_get, body_get = app.handle("GET", "/")
    assert code_get == 200
    expected_target_action = f"/order/march?target={quote('Target')}"
    assert _has_post_form(body_get, expected_target_action)
    assert not _has_post_march_form(body_get)
    assert re.search(
        r"<button\b[^>]*>\s*Target\s*</button>", body_get, flags=re.IGNORECASE
    )

    # No-op: player_duchy_id is None — state frozen, still 200 + page.
    none_app = GameApp(world, game, calendar, Rng(11), player_duchy_id=None)
    world_n, game_n = none_app.world, none_app.game
    code_n, body_n = none_app.handle("POST", "/order/march")
    assert code_n == 200
    assert isinstance(body_n, str)
    assert none_app.world is world_n
    assert none_app.game is game_n
    assert none_app.calendar == calendar
    assert _calendar_stamp(body_n) == (2, 3)
    assert _has_post_march_form(body_n)
    # Would-be march target unchanged (party still at start).
    assert none_app.world.party_at(start) is party
    assert none_app.world.party_at(mid) is None

    # No-op: game is_over — finished sole-duchy world.
    fin_world, fin_game = _finished_world_game()
    fin_cal = Calendar(year=5, month=1)
    fin_app = GameApp(
        fin_world, fin_game, fin_cal, Rng(3), player_duchy_id="north"
    )
    w_f, g_f = fin_app.world, fin_app.game
    code_f, body_f = fin_app.handle("POST", "/order/march")
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
    code_m, _body_m = missing.handle("POST", "/order/march")
    assert code_m == 200
    assert missing.world is w_m
    assert missing.game is g_m
    assert missing.calendar == calendar
    assert missing.world.party_at(start) is party
    assert missing.world.party_at(mid) is None

    # Determinism: two apps, same seed, same march sequence → same bodies/state.
    wa, ga, _, _, _ = _march_ready_world_game()
    wb, gb, _, _, _ = _march_ready_world_game()
    a = GameApp(wa, ga, Calendar(year=2, month=3), Rng(11), player_duchy_id="north")
    b = GameApp(wb, gb, Calendar(year=2, month=3), Rng(11), player_duchy_id="north")
    seq = (
        ("GET", "/"),
        ("POST", "/order/march"),
        ("GET", "/"),
        ("POST", "/order/march"),
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
    # Two successful marches: party advanced Start → Mid → Approach.
    start_r, mid_r, approach_r, target_r = a.world.regions
    assert a.world.party_at(start_r) is None
    assert a.world.party_at(mid_r) is None
    assert a.world.party_at(approach_r) is not None
    assert a.world.party_at(target_r) is None
    assert b.world.party_at(start_r) is None
    assert b.world.party_at(mid_r) is None
    assert b.world.party_at(approach_r) is not None
    assert a.world.party_at(approach_r) == b.world.party_at(approach_r)



def test_game_app_render_march_forms_one_per_foreign_settlement_region():
    """GET / renders one march form per foreign-owned region when player has a party.

    Contract (task-087 / K15.1c):
    - when player_duchy_id is set, game is not over, and the player duchy has
      a party on the map, _render emits one
      ``<form method="post" action="/order/march?target=<name>">`` per region
      in world.regions whose settlement has ``owner_id != player_duchy_id``
      (name URL-encoded via urllib.parse.quote); the bare fallback
      ``/order/march`` form is absent
    - a region with no settlement, or with a settlement owned by the player,
      is not a march target
    - the submit button carries the target region's name
    """
    start, near, far, home = map(
        Region, ("Start", "Near Region", "Far", "Home")
    )
    party = Party(Unit(training=4), (Unit(equipment=1),), owner_id="north")
    near_keep = Settlement("Near Keep", 2, owner_id="south")
    far_keep = Settlement("Far Keep", 2, owner_id="south")
    home_keep = Settlement("Home Keep", 2, owner_id="north")
    world = WorldMap(
        (start, near, far, home),
        settlements={near: near_keep, far: far_keep, home: home_keep},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), settlements=(home_keep,)),
            Duchy("south", Unit(), settlements=(near_keep, far_keep)),
        )
    )
    calendar = Calendar(year=1, month=1)
    app = GameApp(world, game, calendar, Rng(3), player_duchy_id="north")

    code, body = app.handle("GET", "/")
    assert code == 200

    expected_near_action = f"/order/march?target={quote('Near Region')}"
    expected_far_action = f"/order/march?target={quote('Far')}"
    assert _has_post_form(body, expected_near_action)
    assert _has_post_form(body, expected_far_action)
    # Own-owned or settlement-less regions are not march targets.
    assert not _has_post_form(body, "/order/march?target=Home")
    assert not _has_post_form(body, "/order/march?target=Start")
    # Bare fallback form absent: the player has a party on the map.
    assert not _has_post_march_form(body)
    assert "Near Region" in body
    assert "Far" in body


def test_game_app_render_assault_forms_one_per_foreign_settlement_region():
    """GET / renders one assault form per foreign-owned region when player has a party.

    Contract (task-090 / K15.2c):
    - when player_duchy_id is set, game is not over, and the player duchy has
      a party on the map, _render emits one
      ``<form method="post" action="/order/assault?target=<name>">`` per region
      in world.regions whose settlement has ``owner_id != player_duchy_id``
      (name URL-encoded via urllib.parse.quote); the bare fallback
      ``/order/assault`` form is absent
    - a region with no settlement, or with a settlement owned by the player,
      is not an assault target
    - the submit button carries the target region's name
    """
    start, near, far, home = map(
        Region, ("Start", "Near Region", "Far", "Home")
    )
    party = Party(Unit(training=4), (Unit(equipment=1),), owner_id="north")
    near_keep = Settlement("Near Keep", 2, owner_id="south")
    far_keep = Settlement("Far Keep", 2, owner_id="south")
    home_keep = Settlement("Home Keep", 2, owner_id="north")
    world = WorldMap(
        (start, near, far, home),
        settlements={near: near_keep, far: far_keep, home: home_keep},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), settlements=(home_keep,)),
            Duchy("south", Unit(), settlements=(near_keep, far_keep)),
        )
    )
    calendar = Calendar(year=1, month=1)
    app = GameApp(world, game, calendar, Rng(3), player_duchy_id="north")

    code, body = app.handle("GET", "/")
    assert code == 200

    expected_near_action = f"/order/assault?target={quote('Near Region')}"
    expected_far_action = f"/order/assault?target={quote('Far')}"
    assert _has_post_form(body, expected_near_action)
    assert _has_post_form(body, expected_far_action)
    # Own-owned or settlement-less regions are not assault targets.
    assert not _has_post_form(body, "/order/assault?target=Home")
    assert not _has_post_form(body, "/order/assault?target=Start")
    # Bare fallback form absent: the player has a party on the map.
    assert not _has_post_assault_form(body)
    assert "Near Region" in body
    assert "Far" in body


def test_game_app_render_engage_forms_one_per_adjacent_enemy_party_region():
    """GET / renders one engage form per adjacent enemy-party region (task-106 / K19.1c).

    Contract:
    - when player_duchy_id is set, game is not over, and the player duchy has
      a party on the map, _render emits one
      ``<form method="post" action="/order/engage?target=<name>">`` per region
      in ``world.neighbors(player_party_region)`` that holds a party with an
      explicit ``owner_id != player_duchy_id`` (name URL-encoded via
      urllib.parse.quote); the bare fallback ``/order/engage`` form is absent
    - a neighbor with no party, or with a party owned by the player, is not
      an engage target; a non-neighbor enemy party is not a target either
    - the submit button carries the target region's name
    """
    start, near, far, own, empty = map(
        Region, ("Start", "Near", "Far", "Own", "Empty")
    )
    player_party = Party(Unit(training=4), owner_id="north")
    near_enemy = Party(Unit(training=1), owner_id="south")
    far_enemy = Party(Unit(training=1), owner_id="south")
    own_party = Party(Unit(training=1), owner_id="north")
    world = WorldMap(
        (start, near, far, own, empty),
        (
            (start, near),
            (start, far),
            (start, own),
            (start, empty),
        ),
        parties={
            start: player_party,
            near: near_enemy,
            far: far_enemy,
            own: own_party,
        },
    )
    game = GameState(
        (
            Duchy(
                "north",
                player_party.hero,
                parties=(player_party, own_party),
            ),
            Duchy("south", Unit(), parties=(near_enemy, far_enemy)),
        )
    )
    calendar = Calendar(year=1, month=1)
    app = GameApp(world, game, calendar, Rng(3), player_duchy_id="north")

    code, body = app.handle("GET", "/")
    assert code == 200

    expected_near_action = f"/order/engage?target={quote('Near')}"
    expected_far_action = f"/order/engage?target={quote('Far')}"
    assert _has_post_form(body, expected_near_action)
    assert _has_post_form(body, expected_far_action)
    # Own-owned or party-less neighbors are not engage targets.
    assert not _has_post_form(body, "/order/engage?target=Own")
    assert not _has_post_form(body, "/order/engage?target=Empty")
    # Bare fallback form absent: the player has a party on the map.
    assert not _has_post_engage_form(body)
    assert "Near" in body
    assert "Far" in body


def test_game_app_render_develop_order_section_header_before_recruit():
    """GET / has exactly one develop section header immediately before recruit (K30.1a).

    Contract (task-152 / K30.1a):
    - with player_duchy_id set, body contains exactly one
      ``<h2 data-order-section="develop">Rozwój</h2>``
    - that header appears immediately before the recruit form
      (``action="/order/recruit"``)
    - develop header precedes march, assault and engage section headers
      (order: develop → march → assault → engage)
    """
    world, game = _ongoing_world_game()
    app = GameApp(
        world, game, Calendar(year=1, month=1), Rng(3), player_duchy_id="north"
    )

    code, body = app.handle("GET", "/")
    assert code == 200

    develop_header = '<h2 data-order-section="develop">Rozwój</h2>'
    march_header = '<h2 data-order-section="march">Marsz</h2>'
    assault_header = '<h2 data-order-section="assault">Szturm</h2>'
    engage_header = '<h2 data-order-section="engage">Starcie</h2>'
    recruit_form_open = '<form method="post" action="/order/recruit">'

    assert body.count(develop_header) == 1
    assert develop_header + recruit_form_open in body

    develop_pos = body.index(develop_header)
    march_pos = body.index(march_header)
    assault_pos = body.index(assault_header)
    engage_pos = body.index(engage_header)
    assert develop_pos < march_pos < assault_pos < engage_pos


def test_game_app_recruit_button_shows_gold_cost_from_settlement_constant(
    monkeypatch,
):
    """GET /: recruit submit label is Rekrutuj (koszt złota: N) from core (K30.2a).

    Contract (task-153 / K30.2a):
    - form action=/order/recruit submit button text is
      ``Rekrutuj (koszt złota: N)`` where N is ``tbb.settlement.RECRUIT_GOLD_COST``
      (value read from that constant, not a bare ``Rekrutuj`` / template literal)
    - when ``RECRUIT_GOLD_COST`` is monkeypatched to another value, the button
      text shows that new value (proof the label is driven by the core constant)
    - form still POSTs to ``/order/recruit`` (action/method unchanged)
    """
    world, game = _ongoing_world_game()
    app = GameApp(
        world, game, Calendar(year=1, month=1), Rng(1), player_duchy_id="north"
    )

    code, body = app.handle("GET", "/")
    assert code == 200
    assert _has_post_recruit_form(body)
    cost = settlement_module.RECRUIT_GOLD_COST
    assert _form_submit_button_text(body, "/order/recruit") == (
        f"Rekrutuj (koszt złota: {cost})"
    )

    patched_cost = cost + 7
    monkeypatch.setattr(settlement_module, "RECRUIT_GOLD_COST", patched_cost)
    code2, body2 = app.handle("GET", "/")
    assert code2 == 200
    assert _has_post_recruit_form(body2)
    assert _form_submit_button_text(body2, "/order/recruit") == (
        f"Rekrutuj (koszt złota: {patched_cost})"
    )


def test_game_app_render_order_section_headers_precede_their_forms():
    """GET / has one h2 header per order section, in order, before its forms (task-112 / K21.2).

    Contract:
    - body contains exactly one of each:
      ``<h2 data-order-section="march">Marsz</h2>``,
      ``<h2 data-order-section="assault">Szturm</h2>``,
      ``<h2 data-order-section="engage">Starcie</h2>``
    - they appear in this order: march, assault, engage
    - each header precedes the start of its own form group
      (``action="/order/march``, ``action="/order/assault``, ``action="/order/engage``)
    - player_duchy_id=None (observer) still renders the page without error
    """
    start, near = map(Region, ("Start", "Near"))
    world = WorldMap((start, near))
    game = GameState((Duchy("north", Unit()), Duchy("south", Unit())))
    calendar = Calendar(year=1, month=1)
    app = GameApp(world, game, calendar, Rng(3), player_duchy_id=None)

    code, body = app.handle("GET", "/")
    assert code == 200

    march_header = '<h2 data-order-section="march">Marsz</h2>'
    assault_header = '<h2 data-order-section="assault">Szturm</h2>'
    engage_header = '<h2 data-order-section="engage">Starcie</h2>'

    assert body.count(march_header) == 1
    assert body.count(assault_header) == 1
    assert body.count(engage_header) == 1

    march_pos = body.index(march_header)
    assault_pos = body.index(assault_header)
    engage_pos = body.index(engage_header)
    assert march_pos < assault_pos < engage_pos

    march_form_pos = body.index('action="/order/march')
    assault_form_pos = body.index('action="/order/assault')
    engage_form_pos = body.index('action="/order/engage')
    assert march_pos < march_form_pos
    assert assault_pos < assault_form_pos
    assert engage_pos < engage_form_pos


def test_game_app_post_order_march_with_target_applies_march_to():
    """POST /order/march?target=<region> applies march_duchy_party_to + re-syncs.

    Contract (task-086 / K15.1b):
    - handle splits path from query so POST /order/march?target=… routes as march
    - non-empty URL-decoded target matching a name in world.regions applies
      via _apply_player_order the transition
      ``lambda world, duchy: ai.march_duchy_party_to(world, duchy, region)``;
      replaces self.world, re-syncs game from the new map; returns (200, page)
    - target is *not* the nearest enemy settlement, so the step cannot come
      from the automatic march_duchy_party fallback
    """
    start, step_near, near, step_far, far = map(
        Region, ("Start", "StepNear", "Near", "StepFar", "Far")
    )
    party = Party(Unit(training=4), (Unit(equipment=1),), owner_id="north")
    near_keep = Settlement("Near Keep", 2, owner_id="south")
    far_keep = Settlement("Far Keep", 2, owner_id="south")
    world = WorldMap(
        (start, step_near, near, step_far, far),
        (
            (start, step_near),
            (step_near, near),
            (start, step_far),
            (step_far, far),
        ),
        settlements={near: near_keep, far: far_keep},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,)),
            Duchy("south", Unit(), settlements=(near_keep, far_keep)),
        )
    )
    assert not game.is_over
    calendar = Calendar(year=2, month=3)
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")

    world_before = app.world
    game_before = app.game
    # Automatic nearest-enemy march would step toward Near, not Far.
    auto = ai.march_duchy_party(world_before, game_before.duchies[0])
    assert auto.party_at(step_near) is party
    assert auto.party_at(step_far) is None

    expected_world = ai.march_duchy_party_to(
        world_before, game_before.duchies[0], far
    )
    expected_game = game_before.sync_from_world(expected_world)
    assert expected_world.party_at(step_far) is party
    assert expected_world.party_at(start) is None
    assert expected_world.party_at(step_near) is None
    assert expected_world is not world_before

    code, body = app.handle("POST", "/order/march?target=Far")
    assert code == 200
    assert isinstance(body, str)
    assert body.strip() != ""
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"
    assert _calendar_stamp(body) == (2, 3)

    # World replaced with explicit-target march; game re-synced.
    assert app.world is not world_before
    assert app.world.party_at(step_far) is party
    assert app.world.party_at(start) is None
    assert app.world.party_at(step_near) is None
    assert app.world.party_at(step_far) == expected_world.party_at(step_far)
    assert app.game is not game_before
    player = next(d for d in app.game.duchies if d.duchy_id == "north")
    expected_player = next(
        d for d in expected_game.duchies if d.duchy_id == "north"
    )
    assert player.parties == expected_player.parties
    assert app.world.settlement_at(near) is near_keep
    assert app.world.settlement_at(far) is far_keep
    assert app.calendar == calendar
    # Inputs must not have been mutated in place.
    assert world_before.party_at(start) is party
    assert world_before.party_at(step_far) is None


def test_game_app_post_order_march_empty_or_unknown_target_falls_back():
    """POST /order/march?target=<empty|unknown> falls back to march_duchy_party.

    Contract (task-086 / K15.1b): an empty ``target`` value or one that does
    not match any region name in ``world.regions`` is treated the same as no
    ``target`` at all — the nearest-enemy fallback (``ai.march_duchy_party``)
    applies, not ``march_duchy_party_to``.
    """
    start, step_near, near, step_far, far = map(
        Region, ("Start", "StepNear", "Near", "StepFar", "Far")
    )
    party = Party(Unit(training=4), (Unit(equipment=1),), owner_id="north")
    near_keep = Settlement("Near Keep", 2, owner_id="south")
    far_keep = Settlement("Far Keep", 2, owner_id="south")
    world = WorldMap(
        (start, step_near, near, step_far, far),
        (
            (start, step_near),
            (step_near, near),
            (start, step_far),
            (step_far, far),
        ),
        settlements={near: near_keep, far: far_keep},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,)),
            Duchy("south", Unit(), settlements=(near_keep, far_keep)),
        )
    )
    calendar = Calendar(year=2, month=3)

    for query in ("/order/march?target=", "/order/march?target=Nonexistent"):
        app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")
        code, body = app.handle("POST", query)
        assert code == 200
        assert body.strip() != ""
        # Fallback nearest-enemy march steps toward Near, not Far.
        assert app.world.party_at(step_near) is party
        assert app.world.party_at(step_far) is None


def test_game_app_post_order_assault_applies_assault_and_resyncs():
    """POST /order/assault applies ai.assault_duchy_party + re-syncs game.

    Contract (task-084 / K14.2e2):
    - when player_duchy_id is set, game is not is_over, and the player duchy
      exists in game.duchies: applies ai.assault_duchy_party(self.world,
      player_duchy, self.rng, morale_by_owner={d.duchy_id: d.morale for d
      in self.game.duchies}), replaces self.world, re-syncs
      self.game = self.game.sync_from_world(self.world); returns (200, page)
    - player duchy looked up by duchy_id == player_duchy_id
    - party adjacent to enemy settlement resolves assault with duchy morale
    """
    start, target = map(Region, ("Start", "Target"))
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    enemy_keep = Settlement(
        "Enemy Keep", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        (start, target),
        ((start, target),),
        settlements={target: enemy_keep},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), morale=10),
            Duchy("south", Unit(), settlements=(enemy_keep,), morale=-5),
        )
    )
    assert not game.is_over
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(world, game, calendar, Rng(seed), player_duchy_id="north")

    world_before = app.world
    game_before = app.game
    assert world_before.party_at(start) is party
    assert world_before.settlement_at(target) is enemy_keep

    morale_by_owner = {d.duchy_id: d.morale for d in game_before.duchies}
    assert morale_by_owner == {"north": 10, "south": -5}
    player_duchy = next(
        d for d in game_before.duchies if d.duchy_id == "north"
    )
    expected_world = ai.assault_duchy_party(
        world_before,
        player_duchy,
        Rng(seed),
        morale_by_owner=morale_by_owner,
    )
    expected_game = game_before.sync_from_world(expected_world)
    assert expected_world is not world_before
    assert expected_world != world_before

    code, body = app.handle("POST", "/order/assault")
    assert code == 200
    assert isinstance(body, str)
    assert body.strip() != ""
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"
    assert _calendar_stamp(body) == (2, 3)

    # World replaced with assault result; game re-synced from that world.
    assert app.world is not world_before
    assert app.world == expected_world
    assert app.game is not game_before
    player = next(d for d in app.game.duchies if d.duchy_id == "north")
    expected_player = next(
        d for d in expected_game.duchies if d.duchy_id == "north"
    )
    assert player.parties == expected_player.parties
    assert player.settlements == expected_player.settlements
    south = next(d for d in app.game.duchies if d.duchy_id == "south")
    expected_south = next(
        d for d in expected_game.duchies if d.duchy_id == "south"
    )
    assert south.settlements == expected_south.settlements
    assert app.calendar == calendar
    # Inputs to the call must not have been mutated in place.
    assert world_before.party_at(start) is party
    assert world_before.settlement_at(target) is enemy_keep
    assert enemy_keep.owner_id == "south"


def test_game_app_post_order_assault_with_target_applies_assault_to():
    """POST /order/assault?target=<region> applies assault_duchy_party_to + re-syncs.

    Contract (task-089 / K15.2b):
    - handle splits path from query so POST /order/assault?target=… routes as
      assault
    - non-empty URL-decoded target matching a name in world.regions applies
      via _apply_player_order the transition
      ``lambda world, duchy: ai.assault_duchy_party_to(world, duchy, region,
      self.rng, morale_by_owner=...)`` with morale_by_owner built from
      self.game.duchies; replaces self.world, re-syncs game from the new map;
      returns (200, page)
    - target is *not* the nearest enemy settlement (tie-break keeps the first
      region in world.regions order), so the resolved battle cannot come from
      the automatic assault_duchy_party fallback
    """
    start, keep_a_region, keep_b_region = map(
        Region, ("Start", "KeepA", "KeepB")
    )
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    keep_a = Settlement(
        "Keep A", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    keep_b = Settlement(
        "Keep B", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        (start, keep_a_region, keep_b_region),
        ((start, keep_a_region), (start, keep_b_region)),
        settlements={keep_a_region: keep_a, keep_b_region: keep_b},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), morale=10),
            Duchy("south", Unit(), settlements=(keep_a, keep_b), morale=-5),
        )
    )
    assert not game.is_over
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(world, game, calendar, Rng(seed), player_duchy_id="north")

    world_before = app.world
    game_before = app.game
    player_duchy = next(
        d for d in game_before.duchies if d.duchy_id == "north"
    )
    # Automatic nearest-enemy assault ties on distance and keeps the first
    # region in world.regions order: KeepA, not KeepB.
    auto = ai.assault_duchy_party(
        world_before,
        player_duchy,
        Rng(seed),
        morale_by_owner={d.duchy_id: d.morale for d in game_before.duchies},
    )
    assert auto.settlement_at(keep_a_region).owner_id == "north"
    assert auto.settlement_at(keep_b_region).owner_id == "south"

    expected_world = ai.assault_duchy_party_to(
        world_before,
        player_duchy,
        keep_b_region,
        Rng(seed),
        morale_by_owner={d.duchy_id: d.morale for d in game_before.duchies},
    )
    expected_game = game_before.sync_from_world(expected_world)
    assert expected_world.settlement_at(keep_b_region).owner_id == "north"
    assert expected_world.settlement_at(keep_a_region).owner_id == "south"

    code, body = app.handle("POST", "/order/assault?target=KeepB")
    assert code == 200
    assert isinstance(body, str)
    assert body.strip() != ""
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"
    assert _calendar_stamp(body) == (2, 3)

    # World replaced with explicit-target assault result; game re-synced.
    assert app.world is not world_before
    assert app.world.settlement_at(keep_b_region).owner_id == "north"
    assert app.world.settlement_at(keep_a_region).owner_id == "south"
    assert app.game is not game_before
    player = next(d for d in app.game.duchies if d.duchy_id == "north")
    expected_player = next(
        d for d in expected_game.duchies if d.duchy_id == "north"
    )
    assert player.parties == expected_player.parties
    assert player.settlements == expected_player.settlements
    assert app.calendar == calendar
    # Inputs to the call must not have been mutated in place.
    assert world_before.settlement_at(keep_a_region) is keep_a
    assert world_before.settlement_at(keep_b_region) is keep_b
    assert keep_a.owner_id == "south"
    assert keep_b.owner_id == "south"


def test_game_app_post_order_assault_with_target_sets_last_battle_and_renders_svg():
    """POST /order/assault?target=<region> sets last_battle and _render embeds its SVG.

    Contract (task-096 / K16.1d-2):
    - ``GameApp.last_battle`` starts as ``None``.
    - With an explicit ``target``, the assault reuses
      ``ai.assault_duchy_party_to_recorded`` (not the non-recorded variant),
      which returns ``(world, HexBattle)``; ``self.last_battle`` is set to
      that ``HexBattle``.
    - The returned page embeds ``render_battle_svg(self.last_battle)`` because
      ``_render`` calls ``render_game_page(..., battle=self.last_battle)``.
    """
    start, keep_a_region, keep_b_region = map(
        Region, ("Start", "KeepA", "KeepB")
    )
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    keep_a = Settlement(
        "Keep A", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    keep_b = Settlement(
        "Keep B", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        (start, keep_a_region, keep_b_region),
        ((start, keep_a_region), (start, keep_b_region)),
        settlements={keep_a_region: keep_a, keep_b_region: keep_b},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), morale=10),
            Duchy("south", Unit(), settlements=(keep_a, keep_b), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(world, game, calendar, Rng(seed), player_duchy_id="north")
    assert app.last_battle is None

    player_duchy = next(d for d in game.duchies if d.duchy_id == "north")
    _, expected_battle = ai.assault_duchy_party_to_recorded(
        world,
        player_duchy,
        keep_b_region,
        Rng(seed),
        morale_by_owner={d.duchy_id: d.morale for d in game.duchies},
    )
    assert expected_battle is not None

    code, body = app.handle("POST", "/order/assault?target=KeepB")
    assert code == 200
    assert app.last_battle == expected_battle
    assert render_battle_svg(expected_battle) in body


def test_game_app_post_order_recruit_clears_last_battle():
    """POST /order/recruit resets self.last_battle to None (task-097 / K16.1d-3).

    A recorded battle from a prior assault must not linger once the player
    issues a different order: the returned page no longer embeds the old
    battle's SVG.
    """
    start, keep_a_region, keep_b_region = map(
        Region, ("Start", "KeepA", "KeepB")
    )
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    keep_a = Settlement(
        "Keep A", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    keep_b = Settlement(
        "Keep B", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        (start, keep_a_region, keep_b_region),
        ((start, keep_a_region), (start, keep_b_region)),
        settlements={keep_a_region: keep_a, keep_b_region: keep_b},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), morale=10),
            Duchy("south", Unit(), settlements=(keep_a, keep_b), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(world, game, calendar, Rng(seed), player_duchy_id="north")

    code, body = app.handle("POST", "/order/assault?target=KeepB")
    assert code == 200
    assert app.last_battle is not None
    battle_svg = render_battle_svg(app.last_battle)
    assert battle_svg in body

    code2, body2 = app.handle("POST", "/order/recruit")
    assert code2 == 200
    assert app.last_battle is None
    assert battle_svg not in body2


def test_game_app_post_order_march_with_target_clears_last_battle():
    """POST /order/march?target=<region> resets self.last_battle to None (task-097 / K16.1d-3).

    A recorded battle from a prior assault must not linger once the player
    marches a party: the returned page no longer embeds the old battle's SVG.
    """
    start, keep_a_region, keep_b_region = map(
        Region, ("Start", "KeepA", "KeepB")
    )
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    keep_a = Settlement(
        "Keep A", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    keep_b = Settlement(
        "Keep B", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        (start, keep_a_region, keep_b_region),
        ((start, keep_a_region), (start, keep_b_region)),
        settlements={keep_a_region: keep_a, keep_b_region: keep_b},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), morale=10),
            Duchy("south", Unit(), settlements=(keep_a, keep_b), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(world, game, calendar, Rng(seed), player_duchy_id="north")

    code, body = app.handle("POST", "/order/assault?target=KeepB")
    assert code == 200
    assert app.last_battle is not None
    battle_svg = render_battle_svg(app.last_battle)
    assert battle_svg in body

    code2, body2 = app.handle("POST", "/order/march?target=KeepA")
    assert code2 == 200
    assert app.last_battle is None
    assert battle_svg not in body2


def test_game_app_post_order_march_clears_last_battle():
    """POST /order/march (no target) resets self.last_battle to None (task-097 / K16.1d-3).

    Acceptance requires march both with and without ``?target=`` to clear the
    recorded battle; the with-target case is covered separately.
    """
    _assault_then_order_clears_last_battle("/order/march")


def _assault_then_order_clears_last_battle(order_route: str) -> None:
    """Shared body: assault sets last_battle, then order_route clears it (task-097 / K16.1d-3)."""
    start, keep_a_region, keep_b_region = map(
        Region, ("Start", "KeepA", "KeepB")
    )
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    keep_a = Settlement(
        "Keep A", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    keep_b = Settlement(
        "Keep B", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        (start, keep_a_region, keep_b_region),
        ((start, keep_a_region), (start, keep_b_region)),
        settlements={keep_a_region: keep_a, keep_b_region: keep_b},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), morale=10),
            Duchy("south", Unit(), settlements=(keep_a, keep_b), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(world, game, calendar, Rng(seed), player_duchy_id="north")

    code, body = app.handle("POST", "/order/assault?target=KeepB")
    assert code == 200
    assert app.last_battle is not None
    battle_svg = render_battle_svg(app.last_battle)
    assert battle_svg in body

    code2, body2 = app.handle("POST", order_route)
    assert code2 == 200
    assert app.last_battle is None
    assert battle_svg not in body2


def test_game_app_post_order_muster_clears_last_battle():
    """POST /order/muster resets self.last_battle to None (task-097 / K16.1d-3)."""
    _assault_then_order_clears_last_battle("/order/muster")


def test_game_app_post_order_develop_clears_last_battle():
    """POST /order/develop resets self.last_battle to None (task-097 / K16.1d-3)."""
    _assault_then_order_clears_last_battle("/order/develop")


def test_game_app_post_turn_clears_last_battle():
    """POST /turn resets self.last_battle to None (task-097 / K16.1d-3).

    South owns a single settlement and nothing else, so conquering it ends
    the game; the following ``POST /turn`` takes the is_over no-op path
    (task-074 / V13.5a) and still must clear the recorded battle.
    """
    start, target = map(Region, ("Start", "Target"))
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    enemy_keep = Settlement(
        "Enemy Keep", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        (start, target),
        ((start, target),),
        settlements={target: enemy_keep},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), morale=10),
            Duchy("south", None, settlements=(enemy_keep,), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(world, game, calendar, Rng(seed), player_duchy_id="north")

    code, body = app.handle("POST", "/order/assault")
    assert code == 200
    assert app.last_battle is not None
    assert app.game.is_over
    battle_svg = render_battle_svg(app.last_battle)
    assert battle_svg in body

    code2, body2 = app.handle("POST", "/turn")
    assert code2 == 200
    assert app.last_battle is None
    assert battle_svg not in body2


def test_game_app_post_order_assault_without_target_sets_last_battle_and_renders_svg():
    """POST /order/assault (no target) sets last_battle via assault_duchy_party_recorded.

    Contract (task-096 / K16.1d-2):
    - auto (no ``target``) assault reuses ``ai.assault_duchy_party_recorded``,
      which returns ``(world, HexBattle)``; on a hit ``self.last_battle`` is
      set to that ``HexBattle`` and its SVG is embedded via ``_render``.
    - when the transition finds no target (no party / no adjacent enemy), the
      no-op path returns ``(world, None)`` and leaves ``self.last_battle``
      as ``None``.
    """
    start, target = map(Region, ("Start", "Target"))
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    enemy_keep = Settlement(
        "Enemy Keep", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        (start, target),
        ((start, target),),
        settlements={target: enemy_keep},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), morale=10),
            Duchy("south", Unit(), settlements=(enemy_keep,), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(world, game, calendar, Rng(seed), player_duchy_id="north")
    assert app.last_battle is None

    player_duchy = next(d for d in game.duchies if d.duchy_id == "north")
    expected_world, expected_battle = ai.assault_duchy_party_recorded(
        world,
        player_duchy,
        Rng(seed),
        morale_by_owner={d.duchy_id: d.morale for d in game.duchies},
    )
    assert expected_battle is not None
    assert expected_world.settlement_at(target).owner_id == "north"

    code, body = app.handle("POST", "/order/assault")
    assert code == 200
    assert app.last_battle == expected_battle
    assert render_battle_svg(expected_battle) in body

    # No-op: party has no adjacent enemy settlement — transition finds no
    # target, so last_battle stays None even though the order guards pass.
    isolated = Region("Isolated")
    lone_party = Party(Unit(training=5, equipment=6), owner_id="north")
    lone_world = WorldMap((isolated,), (), parties={isolated: lone_party})
    lone_game = GameState((Duchy("north", lone_party.hero, parties=(lone_party,)),))
    lone_app = GameApp(
        lone_world, lone_game, calendar, Rng(seed), player_duchy_id="north"
    )
    code_lone, _body_lone = lone_app.handle("POST", "/order/assault")
    assert code_lone == 200
    assert lone_app.last_battle is None


def test_game_app_order_engage_form_on_get():
    """GET / embeds bare <form method="post" action="/order/engage"> (task-103 / K18.1c).

    Contract: ``_render`` always appends ``_ENGAGE_FORM`` (auto-cel; no per-target
    forms), with a submit button, independent of whether a fight is available.
    """
    world, game = _ongoing_world_game()
    app = GameApp(world, game, Calendar(year=2, month=3), Rng(11), player_duchy_id="north")
    code, body = app.handle("GET", "/")
    assert code == 200
    assert _has_post_engage_form(body)
    assert re.search(
        r"<button\b[^>]*>\s*Starcie\s*</button>", body, flags=re.IGNORECASE
    )


def test_game_app_post_order_engage_sets_last_battle_and_renders_svg():
    """POST /order/engage sets last_battle via ai.engage_duchy_party_recorded (task-103 / K18.1c).

    Contract:
    - route goes through ``_apply_player_assault_order`` with
      ``ai.engage_duchy_party_recorded(world, duchy, self.rng, morale_by_owner=...)``;
      on a hit ``self.last_battle`` is set and its SVG is embedded via ``_render``.
    - no-op (no adjacent enemy party) leaves ``self.last_battle`` as ``None``.
    """
    start, target = map(Region, ("Start", "Target"))
    north_party = Party(Unit(training=5, equipment=6), owner_id="north")
    south_party = Party(Unit(training=1, equipment=1), owner_id="south")
    world = WorldMap(
        (start, target),
        ((start, target),),
        parties={start: north_party, target: south_party},
    )
    game = GameState(
        (
            Duchy("north", north_party.hero, parties=(north_party,), morale=10),
            Duchy("south", south_party.hero, parties=(south_party,), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(world, game, calendar, Rng(seed), player_duchy_id="north")
    assert app.last_battle is None

    player_duchy = next(d for d in game.duchies if d.duchy_id == "north")
    expected_world, expected_battle = ai.engage_duchy_party_recorded(
        world,
        player_duchy,
        Rng(seed),
        morale_by_owner={d.duchy_id: d.morale for d in game.duchies},
    )
    assert expected_battle is not None

    code, body = app.handle("POST", "/order/engage")
    assert code == 200
    assert app.last_battle == expected_battle
    assert render_battle_svg(expected_battle) in body

    # No-op: party has no adjacent enemy party — transition finds no target,
    # so last_battle stays None even though the order guards pass.
    isolated = Region("Isolated")
    lone_party = Party(Unit(training=5, equipment=6), owner_id="north")
    lone_world = WorldMap((isolated,), (), parties={isolated: lone_party})
    lone_game = GameState((Duchy("north", lone_party.hero, parties=(lone_party,)),))
    lone_app = GameApp(
        lone_world, lone_game, calendar, Rng(seed), player_duchy_id="north"
    )
    code_lone, _body_lone = lone_app.handle("POST", "/order/engage")
    assert code_lone == 200
    assert lone_app.last_battle is None


def test_game_app_post_order_engage_noop_when_no_player_duchy_id():
    """POST /order/engage is a no-op when player_duchy_id is None (task-103 / K18.1c).

    Contract: engage goes through the same guard as assault
    (``_apply_player_assault_order``), so with no player id the world/game are
    left untouched, ``self.rng`` is not drawn from, and last_battle stays None,
    while still returning ``(200, page)``.
    """
    start, target = map(Region, ("Start", "Target"))
    north_party = Party(Unit(training=5, equipment=6), owner_id="north")
    south_party = Party(Unit(training=1, equipment=1), owner_id="south")
    world = WorldMap(
        (start, target),
        ((start, target),),
        parties={start: north_party, target: south_party},
    )
    game = GameState(
        (
            Duchy("north", north_party.hero, parties=(north_party,), morale=10),
            Duchy("south", south_party.hero, parties=(south_party,), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)
    none_app = GameApp(world, game, calendar, Rng(11), player_duchy_id=None)
    world_before, game_before = none_app.world, none_app.game

    code, body = none_app.handle("POST", "/order/engage")

    assert code == 200
    assert isinstance(body, str)
    assert none_app.world is world_before
    assert none_app.game is game_before
    assert none_app.last_battle is None
    assert none_app.rng.randint(0, 10**9) == Rng(11).randint(0, 10**9)


def test_game_app_post_order_engage_with_target_applies_explicit_target():
    """POST /order/engage?target=<region> applies engage_duchy_party_to_recorded (task-105 / K19.1b).

    Contract (task-105 / K19.1b):
    - handle routes ``?target=`` through ``_order_target_region``, matching
      the ``/order/assault?target=`` pattern (task-089 / K15.2b)
    - non-empty, known target applies via ``_apply_player_assault_order`` the
      transition ``ai.engage_duchy_party_to_recorded(world, duchy, target,
      self.rng, morale_by_owner=...)`` with morale_by_owner built from
      self.game.duchies
    - target is *not* the auto-picked neighbor (first enemy party in
      ``world.neighbors`` order), so the resolved battle cannot come from the
      automatic ``engage_duchy_party_recorded`` fallback
    """
    start, enemy_a, enemy_b = map(Region, ("Start", "EnemyA", "EnemyB"))
    north_party = Party(Unit(training=5, equipment=6), owner_id="north")
    south_party_a = Party(Unit(training=1, equipment=1), owner_id="south")
    south_party_b = Party(Unit(training=1, equipment=1), owner_id="south")
    world = WorldMap(
        (start, enemy_a, enemy_b),
        ((start, enemy_a), (start, enemy_b)),
        parties={start: north_party, enemy_a: south_party_a, enemy_b: south_party_b},
    )
    game = GameState(
        (
            Duchy("north", north_party.hero, parties=(north_party,), morale=10),
            Duchy(
                "south",
                south_party_a.hero,
                parties=(south_party_a, south_party_b),
                morale=-5,
            ),
        )
    )
    assert not game.is_over
    calendar = Calendar(year=2, month=3)
    seed = 11
    app = GameApp(world, game, calendar, Rng(seed), player_duchy_id="north")

    world_before = app.world
    game_before = app.game
    player_duchy = next(d for d in game_before.duchies if d.duchy_id == "north")

    # Automatic engage picks the first neighbor with an enemy party: EnemyA.
    # (Battle outcomes are symmetric between EnemyA/EnemyB here, so only the
    # *map* distinguishes the auto pick from the explicit target below.)
    auto_world, auto_battle = ai.engage_duchy_party_recorded(
        world_before,
        player_duchy,
        Rng(seed),
        morale_by_owner={d.duchy_id: d.morale for d in game_before.duchies},
    )
    assert auto_battle is not None
    assert auto_world.party_at(enemy_a).owner_id == "north"
    assert auto_world.party_at(enemy_b).owner_id == "south"

    expected_world, expected_battle = ai.engage_duchy_party_to_recorded(
        world_before,
        player_duchy,
        enemy_b,
        Rng(seed),
        morale_by_owner={d.duchy_id: d.morale for d in game_before.duchies},
    )
    expected_game = game_before.sync_from_world(expected_world)
    assert expected_battle is not None

    code, body = app.handle("POST", "/order/engage?target=EnemyB")
    assert code == 200
    assert isinstance(body, str)
    assert body.strip() != ""
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"
    assert _calendar_stamp(body) == (2, 3)

    assert app.world is not world_before
    assert app.last_battle == expected_battle
    # Explicit target EnemyB was engaged, not the auto-picked EnemyA: the
    # winning party moved onto EnemyB while EnemyA is untouched.
    assert app.world.party_at(enemy_a).owner_id == "south"
    assert app.world.party_at(enemy_b).owner_id == "north"
    assert app.game is not game_before
    player = next(d for d in app.game.duchies if d.duchy_id == "north")
    expected_player = next(
        d for d in expected_game.duchies if d.duchy_id == "north"
    )
    assert player.parties == expected_player.parties
    assert app.calendar == calendar
    # Inputs to the call must not have been mutated in place.
    assert world_before.party_at(enemy_a) is south_party_a
    assert world_before.party_at(enemy_b) is south_party_b


def test_game_app_post_order_engage_empty_or_unknown_target_falls_back():
    """POST /order/engage?target=<empty|unknown> falls back to engage_duchy_party_recorded.

    Contract (task-105 / K19.1b): an empty ``target`` value or one that does
    not match any region name in ``world.regions`` is treated the same as no
    ``target`` at all — the auto-cel fallback (``ai.engage_duchy_party_recorded``)
    applies, not ``engage_duchy_party_to_recorded``.
    """
    start, enemy_a, enemy_b = map(Region, ("Start", "EnemyA", "EnemyB"))
    north_party = Party(Unit(training=5, equipment=6), owner_id="north")
    south_party_a = Party(Unit(training=1, equipment=1), owner_id="south")
    south_party_b = Party(Unit(training=1, equipment=1), owner_id="south")
    world = WorldMap(
        (start, enemy_a, enemy_b),
        ((start, enemy_a), (start, enemy_b)),
        parties={start: north_party, enemy_a: south_party_a, enemy_b: south_party_b},
    )
    game = GameState(
        (
            Duchy("north", north_party.hero, parties=(north_party,), morale=10),
            Duchy(
                "south",
                south_party_a.hero,
                parties=(south_party_a, south_party_b),
                morale=-5,
            ),
        )
    )
    calendar = Calendar(year=2, month=3)

    for query in (
        "/order/engage?target=",
        "/order/engage?target=Nonexistent",
    ):
        app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")
        code, body = app.handle("POST", query)
        assert code == 200
        assert body.strip() != ""
        # Auto-cel engage picks the first neighbor with an enemy party:
        # EnemyA, not the never-specified EnemyB.
        assert app.world.party_at(enemy_a).owner_id == "north"
        assert app.world.party_at(enemy_b).owner_id == "south"


def test_game_app_post_order_assault_empty_or_unknown_target_falls_back():
    """POST /order/assault?target=<empty|unknown> falls back to assault_duchy_party.

    Contract (task-089 / K15.2b): an empty ``target`` value or one that does
    not match any region name in ``world.regions`` is treated the same as no
    ``target`` at all — the nearest-enemy fallback (``ai.assault_duchy_party``)
    applies, not ``assault_duchy_party_to``.
    """
    start, keep_a_region, keep_b_region = map(
        Region, ("Start", "KeepA", "KeepB")
    )
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    keep_a = Settlement(
        "Keep A", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    keep_b = Settlement(
        "Keep B", population=1, garrison=(Unit(equipment=1),), owner_id="south"
    )
    world = WorldMap(
        (start, keep_a_region, keep_b_region),
        ((start, keep_a_region), (start, keep_b_region)),
        settlements={keep_a_region: keep_a, keep_b_region: keep_b},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,), morale=10),
            Duchy("south", Unit(), settlements=(keep_a, keep_b), morale=-5),
        )
    )
    calendar = Calendar(year=2, month=3)

    for query in (
        "/order/assault?target=",
        "/order/assault?target=Nonexistent",
    ):
        app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")
        code, body = app.handle("POST", query)
        assert code == 200
        assert body.strip() != ""
        # Fallback nearest-enemy assault ties on distance and keeps the
        # first region in world.regions order: KeepA, not KeepB.
        assert app.world.settlement_at(keep_a_region).owner_id == "north"
        assert app.world.settlement_at(keep_b_region).owner_id == "south"


def test_game_app_order_assault_form_noop_and_determinism():
    """GET form /order/assault; no-op guards; assault sequence determinism.

    Contract (task-084 / K14.2e2; GET form adapted K15.2c):
    - GET / embeds per-target assault forms when the player has a party (K15.2c);
      bare ``/order/assault`` is present only as fallback (no player / no party /
      game over)
    - when player_duchy_id is None, game is is_over, or player duchy is absent
      from game.duchies: POST /order/assault is a no-op (state unchanged, no RNG
      draw), still (200, page)
    - fixed GameApp seed + same handle sequence → identical bodies and state
    """
    def _assault_ready_world_game() -> tuple[
        WorldMap, GameState, Region, Region, Party, Settlement
    ]:
        """World where north party is adjacent to a weak enemy keep (assaultable)."""
        start, target = map(Region, ("Start", "Target"))
        party = Party(Unit(training=5, equipment=6), owner_id="north")
        enemy_keep = Settlement(
            "Enemy Keep",
            population=1,
            garrison=(Unit(equipment=1),),
            owner_id="south",
        )
        w = WorldMap(
            (start, target),
            ((start, target),),
            settlements={target: enemy_keep},
            parties={start: party},
        )
        g = GameState(
            (
                Duchy("north", party.hero, parties=(party,), morale=10),
                Duchy("south", Unit(), settlements=(enemy_keep,), morale=-5),
            )
        )
        return w, g, start, target, party, enemy_keep

    world, game, start, target, party, enemy_keep = _assault_ready_world_game()
    calendar = Calendar(year=2, month=3)

    # GET / embeds per-target assault forms when the player has a party (K15.2c).
    app = GameApp(world, game, calendar, Rng(11), player_duchy_id="north")
    code_get, body_get = app.handle("GET", "/")
    assert code_get == 200
    expected_target_action = f"/order/assault?target={quote('Target')}"
    assert _has_post_form(body_get, expected_target_action)
    assert not _has_post_assault_form(body_get)
    assert re.search(
        r"<button\b[^>]*>\s*Target\s*</button>", body_get, flags=re.IGNORECASE
    )

    # No-op: player_duchy_id is None — state frozen, RNG unused, still 200 + page.
    none_app = GameApp(world, game, calendar, Rng(11), player_duchy_id=None)
    world_n, game_n = none_app.world, none_app.game
    code_n, body_n = none_app.handle("POST", "/order/assault")
    assert code_n == 200
    assert isinstance(body_n, str)
    assert none_app.world is world_n
    assert none_app.game is game_n
    assert none_app.calendar == calendar
    assert none_app.last_battle is None
    assert _calendar_stamp(body_n) == (2, 3)
    assert _has_post_assault_form(body_n)
    # Would-be assault target unchanged (enemy keep still south-owned).
    assert none_app.world.party_at(start) is party
    assert none_app.world.settlement_at(target) is enemy_keep
    assert enemy_keep.owner_id == "south"
    # No RNG draw: next randint matches a fresh Rng(11).
    assert none_app.rng.randint(0, 10**9) == Rng(11).randint(0, 10**9)

    # No-op: game is_over — finished sole-duchy world.
    fin_world, fin_game = _finished_world_game()
    fin_cal = Calendar(year=5, month=1)
    fin_app = GameApp(
        fin_world, fin_game, fin_cal, Rng(3), player_duchy_id="north"
    )
    w_f, g_f = fin_app.world, fin_app.game
    code_f, body_f = fin_app.handle("POST", "/order/assault")
    assert code_f == 200
    assert fin_app.world is w_f
    assert fin_app.game is g_f
    assert fin_app.calendar == fin_cal
    assert fin_app.last_battle is None
    assert _calendar_stamp(body_f) == (5, 1)
    assert fin_app.rng.randint(0, 10**9) == Rng(3).randint(0, 10**9)

    # No-op: player duchy id not present in game.duchies.
    missing = GameApp(
        world, game, calendar, Rng(11), player_duchy_id="ghost"
    )
    w_m, g_m = missing.world, missing.game
    code_m, _body_m = missing.handle("POST", "/order/assault")
    assert code_m == 200
    assert missing.world is w_m
    assert missing.game is g_m
    assert missing.calendar == calendar
    assert missing.last_battle is None
    assert missing.world.party_at(start) is party
    assert missing.world.settlement_at(target) is enemy_keep
    assert missing.rng.randint(0, 10**9) == Rng(11).randint(0, 10**9)

    # Determinism: two apps, same seed, same assault sequence → same bodies/state.
    wa, ga, _, _, _, _ = _assault_ready_world_game()
    wb, gb, _, _, _, _ = _assault_ready_world_game()
    a = GameApp(wa, ga, Calendar(year=2, month=3), Rng(11), player_duchy_id="north")
    b = GameApp(wb, gb, Calendar(year=2, month=3), Rng(11), player_duchy_id="north")
    seq = (
        ("GET", "/"),
        ("POST", "/order/assault"),
        ("GET", "/"),
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
    assert a.world == b.world
    assert a.game.duchies == b.game.duchies


def test_game_app_get_hides_turn_and_orders_when_is_over():
    """When game.is_over, GET / omits turn and order forms/sections (K32.2a).

    Contract (task-164 / K32.2a):
    - finished game (``game.is_over``): GET / body has no form ``action="/turn"``
    - no form whose ``action`` starts with ``/order/`` (recruit/muster/develop/
      march/assault/engage, with or without query)
    - no elements with ``data-order-section`` (section headers)
    """
    fin_world, fin_game = _finished_world_game()
    assert fin_game.is_over
    app = GameApp(
        fin_world,
        fin_game,
        Calendar(year=1, month=1),
        Rng(17),
        player_duchy_id="north",
    )

    code, body = app.handle("GET", "/")
    assert code == 200
    assert isinstance(body, str)
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"

    assert not _has_post_turn_form(body)
    assert not _has_post_form(body, "/turn")

    order_forms = []
    for el in root.iter():
        if _local(el.tag) != "form":
            continue
        method = (el.get("method") or "").lower()
        action = el.get("action") or ""
        if method == "post" and action.startswith("/order/"):
            order_forms.append(action)
    assert order_forms == [], f"unexpected order forms when is_over: {order_forms}"

    # Also cover bare action helpers used elsewhere for the six order routes.
    assert not _has_post_recruit_form(body)
    assert not _has_post_muster_form(body)
    assert not _has_post_develop_form(body)
    assert not _has_post_march_form(body)
    assert not _has_post_assault_form(body)
    assert not _has_post_engage_form(body)

    section_headers = [el for el in root.iter() if el.get("data-order-section") is not None]
    assert section_headers == [], (
        "data-order-section must be absent when is_over; "
        f"found {[el.get('data-order-section') for el in section_headers]}"
    )
    assert 'data-order-section="' not in body


def test_game_app_get_keeps_new_player_and_notice_when_is_over():
    """When game.is_over, GET / still has /new, data-player and data-notice (K32.2a).

    Contract (task-164 / K32.2a):
    - finished game (``game.is_over``): GET / body has exactly one form
      ``method=post action="/new"`` with submit button ``Nowa gra``
    - body still has a ``data-player`` marker equal to ``player_duchy_id``
    - body still has exactly one ``<p data-notice>`` (attribute matches
      ``self.last_notice``, including the empty default)
    """
    fin_world, fin_game = _finished_world_game()
    assert fin_game.is_over
    app = GameApp(
        fin_world,
        fin_game,
        Calendar(year=1, month=1),
        Rng(17),
        player_duchy_id="north",
    )
    assert app.last_notice == ""

    code, body = app.handle("GET", "/")
    assert code == 200
    assert isinstance(body, str)
    root = ET.fromstring(body)
    assert _local(root.tag) == "html"

    new_forms = [
        el
        for el in root.iter()
        if _local(el.tag) == "form"
        and (el.get("method") or "").lower() == "post"
        and (el.get("action") or "") == "/new"
    ]
    assert len(new_forms) == 1
    assert _has_post_form(body, "/new")
    assert _form_submit_button_text(body, "/new") == "Nowa gra"

    players = _find_by_attr(root, "data-player")
    assert len(players) == 1
    assert players[0].get("data-player") == "north"

    notices = _find_by_attr(root, "data-notice")
    assert len(notices) == 1
    assert _local(notices[0].tag) == "p"
    assert notices[0].get("data-notice") == app.last_notice == ""


def test_game_app_post_turn_sets_previous_game_and_embeds_turn_summary():
    """POST /turn (not is_over) stores pre-turn GameState as previous_game (K38.2a).

    Contract (task-186 / K38.2a):
    - ``GameApp.previous_game`` is initialized to ``None``
    - GET / while ``previous_game is None`` → page has no ``data-turn-summary``
    - POST /turn when game is not ``is_over`` → ``self.previous_game`` is the
      ``GameState`` object from before the turn
    - ``_render`` passes it into ``render_game_page``, so the returned page
      embeds exactly ``render_turn_summary(previous_game, app.game)``
    """
    world, game = _ongoing_world_game()
    calendar = Calendar(year=4, month=9)
    app = GameApp(world, game, calendar, Rng(17))
    assert app.previous_game is None

    code_get, body_get = app.handle("GET", "/")
    assert code_get == 200
    assert _find_by_attr(ET.fromstring(body_get), "data-turn-summary") == []
    assert "data-turn-summary" not in body_get

    game_before = app.game
    code, body = app.handle("POST", "/turn")
    assert code == 200
    assert isinstance(body, str)
    assert _calendar_stamp(body) == (4, 10)

    assert app.previous_game is game_before
    assert app.previous_game is not app.game
    expected_summary = render_turn_summary(app.previous_game, app.game)
    assert expected_summary in body
    assert body.count(expected_summary) == 1
    root = ET.fromstring(body)
    assert len(_find_by_attr(root, "data-turn-summary")) == 1


def test_game_app_post_new_orders_and_is_over_turn_clear_previous_game():
    """POST /new, /order/*, is_over /turn set previous_game=None (K38.2a).

    Contract (task-186 / K38.2a): after a successful POST /turn has set
    ``previous_game`` (and embedded the turn summary), every other mutating
    path clears it so the journal does not linger — same pattern as
    ``last_battle``:

    - POST /order/recruit|muster|develop|march|assault|engage → previous_game None
    - POST /new → previous_game None
    - POST /turn when game is already is_over (no-op) → previous_game None
    - returned page has no ``data-turn-summary`` once cleared
    """
    order_routes = (
        "/order/recruit",
        "/order/muster",
        "/order/develop",
        "/order/march",
        "/order/assault",
        "/order/engage",
    )

    def _app_after_turn(*, seed: int | None = None) -> GameApp:
        world, game = _ongoing_world_game()
        app = GameApp(
            world,
            game,
            Calendar(year=4, month=9),
            Rng(17),
            player_duchy_id="north",
            seed=seed,
        )
        code, body = app.handle("POST", "/turn")
        assert code == 200
        assert app.previous_game is not None
        assert len(_find_by_attr(ET.fromstring(body), "data-turn-summary")) == 1
        return app

    for route in order_routes:
        app = _app_after_turn()
        code, body = app.handle("POST", route)
        assert code == 200, route
        assert app.previous_game is None, route
        assert _find_by_attr(ET.fromstring(body), "data-turn-summary") == [], route
        assert "data-turn-summary" not in body, route

    # POST /new clears previous_game (with and without seed; both paths set None).
    for seed in (None, 73):
        app = _app_after_turn(seed=seed)
        code, body = app.handle("POST", "/new")
        assert code == 200
        assert app.previous_game is None
        assert _find_by_attr(ET.fromstring(body), "data-turn-summary") == []
        assert "data-turn-summary" not in body

    # No-op POST /turn when game is already is_over clears a lingering previous_game.
    fin_world, fin_game = _finished_world_game()
    lingering = _app_after_turn().previous_game
    assert lingering is not None
    finished = GameApp(
        fin_world, fin_game, Calendar(year=3, month=7), Rng(5)
    )
    finished.previous_game = lingering
    code_fin, body_fin = finished.handle("POST", "/turn")
    assert code_fin == 200
    assert finished.previous_game is None
    assert _find_by_attr(ET.fromstring(body_fin), "data-turn-summary") == []
    assert "data-turn-summary" not in body_fin


def test_recommended_order_path_assault_and_engage():
    """``recommended_order_path`` maps assault/engage to existing POST routes (K42.1b).

    Contract (task-204): pure ``tbbui.serve.recommended_order_path(action) -> str``
    reuses player order routes — ``"assault"`` → ``"/order/assault"``,
    ``"engage"`` → ``"/order/engage"``. Deterministic, no IO.
    """
    assert recommended_order_path("assault") == "/order/assault"
    assert recommended_order_path("engage") == "/order/engage"

