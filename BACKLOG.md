# BACKLOG — Total Battle Brothers

> **Kolejka zadań.** Każde zadanie = jeden mały, testowalny przyrost (TDD).
> Statusy: `[ ]` do zrobienia, `[~]` w toku, `[x]` zrobione.
> Bierz zadania z góry. Nie łącz wielu przyrostów w jeden. Aktualizuj status i
> dopisuj nowe zadania, gdy wizja się doprecyzowuje. Detale mechaniki → `docs/DESIGN.md`.
> Ukończone milestony przeniesione do `BACKLOG-ARCHIVE.md` (kamienie 0–10 oraz
> A7.1*/A7.2*) — tu zostaje wyłącznie żywy tail w stronę grywalnego MVP.

## Legenda
Każde zadanie ma **kryteria akceptacji** (co musi przejść jako test). Rdzeń przed
prezentacją. Determinizm (seedowalny RNG) jest wymogiem przekrojowym.

---

## Kamienie 7–8 — UKOŃCZONE (headless pętla MVP + ekonomia/kalendarz w driverze)
> `python -m tbb` uruchamia pełną, deterministyczną partię end-to-end: żywa
> miesięczna ekonomia i wzrost osad, płynący kalendarz, wypisany zwycięzca/remis
> wraz z końcową datą (kod wyjścia 0). Wszystkie pozycje w `BACKLOG-ARCHIVE.md`.
> To domyka **minimalną** pętlę z DESIGN §6 pkt 1,3,4,5. Otwarty zostaje pkt 2:
> jednostki są rekrutowane z filarami 0 i nigdy się nie „trenują ani wyposażają"
> — to domyka Kamień milowy 9.

## Kamień milowy 9 — rozwój jednostek w turze — UKOŃCZONE
> Krzywa malejącego zysku (U3.2) wpięta w `Unit` i miesięczne przejście osady:
> garnizon obserwowalnie mocnieje (trening = czas; uzbrojenie = złoto + kuźnia)
> w realnej headless partii. Wszystkie pozycje w `BACKLOG-ARCHIVE.md`.

## Kamień milowy 10 — realne straty i koszty w pętli strategicznej — UKOŃCZONE
> Garnizon ponosi straty po bitwie (G10.1–G10.2), rekrutacja kosztuje złoto
> (G10.3), AI otwiera budynki i rozwija ekonomię w pełnej polityce tury
> (G10.4–G10.5), a rekonstrukcja mapy po podmianie osady jest zdeduplikowana
> w `WorldMap.with_settlement` (R10.1). Wszystkie pozycje (task-022…035)
> w `BACKLOG-ARCHIVE.md`. Strojenie wartości pozostaje balansem.

## Kamień milowy 11 — regeneracja i ciągłość władzy — UKOŃCZONE
> Rany czasowe mijają (garnizon leczy się w łańcuchu miesięcznym), ogłuszenie
> nie wychodzi z bitwy na mapę, a bezhetmańskie księstwo z osadą wystawia
> nowego bohatera w turze (W11.1–W11.3, D11.4a–b; task-036…040). Wszystkie
> pozycje w `BACKLOG-ARCHIVE.md`. Balans kosztów/czasów pozostaje poza kamieniem.

## Kamień milowy 12 — morale w walce i ciągłość dynastii
> Dwa mechanizmy DESIGN są zaimplementowane, ale martwe w pętli: (a)
> `Duchy.morale` (w tym kara sukcesji `SUCCESSION_MORALE_PENALTY`) nigdy nie
> wpływa na bitwę — `auto_resolve` dostaje jednolite `morale=0` dla OBU stron,
> choć §3.2 mówi „morale wpływa wyłącznie na celność"; (b) `heir`/`succeed()`
> nigdy nie awansuje dziedzica, bo nikt go nie wyznacza. Do tego jednostki
> w party nigdy nie leczą ran (W11.3 leczy tylko garnizon). Kamień 12 wpina
> morale księstw w celność stron bitwy, leczy party w turze i domyka linię
> sukcesji. Po drodze mały refaktor duplikacji skanowania osad w `ai.py`.
- [ ] **R12.1** Refaktor: wspólna kwerenda własnych osad w `ai.py`. *(task-051)*
  - AC: prywatny generator `_owned_settlements(world, duchy_id)` reużyty przez
    `develop_duchy_settlement`/`raise_duchy_hero`/`recruit_duchy_unit`/
    `muster_duchy_party`; publiczne sygnatury i zachowanie bez zmian; bez
    nowych testów; cały pakiet zielony.
- [ ] **B12.1a** Morale per strona w auto-rozgrywce bitwy. *(task-052)*
  - AC: `HexBattle.auto_resolve(move_points, rng, attacker_morale=0,
    defender_morale=0)`; tura jednostki dostaje morale JEJ strony; strona
    `+45` vs `-45` wygrywa przy ustalonym seedzie, zamiana odwraca zwycięzcę;
    równe morale obu stron = dotychczasowy przebieg; `WorldMap.resolve_*`
    pomostowo podaje wspólne `morale` obu stronom; DESIGN (B12.1a).
- [ ] **B12.1b** Morale księstw wpięte w bitwy na mapie i w driverze. *(task-053)*
  - AC: `resolve_party_battle`/`resolve_settlement_battle` z
    `attacker_morale`/`defender_morale` zamiast `morale`; `ai.assault…`/
    `take_duchy_military_action`/`take_duchy_turn` z opcjonalnym
    `morale_by_owner`; driver buduje mapę morale z `GameState` przed każdą
    akcją; test: morale księstwa obserwowalnie zmienia wynik szturmu;
    determinizm; DESIGN (B12.1b).
- [ ] **W12.2** Leczenie ran party w miesięcznej turze. *(task-054)*
  - AC: `Party.tick_wounds(months=1)` (bohater + podkomendni, `0` no-op,
    ujemne błąd); `WorldMap.tick_parties()` po `tick_settlements()` w driverze;
    `Bruise` w party znika po 2 turach, `Maimed` zostaje; determinizm;
    DESIGN (W12.2) + ARCHITECTURE.
- [ ] **D12.3** Księstwo wyznacza dziedzica w turze. *(task-055)*
  - AC: `ai.designate_duchy_heir(world, duchy) -> (WorldMap, Duchy)` — no-op
    gdy brak bohatera/jest heir/brak kandydata; inaczej pierwsza własna osada
    z ≥1 wolnym i `HERO_GOLD_COST` złota daje świeżego `Unit` jako `heir`;
    driver wpina po `raise_duchy_hero`, przed `take_duchy_turn`; test: śmierć
    bohatera z dziedzicem → sukcesja w turze, morale −`SUCCESSION_MORALE_PENALTY`;
    determinizm; DESIGN (D12.3).

## Kamień milowy 13 — minimalna warstwa wizualna (obserwator)
> DESIGN §9a: rdzeń dojrzał (kamienie 7–11), a prezentacja nigdy nie powstała.
> K13 buduje osobny pakiet `src/tbbui/` w **czystym stdlib** (SVG/HTML +
> `http.server`; pygame/tkinter są niedostępne w środowisku, a string SVG jest
> w pełni testowalny w TDD): deterministyczny layout i widok mapy strategicznej,
> widok bitwy heksowej, strona partii oraz przeglądarkowy podgląd z przyciskiem
> „następna tura". Rdzeń `tbb` nie importuje `tbbui`. Rozkazy gracza
> z przeglądarki (rekrutacja/marsz/szturm) to kolejny kamień (K14).
>
> **Nota po wsadzie 046–050:** V13.1 (task-046) zostało zaimplementowane
> i przeszło zielono w cyklu 1, ale pętla dobiła do limitu cykli i orkiestrator
> wycofał commit (`git reset` do `forge/task-046-start`; implementacja
> referencyjna w reflogu: `8770d8f`). Zadania 046–050 są martwe — pozycje V13.*
> zostaną wystawione z nowymi numerami w kolejnym wsadzie (po K12).
- [ ] **V13.1** Pakiet `tbbui` + deterministyczny layout mapy. *(kolejny wsad; ref. 8770d8f)*
  - AC: `tbbui.layout.layout_world(world) -> dict[Region, (kolumna, wiersz)]` —
    BFS po komponentach w kolejności regionów, kolumna = dystans, wiersz =
    pierwszy wolny w kolumnie; pozycje unikalne; determinizm, bez RNG;
    ARCHITECTURE dostaje sekcję prezentacji (decyzja stdlib SVG/HTML).
- [ ] **V13.2** SVG mapy strategicznej. *(kolejny wsad)*
  - AC: `render_world_svg(world)` → parsowalny SVG; linia na połączenie,
    element `data-region` + nazwa na region, znaczniki `data-settlement`/
    `data-party` z `data-owner`; stała paleta kolorów właścicieli wg pierwszego
    wystąpienia; identyczny string dla tego samego świata.
- [ ] **V13.3** Geometria heksów i SVG bitwy. *(kolejny wsad)*
  - AC: `hex_to_pixel`/`hex_corners` (pointy-top, sąsiedzi równoodlegli);
    `render_battle_svg(battle)` → SVG z heksami obwiedni rozstawienia ±1,
    wypełnienie z terenu, znaczniki jednostek z `data-side`/`data-hp`/
    `data-stunned`; czyste i deterministyczne.
- [ ] **V13.4** Strona HTML partii + snapshot z CLI. *(kolejny wsad)*
  - AC: `render_game_page(world, game, calendar)` → HTML z SVG mapy,
    kalendarzem, panelem księstw (`data-duchy`, morale, osady, party) i
    `data-result` po rozstrzygnięciu; `python -m tbbui [ścieżka]` zapisuje
    stronę rozegranej partii (domyślnie `out/game.html`), exit 0.
- [ ] **V13.5** Przeglądarkowy podgląd partii z przyciskiem tury. *(kolejny wsad)*
  - AC: `GameApp.handle(method, path)`: `GET /` → strona bieżącego stanu
    z formularzem `POST /turn`; `POST /turn` → dokładnie jedna tura
    (`run_headless_game` z `max_turns=1`), po `is_over` no-op; 404 dla innych
    ścieżek; determinizm dla seeda i sekwencji żądań; `python -m tbbui serve`.

## Później (poza MVP)
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] **Bramkowanie treningu budynkiem (§5 „odpowiednie budynki"):** katalog
      budynku treningowego i wymóg jego czynności w `tick_training` (dziś trening
      jest bezwarunkową funkcją czasu). Analogicznie polityka AI otwierania
      kuźni/budynków treningowych.
- [ ] Balans ekonomii, tempa rozwoju jednostek i krzywych progresji; strojenie AI.
- [ ] Pełna maszyna faz `StrategicTurn` w headless driverze (routing akcji AI przez
      fazy ruch/bitwy zamiast bezpośredniego `take_duchy_turn`). M8 reużywa tylko
      prymitywów `tick_settlements`/`end_turn`, bez wciągania phase-gatingu.
