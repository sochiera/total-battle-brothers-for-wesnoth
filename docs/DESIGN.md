# DESIGN — Total Battle Brothers (nazwa robocza)

> **Dokument żywy.** To jest źródło prawdy o *mechanice i wizji* gry. Każdy agent,
> który zmienia zasady rozgrywki, aktualizuje ten plik w tym samym kroku co kod.
> Decyzje techniczne (język, struktura, komendy) mieszkają w `ARCHITECTURE.md`.
> Kolejka pracy mieszka w `../BACKLOG.md`.

## 1. Pitch
Single-player **sandbox** (bez scenariuszowej kampanii): turowa strategia łącząca
zarządzanie osadami i armiami z taktycznymi bitwami na heksach, w stylu **Battle
for Wesnoth** i **Battle Brothers**. Gracz prowadzi jedno księstwo przeciw
księstwom sterowanym przez **AI**. Skala kameralna: małe osady, nieliczne wojska,
każda jednostka się liczy.

## 2. Klimat i ton
Średniowiecze **bez magii i fantastyki**. Surowy, realistyczny ton. Śmierć jest
prawdziwa i najczęściej permanentna.

## 3. Struktura rozgrywki — dwie warstwy
Gra ma dwie sprzężone warstwy. Rdzeń logiki obu jest oddzielony od prezentacji
(patrz `ARCHITECTURE.md`) i budowany w TDD.

### 3.1 Warstwa strategiczna (mapa świata, turowa)
- **Mapa** w stylu **Total War**: regiony/prowincje z osadami. Party (armia)
  przemieszcza się po mapie kosztem punktów ruchu / tur.
- **Bitwa** startuje przy kontakcie party z wrogą osadą lub wrogim party.
- **Czas:** 1 tura = **1 miesiąc**. Rok = **13 miesięcy po 4 tygodnie**
  (52 tygodnie). Trening i wyposażenie mierzone są w miesiącach.
- **Bohater:** dokładnie **jeden** na księstwo — król i dowódca w jednym. Armia
  rusza się **wyłącznie** razem z bohaterem. Bez bohatera jednostki stoją; mogą
  zostać w osadzie jako **garnizon** (obrona).
- **Party:** bohater prowadzi maksymalnie **12 jednostek**.
- **Następstwo:** gdy bohater ginie, przejmuje **wyznaczony dziedzic**. Osady i
  wojownicy tracą wtedy **morale**, ale gra toczy się dalej.
- **Przegrana:** utrata **wszystkich** osad **oraz** brak bohatera (zginął i nie
  ma dziedzica ani osady, z której dałoby się wystawić nowego).
- **Strony:** każde księstwo (gracza i AI) startuje z **1–3 osadami** w różnym
  stopniu rozwoju. Brak neutralnych band — przeciwnikami są księstwa AI.

### 3.2 Warstwa bitwy (heksy, turowa)
- Turowa, na siatce **heksów**. Gracz steruje pojedynczymi jednostkami.
- **Teren** ma znaczenie — modyfikatory (obrona/celność/koszt ruchu).
  **ROZSTRZYGNIĘTE (B4.1, katalog placeholder):** `Terrain` to niemutowalny typ
  z trzema polami całkowitymi: `move_cost` (koszt wejścia na heks, `≥ 1`),
  `defense_mod` (modyfikator obrony jednostki stojącej na heksie) i `accuracy_mod`
  (modyfikator celności). Startowy katalog: **Plains** (`move_cost=1`, `defense_mod=0`,
  `accuracy_mod=0` — neutralna baza), **Forest** (`move_cost=2`, `defense_mod=+2`,
  `accuracy_mod=-1` — osłona, ale utrudnia celowanie), **Hills** (`move_cost=2`,
  `defense_mod=+1`, `accuracy_mod=+1` — wysoka pozycja). Pole bitwy (`Battlefield`)
  to rzadkie odwzorowanie `Hex → Terrain` z **domyślnym terenem Plains** dla heksów
  bez nadpisania; zwraca modyfikatory przez zapytania (`terrain_at`, `move_cost_at`,
  `defense_at`, `accuracy_at`). **NADAL OTWARTE:** dokładna semantyka aplikowania
  modyfikatorów w walce (czy `accuracy_mod` obrońcy obniża celność atakującego, czy
  własną) dochodzi w **B4.3**; granice/kształt planszy oraz strojenie wartości —
  później.
- **Jednostki dystansowe** obecne (model jak w Wesnoth / Battle Brothers).
- **Morale** wpływa **wyłącznie na celność** (bonus/kara do trafienia). Morale
  **nie** powoduje ucieczek.
- **Śmierć permanentna.** Alternatywnie zamiast zginąć jednostka może zostać
  **ogłuszona** i odnieść **ranę** — trwałą lub czasową.

## 4. Osady, populacja, ekonomia
- **Surowce (dokładnie dwa, celowo prosto):** **pszenica** i **złoto**.
- **Populacja** to kluczowy wskaźnik osady. Rośnie przez **urodzenia** i
  **imigrantów**.
- Populacja to **pula ludzi**, którą zajmują:
  - **rekrutacja jednostek** — każda jednostka pochodzi z populacji osady;
  - **obsada budynków** — np. kowal jest mieszkańcem osady; zbyt mała populacja
    **nie pozwala uruchomić** danego warsztatu. Każdy typ budynku ma **stałą
    liczbę obsady** (`staff`) — tyle populacji zajmuje, gdy działa (E2.2).
- **Zwolnienie populacji:** zamknięcie/opuszczenie budynku oddaje zajmowaną
  populację z powrotem do puli.
- Gracz rozwija osady (budynki), zakłada nowe, może podbijać osady AI.

## 5. Jednostki i progresja
Jakość jednostki wynika z **trzech niezależnych filarów** (każdy z osobnym
wskaźnikiem):
- **Trening** — czas + odpowiednie budynki. Silny zysk na starcie, potem malejący
  (najszybciej się „nasyca" z trzech).
- **Uzbrojenie** — surowce + czas/budynki. Podobnie malejący zysk.
- **Doświadczenie** — **wyłącznie z walki**. Wpływ nieco słabszy niż dwa powyższe.

Filary są niezależne: jednostka może być dobrze wytrenowana, ale słabo uzbrojona
itd. Statystyki bojowe (celność, obrażenia, obrona, HP) są funkcją tych filarów.

**ROZSTRZYGNIĘTE (U3.1, minimalne mapowanie — placeholder):** `Unit` to niemutowalna
encja z trzema filarami całkowitymi i nieujemnymi { training, equipment, experience }.
Statystyki pochodne liczone **liniowo** (waga 1, bez krzywych malejącego zysku — te
dochodzą w U3.2), każdy filar wpływa na **rozłączny** podzbiór statystyk, by
niezależność filarów była testowalna:
- `hp` = `10 + training` (trening = kondycja/wytrzymałość),
- `accuracy` (celność) = `training + experience` (doświadczenie wspiera celność),
- `damage` (obrażenia) = `equipment` (uzbrojenie),
- `defense` (obrona) = `equipment + experience`.

Osłabiona waga doświadczenia (§5: „wpływ nieco słabszy") w mapowaniu filar→statystyka
pozostaje refaktorem na później; **U3.2** dotyczy odrębnego mapowania **nakład→poziom
filaru** z malejącym zyskiem (patrz §10) — samo mapowanie filar→statystyka zostaje
liniowe. Stan bojowy jednostki
{ hp bieżące, wounds[], stunned } dochodzi przy warstwie bitwy (kamień milowy 4).

## 6. Pętla rozgrywki (MVP)
Najmniejsza grywalna pętla, single-player vs **jedno** księstwo AI:
1. Twoje księstwo: 1 osada z populacją, pszenicą i złotem; naprzeciw księstwo AI.
2. **Rozwój:** rekrutuj jednostki z populacji, trenuj i wyposażaj (surowce +
   miesiące).
3. **Marsz:** bohater prowadzi party do wrogiej osady/party; garnizon może zostać
   w obronie.
4. **Bitwa** na heksach: teren, walka wręcz + dystans, morale→celność,
   ogłuszenia/rany, śmierć permanentna.
5. **Cel sandboxa:** pokonać księstwo AI (utrata jego osad **oraz** bohatera).

## 7. Model danych (szkic — do rozwijania)
Wstępne encje rdzenia (nazwy robocze, doprecyzowywane wraz z implementacją):
- `Resources` — { wheat, gold }. Wartości całkowite (jednostki surowca), nigdy
  ujemne. Niemutowalna: operacje (`add`/`subtract`) zwracają **nowy** `Resources`
  (§8, czyste przejścia stanu). Odjęcie ponad stan jest błędem, chyba że jawnie
  dopuszczone (wtedy podłoga na zero).
- `Unit` — filary { training, equipment, experience } → statystyki pochodne;
  stan { hp, wounds[], stunned }.
- `Settlement` — populacja (pula + zajęte), budynki, garnizon, **magazyn surowców**
  (`storage: Resources`, domyślnie pusty). Ekonomia miesięczna to czyste przejście
  stanu zwracające nową osadę (§4, E2.3). **ROZSTRZYGNIĘTE (U3.3, rekrutacja):**
  osada trzyma zrekrutowane jednostki w `garrison: tuple[Unit, ...]`. `recruit()`
  to czyste przejście: **zajmuje 1 populację** z puli wolnej (przez `occupy(1)` —
  żołnierz jest mieszkańcem osady, więc `population` bez zmian, rośnie `occupied`)
  i dokłada `Unit` do garnizonu. Bez argumentu tworzy **świeżego rekruta** `Unit()`
  (filary 0). Brak wolnej populacji **blokuje** rekrutację (`ValueError`). Koszt
  surowców/miesięcy rekrutacji i przenoszenie jednostek do party dochodzą później.
- `Duchy` (księstwo) — bohater, dziedzic, lista osad, party, morale.
- `Party` — bohater + ≤12 jednostek, pozycja na mapie, punkty ruchu.
- `WorldMap` — regiony/prowincje, osady, pozycje party.
- `HexBattle` — siatka heksów, teren, jednostki, kolejka tur, rozstrzyganie walki.
  **ROZSTRZYGNIĘTE (B4.2a, deployment):** `HexBattle` to niemutowalny stan bitwy
  łączący `Battlefield` (teren) z **rozstawieniem** jednostek jako mapa `Hex → Unit`
  (co najwyżej **jedna jednostka na heks**). `deploy(unit, position)` to czyste
  przejście: zwraca **nowy** `HexBattle` z jednostką na wskazanym heksie; wejście na
  **zajęty** heks jest błędem (`ValueError`). Zapytania: `unit_at(position)`
  (jednostka lub `None`), `is_occupied(position)`, `units` (deterministyczna mapa
  pozycji → jednostka); teren dostępny przez `battlefield`. Jednostki są
  identyfikowane przez **pozycję** (nie tożsamość obiektu), bo równe `Unit` są
  nierozróżnialne — dlatego ruch (B4.2b) będzie operował na heksach źródłowym i
  docelowym. **Poza B4.2a:** ruch i punkty ruchu (B4.2b), granice/kształt planszy,
  kolejka tur i rozstrzyganie walki (B4.3+).
- `Rng` — deterministyczny, seedowalny generator (dla powtarzalnych testów).

## 8. Zasady projektowe
- **Determinizm:** cała losowość przez wstrzykiwany, seedowalny RNG — bitwy i
  tury muszą być odtwarzalne w testach.
- **Rdzeń bez prezentacji:** logika nie importuje niczego z warstwy UI/render.
- **Małe, czyste funkcje/przejścia stanu** zamiast wielkich metod z efektami
  ubocznymi — łatwiejsze do testowania.

## 9. Poza zakresem (na start)
Scenariuszowa kampania/fabuła, multiplayer sieciowy, magia/fantastyka, oddziały
masowe (np. 60 ludzi w jednostce), zaawansowana grafika i dźwięk, edytor map.

## 10. Otwarte pytania (do rozstrzygnięcia w trakcie)
Oznaczone, bo decyzja nie jest przesądzona — rozstrzygać przy okazji zadań, które
ich dotykają, i notować wynik tutaj:
- ~~**Geometria heksów:** offset vs axial/cube coords?~~ **ROZSTRZYGNIĘTE (C1.3):**
  rdzeń używa **współrzędnych axial** `(q, r)` z konwersją do **cube** `(x, y, z)`,
  gdzie `x+y+z=0`, do liczenia dystansu i sąsiadów. Offset zostaje wyłącznie dla
  przyszłej warstwy prezentacji.
- ~~**Krzywe malejącego zysku** dla treningu/uzbrojenia/doświadczenia — konkretny
  wzór i parametry.~~ **CZĘŚCIOWO ROZSTRZYGNIĘTE (U3.2, trening/uzbrojenie):**
  poziom filaru **narasta z zainwestowanego nakładu** (miesiące treningu dla
  `training`; jednostki „surowiec·miesiąc" dla `equipment`) z **malejącym zyskiem
  krańcowym**. Model minimalny, całkowity, deterministyczny (bez RNG): osiągnięcie
  poziomu `n` wymaga **skumulowanego** nakładu `T(n) = n·(n+1)/2` (liczby
  trójkątne), więc koszt przejścia `n → n+1` to `n+1` (rośnie liniowo → przyrost
  krańcowy maleje). Wzór odwrotny: `level(inv) = (isqrt(8·inv + 1) − 1) // 2`,
  monotoniczny niemalejący w `inv`, `level(0) = 0`. Doświadczenie ma **inne
  źródło** (tylko walka) — jego krzywa dochodzi przy warstwie bitwy (kamień 4).
  **NADAL OTWARTE:** różne parametry stromości per filar (trening vs uzbrojenie)
  oraz wpływ budynków/mnożników — strojenie przy balansie.
- **Wzór na trafienie:** bazowa celność + teren + morale → prawdopodobieństwo.
- **Model ran:** ile rodzajów, jak wpływają na statystyki, czasowe vs trwałe.
- **Wzrost populacji:** ~~urodzenia~~ **CZĘŚCIOWO ROZSTRZYGNIĘTE (E2.4a, urodzenia):**
  każda osada ma **sufit** `capacity` (max populacji; `None` = brak limitu). Faza
  **wzrostu** następuje po produkcji (§10 kolejność faz) i jest osobnym przejściem
  `tick_growth()` na stanie **po** `tick_economy`. Reguła urodzeń (minimalna,
  deterministyczna): osada **najedzona** (po bilansie miesięcznym `storage.wheat > 0`,
  czyli jest nadwyżka/zapas pszenicy) i **poniżej sufitu** rośnie o **+1 populacji**
  na turę; głodująca (`storage.wheat == 0`) **nie** rośnie; wzrost nigdy nie przekracza
  `capacity`. Nowi mieszkańcy trafiają do puli **wolnej** (nie zmieniają `occupied`).
  Urodzenia **nie** konsumują dodatkowo pszenicy — nadwyżka jest **warunkiem**, nie
  kosztem (uproszczenie do rewizji przy balansie).
  **ROZSTRZYGNIĘTE (E2.4b, imigranci):** dobrobyt przyciąga osadników. Sygnałem jest
  **złoto** (odrębnie od urodzeń, keyowanych na pszenicę). Reguła (minimalna,
  deterministyczna): osada **zamożna** (`storage.gold > 0`) i **najedzona**
  (`storage.wheat > 0`) i **poniżej sufitu** zyskuje **+1 populacji** na turę,
  która trafia do puli **wolnej** (nie zmienia `occupied`). Imigracja **nie**
  konsumuje złota (nadwyżka jest warunkiem, nie kosztem — jak przy urodzeniach)
  i **nigdy** nie przekracza `capacity`. Imigracja to osobne przejście
  `tick_immigration()` w fazie **wzrostu**, stosowane **po** `tick_growth()`
  (urodzenia), na stanie po `tick_economy`. **NADAL OTWARTE:** tempo urodzeń
  i imigracji > 1/turę przy dużej nadwyżce (skalowanie z zamożnością).
- ~~**Ekonomia:** produkcja pszenicy/złota per budynek, konsumpcja, bilans.~~
  **ROZSTRZYGNIĘTE (E2.3, minimalny model):** każdy **aktywny** (obsadzony) budynek
  produkuje swój stały `output: Resources` na turę (miesiąc); budynek zamknięty nie
  produkuje. **Konsumpcja:** cała populacja (wolna + zajęta) je pszenicę — **1
  pszenica / mieszkaniec / miesiąc**; złoto nie jest konsumowane. **Bilans miesięczny:**
  `storage = storage + Σ output_aktywnych − konsumpcja`; niedobór pszenicy jest
  **podłogowany na zero** (skutki głodu — spadek populacji/morale — poza E2.3).
  Startowy katalog: **Farm** (`wheat=3`, `staff=1`), **Market** (`gold=2`, `staff=1`);
  **Smith** nie produkuje surowców (`output` zerowy — to budynek uzbrojenia, M3).
- **AI księstw:** poziom ambicji dla MVP (od skryptowego „rozwijaj i atakuj").
- **Zakończenie tury na mapie:** kolejność faz (produkcja → wzrost → ruch → bitwy).
