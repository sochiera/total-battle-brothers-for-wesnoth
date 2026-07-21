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

## Kamień milowy 25 — czytelna siła bojowa w podglądzie (decyzje o walce) — UKOŃCZONY
> DESIGN §11 (PLAN K25): K22–K24 pokazały gospodarkę, liczności i tożsamość, ale
> nie **realną siłę bojową**. K25 dołożył do paneli zagregowaną siłę
> (HP + atak + obrona) party (K25.1a–b) i garnizonu (K25.2a–b) z istniejących
> `Unit`; po dwóch konsumentach refaktor R25.1 scalił agregację w
> `tbbui.unitstrength.combat_totals`. Wszystkie pozycje (task-129…133) w
> `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 26 — czytelny stan strukturalno-dynastyczny (budynki + władza) — UKOŃCZONY
> DESIGN §11 (PLAN K26): panel osad dostał liczbę i nazwy aktywnych budynków
> (K26.1a–b) z `Settlement.active_buildings`, a wiersz księstwa flagi
> `data-hero`/`data-heir` (K26.2a–b) z `Duchy`. Wszystkie pozycje
> (task-134…137) w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 27 — czytelna gotowość bojowa (rany) i orientacja w układzie strony — UKOŃCZONY
> DESIGN §11 (PLAN K27): panel party (K27.1a) i garnizonu osady (K27.2a) dostały
> liczbę rannych (`data-wounded` / `data-garrison-wounded`, sufiks ` · ranni: W`)
> z `Unit.wounds`; refaktor R27.1 scalił licznik w
> `tbbui.unitstrength.wounded_count`; nagłówki sekcji strony
> (`<h2 data-panel-section="settlements|parties|duchies">`, K27.3a–b) odróżniają
> panele. Wszystkie pozycje (task-138…142) w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb`
> bez zmian.

## Kamień milowy 28 — potwierdzenie skutku rozkazu gracza w podglądzie — UKOŃCZONY
> DESIGN §11: po każdym rozkazie POST `GameApp` ustawia czytelny komunikat
> `<p data-notice>` (`wykonano`/`brak zmian`/`bitwa`, z celem w etykiecie) oraz
> komunikat następnej tury z datą po ruchu AI. Wszystkie pozycje (task-143…147)
> w `BACKLOG-ARCHIVE.md`. `render_game_page` i rdzeń `tbb` bez zmian.

## Kamień milowy 29 — czytelny i zlokalizowany interfejs gracza (grywalny podgląd) — UKOŃCZONY
> DESIGN §11 (PLAN K29): widoczny tekst komunikatu w ciele `<p data-notice>`
> (K29.1a) i pełna lokalizacja etykiet przycisków (K29.2a–b); refaktor R29.1
> scalił guard księstwa gracza w `_resolve_player_duchy()`. Wszystkie pozycje
> (task-148…151) w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb`, `render_game_page` i
> routing bez zmian.

## Kamień milowy 30 — świadome decyzje gracza: podsumowanie księstwa + czytelny panel rozkazów — UKOŃCZONY
> DESIGN §11 (PLAN K30): czysty prymityw `render_player_summary` (gospodarka →
> K30.3a, siła → K30.3b) osadzony w `render_game_page` (K30.3c) oraz czytelniejszy
> panel rozkazów: nagłówek sekcji „Rozwój" (K30.1a) i koszt złota na przycisku
> rekrutacji (K30.2a). Wszystkie pozycje (task-152…156) w `BACKLOG-ARCHIVE.md`.
> Rdzeń `tbb` bez zmian.

## Kamień milowy 31 — grywalna pełna partia w przeglądarce: nowa gra + wynik z perspektywy gracza — UKOŃCZONY
> DESIGN §11 (PLAN K31): restart `POST /new` (K31.1a) z przyciskiem „Nowa gra"
> (K31.1b) i wpięciem seedu w CLI serve (K31.1c), oraz czytelny wynik z
> perspektywy gracza w `render_game_page` (K31.2a). Wszystkie pozycje
> (task-157…160) w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 32 — dokończenie ramy strony i czytelnego końca gry — UKOŃCZONY
> DESIGN §11: tytuł dokumentu (K32.1a), widoczny nagłówek strony (K32.1b) i linia
> celu (K32.1c) w `render_game_page` oraz ukrycie tury/rozkazów w `GET /` po
> `is_over` (K32.2a). Wszystkie pozycje (task-161…164) w `BACKLOG-ARCHIVE.md`.
> Rdzeń `tbb` bez zmian.

## Kamień milowy 33 — czytelny postęp do celu (warunki zwycięstwa na oczach gracza) — UKOŃCZONY
> DESIGN §11: czysty prymityw `render_victory_progress` (licznik
> `data-enemies-remaining` K33.1a, wiersze per-wróg `data-enemy-duchy` K33.1b,
> flaga `data-defeated` z sufiksem „— pokonany" K33.2a), osadzony w
> `render_game_page` przy `player_duchy_id` (K33.1c). Pozycje (task-165…168)
> w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 34 — podpowiedź następnego kroku do zwycięstwa — UKOŃCZONY
> DESIGN §11: czysty prymityw `render_next_objective` (jedno zdanie zależne od
> stanu: odbierz osady / dobij bohaterów / cel osiągnięty) osadzony w
> `render_game_page` po panelu postępu (K34.1a–b; task-170…171).
> Pozycje w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 35 — lokalizacja wrogiego bohatera (lista pościgu) — UKOŃCZONY
> DESIGN §11: czysty prymityw `render_enemy_hero_locator` (region party wroga z
> bohaterem lub „niewystawiony") osadzony w `render_game_page` po podpowiedzi
> celu (K35.1a–b; task-172…173). Pozycje w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb`
> bez zmian.

## Kamień milowy 36 — pościg za wrogim bohaterem: dystans marszu do celu — UKOŃCZONY
> DESIGN §6 pkt 5: rdzeniowy prymityw dystansu w grafie regionów
> (`ai.region_distance`, K36.1a) i czysty panel pościgu `render_hero_chase`
> (dystans marszu od party gracza + flaga „w zasięgu" dla sąsiada, K36.1b–c,
> K36.2a), osadzony w `render_game_page` po lokatorze. Wszystkie pozycje
> (task-174…177) w `BACKLOG-ARCHIVE.md`. Rdzeń: tylko czysta kwerenda grafu.

## Kamień milowy 37 — świadoma decyzja o walce: podgląd siły celu przed atakiem
> DESIGN §6 pkt 4–5: pościg (K36) mówi GDZIE i JAK DALEKO stoi wrogi bohater, ale
> nie CZY warto atakować. K37 dokłada czysty panel `render_engagement_preview`
> porównujący siłę party gracza z sąsiednimi wrogimi celami (osady i party),
> z flagą przewagi, osadzony w `render_game_page` po pościgu. Domyka refaktorem
> R37.1 duplikację lokalizacji party (`first_party_region`). Rdzeń `tbb` bez zmian.
- [x] **K37.1a** Prymityw `render_engagement_preview` — `data-engagement-preview`/`data-player-on-map`/`data-own-*` + wiersze sąsiednich wrogich osad (`data-enemy-*`). *(task-178)*
- [x] **K37.1b** Flaga przewagi `data-advantage="true|false"` + sufiks „ — przewaga"/„ — niekorzystnie". *(task-179)*
- [x] **K37.1c** Osadzenie w `render_game_page` po `data-hero-chase` (bez gracza → bajt-w-bajt jak dotąd). *(task-180)*
- [x] **K37.2a** Rozszerzenie o sąsiednie wrogie party (`data-target-kind="party"`; osada przed party w regionie). *(task-181)*
- [~] **R37.1 (refaktor)** Wspólny helper `tbbui.maplookup.first_party_region` reużyty przez `herolocator`/`herochase`/`engagementpreview` (bez nowych testów paneli). *(task-182)*

## Kamień milowy 38 — czytelny skutek tury AI (dziennik zmian)
> DESIGN §6 pkt 5: po „Następnej turze" gracz widzi tylko datę — nie wie, co
> zrobiło AI (czy stracił osadę, czy wróg stracił bohatera). K38 dokłada czysty
> panel `render_turn_summary` porównujący `GameState` sprzed i po turze (osady +
> bohater per księstwo), osadzony w `render_game_page` sterowany `previous_game`,
> a `GameApp` przewleka stan sprzed tury. Domyka refaktorem R38.1 duplikację
> lokalizacji księstwa gracza (`player_duchy`). Rdzeń `tbb` bez zmian.
- [ ] **K38.1a** Prymityw `render_turn_summary(before, after)` — korzeń `data-turn-summary`/`data-changed` + tekst „Zmiany w tej turze: tak|nie" (bez wierszy). *(task-183)*
- [ ] **K38.1b** Wiersze per-księstwo `data-turn-duchy` (`data-settlements-before/after`, `data-hero-before/after`) + `data-change-count`. *(task-184)*
- [ ] **K38.1c** Osadzenie w `render_game_page` przez opcjonalny `previous_game` (po `data-calendar`; `None` → bajt-w-bajt jak dotąd). *(task-185)*
- [ ] **K38.2a** `GameApp.previous_game` zapisywany po `POST /turn`, zerowany przez inne rozkazy/`/new`; przewleczony do `render_game_page`. *(task-186)*
- [ ] **R38.1 (refaktor)** Wspólny helper `tbbui.gamelookup.player_duchy` reużyty przez 6 paneli (bez nowych testów paneli). *(task-187)*

## Kamień milowy 39 — ostrzeżenie o zagrożeniu obronnym (gdzie się bronić)
> DESIGN §6 pkt 3: `engagementpreview` (K37) mówi GDZIE atakować, ale nic nie
> ostrzega, GDZIE gracz jest zagrożony. K39 dokłada czysty panel
> `render_threat_alert` — własne pozycje (osady/party) mające sąsiednie wrogie
> party, z porównaniem siły obronnej do wroga i flagą „obronisz się", osadzony
> w `render_game_page` po podglądzie starcia. Rdzeń `tbb` bez zmian.
- [ ] **K39.1a** Prymityw `render_threat_alert` — korzeń `data-threat-alert`/`data-threats` + tekst „Zagrożone pozycje: N" (bez wierszy). *(task-188)*
- [ ] **K39.1b** Wiersze per zagrożona pozycja `data-threatened-region` (`data-threatened-kind`, `data-enemy-region`, `data-enemy-owner`) + tekst. *(task-189)*
- [ ] **K39.1c** Osadzenie w `render_game_page` po `data-engagement-preview` (bez gracza → bajt-w-bajt jak dotąd). *(task-190)*
- [ ] **K39.2a** Siła obronna własnej pozycji (`data-own-*`) i wroga (`data-enemy-*`) w wierszu + sufiks tekstu. *(task-191)*
- [ ] **K39.2b** Flaga `data-defensible="true|false"` + sufiks „ — obronisz się"/„ — przewaga wroga". *(task-192)*

## Dług/refaktor
- [ ] **R39.1 (refaktor, przyszłe)** Wspólny predykat „wrogie party u sąsiada"
      (`owner_id is not None` i `!= player`) reużyty przez `engagementpreview`
      i `threatalert`; podjąć po ustabilizowaniu drugiego konsumenta (K39).
- [x] **R33.1 (refaktor)** Kompaktacja DESIGN.md §11: usunięcie bloków narracyjnych „PLAN K14…K33" (historia → git/DECISIONS.md); tylko stan obecny. *(task-169)*
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
