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

> **Kamień 65 — UKOŃCZONE.** Most poleceń kanał IN (`tbbbridge.session`):
> `Session` (world/game/calendar/rng/player_duchy_id/seed/last_battle),
> `new_session`, `Session.next_turn()`, `apply_command` z komendami sterującymi
> (`next_turn`/`new_game`) i pełnym zestawem rozkazów gracza (`develop`/
> `recruit`/`muster`/`march`/`assault`/`engage` — reużycie prymitywów `ai.*`,
> morale z `game.duchies`, współdzielony RNG, `last_battle`). Szczegóły w
> `BACKLOG-ARCHIVE.md`.

## Kamień milowy 66 — proces-most stdio: Godot steruje żywą partią — PRIORYTET
> DESIGN §11: kanał IN (`apply_command`) i OUT (`snapshot`) istnieją, brakuje
> **transportu**. Godot odpala jeden proces Pythona i gada z nim liniami JSON
> (JSON Lines): linia-komenda → linia-odpowiedź `{"ok", "snapshot"|"error",
> "result"?}`. `result` to maszynowe podsumowanie skutku komendy dla dziennika
> kampanii. Warstwa transportu jest cienka — reużywa `apply_command` i
> `Session.snapshot()`; **żadnej** nowej logiki reguł; rdzeń `tbb` bez zmian.
- [ ] **G66.1a** `tbbbridge.protocol.handle_command_line(session, line) -> (Session, dict)` — parsuje linię JSON, deleguje do `apply_command`, zwraca `{"ok", "snapshot"|"error"}`; niepoprawny JSON / `ValueError` → sesja nietknięta; ARCHITECTURE, DECISIONS `G66.0`/`G66.1a`. *(task-319)*
- [ ] **G66.1b** `tbbbridge.protocol.serve_stream(session, in, out) -> Session` — pętla JSON Lines nad strumieniami (pomija puste linie, `flush` po odpowiedzi, EOF → końcowa sesja); ARCHITECTURE, DECISIONS `G66.1b`. *(task-320)*
- [ ] **G66.1c** CLI `python -m tbbbridge serve [seed]` — świeża sesja + `serve_stream` na stdin/stdout; ścieżka snapshot-do-pliku zachowana; ARCHITECTURE, DESIGN §11, DECISIONS `G66.1c`. *(task-321)*
> **G66.2 podsumowanie skutku komendy `result` — pocięte (sterujące/niebitewne, potem bitewne).**
- [ ] **G66.2a** `command_result(before, after, command)` dla `next_turn`/`new_game`/rozkazów niebitewnych (`kind` turn/new_game/order + `changed`) + osadzenie w odpowiedzi `handle_command_line`; ARCHITECTURE, DECISIONS `G66.2a`. *(task-322)*
- [ ] **G66.2b** `command_result` dla rozkazów bojowych `assault`/`engage` (`kind: "battle"` — outcome + straty z raportu bitwy); ARCHITECTURE, DECISIONS `G66.2b`. *(task-323)*

## Kamień milowy 67 — persystencja partii: round-trip serializacja (fundament save/load) — PRIORYTET
> DESIGN §11: gracz ma móc **zapisać/wczytać stan**. Dziś `save_state` daje tylko
> stratny snapshot (widok OUT), bez odczytu. Budujemy w TDD round-trippowalną
> serializację w nowym module `tbbbridge.persist` — **oddolnie**, od typów
> liściowych ku kompozytom (osada/party/świat/sesja w kolejnych wsadach). Rdzeń
> `tbb` bez zmian; most reużywa wyłącznie publiczne API i konstruktory rdzenia.
> **G67.1 liście — UKOŃCZONE.** Round-trip typów liściowych w `tbbbridge.persist`:
> `dump/load_resources` (G67.1a), `dump/load_wound` (G67.1b, w tym
> `duration_months=None`), `dump/load_unit` (G67.1c), `dump/load_building`
> (G67.1d), `dump/load_calendar` (G67.1e). Szczegóły w `docs/ARCHITECTURE.md`
> (sekcja „Persystencja round-trip") i `docs/DECISIONS.md`. *(task-324…328)*

### G67.2 — kompozyty persystencji (oddolnie ku sesji)
- [x] **G67.2a** `tbbbridge.persist.dump_party`/`load_party` — round-trip `Party` (reużycie `load_unit`); ARCHITECTURE, DECISIONS `G67.2a`. *(task-329)*
- [ ] **G67.2b** `tbbbridge.persist.dump_settlement`/`load_settlement` — round-trip `Settlement` (reużycie `load_building`/`load_resources`/`load_unit`); ARCHITECTURE, DECISIONS `G67.2b`. *(task-330)*
- [ ] **G67.2c** `tbbbridge.persist.dump_region`/`load_region` — round-trip `Region` (liść mapy); ARCHITECTURE, DECISIONS `G67.2c`. *(task-331)*
- [ ] **G67.2d** `tbbbridge.persist.dump_world`/`load_world` — round-trip `WorldMap` (regiony, połączenia, osady/party; identyczność regionów przez indeksy); ARCHITECTURE, DECISIONS `G67.2d`. *(task-332)*
- [ ] **G67.2e** `tbbbridge.persist.dump_duchy`/`load_duchy` — round-trip `Duchy` (reużycie `load_unit`/`load_settlement`/`load_party`; `hero`/`heir` opcjonalne); ARCHITECTURE, DECISIONS `G67.2e`. *(task-333)*
> **Dalej (kolejne wsady):** serializacja RNG (state — wymaga seamu w rdzeniu,
> osobny wsad), `GameState` (reużycie `load_duchy`), `Session`
> (world/game/calendar/rng/seed/player_duchy_id/last_battle); komendy
> `save`/`load` w protokole JSON Lines + `load_state` plikowe.

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
