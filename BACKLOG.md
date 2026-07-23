# BACKLOG — Total Battle Brothers

> **Kolejka zadań.** Każde zadanie = jeden mały, testowalny przyrost (TDD).
> Statusy: `[ ]` do zrobienia, `[~]` w toku, `[x]` zrobione.
> Bierz zadania z góry. Nie łącz wielu przyrostów w jeden. Aktualizuj status i
> dopisuj nowe zadania, gdy wizja się doprecyzowuje. Detale mechaniki → `docs/DESIGN.md`.
> Ukończone milestony (kamienie 0–53 oraz A7.1*/A7.2*) przeniesione do
> `BACKLOG-ARCHIVE.md` — tu zostaje wyłącznie żywy tail w stronę grywalnego MVP.

## Legenda
Każde zadanie ma **kryteria akceptacji** (co musi przejść jako test). Rdzeń przed
prezentacją. Determinizm (seedowalny RNG) jest wymogiem przekrojowym.

---

> **Kamienie 0–53 — UKOŃCZONE.** Pełne streszczenia w `BACKLOG-ARCHIVE.md`
> (headless pętla MVP, ekonomia/kalendarz, rozwój jednostek, straty/koszty,
> regeneracja/sukcesja, morale, warstwa wizualna `tbbui` i cała seria rady
> w jeden klik K41–K52, trening party K53). Żywy tail zaczyna się od K54.

> **Kamienie 54–55 — UKOŃCZONE.** Bramkowanie treningu garnizonu Koszarami
> (katalog `BARRACKS`, AI otwierające je przed Market, no-op `tick_training`
> bez Koszar) oraz czytelna gotowość treningu w panelu osad (flaga
> `data-training-ready` + sufiks ` · trening: …`). Szczegóły w
> `BACKLOG-ARCHIVE.md`.

> **Kamień 56 — UKOŃCZONE.** Czytelna gotowość uzbrojenia garnizonu (Kuźnia) w
> panelu osady (flaga `data-equip-ready` + sufiks ` · uzbrojenie: …`) oraz
> refaktor R56.1 (wspólny helper gotowości bramkowanej budynkiem). Szczegóły w
> `BACKLOG-ARCHIVE.md`.

> **Kamień 57 — UKOŃCZONE.** Czytelny bilans ekonomiczny osady w panelu:
> atrybuty `data-wheat-production` / `data-gold-production` /
> `data-wheat-consumption` + flaga `data-wheat-surplus` i czytelne sufiksy
> ` · produkcja/mies.: … · konsumpcja: …` oraz ` · bilans pszenicy:
> nadwyżka|deficyt`. Szczegóły w `BACKLOG-ARCHIVE.md`.

> **Kamień 58 — UKOŃCZONE.** Zbiorcza gospodarka pszenicy księstwa w
> podsumowaniu gracza (`data-wheat-production` / `data-wheat-consumption` /
> `data-wheat-surplus` / `data-wheat-net` + czytelne sufiksy produkcji,
> konsumpcji, bilansu i salda). Szczegóły w `BACKLOG-ARCHIVE.md`.

> **Kamień 59 — UKOŃCZONE.** Zbiorcza produkcja złota księstwa w podsumowaniu
> gracza (`data-gold-production` + grupa tekstu `produkcja/mies.: +Pw pszenicy,
> +Pg złota`). Szczegóły w `BACKLOG-ARCHIVE.md`.

> **Kamień 60 — UKOŃCZONE.** Alert gospodarczy głodujących osad
> (`tbbui.economyalert.render_economy_alert`: korzeń `data-economy-alert` +
> `data-starving-settlements="N"`, tekst `Osady na deficycie pszenicy: N`,
> osadzenie w `render_game_page` po `data-player-summary`). Szczegóły w
> `BACKLOG-ARCHIVE.md`.

> **Kamień 61 — UKOŃCZONE.** Alert gospodarczy: wiersze per głodująca osada
> (`data-starving-settlement` / `data-wheat-deficit` + tekst `<name>: deficyt D
> pszenicy/mies.`), łączny deficyt księstwa (`data-total-wheat-deficit` + sufiks
> nagłówka) oraz flaga i nota krytyczności (`data-economy-critical` /
> `data-economy-caution`). Szczegóły w `BACKLOG-ARCHIVE.md`.

## Kamień milowy 63 — most stanu gry do klienta Godota (snapshot JSON) — PRIORYTET
> **Zmiana zakresu (brief, DECISIONS G63.0):** docelowy klient to natywna gra
> Godot 4 na Linux, a komunikacja z rdzeniem idzie przez testowalny snapshot
> JSON. HTML/SVG `tbbui` degradowane do narzędzia diagnostycznego. Zanim powstaną
> sceny Godota, budujemy w TDD **kontrakt danych**: nowy pakiet-most `tbbbridge`
> serializujący publiczny stan rdzenia do json-serializowalnych słowników. To
> fundament, którego Godot będzie konsumentem; rdzeń `tbb` pozostaje jedynym
> źródłem reguł i nie zależy od mostu.
- [x] **G63.1a** `tbbbridge.snapshot.settlement_state(settlement) -> dict` (czysty, json-serializowalny słownik osady); ARCHITECTURE (nowa sekcja `tbbbridge`), DECISIONS `G63.1a`. *(task-296)*
- [x] **G63.1b** `tbbbridge.snapshot.party_state(party) -> dict` (owner/size/hp/attack/defense/wounded z `unitstrength`); ARCHITECTURE, DECISIONS `G63.1b`. *(task-297)*
- [x] **G63.1c** `tbbbridge.snapshot.map_state(world) -> dict` (regiony z `col`/`row` z `layout_world`, osada/party, `connections`); ARCHITECTURE, DECISIONS `G63.1c`. *(task-298)*
- [x] **G63.1d** `tbbbridge.snapshot.game_state(world, game, calendar, player_duchy_id=None) -> dict` (calendar/duchies/map/result); re-issue po review-fail task-299 (rdzeń bez zmian); ARCHITECTURE, DECISIONS `G63.1d`. *(task-301)*
- [x] **G63.2a** `tbbbridge.snapshot.save_state(world, game, calendar, path, player_duchy_id=None)` — deterministyczny JSON do pliku (`indent=2`, `ensure_ascii=False`, końcowy `\n`); ARCHITECTURE, DECISIONS `G63.2a`. *(task-302)*
> **Kamienie 63–64 — UKOŃCZONE.** Most snapshotu JSON (`tbbbridge.snapshot`:
> `settlement_state`/`party_state`/`map_state`/`game_state`/`battle_state`,
> `save_state` + CLI `python -m tbbbridge`, osadzenie bitwy w `game_state`).
> Pełne streszczenia w `BACKLOG-ARCHIVE.md`.

## Kamień milowy 65 — most poleceń: Godot steruje partią przez JSON — PRIORYTET
> DESIGN §11: komunikacja Godot↔rdzeń jest dwukierunkowa — obok snapshotu OUT
> (Kamień 63/64) potrzebny jest kanał IN. `tbbbridge.session` daje uchwyt sesji
> `Session` (world/game/calendar/rng/player_duchy_id/seed) oraz json-owy punkt
> wejścia `apply_command`, którym Godot posuwa turę i wydaje rozkazy księstwu
> gracza. Most reużywa czyste prymitywy `ai.*` i driver headless — **żadnej**
> nowej logiki reguł; rdzeń `tbb` bez zmian.
- [x] **G65.1a** `tbbbridge.session.Session` + `new_session(seed=73, player_duchy_id="player")` + `Session.snapshot()`; ARCHITECTURE (podsekcja „Most poleceń”), DECISIONS `G65.0`/`G65.1a`. *(task-311)*
- [x] **G65.1b** `Session.next_turn()` — jedna tura `run_headless_game` (RNG współdzielony), `is_over` → no-op; ARCHITECTURE, DECISIONS `G65.1b`. *(task-312)*
- [x] **G65.1c** `apply_command(session, {"type": "next_turn"|"new_game"})` — dyspozytor poleceń sterujących; nieznany `type` → `ValueError`; ARCHITECTURE, DECISIONS `G65.1c`. *(task-313)*
- [x] **G65.2a** rozkazy gracza bez bitwy `develop`/`recruit`/`muster` (`ai.*` + `sync_from_world`, guardy jak `tbbui.serve`); ARCHITECTURE, DECISIONS `G65.2a`. *(task-314)*
- [x] **G65.2b** rozkaz `march` (auto / do wskazanego regionu przez `ai.march_duchy_party[_to]`); ARCHITECTURE, DECISIONS `G65.2b`. *(task-315)*
> **G65.3 rozkazy bitewne — pocięte (RNG, morale, rejestr bitwy w snapshotcie).**
- [x] **G65.3a** `Session.last_battle: HexBattle | None` + `Session.snapshot()` osadza ją przez `game_state(..., battle=)`; `_derive` przewodzi/zeruje pole; ARCHITECTURE, DECISIONS `G65.3a`. *(task-316)*
- [ ] **G65.3b** rozkaz `assault` (auto / do wskazanej osady przez `ai.assault_duchy_party[_to]_recorded`; morale z `game.duchies`, RNG, `last_battle`); ARCHITECTURE, DECISIONS `G65.3b`. *(task-317)*
- [ ] **G65.3c** rozkaz `engage` (auto / do wskazanego regionu przez `ai.engage_duchy_party[_to]_recorded`; morale, RNG, `last_battle`); ARCHITECTURE, DESIGN §11 (pełny zestaw rozkazów), DECISIONS `G65.3c`. *(task-318)*

## Dług/refaktor
- [x] **R33.1 (refaktor)** Kompaktacja DESIGN.md §11: usunięcie bloków narracyjnych „PLAN K14…K33" (historia → git/DECISIONS.md); tylko stan obecny. *(task-169)*
- [x] **R21.1 (refaktor)** Wspólny emiter formularzy celu marsz/szturm/starcie w `serve.py`. *(task-113)*
- [x] **R15.1 (refaktor)** Kompaktacja DESIGN.md do stanu obecnego; historia → DECISIONS.md. *(task-094)*
- [x] **R16.1 (refaktor)** Wspólny generator formularzy celu marsz/szturm w `serve.py`. *(task-098)*

## Później (poza MVP)
- [ ] **K62 (WSTRZYMANE — DECISIONS G63.0)** Rozbudowa alertu gospodarczego HTML
      (osada priorytetowa + remedium: `data-priority-settlement` /
      `data-priority-hint` / `data-priority-remedy`). Zaplanowane task-292…295
      **zdjęte z kolejki i usunięte** — to dalsza polish diagnostycznego klientu
      HTML, którą brief degraduje na rzecz klienta Godota. Podjąć dopiero, jeśli
      wróci realna potrzeba tej podpowiedzi (najpewniej już jako element klienta
      Godota, nie HTML).
- [ ] **R12.1 (opcjonalny dług)** Wspólna kwerenda własnych osad w `ai.py`:
      generator `_owned_settlements(world, duchy_id)` reużyty przez
      `develop_duchy_settlement`/`raise_duchy_hero`/`recruit_duchy_unit`/
      `muster_duchy_party`. Zdjęty z K12 po dwóch micro-cap porażkach refaktorów
      w pętli — duplikacja ~4 linii × 4 funkcje nie blokuje MVP. Podjąć tylko
      gdy pojawi się kolejny konsument tego wzorca.
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] Balans ekonomii, tempa rozwoju jednostek i krzywych progresji; strojenie AI.
- [ ] Pełna maszyna faz `StrategicTurn` w headless driverze (routing akcji AI przez
      fazy ruch/bitwy zamiast bezpośredniego `take_duchy_turn`). M8 reużywa tylko
      prymitywów `tick_settlements`/`end_turn`, bez wciągania phase-gatingu.
