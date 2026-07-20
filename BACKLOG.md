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

## Kamień milowy 12 — morale w walce i ciągłość dynastii — UKOŃCZONE
> Morale księstw (w tym kara sukcesji) realnie steruje celnością stron bitwy
> w headless, party leczą rany w turze mapy, a bezhetmańskie księstwo wyznacza
> dziedzica prowadzącego do sukcesji. Wszystkie pozycje (task-056…064)
> w `BACKLOG-ARCHIVE.md`.

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
- [x] **V13.1** Pakiet `tbbui` + deterministyczny layout mapy. *(task-065; ref. 8770d8f)*
  - AC: `tbbui.layout.layout_world(world) -> dict[Region, (kolumna, wiersz)]` —
    BFS po komponentach w kolejności regionów, kolumna = dystans, wiersz =
    pierwszy wolny w kolumnie; pozycje unikalne; determinizm, bez RNG;
    ARCHITECTURE dostaje sekcję prezentacji (decyzja stdlib SVG/HTML).
> **V13.2 pocięte drobniej (wsad 066–069):** monolityczne SVG mapy (parse +
> linie + znaczniki + paleta) to zbyt duża powierzchnia dla jednej pętli
> (jak martwe V13.* z 046–050). Rozbite na cztery przyrosty, każdy z
> deterministycznym testem stringu/parsu, bez zależności od seeda. V13.3
> zaczyna się od czystej geometrii (070) przed `render_battle_svg`.
- [x] **V13.2a** Szkielet SVG mapy + węzły regionów. *(task-066)*
- [x] **V13.2b** Linie połączeń mapy SVG. *(task-067)*
- [x] **V13.2c** Znaczniki osad i party na mapie SVG. *(task-068)*
- [x] **V13.2d** Paleta kolorów właścicieli. *(task-069)*
- [x] **V13.3a** Geometria heksów pointy-top. *(task-070)*
> **Wsad 071–075 (domknięcie K13):** monolityczne V13.4 (strona + snapshot CLI)
> i V13.5 (routing + serwer) rozbite na a/b — nowa powierzchnia API oddzielona
> od CLI/serwera, każdy przyrost z deterministycznym testem stringu/parsu bez
> zależności od gniazda. Kolejność: render bitwy → strona → snapshot CLI →
> routing `GameApp.handle` → serwer `http.server`.
- [ ] **V13.3b** `render_battle_svg` — pole bitwy heksowej. *(task-071)*
  - AC: `tbbui.battlesvg.render_battle_svg(battle)` → parsowalny SVG z heksami
    obwiedni rozstawienia ±1 (`<polygon>` z `hex_corners`, wypełnienie z terenu),
    znaczniki jednostek z `data-side`/`data-hp`/`data-stunned`; czyste i det.
- [ ] **V13.4a** `render_game_page` — strona HTML partii. *(task-072)*
  - AC: `tbbui.gamepage.render_game_page(world, game, calendar)` → parsowalny
    HTML z osadzonym SVG mapy, `data-calendar` (rok/miesiąc), panelem księstw
    (`data-duchy`, `data-morale`, `data-settlements`, `data-parties`) i
    `data-result` (zwycięzca/`draw`/`ongoing`); czyste i deterministyczne.
- [ ] **V13.4b** Snapshot partii z CLI. *(task-073)*
  - AC: `tbbui.__main__.main(argv)` rozgrywa deterministyczną partię headless
    i zapisuje `render_game_page` do HTML (domyślnie `out/game.html`, katalog
    tworzony); exit 0; plik parsowalny z `data-result`; determinizm dwóch uruchomień.
- [ ] **V13.5a** `GameApp.handle` — routing podglądu (bez gniazda). *(task-074)*
  - AC: `tbbui.serve.GameApp(world, game, calendar, rng).handle(method, path)`:
    `GET /` → `(200, strona)` z formularzem `POST /turn`; `POST /turn` → jedna
    tura (`run_headless_game` `max_turns=1`), po `is_over` no-op; inne → `404`;
    determinizm seeda i sekwencji żądań.
- [ ] **V13.5b** Serwer podglądu `http.server` + `python -m tbbui serve`. *(task-075)*
  - AC: `make_server(app, host, port=0)` → `HTTPServer` (bez `serve_forever`),
    handler deleguje GET/POST do `app.handle` przez wspólny
    `handle_request(app, method, path)`; `python -m tbbui serve [port]` startuje
    serwer; test wiązania portu i delegacji bez realnego ruchu w pętli.

## Później (poza MVP)
- [ ] **R12.1 (opcjonalny dług)** Wspólna kwerenda własnych osad w `ai.py`:
      generator `_owned_settlements(world, duchy_id)` reużyty przez
      `develop_duchy_settlement`/`raise_duchy_hero`/`recruit_duchy_unit`/
      `muster_duchy_party`. Zdjęty z K12 po dwóch micro-cap porażkach refaktorów
      w pętli — duplikacja ~4 linii × 4 funkcje nie blokuje MVP. Podjąć tylko
      gdy pojawi się kolejny konsument tego wzorca.
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] **Bramkowanie treningu budynkiem (§5 „odpowiednie budynki"):** katalog
      budynku treningowego i wymóg jego czynności w `tick_training` (dziś trening
      jest bezwarunkową funkcją czasu). Analogicznie polityka AI otwierania
      kuźni/budynków treningowych.
- [ ] Balans ekonomii, tempa rozwoju jednostek i krzywych progresji; strojenie AI.
- [ ] Pełna maszyna faz `StrategicTurn` w headless driverze (routing akcji AI przez
      fazy ruch/bitwy zamiast bezpośredniego `take_duchy_turn`). M8 reużywa tylko
      prymitywów `tick_settlements`/`end_turn`, bez wciągania phase-gatingu.
