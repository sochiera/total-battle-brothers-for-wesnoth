# BACKLOG ARCHIVE — Total Battle Brothers

> Ukończone zadania przeniesione z `BACKLOG.md`, by kolejka robocza nie puchła.
> Szczegóły decyzji mechaniki/architektury żyją w `docs/DESIGN.md` i
> `docs/ARCHITECTURE.md`. Tu zostaje jedynie ślad, co i kiedy zamknięto.

## Kamień milowy 14 — rozkazy gracza w podglądzie (single-player) — UKOŃCZONY
- [x] **K14.1a** Driver pomija turę AI księstwa gracza. *(task-076)*
- [x] **K14.1b** GameApp zna gracza; `/turn` odpala tylko AI. *(task-077)*
- [x] **K14.2a** Rozkaz gracza: rekrutacja (`POST /order/recruit`). *(task-078)*
- [x] **K14.2b** Rozkaz gracza: wystawienie party (`POST /order/muster`). *(task-079)*
- [x] **K14.2c** Rozkaz gracza: rozwój osady (`POST /order/develop`). *(task-080)*
- [x] **K14.2d1** Prymityw AI marszu party księstwa (`ai.march_duchy_party`). *(task-081)*
- [x] **K14.2d2** Rozkaz gracza: marsz party (`POST /order/march`). *(task-082)*
- [x] **K14.2e1** Prymityw AI szturmu party księstwa (`ai.assault_duchy_party`). *(task-083)*
- [x] **K14.2e2** Rozkaz gracza: szturm osady (`POST /order/assault`). *(task-084)*

## Kamień milowy 15 — wybór celu przez gracza (realna sprawczość) — UKOŃCZONY
- [x] **K15.1a** Prymityw AI marszu na wskazany region (`ai.march_duchy_party_to`). *(task-085)*
- [x] **K15.1b** Rozkaz gracza: marsz na wskazany region (`POST /order/march?target=`). *(task-086)*
- [x] **K15.1c** UI wyboru celu marszu (formularze per region-cel). *(task-087)*
- [x] **K15.2a** Prymityw AI szturmu na wskazaną osadę (`ai.assault_duchy_party_to`). *(task-088)*
- [x] **K15.2b** Rozkaz gracza: szturm na wskazaną osadę (`POST /order/assault?target=`). *(task-089)*
- [x] **K15.2c** UI wyboru celu szturmu (formularze per obca osada). *(task-090)*

## Kamień milowy 16 — obserwowalna bitwa gracza w podglądzie — UKOŃCZONY
- [x] **K16.1a** Strona partii z opcjonalnym slotem SVG bitwy (`render_game_page(..., battle=None)`). *(task-091)*
- [x] **K16.1b** Rdzeń: nagrana wersja szturmu osady (`resolve_settlement_battle_recorded`). *(task-092)*
- [x] **K16.1c** Prymityw AI szturmu na wskazaną osadę zwraca bitwę (`ai.assault_duchy_party_to_recorded`). *(task-093)*
- [x] **K16.1d-1** Prymityw AI auto-szturmu z nagraniem (`ai.assault_duchy_party_recorded`). *(task-095)*
- [x] **K16.1d-2** `GameApp` nagrywa i renderuje ostatnią bitwę po szturmie (`last_battle`). *(task-096)*
- [x] **K16.1d-3** Inne rozkazy i `POST /turn` czyszczą `last_battle`. *(task-097)*
- [x] **R16.1 (refaktor)** Wspólny generator formularzy celu marsz/szturm w `serve.py`. *(task-098)*
- [x] **R15.1 (refaktor)** Kompaktacja DESIGN.md do stanu obecnego; historia → DECISIONS.md. *(task-094)*

## Kamień milowy 17 — czytelny wynik bitwy gracza w podglądzie — UKOŃCZONY
- [x] **K17.1a** Prymityw HTML raportu bitwy (`tbbui.battlereport.render_battle_report(battle)`). *(task-099)*
- [x] **K17.1b** Strona partii osadza raport bitwy (`render_game_page(..., battle=…)`). *(task-100)*

## Kamień milowy 18 — starcie party↔party gracza (dobicie wędrującego bohatera) — UKOŃCZONY
- [x] **K18.1a** Rdzeń: nagrana wersja bitwy party↔party (`WorldMap.resolve_party_battle_recorded`). *(task-101)*
- [x] **K18.1b** Prymityw AI auto-starcia party↔party z nagraniem (`ai.engage_duchy_party_recorded`). *(task-102)*
- [x] **K18.1c** Rozkaz gracza `POST /order/engage` ustawia i renderuje `last_battle`. *(task-103)*

## Kamień milowy 19 — jawny wybór celu starcia party↔party — UKOŃCZONY
- [x] **K19.1a** Prymityw AI starcia na wskazany cel (`ai.engage_duchy_party_to_recorded`). *(task-104)*
- [x] **K19.1b** Routing `POST /order/engage?target=` (fallback auto). *(task-105)*
- [x] **K19.1c** Formularze celu starcia w GET `/` (sąsiednie wrogie party). *(task-106)*

## Kamień milowy 20 — czytelna dla człowieka strona partii — UKOŃCZONY
- [x] **K20.1a** Czytelny banner wyniku (`<p data-result-text>`). *(task-107)*
- [x] **K20.1b** Czytelny wiersz statusu księstwa w panelu `data-duchy`. *(task-108)*

## Kamień milowy 10 — realne straty i koszty w pętli strategicznej — UKOŃCZONY
- [x] **G10.1** Osada wchłania ocalałych obrońców po bitwie
      (`Settlement.absorb_defenders(survivors)` — garnizon = ocalali, polegli
      zmniejszają `population`/`occupied` po `free`; niemutowalne, bez RNG).
- [x] **G10.2a** Straty garnizonu obrońcy przy `DEFENDER_WIN`/`DRAW`
      (`apply_settlement_battle_result` z `battle` zastępuje garnizon
      `side_survivors(DEFENDER)`; `battle is None` = zgodność wsteczna).
- [x] **G10.2b** Garnizon zdobytej osady przy `ATTACKER_WIN`
      (podbój: `owner_id`→atakujący i garnizon = `side_survivors(DEFENDER)`,
      party wchodzi jak w BW.3c; stare stany wliczają garnizon do `occupied`).
- [x] **G10.3** Koszt złota rekrutacji (`Settlement.recruit()` pobiera
      `RECRUIT_GOLD_COST` ze `storage`; brak złota lub populacji → `ValueError`;
      AI pomija osady bez dość złota; niemutowalne, deterministyczne).
- [x] **G10.4** Polityka AI: otwieranie budynków ekonomii/kuźni
      (`ai.develop_duchy_settlement` otwiera pierwszy brakujący budynek wg
      priorytetu `Farm`→`Smith`→`Market` w pierwszej własnej osadzie z dość
      wolną populacją; brak kandydata = no-op; niemutowalne, bez RNG).
- [x] **G10.5a** `take_duchy_turn`: rozwój → rekrutacja → wojsko *(task-032)*
      (`develop_duchy_settlement` przed `recruit_duchy_unit` i akcją wojskową;
      brak możliwości rozwoju nie przerywa dalszych etapów).
- [x] **G10.5b** Progresja priorytetu `Farm`→`Smith` w kolejnych turach
      *(task-033)* (dwa kolejne `take_duchy_turn` otwierają Farm, potem Smith).
- [x] **G10.5c** Integracja rozwoju AI w realnej partii headless *(task-034)*
      (`run_headless_game` z `create_headless_game`: osada AI otwiera `Farm`;
      determinizm end-to-end).
- [x] **R10.1** Refaktor: `WorldMap.with_settlement`, dedup rekonstrukcji mapy
      *(task-035)* (`ai.py` i `world.py` reużywają wspólnego czystego przejścia;
      zero zmian zachowania).

## Kamień milowy 9 — rozwój jednostek w turze (§6 pkt 2: „trenuj i wyposażaj")
- [x] **U9.1** Trening jednostki jako czyste przejście z malejącym zyskiem
      (`Unit.train(months)` + `training_progress`, krzywa trójkątna U3.2).
- [x] **U9.2** Uzbrojenie jednostki jako czyste przejście z malejącym zyskiem
      (`Unit.equip(investment)` + `equipment_progress`; `damage`/`defense` z `equipment`).
- [x] **U9.3** Miesięczny trening garnizonu (`Settlement.tick_training()`).
- [x] **U9.4** Miesięczne uzbrajanie garnizonu przez kuźnię (`Settlement.tick_equipment()`).
- [x] **U9.5** Rozwój garnizonu w `tick_settlements` i driverze
      (łańcuch `economy→growth→immigration→training→equipment`, determinizm end-to-end).

## Kamień milowy 8 — pełna tura strategiczna w driverze (ekonomia + kalendarz)
- [x] **M8.1** Miesięczna ekonomia w pętli tury headless
      (`tick_settlements()` na początku tury + sync `GameState`).
- [x] **M8.2** Kalendarz przesuwa się o miesiąc na ukończoną turę
      (`run_headless_game` przewleka `Calendar`, zwraca trójkę).
- [x] **M8.3** CLI raportuje datę zakończenia partii (rok/miesiąc obok wyniku).

## Kamień milowy 0 — szkielet (bootstrap)
- [x] **B0.1** Szkielet projektu + pytest + jeden trywialny zielony test.

## Kamień milowy 1 — fundament rdzenia
- [x] **C1.1** Seedowalny RNG (`tbb/rng.py`).
- [x] **C1.2** `Resources` (pszenica, złoto) — dodawanie, odejmowanie, walidacja.
- [x] **C1.3** Współrzędne heksów (`tbb/hex.py`, axial/cube).

## Kamień milowy 2 — osada i ekonomia
- [x] **E2.1** `Settlement` z pulą populacji (wolna vs zajęta).
- [x] **E2.2** Budynki: uruchomienie wymaga wolnej populacji; zamknięcie ją zwalnia.
- [x] **E2.3** Produkcja surowców per tura (pszenica/złoto z budynków) + konsumpcja.
- [x] **E2.4a** Wzrost populacji — urodzenia + sufit (`capacity`).
- [x] **E2.4b** Wzrost populacji — imigranci (dopływ zależny od dobrobytu).

## Kamień milowy 3 — jednostki i progresja
- [x] **U3.1** `Unit` z trzema filarami (trening/uzbrojenie/doświadczenie).
- [x] **U3.2** Malejący zysk treningu i uzbrojenia (czas/surowce → poziom filaru).
- [x] **U3.3** Rekrutacja jednostki z populacji osady.

## Kamień milowy 4 — bitwa heksowa
- [x] **B4.1** Plansza heksowa + teren z modyfikatorami.
- [x] **B4.2a** Rozstawienie jednostek na planszy (deployment, bez ruchu).
- [x] **B4.2b** Ruch jednostki po punktach ruchu z kosztem terenu.
- [x] **B4.3a** Walka wręcz: czyste wyliczenie szansy trafienia.
- [x] **B4.3b1** Stan bieżącego HP jednostek w bitwie.
- [x] **B4.3b2** Walka wręcz: strony, sąsiedztwo, rzut na trafienie i obrażenia.
- [x] **B4.4a** Minimalny atak dystansowy: profil jednostki, zasięg i obrażenia.
- [x] **B4.4b1** Deterministyczna linia heksów dla widoczności.
- [x] **B4.4b2** Jednostki jako przeszkody dla ataku dystansowego.
- [x] **B4.5a** Minimalny model ran czasowych i trwałych.
- [x] **B4.5b** Rozstrzygnięcie jednostki z 0 HP: śmierć albo ogłuszenie + rana.
- [x] **B4.6a** Warunek końca bitwy i zwycięska strona.
- [x] **B4.6b** Raport wyniku bitwy: polegli, ogłuszeni i zdolni do działania.
- [x] **B4.6c** Doświadczenie za udział w rozstrzygniętej bitwie.

## Kamień milowy 5 — mapa strategiczna i tura
- [x] **M5.1a** `WorldMap`: niemutowalny graf regionów i rozmieszczenie osad.
- [x] **M5.2a** Party (bohater + ≤12 jednostek), bez mapy i ruchu.
- [x] **M5.1b** Pozycje party na `WorldMap`.
- [x] **M5.2b** Ruch party między sąsiednimi regionami z punktami ruchu.
- [x] **M5.3a** Kontakt dwóch party tworzy minimalną bitwę heksową.
- [x] **M5.3b1** Kontakt party z garnizonem osady tworzy minimalną bitwę.
- [x] **M5.3b2** Własność strategiczna ogranicza kontakt do wrogich celów.
- [x] **M5.4a** Kalendarz strategiczny: 1 tura = 1 miesiąc, 13 miesięcy po 4 tygodnie.
- [x] **M5.4b** Miesięczne przejście osad: produkcja → urodzenia → imigracja.
- [x] **M5.4c1** Maszyna faz strategicznej tury: osady → ruch → bitwy → zakończona.
- [x] **M5.4c2** Bramkowanie akcji tury fazą (ruch i rozpoczęcie bitew).

## Kamień milowy 6 — księstwa, następstwo, warunki gry
- [x] **D6.1a** `Duchy` minimalny: identyfikator + jeden bohater + morale.
- [x] **D6.1b1** `Duchy`: wyznaczony dziedzic (opcjonalny `heir`).
- [x] **D6.1b2** `Duchy`: lista osad i party (spięcie z mapą).
- [x] **D6.2a** Śmierć bohatera z dziedzicem → sukcesja + kara morale.
- [x] **D6.2b** Śmierć bohatera bez dziedzica → księstwo bez bohatera (sygnał).
- [x] **D6.3a** Predykat porażki księstwa (`Duchy.is_defeated`).
- [x] **D6.3b** Rozstrzygnięcie wygranej/przegranej między księstwami (stan gry).

## Kamień milowy 6.5 — automatyczne rozegranie bitwy (driver)
- [x] **BD.1** Wybór najbliższego wrogiego celu (`HexBattle.nearest_enemy`).
- [x] **BD.2** Tura pojedynczej jednostki: podejście + atak wręcz.
- [x] **BD.3** Pełna auto-rozgrywka bitwy (`HexBattle.auto_resolve`).

## Kamień milowy 6.6 — skutki bitwy na mapie strategicznej
- [x] **BW.1** Zapis wyniku bitwy party↔party (`WorldMap.apply_party_battle_result`).
- [x] **BW.2** Zapis wyniku bitwy party↔osada (`WorldMap.apply_settlement_battle_result`).
- [x] **BW.3a** Uporządkowana kwerenda ocalałych strony (`HexBattle.side_survivors`).
- [x] **BW.3b** Czyste odtworzenie składu party z ocalałych (`Party.reconstruct`).
- [x] **BW.3c** Wpięcie rekonstrukcji w `apply_*_battle_result`.

## Kamień milowy 6.7 — rozstrzyganie kontaktu na mapie (driver strategiczny)
- [x] **BM.1** Rozstrzygnięcie kontaktu party↔party (`WorldMap.resolve_party_battle`).
- [x] **BM.2** Rozstrzygnięcie kontaktu party↔osada (`WorldMap.resolve_settlement_battle`).

## Kamień milowy 6.8 — wystawienie party z osady (muster)
- [x] **MU.1** Wystawienie party z garnizonu osady (`Settlement.muster`).
- [x] **MU.2** Atomowe wystawienie party z osady na mapę (`WorldMap.muster_party`).

## Kamień milowy 7 — AI i grywalna pętla MVP (ukończona część)
- [x] **A7.1a** Wybór najbliższej wrogiej osady przez AI.
- [x] **A7.1b1** Wybór następnego kroku marszu ku wrogiej osadzie.
- [x] **A7.1b2** Wykonanie jednego kroku marszu istniejącego party AI.
- [x] **A7.1b3** Szturm istniejącego party AI na sąsiednią wrogą osadę.
- [x] **A7.1b4** Wystawienie party AI z własnej osady.
- [x] **A7.1b5a** Wojskowa akcja tury AI (muster → marsz → szturm).
- [x] **A7.1b5b1** Rekrutacja jednego żołnierza przez AI.
- [x] **A7.1b5b2** Pełna polityka tury AI: rekrutacja → akcja wojskowa.
- [x] **A7.2a** Deterministyczny setup partii headless.
- [x] **A7.2b1** Synchronizacja kolekcji księstw z mapą świata
      (`GameState.sync_from_world`).
- [x] **A7.2b2** Aktualizacja życia bohatera po wojskowej akcji tury
      (`driver.resolve_hero_survival`).
- [x] **A7.2b3a** Szkielet drivera headless i bezpiecznik
      (`driver.run_headless_game`: wyjścia dla `is_over`/`max_turns == 0`).
- [x] **A7.2b3b1** Jedna tura: akcje księstw na wspólnej mapie
      (`take_duchy_turn` przewleczone przez kolejność `game.duchies`).
- [x] **A7.2b3b2** Synchronizacja stanu gry po akcji księstwa
      (`GameState.sync_from_world` po każdym `take_duchy_turn`).
- [x] **A7.2b3b3** Przeżycie bohatera w akcji tury
      (`resolve_hero_survival` wpięte przed sync, sukcesja w tej samej turze).
- [x] **A7.2b3c** Pętla drivera do rozstrzygnięcia i determinizm
      (powtarza tury aż `is_over` albo do `max_turns`; ten sam seed → ten sam wynik).
- [x] **A7.2b4** Headless CLI wypisuje wynik całej partii
      (`python -m tbb`/`run.sh`: zwycięzca albo remis, kod wyjścia 0).

## Kamień milowy 12 — morale w walce i ciągłość dynastii — UKOŃCZONE
> Morale księstw (w tym kara sukcesji) realnie steruje celnością stron bitwy
> w headless, party leczą rany w turze mapy, a bezhetmańskie księstwo wyznacza
> dziedzica prowadzącego do sukcesji.
- [x] **W12.2a** Leczenie ran party — `Party.tick_wounds`. *(task-056)*
- [x] **W12.2b** Leczenie party w turze mapy i driverze — `WorldMap.tick_parties`. *(task-057)*
- [x] **B12.1a** Morale per strona w auto-rozgrywce bitwy. *(task-058)*
- [x] **B12.1b-1** Per-strona morale w sygnaturach `WorldMap.resolve_*`. *(task-059)*
- [x] **B12.1b-2a** `assault_nearest_enemy_settlement` z `morale_by_owner`. *(task-061)*
- [x] **B12.1b-2b** `morale_by_owner` przez `take_duchy_military_action`/`take_duchy_turn`. *(task-062)*
- [x] **B12.1b-2c** Driver buduje mapę morale z `GameState` + DESIGN. *(task-063)*
- [x] **D12.3** Księstwo wyznacza dziedzica w turze — `ai.designate_duchy_heir`. *(task-064)*

## Kamień milowy 13 — minimalna warstwa wizualna (obserwator) — UKOŃCZONY
> Osobny pakiet `src/tbbui/` w czystym stdlib (SVG/HTML + `http.server`):
> deterministyczny layout i widok mapy strategicznej, pole bitwy heksowej,
> strona partii oraz przeglądarkowy podgląd z „następną turą". Rdzeń `tbb`
> nie importuje `tbbui`.
- [x] **V13.1** Pakiet `tbbui` + deterministyczny layout mapy. *(task-065)*
- [x] **V13.2a** Szkielet SVG mapy + węzły regionów. *(task-066)*
- [x] **V13.2b** Linie połączeń mapy SVG. *(task-067)*
- [x] **V13.2c** Znaczniki osad i party na mapie SVG. *(task-068)*
- [x] **V13.2d** Paleta kolorów właścicieli. *(task-069)*
- [x] **V13.3a** Geometria heksów pointy-top (`tbbui.hexgeom`). *(task-070)*
- [x] **V13.3b** `render_battle_svg` — pole bitwy heksowej. *(task-071)*
- [x] **V13.4a** `render_game_page` — strona HTML partii. *(task-072)*
- [x] **V13.4b** Snapshot partii z CLI (`python -m tbbui`). *(task-073)*
- [x] **V13.5a** `GameApp.handle` — routing podglądu (bez gniazda). *(task-074)*
- [x] **V13.5b** Serwer podglądu `http.server` + `python -m tbbui serve`. *(task-075)*

## Kamień milowy 21 — dokończenie czytelności strony w przeglądarce — UKOŃCZONY
> Widoczny tekst kalendarza i raportu bitwy oraz odróżnialne nagłówki sekcji
> rozkazów; refaktor emitera formularzy celu. Maszynowe `data-*` i routing bez
> zmian; rdzeń bez zmian.
- [x] **K21.1a** Czytelny tekst kalendarza (`Rok N, miesiąc M`) w `data-calendar`. *(task-109)*
- [x] **K21.1b** Czytelny tekst wyniku bitwy w `render_battle_report`. *(task-110)*
- [x] **K21.1c** Czytelne straty per strona w `render_battle_report`. *(task-111)*
- [x] **K21.2** Nagłówki sekcji rozkazów w `GET /` (`data-order-section`). *(task-112)*
- [x] **R21.1 (refaktor)** Wspólny emiter formularzy celu marsz/szturm/starcie. *(task-113)*

## Kamień milowy 22 — czytelny stan gospodarczo-wojskowy w podglądzie — UKOŃCZONY
> Czyste panele prezentacji gospodarki osad (pszenica/złoto, populacja, garnizon)
> i siły oddziałów na mapie, osadzone w stronie partii. Rdzeń bez zmian.
- [x] **K22.1a** Panel osad z zasobami (`render_settlement_panel`, `data-settlement-row`/`data-wheat`/`data-gold`). *(task-114)*
- [x] **K22.1b** Panel osad: populacja i garnizon (`data-population`/`data-free`/`data-garrison`). *(task-115)*
- [x] **K22.1c** Osadzenie panelu osad w `render_game_page`. *(task-116)*
- [x] **K22.2a** Panel party z siłą oddziału (`render_party_panel`, `data-party-row`/`data-size`). *(task-117)*
- [x] **K22.2b** Osadzenie panelu party w `render_game_page`. *(task-118)*

## Kamień milowy 23 — orientacja gracza w podglądzie (legenda + tożsamość) — ukończone przyrosty
> Czysta legenda właścicieli oraz maszynowe oznaczenie księstwa i osad gracza —
> opcjonalne, wsteczne przyrosty prezentacji. Rdzeń bez zmian. (K23.3b/task-124
> otwarte w BACKLOG.)
- [x] **K23.1a** Legenda właścicieli (`render_owner_legend`, `data-owner-legend`/`data-owner-legend-row`/`data-color`). *(task-119)*
- [x] **K23.1b** Osadzenie legendy w `render_game_page`. *(task-120)*
- [x] **K23.2a** Oznaczenie księstwa gracza w stronie (`render_game_page(..., player_duchy_id=None)`, `data-player-duchy` + prefiks `» `). *(task-121)*
- [x] **K23.2b** Przewleczenie `player_duchy_id` z `GameApp._render`. *(task-122)*
- [x] **K23.3a** Panel osad wyróżnia osady gracza (`render_settlement_panel(..., player_duchy_id=None)`, `data-player-owned`). *(task-123)*
- [x] **K23.3b** Przewleczenie `player_duchy_id` do panelu osad w `render_game_page`. *(task-124)*
- [x] **K24.1a** Panel party wyróżnia party gracza (`render_party_panel(..., player_duchy_id=None)`, `data-player-owned`). *(task-125)*
- [x] **K24.1b** Przewleczenie `player_duchy_id` do panelu party w `render_game_page`. *(task-126)*
- [x] **K24.2a** Legenda wyróżnia kolor gracza (`render_owner_legend(..., player_duchy_id=None)`, `data-player-owner` + prefiks `» `). *(task-127)*
- [x] **K24.2b** Przewleczenie `player_duchy_id` do legendy w `render_game_page`. *(task-128)*

## Kamień milowy 25 — czytelna siła bojowa w podglądzie (decyzje o walce) — UKOŃCZONY
> Zagregowana siła bojowa (HP + atak + obrona) w panelach party i osad z
> istniejących `Unit`; refaktor R25.1 scalił agregację w
> `tbbui.unitstrength.combat_totals`. Rdzeń `tbb` bez zmian.
- [x] **K25.1a** Panel party pokazuje siłę (HP) oddziału (`data-hp` = suma `Unit.hp` po bohaterze+podkomendnych; sufiks ` · siła: HP H`). *(task-129)*
- [x] **K25.1b** Panel party pokazuje atak i obronę oddziału (`data-attack`/`data-defense`; sufiks `, atak A, obrona D`). *(task-130)*
- [x] **K25.2a** Panel osad pokazuje siłę (HP) garnizonu (`data-garrison-hp`; sufiks ` · siła garnizonu: HP H`). *(task-131)*
- [x] **K25.2b** Panel osad pokazuje atak i obronę garnizonu (`data-garrison-attack`/`data-garrison-defense`; sufiks `, atak A, obrona D`). *(task-132)*
- [x] **R25.1 (refaktor)** Wspólny helper agregacji siły bojowej sekwencji `Unit` (`combat_totals`) reużyty przez oba panele. *(task-133)*

## Kamień milowy 26 — czytelny stan strukturalno-dynastyczny (budynki + władza) — UKOŃCZONY
> Panel osad dostał liczbę i nazwy aktywnych budynków (K26.1a–b) z
> `Settlement.active_buildings`, a wiersz księstwa flagi `data-hero`/`data-heir`
> (K26.2a–b) z `Duchy`. Rdzeń `tbb` bez zmian.
- [x] **K26.1a** Panel osad pokazuje liczbę aktywnych budynków (`data-buildings` = `len(active_buildings)`; sufiks ` · budynki: N`). *(task-134)*
- [x] **K26.1b** Panel osad wymienia nazwy aktywnych budynków (`data-building-names`; przy N>0 tekst ` (nazwa1, nazwa2)`). *(task-135)*
- [x] **K26.2a** Wiersz księstwa pokazuje obecność bohatera (`data-hero`; tekst `, bohater tak|nie`). *(task-136)*
- [x] **K26.2b** Wiersz księstwa pokazuje obecność dziedzica (`data-heir`; tekst `, dziedzic tak|nie`). *(task-137)*

## Kamień milowy 27 — czytelna gotowość bojowa (rany) i orientacja w układzie strony — UKOŃCZONY
> Panel party (K27.1a) i garnizonu osady (K27.2a) dostały liczbę rannych
> (`data-wounded` / `data-garrison-wounded`) z `Unit.wounds`; refaktor R27.1
> scalił licznik w `tbbui.unitstrength.wounded_count`; nagłówki sekcji strony
> (`<h2 data-panel-section="settlements|parties|duchies">`, K27.3a–b) odróżniają
> panele. Rdzeń `tbb` bez zmian.
- [x] **K27.1a** Panel party pokazuje liczbę rannych w oddziale (`data-wounded`; sufiks ` · ranni: W`). *(task-138)*
- [x] **K27.2a** Panel osad pokazuje liczbę rannych w garnizonie (`data-garrison-wounded`; sufiks ` · ranni: W`). *(task-139)*
- [x] **R27.1 (refaktor)** Wspólny licznik `tbbui.unitstrength.wounded_count`; bez nowych testów. *(task-140)*
- [x] **K27.3a** Nagłówek sekcji osad na stronie (`<h2 data-panel-section="settlements">Osady</h2>`). *(task-141)*
- [x] **K27.3b** Nagłówki sekcji party i księstw na stronie (`parties`/`duchies`). *(task-142)*

## Kamień milowy 28 — potwierdzenie skutku rozkazu gracza w podglądzie — UKOŃCZONY
> Po każdym rozkazie POST `GameApp` ustawia czytelny komunikat `<p data-notice>`
> na podstawie zmiany stanu (`wykonano`/`brak zmian`) lub powstania bitwy
> (`bitwa`), z celem w etykiecie; `POST /turn` daje datę po ruchu AI.
> `render_game_page` i rdzeń `tbb` bez zmian.
- [x] **K28.1a** Slot komunikatu rozkazu (`GameApp.last_notice`, `<p data-notice>`; świeży GET → pusty). *(task-143)*
- [x] **K28.1b** Komunikat skutku recruit/muster/develop (`wykonano`/`brak zmian` przez `_apply_player_order(transition, label)`). *(task-144)*
- [x] **K28.1c** Komunikat skutku marszu z nazwą celu (`Marsz do <region>` / `Marsz`). *(task-145)*
- [x] **K28.1d** Komunikat skutku szturmu i starcia (`bitwa`/`brak zmian` przez `_apply_player_assault_order(transition, label)`). *(task-146)*
- [x] **K28.1e** Komunikat następnej tury z datą po ruchu AI (`Następna tura: rok N, miesiąc M`). *(task-147)*

## Kamień milowy 29 — czytelny i zlokalizowany interfejs gracza (grywalny podgląd) — UKOŃCZONY
> Widoczny tekst komunikatu w ciele `<p data-notice>` (K29.1a) i pełna
> lokalizacja etykiet przycisków (K29.2a–b); refaktor R29.1 scalił guard
> księstwa gracza w `_resolve_player_duchy()`. Rdzeń `tbb`, `render_game_page`
> i routing bez zmian.
- [x] **K29.1a** Widoczny tekst komunikatu w ciele `<p data-notice>` (jak widoczny kalendarz K21.1a). *(task-148)*
- [x] **K29.2a** Polskie etykiety przycisków tury i rozwoju (`Następna tura`/`Rekrutuj`/`Zbierz oddział`/`Rozbuduj osadę`). *(task-149)*
- [x] **K29.2b** Polskie etykiety bare przycisków marsz/szturm/starcie (`Marsz`/`Szturm`/`Starcie`). *(task-150)*
- [x] **R29.1 (refaktor)** Wspólny guard `_resolve_player_duchy()` w `serve.py`; bez nowych testów. *(task-151)*

## Kamień milowy 30 — świadome decyzje gracza: podsumowanie księstwa + czytelny panel rozkazów — UKOŃCZONY
> Czysty prymityw `render_player_summary` (gospodarka K30.3a, siła K30.3b)
> osadzony w `render_game_page` (K30.3c); nagłówek sekcji „Rozwój" (K30.1a) i
> koszt złota na przycisku rekrutacji (K30.2a). Rdzeń `tbb` bez zmian.
- [x] **K30.1a** Nagłówek sekcji `<h2 data-order-section="develop">Rozwój</h2>` nad rozkazami recruit/muster/develop. *(task-152)*
- [x] **K30.2a** Koszt złota na przycisku „Rekrutuj" z `tbb.settlement.RECRUIT_GOLD_COST`. *(task-153)*
- [x] **K30.3a** Panel podsumowania księstwa gracza — gospodarka (`render_player_summary`: osady/oddziały/złoto/pszenica). *(task-154)*
- [x] **K30.3b** Panel podsumowania — łączna siła bojowa oddziałów (reużycie `combat_totals`). *(task-155)*
- [x] **K30.3c** Osadzenie podsumowania w `render_game_page` (bez gracza → bajt-w-bajt jak dotąd). *(task-156)*

## Kamień milowy 31 — grywalna pełna partia w przeglądarce: nowa gra + wynik z perspektywy gracza — UKOŃCZONY
> DESIGN §11 (PLAN K31): restart `POST /new` + przycisk „Nowa gra" + seed w CLI
> serve oraz czytelny wynik z perspektywy gracza w `render_game_page`. Domyka
> pętlę §6 w przeglądarce: partię można rozegrać, zakończyć, odczytać wynik i
> zacząć od nowa bez restartu procesu. Rdzeń `tbb` bez zmian.
- [x] **K31.1a** Restart partii przez `POST /new` (GameApp `seed`; reset do świeżej deterministycznej gry). *(task-157)*
- [x] **K31.1b** Przycisk „Nowa gra" w `GET /` (`<form action="/new">`). *(task-158)*
- [x] **K31.1c** CLI `python -m tbbui serve` przekazuje `seed=HEADLESS_SEED` do `GameApp`. *(task-159)*
- [x] **K31.2a** Wynik gry z perspektywy gracza w `render_game_page` (`data-player-result-text`). *(task-160)*

## Kamień milowy 32 — dokończenie ramy strony i czytelnego końca gry — UKOŃCZONY
> DESIGN §11: tytuł dokumentu, widoczny nagłówek strony i linia celu w
> `render_game_page` oraz ukrycie tury/rozkazów w `GET /` po `is_over`
> (zostaje „Nowa gra"). Rdzeń `tbb` bez zmian.
- [x] **K32.1a** Tytuł dokumentu `<head><title>Total Battle Brothers</title></head>` w `render_game_page`. *(task-161)*
- [x] **K32.1b** Widoczny nagłówek strony `<h1 data-page-title>` na początku `<body>`. *(task-162)*
- [x] **K32.1c** Linia celu gry `<p data-objective>` pod nagłówkiem. *(task-163)*
- [x] **K32.2a** `GET /` ukrywa turę i sekcje rozkazów gdy `game.is_over` (zostaje „Nowa gra"). *(task-164)*

## Kamień milowy 33 — czytelny postęp do celu (warunki zwycięstwa na oczach gracza) — UKOŃCZONY
> DESIGN §11: czysty prymityw `render_victory_progress` (licznik
> `data-enemies-remaining`, wiersze per-wróg `data-enemy-duchy`, flaga
> `data-defeated` z sufiksem „— pokonany"), osadzony w `render_game_page` przy
> `player_duchy_id`. Rdzeń `tbb` bez zmian.
- [x] **K33.1a** Prymityw `render_victory_progress` — licznik `data-enemies-remaining` + tekst. *(task-165)*
- [x] **K33.1b** Wiersze per-wróg `data-enemy-duchy` (`data-settlements`/`data-hero` + tekst). *(task-166)*
- [x] **K33.1c** Osadzenie panelu w `render_game_page` (bez gracza → bajt-w-bajt jak dotąd). *(task-167)*
- [x] **K33.2a** Flaga `data-defeated` + sufiks „— pokonany" w wierszu wroga. *(task-168)*

## Kamień milowy 34 — podpowiedź następnego kroku do zwycięstwa — UKOŃCZONY
- [x] **K34.1a** Prymityw `render_next_objective(game, player_duchy_id)` — `data-next-objective` + tekst zależny od stanu. *(task-170)*
- [x] **K34.1b** Osadzenie w `render_game_page` po `data-victory-progress` (bez gracza → bajt-w-bajt jak dotąd). *(task-171)*

## Kamień milowy 35 — lokalizacja wrogiego bohatera (lista pościgu) — UKOŃCZONY
- [x] **K35.1a** Prymityw `render_enemy_hero_locator` — `data-hero-locator`/`data-heroes-on-map`, wiersze `data-enemy-duchy`/`data-hero-region`. *(task-172)*
- [x] **K35.1b** Osadzenie w `render_game_page` po `data-next-objective` (bez gracza → bajt-w-bajt jak dotąd). *(task-173)*

## Kamień milowy 36 — pościg za wrogim bohaterem: dystans marszu do celu — UKOŃCZONY
- [x] **K36.1a** Prymityw `ai.region_distance(world, start, target)` — BFS dystans grafu regionów. *(task-174)*
- [x] **K36.1b** Prymityw `render_hero_chase(world, game, player_duchy_id)` — `data-hero-chase` + wiersze `data-enemy-duchy`/`data-distance`. *(task-175)*
- [x] **K36.1c** Osadzenie w `render_game_page` po `data-hero-locator` (bez gracza → bajt-w-bajt jak dotąd). *(task-176)*
- [x] **K36.2a** Oznaczenie celu w zasięgu (`data-in-reach` + sufiks „ — w zasięgu" dla dystansu 1). *(task-177)*

## Kamień milowy 37 — świadoma decyzja o walce: podgląd siły celu przed atakiem — UKOŃCZONY
- [x] **K37.1a** Prymityw `render_engagement_preview` — `data-engagement-preview`/`data-player-on-map`/`data-own-*` + wiersze sąsiednich wrogich osad (`data-enemy-*`). *(task-178)*
- [x] **K37.1b** Flaga przewagi `data-advantage="true|false"` + sufiks „ — przewaga"/„ — niekorzystnie". *(task-179)*
- [x] **K37.1c** Osadzenie w `render_game_page` po `data-hero-chase` (bez gracza → bajt-w-bajt jak dotąd). *(task-180)*
- [x] **K37.2a** Rozszerzenie o sąsiednie wrogie party (`data-target-kind="party"`; osada przed party w regionie). *(task-181)*
- [x] **R37.1 (refaktor)** Wspólny helper `tbbui.maplookup.first_party_region` reużyty przez `herolocator`/`herochase`/`engagementpreview` (bez nowych testów paneli). *(task-182)*

## Kamień milowy 38 — czytelny skutek tury AI (dziennik zmian) — UKOŃCZONY
- [x] **K38.1a** Prymityw `render_turn_summary(before, after)` — korzeń `data-turn-summary`/`data-changed` + tekst „Zmiany w tej turze: tak|nie" (bez wierszy). *(task-183)*
- [x] **K38.1b** Wiersze per-księstwo `data-turn-duchy` (`data-settlements-before/after`, `data-hero-before/after`) + `data-change-count`. *(task-184)*
- [x] **K38.1c** Osadzenie w `render_game_page` przez opcjonalny `previous_game` (po `data-calendar`; `None` → bajt-w-bajt jak dotąd). *(task-185)*
- [x] **K38.2a** `GameApp.previous_game` zapisywany po `POST /turn`, zerowany przez inne rozkazy/`/new`; przewleczony do `render_game_page`. *(task-186)*
- [x] **R38.1 (refaktor)** Wspólny helper `tbbui.gamelookup.player_duchy` reużyty przez 6 paneli (bez nowych testów paneli). *(task-187)*

## Kamień milowy 39 — ostrzeżenie o zagrożeniu obronnym (gdzie się bronić) — UKOŃCZONY
- [x] **K39.1a** Prymityw `render_threat_alert` — korzeń `data-threat-alert`/`data-threats` + tekst „Zagrożone pozycje: N" (bez wierszy). *(task-188)*
- [x] **K39.1b** Wiersze per zagrożona pozycja `data-threatened-region` (`data-threatened-kind`, `data-enemy-region`, `data-enemy-owner`) + tekst. *(task-189)*
- [x] **K39.1c** Osadzenie w `render_game_page` po `data-engagement-preview` (bez gracza → bajt-w-bajt jak dotąd). *(task-190)*
- [x] **K39.2a** Siła obronna własnej pozycji (`data-own-*`) i wroga (`data-enemy-*`) w wierszu + sufiks tekstu. *(task-191)*
- [x] **K39.2b** Flaga `data-defensible="true|false"` + sufiks „ — obronisz się"/„ — przewaga wroga". *(task-192)*

## Kamień milowy 16 — obserwowalna bitwa gracza w podglądzie — UKOŃCZONY
- [x] **K16.1a** Strona partii z opcjonalnym slotem SVG bitwy (`render_game_page(..., battle=None)`). *(task-091)*
- [x] **K16.1b** Rdzeń: nagrana wersja szturmu osady (`resolve_settlement_battle_recorded → (WorldMap, HexBattle)`). *(task-092)*
- [x] **K16.1c** Prymityw AI szturmu na wskazaną osadę zwraca bitwę (`ai.assault_duchy_party_to_recorded`). *(task-093)*
- [x] **K16.1d-1** Prymityw AI auto-szturmu z nagraniem (`ai.assault_duchy_party_recorded`). *(task-095)*
- [x] **K16.1d-2** `GameApp` nagrywa i renderuje ostatnią bitwę po szturmie (`last_battle`). *(task-096)*
- [x] **K16.1d-3** Inne rozkazy i `POST /turn` czyszczą `last_battle`. *(task-097)*

## Kamień milowy 40 — skrót sytuacji taktycznej (bronić się czy atakować) — UKOŃCZONY
- [x] **R39.1 (refaktor)** Wspólny predykat „wrogie party u sąsiada" `tbbui.maplookup.is_hostile_owner` reużyty przez `threatalert`/`engagementpreview` (bez nowych testów). *(task-193)*
- [x] **K40.1a** Prymityw `render_situation_report` — korzeń `data-situation-report`/`data-threatened-count` + tekst „Sytuacja: zagrożone pozycje N". *(task-194)*
- [x] **K40.1b** `data-opportunity-count` (korzystne cele z przewagą) + rozszerzenie tekstu. *(task-195)*
- [x] **K40.1c** Osadzenie w `render_game_page` po `data-threat-alert` (bez gracza → bajt-w-bajt jak dotąd). *(task-196)*
- [x] **K40.2a** Flaga `data-net-posture="offensive|defensive|balanced"` + sufiks postawy. *(task-197)*

## Kamień milowy 41 — zalecany następny rozkaz (rada wykonalna) — UKOŃCZONY
- [x] **K41.1a** Prymityw `render_recommended_action` — korzeń `data-recommended-action`/`data-posture` + ogólny tekst zalecenia; `situationreport.net_posture` publiczny. *(task-198)*
- [x] **K41.1b** Zalecenie ofensywne z celem (`engagementpreview.first_advantageous_target`): „szturmuj osadę <R>"/„zaatakuj oddział <R>". *(task-199)*
- [x] **K41.1c** Zalecenie defensywne z regionem (`threatalert.first_threatened_region`): „broń pozycji <R>". *(task-200)*
- [x] **K41.2a** Maszynowa flaga `data-action="assault|engage|defend|develop"` po `data-posture`. *(task-201)*
- [x] **K41.3a** Osadzenie w `render_game_page` po `data-situation-report` (bez gracza → bajt-w-bajt jak dotąd). *(task-202)*

## Kamień milowy 42 — wykonalny zalecany rozkaz (rada w jeden klik) — UKOŃCZONY
- [x] **K42.1a** Czysty `recommended_order(world, game, player_duchy_id)` → `(action, target|None)|None`; `render_recommended_action` deleguje (bajt-w-bajt jak dotąd). *(task-203)*
- [x] **K42.1b** Mapa `serve.recommended_order_path(action)`: assault→`/order/assault`, engage→`/order/engage`, defend→`/order/march`, develop→`/order/develop`. *(task-204)*
- [x] **K42.1c** GameApp osadza jeden `<form data-recommended-order>` w `GET /` (action=path+target, przed `data-order-section="develop"`; guardy gracz/`is_over`/`None`). *(task-205)*
- [x] **K42.2a** `recommended_order_text(action, target)` + przycisk „Wykonaj zalecenie: <opis>"; `render_recommended_action` reużywa (bajt-w-bajt jak dotąd). *(task-206)*

## Kamień milowy 43 — dziennik rozkazów gracza (pamięć kampanii w podglądzie) — UKOŃCZONY
- [x] **R43.1 (refaktor)** Kompaktacja DESIGN.md do stanu obecnego: §11 nie powiela per-funkcyjnych kontraktów `data-*` z ARCHITECTURE.md; bez utraty żadnej reguły; bez nowych testów. *(task-207)*
- [x] **K43.1a** Czysty `orderlog.render_order_log(entries)` → `<div data-order-log data-count=N>` + dzieci `data-order-log-entry` (ciało escapowane). *(task-208)*
- [x] **K43.1b** `GameApp.order_log` (init `[]`) — każdy POST znaną trasą dokłada `last_notice`; `POST /new` czyści i zapisuje wpis startowy. *(task-209)*
- [x] **K43.1c** `GameApp._render` osadza jeden `render_order_log(self.order_log)` w `GET /`, także przy `is_over`. *(task-210)*
- [x] **K43.2a** `serve.ORDER_LOG_LIMIT` (placeholder `10`) — dziennik przycięty do ostatnich N wpisów (najstarsze wypadają). *(task-211)*

## Kamień milowy 44 — czytelny, zakotwiczony w czasie dziennik kampanii — UKOŃCZONY
- [x] **K44.1a** Czysty `orderlog.format_log_entry(notice, calendar)` → `f"Rok {year}, miesiąc {month} — {notice}"` (bez escapowania, bez mutacji). *(task-212)*
- [x] **K44.1b** `GameApp._append_order_log` dokłada `format_log_entry(notice, self.calendar)` (wpis z prefiksem daty); `data-notice` i limit bez zmian. *(task-213)*
- [x] **K44.2a** `render_order_log` osadza pierwszy nagłówek `<h2 data-order-log-header>Dziennik rozkazów</h2>`; `data-count`/wpisy bez zmian. *(task-214)*
- [x] **K44.2b** `render_order_log` dla pustej sekwencji dokłada `<p data-order-log-empty>Brak rozkazów w tej kampanii</p>`; niepusta → brak elementu. *(task-215)*

## Kamień milowy 45 — dziennik kampanii: najnowsze na wierzchu, objętość i skróty — UKOŃCZONY
- [x] **K45.1a** `render_order_log` wypisuje `data-order-log-entry` w kolejności `reversed(entries)` (najnowszy pierwszy); `data-count`, escaping, nagłówek i stan pusty bez zmian. *(task-216)*
- [x] **K45.2a** Najnowszy (pierwszy) wpis niesie `data-order-log-latest=""` i badge `<span data-order-log-latest-badge="">najnowszy</span>` przed ciałem; pozostałe bez tego. *(task-217)*
- [x] **K45.3a** Nagłówek `<h2 data-order-log-header="">Dziennik rozkazów ({N})</h2>` (N=`len(entries)`, także 0); `data-count`/dzieci bez zmian. *(task-218)*
- [x] **K45.4a** `render_order_log(entries, at_limit=False)`: `at_limit=True` + niepusta → jedno `<p data-order-log-truncated="">Pokazano ostatnie wpisy</p>` po ostatnim wpisie; inaczej brak (bajt-w-bajt jak dotąd). *(task-219)*
- [x] **K45.4b** `GameApp._render` woła `render_order_log(self.order_log, at_limit=len(self.order_log) >= ORDER_LOG_LIMIT)`; `data-order-log-truncated` iff dziennik osiągnął limit. *(task-220)*

## Kamień milowy 46 — czytelny wynik rozkazu bitewnego gracza (dziennik/komunikat) — UKOŃCZONY
- [x] **K46.1a** `tbbui.battlereport.battle_outcome_text(battle)` z perspektywy atakującego: `ATTACKER_WIN`→`"zwycięstwo"`, `DEFENDER_WIN`→`"porażka"`, `DRAW`→`"remis"`; nierozstrzygnięta → `ValueError`; czysty. *(task-221)*
- [x] **K46.1b** `_apply_player_assault_order` przy bitwie ustawia `last_notice = f"{label}: {battle_outcome_text(battle)}"` (szturm+starcie), zamiast literału „bitwa". *(task-222)*
- [x] **K46.2a** `tbbui.battlereport.attacker_losses(battle)` = `len(battle.report().attacker.fallen)`; nierozstrzygnięta → `ValueError`; czysty. *(task-223)*
- [x] **K46.2b** `_apply_player_assault_order` przy bitwie ustawia `last_notice = f"{label}: {battle_outcome_text(battle)} (straty: {attacker_losses(battle)})"`. *(task-224)*

## Kamień milowy 47 — pełny bilans strat bitwy gracza (obie strony) — UKOŃCZONY
- [x] **K47.1a** `tbbui.battlereport.defender_losses(battle)` = `len(battle.report().defender.fallen)`; nierozstrzygnięta → `ValueError`; czysty. *(task-225)*
- [x] **K47.1b** `_apply_player_assault_order` przy bitwie ustawia `last_notice = f"{label}: {battle_outcome_text(battle)} (straty: {attacker_losses(battle)}, wróg: {defender_losses(battle)})"`. *(task-226)*
