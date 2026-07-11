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
- **ROZSTRZYGNIĘTE (M5.1a, minimalna mapa świata):** warstwa strategiczna jest
  skończonym, niemutowalnym **grafem regionów**. `Region` jest identyfikowany
  przez niemutowalną wartość `name`, a jawne połączenia są dwukierunkowe; ruch
  między niesąsiadującymi regionami nie jest bezpośrednio możliwy. Region może
  zawierać najwyżej jedną `Settlement`, ale może też być pusty. Kolejność regionów
  zadana przy tworzeniu mapy wyznacza deterministyczną kolejność zapytań o
  sąsiadów. Pozycje party, koszty ruchu i przejście ruchu dochodzą osobno w M5.1b
  i M5.2b, po utworzeniu modelu `Party` w M5.2a.
- **ROZSTRZYGNIĘTE (M5.1b, minimalne pozycje party):** pozycją party jest region,
  a `WorldMap` przechowuje niemutowalne odwzorowanie `Region → Party`. W regionie
  może znajdować się najwyżej jedno party; osada nie zajmuje tego samego slotu,
  więc party może wejść do regionu z osadą (kontakt zostanie rozstrzygnięty
  w M5.3). `party_at(region)` jest podstawowym zapytaniem o pozycję/obsadę,
  a `place_party()` to czyste przejście do nowej mapy, odrzucające region spoza
  grafu i region zajęty. Ruch, punkty ruchu i rozstrzyganie próby wejścia do
  regionu z wrogim party pozostają w M5.2b–M5.3.
- **ROZSTRZYGNIĘTE (M5.2b, minimalny ruch party):** pojedyncze przejście ruchu
  przenosi całe party (bohatera razem z podkomendnymi) z regionu źródłowego do
  wolnego, bezpośrednio sąsiedniego regionu. Każde połączenie ma na tym etapie
  jednolity koszt **1 punktu ruchu**, a dostępny budżet jest jawnym argumentem
  przejścia i musi wynosić co najmniej 1. Ruch tworzy nową `WorldMap`; mapa
  wejściowa, osady i ich garnizony pozostają bez zmian. Wejście do regionu już
  zajętego przez party jest jeszcze odrzucane — kontakt z wrogiem i rozpoczęcie
  bitwy zastąpią tę regułę w M5.3. Przechowywanie oraz odnawianie punktów ruchu,
  różne koszty regionów i ruch wieloodcinkowy pozostają na później.
- **Bitwa** startuje przy kontakcie party z wrogą osadą lub wrogim party.
  **ROZSTRZYGNIĘTE (M5.3a, minimalny kontakt party↔party):** próba starcia
  dwóch party stojących w bezpośrednio sąsiednich regionach tworzy nowy
  `HexBattle`, nie mutując ani nie przesuwając party na mapie. Party inicjujące
  jest stroną atakującą, a party w regionie docelowym — broniącą. Każdy
  skład trafia do bitwy w kolejności **bohater, potem podkomendni**; pozycje
  startowe są deterministycznymi, rozłącznymi rzędami na domyślnym terenie
  Plains. To rozstawienie jest placeholderem integracyjnym. Kontakt z osadą,
  własność księstw, teren zależny od regionu oraz zapis wyniku z powrotem
  na mapę pozostają poza M5.3a.
- **ROZSTRZYGNIĘTE (M5.3b1, minimalny kontakt party↔osada):** jawne rozpoczęcie
  starcia party z garnizonem osady w bezpośrednio sąsiednim regionie tworzy nowy
  `HexBattle`, nie mutując mapy, party, osady ani garnizonu. Bohater i podkomendni
  party są atakującymi, a jednostki garnizonu — obrońcami; obie strony zachowują
  kolejność wejściową i trafiają do deterministycznych, rozłącznych rzędów na
  domyślnym terenie Plains. Własność strategiczna powstanie w M5.3b2; do tego
  czasu wrogość jest założeniem jawnego polecenia rozpoczęcia bitwy.
- **Czas:** 1 tura = **1 miesiąc**. Rok = **13 miesięcy po 4 tygodnie**
  (52 tygodnie). Trening i wyposażenie mierzone są w miesiącach.
- **Bohater:** dokładnie **jeden** na księstwo — król i dowódca w jednym. Armia
  rusza się **wyłącznie** razem z bohaterem. Bez bohatera jednostki stoją; mogą
  zostać w osadzie jako **garnizon** (obrona).
- **Party:** bohater prowadzi maksymalnie **12 jednostek**.
  **ROZSTRZYGNIĘTE (M5.2a, minimalny skład party):** `Party` jest
  niemutowalnym stanem z jednym wymaganym `hero: Unit` oraz krotką najwyżej
  12 podkomendnych `units`. Bohater zajmuje osobne pole i **nie wlicza się** do
  limitu 12 jednostek. Rola bohatera wynika z pola `hero`; na tym etapie korzysta
  on z tego samego modelu bojowego `Unit`, bez osobnego typu i bez reguł
  następstwa. Party nie przechowuje jeszcze pozycji ani punktów ruchu, a jego
  utworzenie nie przenosi jednostek z garnizonu — te przejścia dochodzą osobno.
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
  **ROZSTRZYGNIĘTE (B4.4a, minimalny profil dystansowy):** `Unit` ma niemutowalne
  pole `ranged_range` (domyślnie `0`, czyli brak ataku dystansowego). Wartość
  `>= 2` pozwala wykonać strzał do wrogiej jednostki w odległości heksowej od `2`
  do `ranged_range` włącznie; dystans `1` pozostaje domeną ataku wręcz. Strzał
  używa tego samego wzoru szansy trafienia co walka wręcz oraz `Unit.damage`,
  wykonuje jeden rzut RNG i nie wywołuje kontrataku. Jest to profil placeholder:
  bez kary za odległość, amunicji i osobnej statystyki obrażeń dystansowych.
  **ROZSTRZYGNIĘTE (B4.4b1, geometria linii):** `Hex.line_to(other)` zwraca
  niemutowalną, deterministyczną sekwencję heksów od źródła do celu włącznie,
  długości `distance + 1`; kolejne elementy są sąsiadami, a zamiana końców
  dokładnie odwraca wynik. Linia powstaje przez interpolację w układzie cube i
  zaokrąglenie do heksu. Interpolacja używa dokładnej arytmetyki całkowitej/
  wymiernej, więc zachowuje kontrakt także dla dowolnie dużych współrzędnych;
  przypadki biegnące dokładnie po granicy rozstrzyga stała, symetryczna reguła
  remisu, aby widoczność nie zależała od kierunku sprawdzania.
  **ROZSTRZYGNIĘTE (B4.4b2, przeszkody jednostkowe):** każda jednostka — własna
  lub wroga — na dowolnym heksie pośrednim `attacker.line_to(target)` blokuje
  atak dystansowy. Heksy atakującego i celu nie są przeszkodami. Zablokowany
  strzał jest odrzucany przed rzutem RNG i nie zmienia stanu bitwy.
  Teren blokujący widoczność i typy broni pozostają na później.
- **Morale** wpływa **wyłącznie na celność** (bonus/kara do trafienia). Morale
  **nie** powoduje ucieczek.
- **ROZSTRZYGNIĘTE (B4.3a, szansa trafienia w zwarciu):** szansa jest liczona jako
  całkowity procent
  `clamp(50 + accuracy_atakującego + accuracy_mod_terenu_atakującego + morale
  - defense_obrońcy - defense_mod_terenu_obrońcy, 5, 95)`. Morale jest podpisanym
  modyfikatorem celności (wartość dodatnia pomaga, ujemna przeszkadza). Modyfikator
  `accuracy_mod` dotyczy jednostki stojącej na danym terenie, a `defense_mod` —
  obrońcy stojącego na danym terenie. Na tym etapie wzór jest czystym wyliczeniem
  bez RNG; rzut, wymóg sąsiedztwa, obrażenia i bieżące HP dochodzą w B4.3b.
- **Śmierć permanentna.** Alternatywnie zamiast zginąć jednostka może zostać
  **ogłuszona** i odnieść **ranę** — trwałą lub czasową.
  **ROZSTRZYGNIĘTE (B4.5a, minimalny model ran):** rana jest niemutowalnym
  modyfikatorem `accuracy` i `defense`, z czasem trwania wyrażonym w miesiącach;
  `duration_months=None` oznacza ranę trwałą. Kary wielu ran sumują się,
  a efektywne statystyki nie spadają poniżej `0`. Startowy katalog placeholder:
  **Bruise** (czasowa, 2 miesiące, `accuracy=-1`, `defense=-1`) oraz **Maimed**
  (trwała, `accuracy=-2`, `defense=-2`). Rany należą do trwałego modelu
  `Unit`, aby mogły przejść z bitwy na warstwę strategiczną. Upływ czasu ran
  dochodzi w osobnym przyroście.
  **ROZSTRZYGNIĘTE (B4.5b, minimalne rozstrzygnięcie 0 HP):** jednostkę, której
  bieżące HP spadło do `0`, rozstrzyga się dokładnie jednym rzutem RNG: **50%**
  oznacza śmierć i usunięcie jej z rozstawienia, a pozostałe 50% — pozostawienie
  jej na heksie jako `stunned=True` z dodaną raną **Bruise**. To celowo prosty
  placeholder (bez wpływu rodzaju ciosu i bez losowania rodzaju rany). Rozstrzygać
  można wyłącznie jeszcze nieogłuszoną jednostkę z `0 HP`; pusty heks, jednostka
  mająca HP lub już ogłuszona są błędem. Ogłuszona jednostka nie może się ruszać
  ani atakować. Usunięcie ogłuszonej jednostki z pola i przeniesienie ocalałej
  wraz z ranami do warstwy strategicznej nastąpi przy wyniku bitwy (B4.6).
- **ROZSTRZYGNIĘTE (B4.6a, minimalny koniec bitwy):** jednostka jest **aktywna**,
  gdy ma bieżące HP większe od `0` i nie jest ogłuszona. Po zakończeniu rozstawienia
  bitwa trwa, dopóki obie strony mają co najmniej jedną aktywną jednostkę. Gdy
  aktywne jednostki ma tylko jedna strona, ta strona wygrywa; brak aktywnych
  jednostek obu stron oznacza remis. Wycofanie nie jest jeszcze dostępne, więc nie
  uczestniczy w tym przyroście. Raport strat i przyznanie doświadczenia powstaną
  osobno w B4.6b–c.
- **ROZSTRZYGNIĘTE (B4.6b, minimalny raport bitwy):** rozstrzygnięta bitwa zwraca
  niemutowalny raport zawierający wynik oraz, osobno dla każdej strony, jednostki
  **poległe**, **ogłuszone** i **zdolne do działania**. `HexBattle` zachowuje
  niemutowalny rejestr poległych wraz z ich stroną, ponieważ śmierć usuwa jednostkę
  z rozstawienia; ogłuszeni i aktywni pochodzą z końcowego rozstawienia. Kolejność
  w każdej kategorii jest deterministyczna (kolejność rozstawienia/rozstrzygania).
  Raport można utworzyć dopiero po końcu bitwy; nie zmienia stanu i nie przyznaje
  doświadczenia — to osobny przyrost B4.6c.
- **ROZSTRZYGNIĘTE (B4.6c, doświadczenie za udział):** po rozstrzygnięciu bitwy
  każda ocalała jednostka — zarówno zdolna do działania, jak i ogłuszona — otrzymuje
  **+1 doświadczenia**. Polegli nie otrzymują nagrody. Przyrost jest stały,
  deterministyczny i zachowuje pozostały stan jednostki (w tym rany oraz
  ogłuszenie); jest przyznawany przez osobne czyste przejście tworzące nagrodzony
  raport, więc raport bazowy i stan bitwy pozostają niezmienione. To minimalny
  placeholder za sam udział, bez premii za zwycięstwo, zabójstwa lub obrażenia;
  tempo progresji doświadczenia pozostaje do późniejszego balansu.

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
  nierozróżnialne — dlatego ruch operuje na heksach źródłowym i docelowym.
  **ROZSTRZYGNIĘTE (B4.2b, ruch):** `move(source, destination, move_points)` to czyste
  przejście: zwraca **nowy** `HexBattle` z jednostką przeniesioną z `source` na
  `destination`. Koszt ruchu = suma `move_cost` **wchodzonych** heksów po
  **najtańszej ścieżce** (koszt wejścia na heks, źródło się nie liczy); ruch legalny,
  gdy koszt `≤ move_points`. **Inne jednostki blokują** — nie można przez nie
  przechodzić ani na nie wejść. Cel musi być wolny. Nielegalny ruch (brak jednostki
  w `source`, zajęty/nieosiągalny w budżecie `destination`) to błąd (`ValueError`).
  Zapytanie `reachable(source, move_points)` zwraca deterministyczny zbiór wolnych,
  osiągalnych heksów (bez `source`). Wyszukiwanie to Dijkstra ograniczony budżetem —
  plansza jest nieskończona (domyślny Plains), więc budżet domyka przeszukanie.
  **Punkty ruchu jako parametr:** wyprowadzenie `move_points` z filarów jednostki
  dochodzi później (kamień 4/5). **Poza B4.2b:** granice/kształt planszy,
  kolejka tur i rozstrzyganie walki (B4.3+).
  **ROZSTRZYGNIĘTE (B4.3b1, bieżące HP):** rozstawienie jednostki inicjalizuje jej
  bieżące HP wartością maksymalną `Unit.hp`. Obrażenia odejmuje się od bieżącego HP
  z podłogą na `0`; wartość `0` oznacza jednostkę pokonaną, ale jej usunięcie oraz
  rozstrzygnięcie śmierci/ogłuszenia pozostają w B4.5. Bieżące HP jest częścią
  niemutowalnego stanu bitwy i podczas ruchu podąża razem z jednostką. Zadawanie
  obrażeń jest na razie niskopoziomowym, czystym przejściem po pozycji; rzut na
  trafienie, strony konfliktu i legalność ataku dochodzą w B4.3b2.
  **ROZSTRZYGNIĘTE (B4.3b2, kontrakt walki wręcz):** każda rozstawiona jednostka
  należy do jednej z dwóch jawnych stron bitwy (`ATTACKER` albo `DEFENDER`), a
  informacja o stronie podczas ruchu podąża razem z jednostką. Atak wręcz wskazuje
  heks atakującego i celu; jest legalny wyłącznie między wrogimi jednostkami na
  sąsiednich heksach. Szansa trafienia pochodzi z wzoru B4.3a i terenu obu pozycji,
  a wstrzyknięty `Rng` wykonuje jeden rzut. Pudło nie zmienia HP, trafienie odejmuje
  `Unit.damage` od bieżącego HP celu. Kontratak, punkty akcji/kolejka tur, usuwanie
  jednostki przy 0 HP oraz raport zdarzenia dochodzą w kolejnych przyrostach.
  **ROZSTRZYGNIĘTE (B4.5b, stan pokonanej jednostki):** `Unit.stunned` jest
  niemutowalną flagą (domyślnie `False`). `HexBattle.resolve_defeat(position, rng)`
  rozstrzyga jednostkę z `0 HP` zgodnie z regułą z §3.2 i zwraca nowy stan.
  W wariancie śmierci usuwa spójnie jednostkę, HP i stronę z map bitwy; w wariancie
  ogłuszenia zastępuje jednostkę kopią z `stunned=True` i dopisaną raną `BRUISE`,
  zachowując pozycję, stronę i `0 HP`.
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
  źródło** (tylko walka). **ROZSTRZYGNIĘTE (B4.6c, minimalny przyrost):** każda
  bitwa przeżyta przez jednostkę daje +1 doświadczenia; odrębna krzywa lub premie
  zależne od wyniku pozostają poza MVP.
  **NADAL OTWARTE:** różne parametry stromości per filar (trening vs uzbrojenie)
  oraz wpływ budynków/mnożników — strojenie przy balansie.
- ~~**Wzór na trafienie:** bazowa celność + teren + morale → prawdopodobieństwo.~~
  **ROZSTRZYGNIĘTE (B4.3a):** całkowity procent z bazą 50 i limitem 5–95; pełny
  wzór oraz semantyka modyfikatorów terenu są w §3.2.
- ~~**Model ran:** ile rodzajów, jak wpływają na statystyki, czasowe vs trwałe.~~
  **CZĘŚCIOWO ROZSTRZYGNIĘTE (B4.5a):** minimalny katalog i wpływ na statystyki
  opisano w §3.2. **NADAL OTWARTE:** bogatszy katalog, leczenie i balans kar.
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
