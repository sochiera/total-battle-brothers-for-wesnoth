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
