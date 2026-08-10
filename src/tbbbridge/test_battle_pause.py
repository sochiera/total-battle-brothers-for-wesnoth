"""Testy pauzy bitwy gracza na żywym moście (G119.1b, task-672).

Bramka kryje kryteria akceptacji 1 (assault/engage pauzuje bitwę i odpowiada
``battle_pending`` z planszą rozstawienia), 2 (``battle_advance`` rozgrywa
dokładnie jedną rundę i bitwa nadal trwa — także gdy kolejna runda domyka
bitwę i wynik zostaje zastosowany do świata jak na dzisiejszej ścieżce
``_recorded``), 3 (``battle_auto`` rozstrzyga resztę bitwy i stosuje wynik do
świata identycznie jak dzisiejszy auto-rozstrzygany rozkaz na tym samym
ziarnie; bez bitwy w toku obie komendy bitewne odpowiadają ``changed:false``
z niepustym powodem) oraz 4 (bitwa w toku blokuje inne rozkazy i ``next_turn``
przez ``changed:false`` z niepustym powodem, bez zmian w świecie, kalendarzu
i RNG). Ścieżkę AI (kryterium 5) strzegą istniejące bramki nietkniętego
``take_duchy_turn``; kryterium 6 (regresje seed=73) pokrywają legacy-piny w
``test_protocol.py``/``test_session.py`` zaktualizowane do przepływu pauza +
``battle_auto`` (rush wygrywa w R1M4, bierny gracz przegrywa, K112/K117
stoją). Negatywna połowa kryterium 1 (rozkaz, który nie zaczyna
bitwy, nigdy nie odpowiada ``battle_pending``) zostaje przy istniejącej bramce
``test_military_order_result_carries_core_refusal_reason_as_success``.

Realistyczny defekt, którego dzisiejsze bramki nie wykrywają: most może dalej
rozstrzygać bitwę gracza od razu (stare ``kind: "battle"``), ``battle_advance``
może rozegrać całą bitwę zamiast jednej rundy albo ciągnąć RNG z innego
momentu, ``battle_auto`` może podnosić błąd protokołu zamiast rozstrzygać
resztę bitwy (albo rozstrzygać ją od rozstawienia zamiast od bieżącej rundy),
a blokada innych rozkazów może konsumować RNG/akcję miesiąca, zwracać błąd
protokołu albo powód właściwy samemu rozkazowi zamiast powodu bitwy w toku.
"""

import json

import pytest

import tbb.ai as ai
from tbb.battle import BattleSide, HexBattle
from tbb.battlefield import Battlefield
from tbb.duchy import Duchy
from tbb.driver import resolve_hero_survival
from tbb.game import GameState
from tbb.hex import Hex
from tbb.party import Party
from tbb.rng import Rng
from tbb.settlement import Settlement
from tbb.turn import Calendar
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbbridge.protocol import handle_command_line
from tbbbridge.session import PendingBattle, Session, new_session
from tbbbridge.snapshot import battle_state, game_state


_SETUP_COMMANDS = (
    '{"type":"order","order":"recruit"}',
    '{"type":"order","order":"recruit"}',
    '{"type":"order","order":"muster"}',
    '{"type":"order","order":"march"}',
    '{"type":"next_turn"}',
)
_ENGAGE_BORDER = '{"type":"order","order":"engage","target":"border"}'


def _setup_session():
    """Zmierzona ścieżka seed=73 do momentu, w którym engage zaczyna bitwę."""
    session = new_session(seed=73, player_duchy_id="player")
    for line in _SETUP_COMMANDS:
        session, response = handle_command_line(session, line)
        assert response["ok"] is True
    return session


def _player_position(world):
    return next(
        region
        for region in world.regions
        if (party := world.party_at(region)) is not None
        and party.owner_id == "player"
    )


def _region_by_name(world, name):
    return next(region for region in world.regions if region.name == name)


def _morale_of(session, owner_id):
    return next(
        duchy.morale for duchy in session.game.duchies if duchy.duchy_id == owner_id
    )


def _pause_on_border_engage():
    session = _setup_session()
    paused, response = handle_command_line(session, _ENGAGE_BORDER)
    assert response["ok"] is True
    assert response["result"]["kind"] == "battle_pending"
    return session, paused


def _pause_on_keep_assault():
    keep = Region("Keep")
    attacker = Party(Unit(equipment=1), owner_id="player")
    settlement = Settlement(
        "Keep",
        population=1,
        garrison=(Unit(equipment=1),),
        owner_id="ai",
    )
    world = WorldMap(
        (keep,),
        settlements={keep: settlement},
        parties={keep: attacker},
    )
    session = Session(
        world=world,
        game=GameState(
            (
                Duchy("player", attacker.hero, parties=(attacker,)),
                Duchy("ai", Unit(), settlements=(settlement,)),
            )
        ),
        calendar=Calendar(),
        rng=Rng(73),
        player_duchy_id="player",
        seed=73,
    )
    paused, response = handle_command_line(
        session, '{"type":"order","order":"assault"}'
    )
    assert response["ok"] is True
    assert response["result"]["kind"] == "battle_pending"
    return session, paused


def _battle_target_command(attacker: tuple[int, int], target: tuple[int, int]) -> str:
    return json.dumps(
        {
            "type": "battle_target",
            "attacker": {"q": attacker[0], "r": attacker[1]},
            "target": {"q": target[0], "r": target[1]},
        }
    )


def _two_target_battle_session() -> Session:
    """Public bridge fixture with one attacker and two active enemy hexes."""
    start, border = Region("Start"), Region("Border")
    attacker = Party(Unit(equipment=1), owner_id="player")
    defender = Party(
        Unit(equipment=1),
        units=(Unit(equipment=1),),
        owner_id="ai",
    )
    world = WorldMap(
        (start, border),
        ((start, border),),
        parties={start: attacker, border: defender},
    )
    game = GameState(
        (
            Duchy("player", attacker.hero, parties=(attacker,)),
            Duchy("ai", defender.hero, parties=(defender,)),
        )
    )
    return Session(
        world=world,
        game=game,
        calendar=Calendar(),
        rng=Rng(73),
        player_duchy_id="player",
        seed=73,
    )


def _pause_two_target_battle():
    session = _two_target_battle_session()
    paused, response = handle_command_line(
        session, '{"type":"order","order":"engage"}'
    )
    assert response["ok"] is True
    assert response["result"]["kind"] == "battle_pending"
    return paused


def _pause_battle_with_two_attacking_units() -> Session:
    """Build a pending bridge session whose two attackers have distinct routes."""
    session = _two_target_battle_session()
    start, border = session.world.regions
    battle = (
        HexBattle(Battlefield())
        .deploy(Unit(equipment=1), Hex(0, 0), BattleSide.ATTACKER)
        .deploy(Unit(equipment=1), Hex(1, 0), BattleSide.DEFENDER)
        .deploy(Unit(equipment=1), Hex(0, 3), BattleSide.ATTACKER)
        .deploy(Unit(equipment=1), Hex(1, 3), BattleSide.DEFENDER)
    )
    return Session(
        world=session.world,
        game=session.game,
        calendar=session.calendar,
        rng=session.rng,
        player_duchy_id=session.player_duchy_id,
        seed=session.seed,
        pending_battle=PendingBattle(
            battle=battle,
            source=start,
            target=border,
            kind="party",
            attacker_owner_id="player",
            defender_owner_id="ai",
        ),
    )


def _pause_zero_damage_battle() -> Session:
    """Build a pending battle that remains unresolved through auto_resolve."""
    session = _two_target_battle_session()
    start, border = session.world.regions
    battle = (
        HexBattle(Battlefield())
        .deploy(Unit(equipment=0), Hex(0, 0), BattleSide.ATTACKER)
        .deploy(Unit(equipment=0), Hex(1, 0), BattleSide.DEFENDER)
    )
    return Session(
        world=session.world,
        game=session.game,
        calendar=session.calendar,
        rng=session.rng,
        player_duchy_id=session.player_duchy_id,
        seed=session.seed,
        pending_battle=PendingBattle(
            battle=battle,
            source=start,
            target=border,
            kind="party",
            attacker_owner_id="player",
            defender_owner_id="ai",
        ),
    )


def _attacker_positions(snapshot: dict) -> list[tuple[int, int]]:
    return [
        (hex_state["q"], hex_state["r"])
        for hex_state in snapshot["battle"]["hexes"]
        if hex_state["side"] == "attacker"
    ]


@pytest.mark.parametrize(
    ("pause_factory", "attacker", "target"),
    (
        pytest.param(_pause_on_border_engage, (0, 0), (2, 1), id="engage"),
        pytest.param(_pause_on_keep_assault, (0, 0), (2, 0), id="assault"),
    ),
)
def test_battle_target_records_intent_without_resolving_pending_battle(
    pause_factory, attacker, target
):
    """G120.1b AC1: a valid target keeps an assault or engage battle paused."""
    _, paused = pause_factory()
    before_snapshot = paused.snapshot()
    before_rng = paused.rng.state()
    before_calendar = paused.calendar

    returned, response = handle_command_line(
        paused, _battle_target_command(attacker, target)
    )

    assert response["ok"] is True, response
    assert response["result"]["kind"] == "battle_target", response
    assert response["result"]["changed"] is True, response
    assert returned.pending_battle is not None
    assert returned.last_battle is None
    assert response["snapshot"]["battle"]["result"] is None
    public_battle = response["snapshot"]["battle"]
    assert "attack_targets" in public_battle, (
        "kryterium 1: battle_pending musi eksponować ustawione cele ataku"
    )
    assert public_battle["attack_targets"] == [{
        "attacker": {"q": attacker[0], "r": attacker[1]},
        "target": {"q": target[0], "r": target[1]},
    }]
    assert returned.world is paused.world
    assert returned.calendar == before_calendar
    assert returned.rng.state() == before_rng
    returned_snapshot = returned.snapshot()
    assert returned_snapshot["calendar"] == before_snapshot["calendar"]
    assert returned_snapshot["player_duchy"] == before_snapshot["player_duchy"]
    assert returned_snapshot["duchies"] == before_snapshot["duchies"]
    assert returned_snapshot["map"] == before_snapshot["map"]
    assert returned_snapshot["result"] == before_snapshot["result"]
    assert returned_snapshot["battle"]["hexes"] == before_snapshot["battle"]["hexes"]
    assert returned_snapshot["battle"]["result"] == before_snapshot["battle"]["result"]

    advanced, advance_response = handle_command_line(
        returned, '{"type":"battle_advance"}'
    )
    assert advance_response["ok"] is True
    assert advanced.snapshot()["battle"].get("attack_targets", []) == [], (
        "kryterium 2: zużyty cel nie może sterować kolejną rundą"
    )


def test_battle_target_changes_the_next_round_toward_the_indicated_enemy():
    """G120.1b AC2: an indicated non-nearest enemy changes the next round."""
    baseline = _pause_two_target_battle()
    baseline_after, baseline_response = handle_command_line(
        baseline, '{"type":"battle_advance"}'
    )
    assert baseline_response["ok"] is True
    assert baseline_response["result"]["kind"] == "battle_pending"

    targeted = _pause_two_target_battle()
    targeted, target_response = handle_command_line(
        targeted, _battle_target_command((0, 0), (2, 1))
    )
    assert target_response["ok"] is True
    assert target_response["result"]["changed"] is True
    targeted_after, advance_response = handle_command_line(
        targeted, '{"type":"battle_advance"}'
    )

    assert advance_response["ok"] is True
    assert advance_response["result"]["kind"] == "battle_pending"
    assert targeted_after.pending_battle is not None
    assert targeted_after.snapshot()["battle"]["result"] is None
    assert _attacker_positions(baseline_after.snapshot()) == [(1, 0)]
    assert _attacker_positions(targeted_after.snapshot()) == [(0, 1)]
    assert _attacker_positions(targeted_after.snapshot()) != _attacker_positions(
        baseline_after.snapshot()
    )


def test_battle_target_merges_multiple_attacker_intents_for_one_advance():
    """G120.1b AC1-2: two targets survive and affect one public round."""
    paused = _pause_battle_with_two_attacking_units()

    paused, first_response = handle_command_line(
        paused, _battle_target_command((0, 0), (1, 3))
    )
    assert first_response["ok"] is True
    assert first_response["result"]["changed"] is True

    paused, second_response = handle_command_line(
        paused, _battle_target_command((0, 3), (1, 0))
    )
    assert second_response["ok"] is True
    assert second_response["result"]["changed"] is True

    advanced, advance_response = handle_command_line(
        paused, '{"type":"battle_advance"}'
    )

    assert advance_response["ok"] is True
    assert advance_response["result"]["kind"] == "battle_pending"
    assert _attacker_positions(advanced.snapshot()) == [(0, 1), (0, 2)]


def test_battle_target_is_used_by_battle_auto_and_is_deterministic():
    """G120.1b AC4-5: auto honours a target and repeats the public sequence."""

    def run_targeted_auto():
        session = _pause_two_target_battle()
        session, target_response = handle_command_line(
            session, _battle_target_command((0, 0), (2, 1))
        )
        assert target_response["ok"] is True
        assert target_response["result"]["changed"] is True

        session, auto_response = handle_command_line(
            session, '{"type":"battle_auto"}'
        )
        assert auto_response["ok"] is True
        assert auto_response["result"]["kind"] == "battle"
        return auto_response, session.snapshot(), session.rng.state()

    first = run_targeted_auto()
    second = run_targeted_auto()

    assert first == second
    assert _attacker_positions(first[1]) == [(0, 1)]


def test_battle_auto_consumes_targets_when_battle_remains_pending():
    """A non-resolving auto step must not retain its one-shot target map."""
    paused = _pause_zero_damage_battle()
    paused, target_response = handle_command_line(
        paused, _battle_target_command((0, 0), (1, 0))
    )
    assert target_response["ok"] is True
    assert target_response["result"]["changed"] is True

    advanced, auto_response = handle_command_line(
        paused, '{"type":"battle_auto"}'
    )

    assert auto_response["ok"] is True
    assert auto_response["result"]["kind"] == "battle_pending"
    assert advanced.pending_battle is not None
    assert advanced.pending_battle.attack_targets == {}


@pytest.mark.parametrize(
    ("label", "attacker", "target"),
    (
        ("empty attacker", (1, 0), (2, 1)),
        ("defender as attacker", (2, 0), (2, 1)),
        ("empty target", (0, 0), (1, 0)),
        ("ally target", (0, 0), (0, 1)),
        ("same hex", (0, 0), (0, 0)),
    ),
)
def test_battle_target_refuses_invalid_hex_pairs_with_reason(label, attacker, target):
    """G120.1b AC3: invalid pairs are successful protocol refusals without mutation."""
    _, paused = _pause_on_border_engage()
    before_snapshot = paused.snapshot()
    before_rng = paused.rng.state()

    returned, response = handle_command_line(
        paused, _battle_target_command(attacker, target)
    )

    assert response["ok"] is True, (label, response)
    result = response["result"]
    assert result["kind"] == "battle_target", (label, result)
    assert result["changed"] is False, (label, result)
    assert isinstance(result.get("reason"), str) and result["reason"].strip(), (
        label,
        result,
    )
    assert returned.world is paused.world
    assert returned.snapshot() == before_snapshot
    assert returned.rng.state() == before_rng


def test_battle_target_without_pending_battle_is_successful_refusal_with_reason():
    """G120.1b AC3: the command is refused cleanly when no battle is pending."""
    session = new_session(seed=73, player_duchy_id="player")
    before_snapshot = session.snapshot()
    before_rng = session.rng.state()

    returned, response = handle_command_line(
        session, _battle_target_command((0, 0), (2, 1))
    )

    assert response["ok"] is True, response
    result = response["result"]
    assert result["kind"] == "battle_target"
    assert result["changed"] is False
    assert isinstance(result.get("reason"), str) and result["reason"].strip()
    assert returned.world is session.world
    assert returned.snapshot() == before_snapshot
    assert returned.rng.state() == before_rng


def test_engage_that_starts_battle_pauses_with_battle_pending_deployment_board():
    """G119.1b kryt-1: engage zaczynające bitwę pauzuje ją przed pierwszą rundą.

    Odpowiedź mostu to ``{"kind": "battle_pending", "battle": …}`` z planszą
    rozstawienia obu stron (wynik ``null``), a nie dzisiejsze
    ``{"kind": "battle", …}`` z rozstrzygnięciem. Pauza nie zmienia świata,
    kalendarza ani RNG — bitwa jeszcze się nie rozegrała.
    """
    session = _setup_session()
    position = _player_position(session.world)
    border = _region_by_name(session.world, "border")
    deployment = battle_state(session.world.start_battle(position, border))
    assert deployment["result"] is None
    rng_before = session.rng.state()

    returned, response = handle_command_line(session, _ENGAGE_BORDER)

    assert response["ok"] is True
    assert "error" not in response
    result = response["result"]
    assert result["kind"] == "battle_pending"
    assert result["battle"] == deployment
    assert result["battle"]["result"] is None
    assert "outcome" not in result
    json.dumps(response)
    assert returned.world is session.world
    assert returned.rng.state() == rng_before
    assert returned.snapshot()["calendar"] == {"year": 1, "month": 2}


def test_battle_advance_plays_exactly_one_round_and_keeps_battle_in_progress():
    """G119.1b kryt-2: battle_advance rozgrywa jedną rundę, bitwa trwa dalej.

    Oracle: bliźniacza sesja przechodzi tę samą ścieżkę, a jej rozstawienie
    (``start_battle``) plus dokładnie jeden ``resolve_round`` na wspólnym RNG
    (punkty ruchu 1, morale księstw ze stanu gry) daje oczekiwaną planszę.
    Odpowiedź nadal mówi, że bitwa jest w toku; świat i RNG po stronie mostu
    są zgodne z pojedynczą rundą.
    """
    _, paused = _pause_on_border_engage()

    twin = _setup_session()
    position = _player_position(twin.world)
    border = _region_by_name(twin.world, "border")
    deployment = twin.world.start_battle(position, border)
    defender_owner = twin.world.party_at(border).owner_id
    expected = deployment.resolve_round(
        1,
        twin.rng,
        attacker_morale=_morale_of(twin, "player"),
        defender_morale=_morale_of(twin, defender_owner),
    )
    assert expected.result() is None

    returned, response = handle_command_line(paused, '{"type":"battle_advance"}')

    assert response["ok"] is True
    assert "error" not in response
    result = response["result"]
    assert result["kind"] == "battle_pending"
    assert result["battle"] == battle_state(expected)
    assert result["battle"]["result"] is None
    assert returned.rng.state() == twin.rng.state()
    assert returned.world is paused.world
    json.dumps(response)


@pytest.mark.parametrize(
    ("order", "target"),
    (
        ("develop", None),
        ("recruit", None),
        ("muster", None),
        ("reinforce", None),
        ("move", "border"),
        ("march", None),
        ("assault", None),
        ("engage", None),
    ),
)
def test_unresolved_player_battle_blocks_other_orders_with_reason(order, target):
    """G119.1b kryt-4: każdy inny rozkaz podczas bitwy w toku jest blokadą.

    Wzorzec K111/K114/K118: ``ok:true``, ``changed:false`` i niepusty powód;
    świat, kalendarz i RNG zostają bez zmian, a snapshot (wraz ze stanem bitwy
    w toku) jest identyczny jak przed zablokowanym rozkazem.
    """
    _, paused = _pause_on_border_engage()
    command = {"type": "order", "order": order}
    if target is not None:
        command["target"] = target
    snapshot_before = paused.snapshot()
    rng_before = paused.rng.state()

    returned, response = handle_command_line(paused, json.dumps(command))

    assert response["ok"] is True
    assert "error" not in response
    result = response["result"]
    assert result["kind"] == "order"
    assert result["order"] == order
    assert result["changed"] is False
    assert isinstance(result.get("reason"), str)
    assert result["reason"].strip()
    assert returned.world is paused.world
    assert returned.rng.state() == rng_before
    assert returned.snapshot() == snapshot_before
    json.dumps(response)


def test_unresolved_player_battle_blocks_next_turn_with_the_same_reason():
    """G119.1b kryt-4: next_turn podczas bitwy w toku też niesie powód blokady.

    ``next_turn`` nie może posunąć tury AI, dopóki bitwa gracza jest
    nierozstrzygnięta; odpowiedź jest sukcesem z ``changed:false`` i tym samym
    niepustym powodem blokady, który dostają zablokowane rozkazy.
    """
    _, paused = _pause_on_border_engage()
    snapshot_before = paused.snapshot()
    rng_before = paused.rng.state()

    _, order_response = handle_command_line(
        paused, '{"type":"order","order":"develop"}'
    )
    assert order_response["ok"] is True
    order_reason = order_response["result"]["reason"]
    assert isinstance(order_reason, str) and order_reason.strip()

    returned, response = handle_command_line(paused, '{"type":"next_turn"}')

    assert response["ok"] is True
    assert "error" not in response
    result = response["result"]
    assert result["changed"] is False
    assert result.get("reason") == order_reason
    assert returned.world is paused.world
    assert returned.rng.state() == rng_before
    assert returned.snapshot() == snapshot_before
    json.dumps(response)


def _engagement_facts():
    """Oracle równoważności dla engage/border na seed=73.

    Zwraca ``(rounds, resolved, expected_snapshot, expected_rng_state)``:
    liczbę rund ``resolve_round`` do rozstrzygnięcia (bliźniak liczący, RNG
    od rozstawienia), rozstrzygniętą bitwę ze starej ścieżki
    ``ai.engage_duchy_party_to_recorded`` oraz snapshot i stan RNG sesji, w
    której ta ścieżka przeszła wraz z ``resolve_hero_survival`` (bez RNG) i
    synchronizacją gry — czyli stan identyczny z dzisiejszym auto-rozstrzyganym
    rozkazem na tym samym ziarnie (kryteria 2 i 3).
    """
    counter = _setup_session()
    position = _player_position(counter.world)
    border = _region_by_name(counter.world, "border")
    defender_owner = counter.world.party_at(border).owner_id
    battle = counter.world.start_battle(position, border)
    rounds = 0
    while battle.result() is None:
        battle = battle.resolve_round(
            1,
            counter.rng,
            attacker_morale=_morale_of(counter, "player"),
            defender_morale=_morale_of(counter, defender_owner),
        )
        rounds += 1

    twin = _setup_session()
    twin_position = _player_position(twin.world)
    twin_border = _region_by_name(twin.world, "border")
    duchy = next(d for d in twin.game.duchies if d.duchy_id == "player")
    morale = {d.duchy_id: d.morale for d in twin.game.duchies}
    new_world, resolved = ai.engage_duchy_party_to_recorded(
        twin.world, duchy, twin_border, twin.rng, morale_by_owner=morale
    )
    assert resolved is not None and resolved.result() is not None
    resolved_duchy = resolve_hero_survival(duchy, twin.world, new_world)
    new_game = GameState(
        resolved_duchy if d.duchy_id == duchy.duchy_id else d
        for d in twin.game.duchies
    ).sync_from_world(new_world)
    expected_snapshot = game_state(
        new_world, new_game, twin.calendar, "player", battle=resolved
    )
    return rounds, resolved, expected_snapshot, twin.rng.state()


def test_battle_advance_without_pending_battle_is_success_refusal_with_reason():
    """G119.1b kryt-2 negatyw: battle_advance bez bitwy w toku nie zmienia sesji.

    Wzorzec K111/K114/K118: ``ok:true``, ``changed:false`` i niepusty powód;
    świat i RNG zostają bez zmian, snapshot jest identyczny jak przed komendą.
    """
    session = _setup_session()
    snapshot_before = session.snapshot()
    rng_before = session.rng.state()

    returned, response = handle_command_line(session, '{"type":"battle_advance"}')

    assert response["ok"] is True
    assert "error" not in response
    result = response["result"]
    assert result["changed"] is False
    assert isinstance(result.get("reason"), str)
    assert result["reason"].strip()
    assert returned.world is session.world
    assert returned.rng.state() == rng_before
    assert returned.snapshot() == snapshot_before
    json.dumps(response)


def test_battle_advance_rounds_until_resolution_match_recorded_path_exactly():
    """G119.1b kryt-2: advance domykający bitwę stosuje wynik jak stara ścieżka.

    Każde ``battle_advance`` to dokładnie jedna runda: liczba advance'ów do
    rozstrzygnięcia równa się liczbie rund ``resolve_round`` na bliźniaku, a
    domykający advance odpowiada ``{"kind": "battle", …}`` z outcome i
    stratami (bez nazwy rozkazu). Świat, gra, kalendarz i RNG są bajtowo
    identyczne z bliźniaczą sesją, która rozegrała ten sam rozkaz starą
    ścieżką ``engage_duchy_party_to_recorded`` (wraz z losem bohatera i
    synchronizacją gry), a po rozstrzygnięciu bitwa przestaje blokować:
    powtórzony rozkaz w tym samym miesiącu jest zwykłą odmową K118
    (akcja miesiąca zużyta przez rozstrzygnięcie), nigdy ``battle_pending``.
    """
    _, paused = _pause_on_border_engage()
    rounds, resolved, expected_snapshot, expected_rng = _engagement_facts()

    current = paused
    advance_count = 0
    response = None
    while True:
        assert advance_count < rounds
        current, response = handle_command_line(current, '{"type":"battle_advance"}')
        advance_count += 1
        assert response["ok"] is True
        assert "error" not in response
        result = response["result"]
        if result["kind"] == "battle":
            break
        assert result["kind"] == "battle_pending"
        assert result["battle"]["result"] is None
    assert advance_count == rounds

    result = response["result"]
    assert "order" not in result
    assert result["outcome"] == "zwycięstwo"
    assert result["attacker_losses"] == len(resolved.side_fallen(BattleSide.ATTACKER))
    assert result["defender_losses"] == len(resolved.side_fallen(BattleSide.DEFENDER))
    assert current.pending_battle is None
    assert current.snapshot() == expected_snapshot
    assert current.rng.state() == expected_rng
    json.dumps(response)

    returned, second_response = handle_command_line(
        current, '{"type":"order","order":"engage"}'
    )
    assert second_response["ok"] is True
    assert "error" not in second_response
    second = second_response["result"]
    assert second["kind"] == "order"
    assert second["changed"] is False
    assert isinstance(second.get("reason"), str)
    assert second["reason"].strip()
    assert returned.world is current.world
    assert returned.rng.state() == expected_rng
    json.dumps(second_response)


def test_battle_auto_resolves_rest_of_paused_battle_and_applies_result_like_recorded_path():
    """G119.1b kryt-3: battle_auto rozstrzyga resztę bitwy i stosuje wynik.

    Po pauzie i jednym ``battle_advance`` (bitwa nadal trwa) ``battle_auto``
    rozstrzyga pozostałe rundy od bieżącej planszy i stosuje wynik do świata
    istniejącą regułą — odpowiedź to ``{"kind": "battle", …}`` z outcome i
    stratami (bez nazwy rozkazu), a świat, gra, kalendarz i RNG są bajtowo
    identyczne z bliźniaczą sesją, która rozegrała ten sam rozkaz starą
    ścieżką ``engage_duchy_party_to_recorded`` (razem z losem bohatera i
    synchronizacją gry). Po rozstrzygnięciu pauza znika i ``next_turn`` znów
    działa — tura AI rusza bez bitwy gracza w toku (kryterium 5).
    """
    _, paused = _pause_on_border_engage()
    rounds, resolved, expected_snapshot, expected_rng = _engagement_facts()
    assert rounds > 1

    current, response = handle_command_line(paused, '{"type":"battle_advance"}')
    assert response["ok"] is True
    assert response["result"]["kind"] == "battle_pending"

    current, response = handle_command_line(current, '{"type":"battle_auto"}')

    assert response["ok"] is True
    assert "error" not in response
    result = response["result"]
    assert result["kind"] == "battle"
    assert "order" not in result
    assert result["outcome"] == "zwycięstwo"
    assert result["attacker_losses"] == len(resolved.side_fallen(BattleSide.ATTACKER))
    assert result["defender_losses"] == len(resolved.side_fallen(BattleSide.DEFENDER))
    assert current.pending_battle is None
    assert current.snapshot() == expected_snapshot
    assert current.rng.state() == expected_rng
    json.dumps(response)

    _, turn_response = handle_command_line(current, '{"type":"next_turn"}')
    assert turn_response["ok"] is True
    assert "error" not in turn_response
    turn_result = turn_response["result"]
    assert turn_result["kind"] == "turn"
    assert turn_result["date"] == {"year": 1, "month": 3}
    assert "reason" not in turn_result
    json.dumps(turn_response)


def test_battle_auto_without_pending_battle_is_success_refusal_with_reason():
    """G119.1b kryt-3 negatyw: battle_auto bez bitwy w toku nie zmienia sesji.

    Wzorzec K111/K114/K118: ``ok:true``, ``changed:false`` i niepusty powód —
    ten sam, który dostaje ``battle_advance`` bez bitwy; świat i RNG bez zmian.
    """
    session = _setup_session()
    rng_before = session.rng.state()

    _, advance_response = handle_command_line(session, '{"type":"battle_advance"}')
    assert advance_response["ok"] is True
    advance_result = advance_response["result"]
    assert advance_result["changed"] is False
    advance_reason = advance_result.get("reason")
    assert isinstance(advance_reason, str) and advance_reason.strip()

    returned, response = handle_command_line(session, '{"type":"battle_auto"}')

    assert response["ok"] is True
    assert "error" not in response
    result = response["result"]
    assert result["changed"] is False
    assert result.get("reason") == advance_reason
    assert returned.world is session.world
    assert returned.rng.state() == rng_before
    json.dumps(response)
