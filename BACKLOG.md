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

## Kamień milowy 13 — minimalna warstwa wizualna (obserwator) — UKOŃCZONY
> DESIGN §9a: osobny pakiet `src/tbbui/` w czystym stdlib (SVG/HTML +
> `http.server`) daje deterministyczny widok mapy strategicznej, pola bitwy
> heksowej, stronę partii oraz przeglądarkowy podgląd z „następną turą".
> Rdzeń `tbb` nie importuje `tbbui`. Wszystkie pozycje (task-065…075) w
> `BACKLOG-ARCHIVE.md`. Rozkazy gracza z przeglądarki — Kamień 14.

## Kamień milowy 14 — rozkazy gracza w podglądzie (single-player) — UKOŃCZONY
> DESIGN §9a/§6: podgląd K13 to obserwator AI-vs-AI. K14 dał graczowi realną
> sprawczość: steruje **jednym** księstwem (`player`), AI resztą. „Następna
> tura" rusza wyłącznie AI (K14.1), a gracz wydaje rozkazy przez `POST /order/*`
> reużywające istniejące czyste prymitywy `ai.*` — wybór celu automatyczny
> (placeholder), gracz decyduje *czy* wykonać akcję. Wszystkie pozycje
> (task-076…084) w `BACKLOG-ARCHIVE.md`. Wybór konkretnej osady/celu → Kamień 15.

## Kamień milowy 15 — wybór celu przez gracza (realna sprawczość) — UKOŃCZONY
> DESIGN §9a (PLAN K15): K14 dał decyzję *czy*, cel wybierał automat. K15
> **odwrócił** placeholder: gracz wskazuje *dokąd* maszeruje i *którą* obcą osadę
> szturmuje (K15.1a–c, K15.2a–c; task-085…090). Wszystkie pozycje w
> `BACKLOG-ARCHIVE.md`. Wybór celu nie zmienił rozstrzygania bitwy ani morale.

## Kamień milowy 16 — obserwowalna bitwa gracza w podglądzie — UKOŃCZONY
> DESIGN §9a (PLAN K16): rozkaz szturmu nagrywa rozstrzygniętą `HexBattle`, a
> `GameApp` renderuje ostatnią bitwę (SVG) w stronie partii; inne rozkazy i tura
> ją zerują. Wszystkie pozycje (task-091…098, w tym refaktor R16.1) ukończone.
- [x] **K16.1a** Strona partii z opcjonalnym slotem SVG bitwy (`render_game_page(..., battle=None)`). *(task-091)*
- [x] **K16.1b** Rdzeń: nagrana wersja szturmu osady (`resolve_settlement_battle_recorded → (WorldMap, HexBattle)`). *(task-092)*
- [x] **K16.1c** Prymityw AI szturmu na wskazaną osadę zwraca bitwę (`ai.assault_duchy_party_to_recorded`). *(task-093)*
- [x] **K16.1d-1** Prymityw AI auto-szturmu z nagraniem (`ai.assault_duchy_party_recorded`). *(task-095)*
- [x] **K16.1d-2** `GameApp` nagrywa i renderuje ostatnią bitwę po szturmie (`last_battle`). *(task-096)*
- [x] **K16.1d-3** Inne rozkazy i `POST /turn` czyszczą `last_battle`. *(task-097)*

## Kamień milowy 17 — czytelny wynik bitwy gracza w podglądzie — UKOŃCZONY
> DESIGN §11 (PLAN K17): raport HTML bitwy (wynik + polegli/ogłuszeni/zdolni per
> strona) osadzony w stronie partii. Pozycje w `BACKLOG-ARCHIVE.md`.

## Kamień milowy 18 — starcie party↔party gracza (dobicie wędrującego bohatera) — UKOŃCZONY
> DESIGN §11 (PLAN K18): nagrana bitwa party↔party → prymityw AI auto-starcia →
> rozkaz gracza `POST /order/engage` (auto-cel). Pozycje (task-101…103) w
> `BACKLOG-ARCHIVE.md`. Jawny wybór celu party → Kamień 19.

## Kamień milowy 19 — jawny wybór celu starcia party↔party — UKOŃCZONY
> DESIGN §11 (PLAN K19): gracz wskazuje *którą* sąsiednią wrogą party zaatakować
> (prymityw → routing `?target=` → formularze celu). Wszystkie pozycje
> (task-104…106) w `BACKLOG-ARCHIVE.md`. Bez zmian w rozstrzyganiu bitwy ani morale.

## Kamień milowy 20 — czytelna dla człowieka strona partii — UKOŃCZONY
> DESIGN §11 (PLAN K20): widoczny banner wyniku (`data-result-text`) i wiersze
> statusu księstw obok maszynowych markerów. Pozycje (task-107…108)
> w `BACKLOG-ARCHIVE.md`.

## Kamień milowy 21 — dokończenie czytelności strony w przeglądarce (grywalność) — UKOŃCZONY
> DESIGN §11 (PLAN K21): K20 udostępnił banner wyniku i wiersze księstw, ale
> kalendarz, raport bitwy i sekcje rozkazów pozostały dla człowieka nieczytelne.
> K21 dołożył widoczny tekst kalendarza i raportu bitwy oraz odróżnialne nagłówki
> sekcji rozkazów (K21.1a–c, K21.2) plus refaktor emitera formularzy (R21.1).
> Pozycje (task-109…113) w `BACKLOG-ARCHIVE.md`. Maszynowe `data-*` i routing bez
> zmian; rdzeń bez zmian.

## Kamień milowy 22 — czytelny stan gospodarczo-wojskowy w podglądzie — UKOŃCZONY
> DESIGN §11 (PLAN K22): strona pokazuje gospodarkę własnych osad (pszenica/złoto,
> populacja, garnizon) i siłę oddziałów na mapie przez czyste panele
> `render_settlement_panel` (K22.1a–b) i `render_party_panel` (K22.2a) osadzone
> w `render_game_page` (K22.1c/K22.2b). Wszystkie pozycje (task-114…118)
> w `BACKLOG-ARCHIVE.md`. Rdzeń bez zmian.

## Kamień milowy 23 — orientacja gracza w podglądzie (legenda + tożsamość) — UKOŃCZONY
> DESIGN §11 (PLAN K23): legenda właścicieli (K23.1a–b), oznaczenie księstwa
> gracza (K23.2a–b) i osad gracza w panelu (K23.3a–b). Wszystkie pozycje
> (task-119…124) w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 24 — dokończenie orientacji gracza (własna party + kolor na mapie) — UKOŃCZONY
> DESIGN §11 (PLAN K24): opcjonalny `player_duchy_id` znakuje własne party
> (`data-player-owned`, K24.1a–b) i wiersz gracza w legendzie
> (`data-player-owner` + prefiks `» `, K24.2a–b), przewleczony przez
> `render_game_page`. Nowe argumenty domyślnie `None` → bajt-w-bajt jak dziś.
> Wszystkie pozycje (task-125…128) w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 25 — czytelna siła bojowa w podglądzie (decyzje o walce)
> DESIGN §11 (PLAN K25): K22–K24 pokazały gospodarkę, liczności i tożsamość, ale
> nie **realną siłę bojową** — gracz nie oceni, czy oddział wygra starcie ani czy
> garnizon obroni osadę (§6 pkt 2). K25 dokłada do paneli zagregowaną siłę
> (HP + atak + obrona) party (K25.1a–b) i garnizonu (K25.2a–b) z istniejących
> `Unit`; po dwóch konsumentach refaktor R25.1 scala agregację. Rdzeń `tbb` bez
> zmian; panele osadzone w `render_game_page` re-embedują zmianę automatycznie.
- [ ] **K25.1a** Panel party pokazuje siłę (HP) oddziału (`data-hp` = suma `Unit.hp` po bohaterze+podkomendnych; sufiks ` · siła: HP H`). *(task-129)*
- [ ] **K25.1b** Panel party pokazuje atak i obronę oddziału (`data-attack`/`data-defense`; sufiks `, atak A, obrona D`). *(task-130)*
- [ ] **K25.2a** Panel osad pokazuje siłę (HP) garnizonu (`data-garrison-hp`; sufiks ` · siła garnizonu: HP H`). *(task-131)*
- [ ] **K25.2b** Panel osad pokazuje atak i obronę garnizonu (`data-garrison-attack`/`data-garrison-defense`; sufiks `, atak A, obrona D`). *(task-132)*
- [ ] **R25.1 (refaktor)** Wspólny helper agregacji siły bojowej sekwencji `Unit` reużyty przez oba panele; bez nowych testów. *(task-133)*

## Dług/refaktor
- [x] **R21.1 (refaktor)** Wspólny emiter formularzy celu marsz/szturm/starcie w `serve.py`. *(task-113)*
- [x] **R15.1 (refaktor)** Kompaktacja DESIGN.md do stanu obecnego; historia → DECISIONS.md. *(task-094)*
- [x] **R16.1 (refaktor)** Wspólny generator formularzy celu marsz/szturm w `serve.py`. *(task-098)*

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
