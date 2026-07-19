# BACKLOG ARCHIVE — Total Battle Brothers

> Ukończone zadania przeniesione z `BACKLOG.md`, by kolejka robocza nie puchła.
> Szczegóły decyzji mechaniki/architektury żyją w `docs/DESIGN.md` i
> `docs/ARCHITECTURE.md`. Tu zostaje jedynie ślad, co i kiedy zamknięto.

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
