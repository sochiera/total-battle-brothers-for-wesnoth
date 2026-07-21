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
> ją zerują. Wszystkie pozycje (task-091…098, w tym refaktor R16.1)
> w `BACKLOG-ARCHIVE.md`.

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

## Kamień milowy 37 — świadoma decyzja o walce: podgląd siły celu przed atakiem — UKOŃCZONY
> DESIGN §6 pkt 4–5: czysty panel `render_engagement_preview` porównujący siłę
> party gracza z sąsiednimi wrogimi celami (osady i party) z flagą przewagi,
> osadzony w `render_game_page` po pościgu; refaktor R37.1 scalił lokalizację
> party (`first_party_region`). Wszystkie pozycje (task-178…182)
> w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 38 — czytelny skutek tury AI (dziennik zmian) — UKOŃCZONY
> DESIGN §6 pkt 5: czysty panel `render_turn_summary` porównujący `GameState`
> sprzed i po turze (osady + bohater per księstwo), osadzony w `render_game_page`
> przez `previous_game` (przewlekany przez `GameApp`); refaktor R38.1 scalił
> lokalizację księstwa gracza (`player_duchy`). Wszystkie pozycje (task-183…187)
> w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 39 — ostrzeżenie o zagrożeniu obronnym (gdzie się bronić) — UKOŃCZONY
> DESIGN §6 pkt 3: `engagementpreview` (K37) mówi GDZIE atakować; K39 dołożył
> czysty panel `render_threat_alert` — własne pozycje (osady/party) mające
> sąsiednie wrogie party, z porównaniem siły obronnej do wroga i flagą
> „obronisz się", osadzony w `render_game_page` po podglądzie starcia. Wszystkie
> pozycje (task-188…192) w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 40 — skrót sytuacji taktycznej (bronić się czy atakować) — UKOŃCZONY
> DESIGN §11: czysty `render_situation_report` — jednolinijkowy skrót „na jeden
> rzut oka": liczba zagrożonych pozycji (`data-threatened-count`) vs korzystnych
> celów (`data-opportunity-count`) z werdyktem postawy
> (`data-net-posture=offensive|defensive|balanced`), osadzony w `render_game_page`
> po alercie zagrożeń; poprzedzony refaktorem R39.1 (wspólny predykat wrogiego
> party). Wszystkie pozycje (task-193…197) w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb`
> bez zmian.

## Kamień milowy 41 — zalecany następny rozkaz (rada wykonalna) — UKOŃCZONY
> DESIGN §11: K33–K40 dały bogate panele i werdykt postawy; K41 zamienił werdykt
> w jeden konkretny **zalecany rozkaz** — czysty `render_recommended_action`
> nazywa cel (szturm/starcie na korzystny cel, obrona zagrożonej pozycji, rozwój)
> i niesie maszynowe `data-action`, osadzony w `render_game_page` po skrócie
> sytuacji. Wszystkie pozycje (task-198…202) w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb`
> bez zmian.

## Kamień milowy 42 — wykonalny zalecany rozkaz (rada w jeden klik) — UKOŃCZONY
> DESIGN §11: K41 pokazał zalecany rozkaz, ale gracz musiał go wykonać sam,
> szukając właściwej sekcji. K42 domknął pętlę rada→akcja: maszynowa decyzja rady
> (`recommended_order`, K42.1a) → mapa akcji na istniejącą trasę POST
> (`recommended_order_path`, K42.1b) → jeden formularz `data-recommended-order` w
> `GET /` (K42.1c) z czytelnym przyciskiem „Wykonaj zalecenie: <opis>" (K42.2a).
> Reużywa trasy `/order/*` — bez nowego backendu rozkazów. Wszystkie pozycje
> (task-203…206) w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 43 — dziennik rozkazów gracza (pamięć kampanii w podglądzie) — UKOŃCZONY
> DESIGN §11: gracz widział tylko OSTATNI komunikat (`data-notice`); K43 dołożył
> przewijalny dziennik ostatnich rozkazów i skutków tur: czysty `render_order_log`
> (K43.1a) zasilany akumulatorem `GameApp.order_log` (K43.1b), osadzony w `GET /`
> niezależnie od `is_over` (K43.1c), z limitem ostatnich `ORDER_LOG_LIMIT` wpisów
> (K43.2a); poprzedzony refaktorem R43.1 (kompaktacja DESIGN §11). Wszystkie
> pozycje (task-207…211) w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 44 — czytelny, zakotwiczony w czasie dziennik kampanii — UKOŃCZONY
> DESIGN §11: `format_log_entry(notice, calendar)` (K44.1a) wpięty w akumulator
> `GameApp` (K44.1b) zakotwicza każdy wpis prefiksem daty, a `render_order_log`
> dostał widoczny nagłówek (K44.2a) i komunikat stanu pustego (K44.2b). Wszystkie
> pozycje (task-212…215) w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 45 — dziennik kampanii: najnowsze na wierzchu, objętość i skróty — UKOŃCZONY
> DESIGN §11: dziennik czytany od najnowszego (K45.1a), znacznik najnowszego
> wpisu (K45.2a), liczba wpisów w nagłówku (K45.3a) oraz nota o obcięciu przy
> limicie (K45.4a) wpięta w `GameApp` (K45.4b). Reużywa istniejące
> `order_log`/`ORDER_LOG_LIMIT`. Pozycje (task-216…220) w `BACKLOG-ARCHIVE.md`.
> Rdzeń `tbb` bez zmian.

## Kamień milowy 46 — czytelny wynik rozkazu bitewnego gracza (dziennik/komunikat) — UKOŃCZONY
> DESIGN §11: po szturmie/starciu komunikat niósł tylko „bitwa"; K46 dołożył
> wynik z perspektywy atakującego (`battle_outcome_text`, K46.1a–b) i liczbę
> własnych strat (`attacker_losses`, K46.2a–b). Wszystkie pozycje (task-221…224)
> w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 47 — pełny bilans strat bitwy gracza (obie strony) — UKOŃCZONY
> DESIGN §11: K47 dołożył czysty `defender_losses` (K47.1a) wpięty w komunikat
> obok `attacker_losses` (K47.1b): `... (straty: A, wróg: D)`. Wszystkie pozycje
> (task-225…226) w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 48 — zalecenie zebrania oddziału dla gracza bez party — UKOŃCZONY
> DESIGN §11: K48 dołożył czysty predykat `player_can_muster` (K48.1a), tekst
> rady „zbierz oddział" (K48.1b), priorytet akcji `muster` nad postawą w
> `recommended_order`/renderze (K48.1c) i mapowanie `muster`→`/order/muster`
> domykające radę w jeden klik (K48.1d). Wszystkie pozycje (task-227…230)
> w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 49 — zalecenie marszu ku wrogowi dla bezczynnego party gracza — UKOŃCZONY
> DESIGN §11: rada w jeden klik (K41–K48) mówiła graczowi z party na mapie, ale
> bez sąsiedniego celu, tylko „rozwijaj księstwo" — nigdy „maszeruj ku wrogowi".
> K49 dołożył czysty cel marszu `player_march_target` (K49.1a), tekst rady
> „maszeruj ku osadzie" (K49.1b) oraz gałąź akcji `march` w gałęzi zrównoważonej
> `recommended_order`/renderze przed `develop` (K49.1c); domknięcie rada→akcja
> (`recommended_order_path("march")`→`/order/march` + formularz jednego kliknięcia
> w `GET /`, K49.1d) weszło razem z K49.1c w task-233 (task-234 pominięty jako
> duplikat). `POST /order/march` reużywa istniejącą trasę `ai.march_duchy_party_to`
> (K14/K28, bez nowego backendu). Wszystkie pozycje (task-231…233) w
> `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 50 — czytelne uzasadnienie zalecanego rozkazu (dlaczego ta rada) — UKOŃCZONY
> DESIGN §11: czyste, deterministyczne uzasadnienie rady zależne od akcji —
> prymityw `recommended_order_reason` (K50.1a) osadzony w panelu rady (K50.1b)
> i przy przycisku wykonania w jeden klik (K50.1c). Pozycje (task-235…237)
> w `BACKLOG-ARCHIVE.md`. Rdzeń `tbb` bez zmian.

## Kamień milowy 51 — przewidywana siła zalecanej bitwy (ryzyko rady) — UKOŃCZONY
> DESIGN §11: czysta prognoza siły dla rady bojowej — `recommended_battle_forecast`
> `(own, enemy)` dla szturmu/starcia (K51.1a) i obrony (K51.1b), tekst z werdyktem
> przewaga/ryzyko (K51.1c) osadzony w panelu rady (K51.1d) i przy przycisku
> wykonania w jeden klik (K51.1e). Pozycje (task-238…242) w `BACKLOG-ARCHIVE.md`.
> Rdzeń `tbb` bez zmian.

## Kamień milowy 52 — czytelne wyróżnienie ryzyka rady bitewnej
> DESIGN §11: K51 pokazało prognozę siły z werdyktem „ryzyko", ale werdykt tonie
> w jednym zdaniu. K52 wyróżnia radę bojową o przewidywanym deficycie siły —
> maszynowo i po ludzku — by gracz nie wykonał w ciemno przegranej bitwy: czysty
> predykat `recommended_battle_is_risky` (K52.1a), flaga `data-recommended-risk`
> i nota ostrożności w panelu rady (K52.1b–c) oraz przy przycisku wykonania rady
> w jeden klik (K52.1d–e). Reużywa `recommended_battle_forecast`; bez nowego
> backendu, bez zmiany routingu; rdzeń `tbb` bez zmian.
- [ ] **K52.1a** `tbbui.recommendedaction.recommended_battle_is_risky(world, game, player_duchy_id=None) -> bool` zwraca `False`, gdy `recommended_battle_forecast(...) is None`; przy prognozie `(own, enemy)` zwraca `True` iff `own < enemy` (spójnie z werdyktem `ryzyko`); czysty, bez mutacji, deleguje do `recommended_battle_forecast`. *(task-243)*
- [ ] **K52.1b** Gdy `recommended_battle_is_risky(...)` jest `True`, korzeń `<div data-recommended-action="">` z `render_recommended_action` niesie pusty atrybut `data-recommended-risk=""` po `data-action`; `False` → brak atrybutu, fragment bajt-w-bajt jak dotąd. *(task-244)*
- [ ] **K52.1c** Gdy `recommended_battle_is_risky(...)` jest `True`, `render_recommended_action` osadza po `data-recommended-forecast` jedno `<p data-recommended-caution="{text}">{text}</p>` (`text = "Uwaga: przewidywany deficyt siły — rozważ inny rozkaz"`, `html.escape(quote=True)`); `False` → brak elementu. *(task-245)*
- [ ] **K52.1d** Gdy formularz `_recommended_order_form()` jest emitowany i `recommended_battle_is_risky(...)` jest `True`, `<form ... data-recommended-order="">` niesie pusty atrybut `data-recommended-risk=""` po `data-recommended-order=""`; przypadki `""` i `False` → brak atrybutu, formularz jak dotąd. *(task-246)*
- [ ] **K52.1e** Gdy formularz `_recommended_order_form()` jest emitowany i `recommended_battle_is_risky(...)` jest `True`, po `data-recommended-order-forecast` dokłada jedno `<p data-recommended-order-caution="{text}">{text}</p>` (ten sam tekst co K52.1c, `html.escape(quote=True)`); `False` / brak formularza → brak elementu. *(task-247)*

## Kamień milowy 53 — dług po serii rady bojowej + trening jednostek w maszerującym party
> Po K52 seria „zalecany rozkaz" (K41–K52) się domyka; ten kamień najpierw
> sprząta powielony HTML akapitów rady dołożony w K50–K52 (R52.1), potem
> zaczyna rozstrzygać jedno z otwartych pytań DESIGN §12: jednostki w
> maszerującym party trenują się razem z leczeniem ran w miesięcznym ticku
> mapy (T53.1a–b), tak jak dziś garnizon w `tick_settlements`. Uzbrojenie
> zostaje poza zakresem — party nie ma dostępu do złota/kuźni osady.
- [ ] **R52.1 (refaktor)** Wspólny helper escapowanego akapitu `<p data-X="…">…</p>` w `tbbui/recommendedaction.py`, reużyty przez `render_recommended_action` i `GameApp._recommended_order_form` (dedup powielenia z K50–K52); bez nowych testów, wynik bajt-w-bajt jak dziś. *(task-248)*
- [ ] **T53.1a** `tbb.party.Party.tick_training(months=1) -> Party` — czysta metoda treningu hero+units (mirror `tick_wounds`, deleguje do `Unit.train`); jeszcze niepodpięta w `WorldMap.tick_parties`. *(task-249)*
- [ ] **T53.1b** `WorldMap.tick_parties()` stosuje `party.tick_wounds(1).tick_training(1)` na każdym party; scenariusz bazowy headless i DESIGN §5/§8 zaktualizowane do nowego, faktycznego stanu. *(task-250)*

## Dług/refaktor
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
