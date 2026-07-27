# PROJECT — Total Battle Brothers (nazwa robocza)

> Trwały kontekst planisty. Co budujemy, dla kogo, po co i w jakiej kolejności.
> Detale mechaniki → `docs/DESIGN.md`, decyzje techniczne → `docs/ARCHITECTURE.md`
> i `docs/DECISIONS.md`, kolejka zadań → `BACKLOG.md`.
> Rozróżnienie: **[W] wymaganie** (z briefu, nienegocjowalne), **[P] preferencja**
> (kierunek, można uzasadnić odstępstwo), **[O] opcja** (pomysł, wolno pominąć).

## Projekt i odbiorca
Single-player **sandbox** (bez scenariuszowej kampanii): turowa strategia łącząca
zarządzanie osadami i armiami z taktycznymi bitwami na heksach — w duchu
**Battle for Wesnoth / Battle Brothers / Total War**. Gracz prowadzi jedno
księstwo przeciw księstwom sterowanym przez AI. **[W]**

Odbiorca: pojedynczy gracz na **Linuksie x86-64**, który uruchamia natywną
aplikację i gra myszą/klawiaturą — **bez terminala, bez ręcznego odpalania
Pythona czy edytora Godota**. **[W]**

Skala kameralna: małe osady, nieliczne wojska, każda jednostka się liczy. **[W]**

## Cel docelowy i kryterium sukcesu
**Gotowe dopiero wtedy**, gdy użytkownik uruchamia natywną aplikację na Linuksie
i bez terminala może: **zarządzać osadą, przemieszczać armię, rozegrać bitwę,
zapisać i wczytać stan**. **[W]**

Rozgrywkowo: pętla sandboxa domyka się, gdy da się pokonać księstwo AI (utrata
jego osad **oraz** śmierć jego bohatera — to również warunek przegranej gracza).

Kryterium pomocnicze, po którym poznajemy postęp: **da się grać patrząc, a nie
czytając logi**. Widok mapy i widok bitwy mają nieść stan gry wizualnie. **[W]**

**Assety są częścią kryterium, nie polishem po MVP.** Feedback autora briefu
(2026-07-27): *„prawdziwe MVP będzie wtedy, kiedy będą assety i tekstury. Nie
musi być dużo budynków/rodzajów jednostek/terenu itp, ale żeby były jakieś
sensowne prawdziwe assety."* Czyli: widoki mają rysować **realne pliki
graficzne**, nie jednolite prostokąty z etykietą tekstową. Zakres świadomie
mały — po kilka kafli terenu, sylwetek jednostek i budynków — ale prawdziwych.
**[W]**

## Stan faktyczny (aktualizowany przy przeglądach)
- Rdzeń `tbb` (Python): kampania, ekonomia (pszenica/złoto, populacja, budynki),
  kalendarz 13×4 tygodnie, jednostki i trzy filary progresji, morale, bitwa na
  heksach, AI księstw, sukcesja — **działa headless, pokryty TDD**.
- Most `tbbbridge`: snapshot JSON (OUT), komendy i rozkazy gracza (IN), protokół
  JSON Lines na stdio, `serve` / `serve --resume`, round-trip persystencji
  (save/load całej sesji łącznie z RNG i `last_battle`) — **gotowe**.
- Klient Godot 4 w `game/`: `SnapshotModel`, `BridgeClient` (jedno-strzałowe
  wywołania procesu mostu + plik stanu), scena z datą, listą regionów, statusem
  księstwa, położeniem oddziału, statusem ostatniego rozkazu oraz przyciskami
  „Następna tura", „Rozwiń osadę", „Rekrutuj jednostkę", „Zbierz oddział",
  „Wyrusz w pole", „Szturmuj osadę".
- **Start bez terminala działa** (K82): bez żadnej zmiennej `TBB_*` klient sam
  składa komendę mostu, ścieżkę stanu w katalogu użytkownika i ziarno, a gdy
  most nie wstanie — pokazuje komunikat zamiast martwej sceny.
- **Układ ekranu czytelny** (K83): kontrolki w kontenerach, grupa stanu oddzielona
  od grupy rozkazów, prostokąty parami rozłączne.
- Repo gry posprzątane (R82.1): sondy testowe poza kodem produkcyjnym, `out/`
  poza gitem.
- **Widok mapy działa** (K84): `MapView` rysuje kafel na region po `col`/`row`,
  właściciel rozróżnialny, oddział gracza oznaczony i przesuwający się.
- **Widok bitwy działa** (K85): `BattleView` rysuje kafle heksów po `(q, r)`,
  strony rozróżnialne, wynik bitwy czytelny po kliknięciu „Szturmuj osadę".
- **Zapis/odczyt z UI — w toku** (K86): konfiguracja niesie `save_path`, a
  `BridgeClient` zapisuje i wczytuje partię gracza; brakuje jeszcze przycisków
  w scenie i ich wiązania.
- `tbbui` (HTML/SVG) — **wyłącznie narzędzie diagnostyczne**, nie docelowy klient.

**Czego brakuje do celu (nazwane wprost, bo tu jest cała reszta pracy):**
1. **Zero assetów.** W repo nie ma ani jednego pliku graficznego — cała warstwa
   wizualna to `ColorRect` w jednolitym kolorze plus `Label` z nazwą. Wedle
   nowego kryterium to **nie jest** MVP (patrz sekcja „Cel docelowy").
2. Zapis/odczyt z poziomu UI niedokończony (K86: zostały przyciski i wiązanie).
3. Nie ma presetu eksportu ani pakietu na Linuksa — i to może podważyć start bez
   terminala (patrz wniosek 4).

## Ograniczenia i priorytety
- **[W]** Rdzeń `tbb` jest **jedynym źródłem reguł gry**. Godot nie duplikuje
  logiki; Python nie zależy od Godota ani żadnego UI.
- **[W]** Komunikacja Godot↔Python przez jawny, testowalny interfejs (stan gry
  jako JSON). Transport i kształt API wybiera i uzasadnia agent — obecnie:
  proces `python -m tbbbridge serve`, JSON Lines po stdio, stan w pliku.
- **[W]** Budowa klienta Godota jest **bieżącym priorytetem**. Nie wolno w
  nieskończoność dokładać mechaniki kosztem widocznej, grywalnej gry.
- **[W]** Determinizm: seedowalny RNG, testy bez losowości.
- **[W]** TDD, małe przyrosty; każde zadanie ma kryteria akceptacji. Trudność
  `simple|standard|complex` + flagi ryzyka; bootstrap/toolchain/integracja
  Godot↔Python idą jako `complex` i przechodzą review pętli agentowej.
- **[P]** Rdzeń przed prezentacją **wewnątrz jednego plasterka** — ale plasterek
  ma kończyć się czymś widocznym na ekranie, nie samą regułą.
- **[W]** Widoki mają rysować **prawdziwe assety graficzne** (patrz kryterium
  sukcesu). Ilość jest mała i negocjowalna; *istnienie* assetów nie jest.
- **[P]** Źródłem assetów są gotowe paczki open source (CC0: Kenney,
  OpenGameArt) zamiast rysowania własnych; licencja i atrybucja zapisane w repo.
  Grafika ma być czytelna, nie ładna.
- **[O]** Wykorzystanie kodu/zasobów z Battle for Wesnoth.

**Wnioski z dotychczasowej pracy, które zmieniają kierunek:**
1. Ostatnie kamienie (K75–K81) to była seria „kolejny przycisk rozkazu". Ścieżka
   rozkazu jest już sparametryzowana — dokładanie szóstego przycisku nie zbliża
   do celu. **Kolejne plasterki mają iść w: start bez terminala → czytelny układ
   ekranu → widok mapy → widok bitwy → pakiet na Linuksa.**
2. Godot 4.2.2 nie ma `OS.execute_with_pipe`, więc most wołamy jedno-strzałowo,
   a ciągłość partii daje plik stanu (`serve --resume`). To zadziałało i zostaje.
3. Odchudzanie kontraktu na liście (jedno pole / jedna grupa pól na zadanie)
   ratuje mikro-TDD tam, gdzie „cały słownik naraz" wcześniej wykładał kodera.
4. **Start bez terminala jest zweryfikowany tylko w drzewie źródeł.** Domyślna
   komenda mostu składa `PYTHONPATH=res://../src python3 -m tbbbridge`; po
   eksporcie `res://` przestaje wskazywać na repo, więc kamień „pakiet na
   Linuksa" musi *od nowa* udowodnić start bez terminala i dołączyć `src/` do
   pakietu. Dodatkowo w środowisku nie ma zainstalowanych szablonów eksportu
   Godota — to prerekwizyt toolchainu, nie zaskoczenie na koniec.
5. Snapshot bitwy (`battle.hexes`) niesie **wyłącznie heksy zajęte przez
   jednostki**, bez wymiarów pola i terenu pustych heksów. Pierwszy widok bitwy
   rysuje więc jednostki, nie całą planszę; pełna siatka to osobna, późniejsza
   zmiana mostu.
6. **Kolorowy prostokąt wystarczył na „widać stan gry", ale nie na MVP.** K84 i
   K85 domknęły kryterium „da się grać patrząc" *strukturalnie* (kafle, siatka,
   rozróżnialne strony), lecz autor briefu nazwał brakujący element wprost:
   assety. Kolejny kamień podmienia `ColorRect` na tekstury — geometria i testy
   rozmieszczenia z K84/K85 zostają, zmienia się nośnik.
7. **Import tekstur w Godocie to prerekwizyt toolchainu, nie detal.** Sondy
   headless ładują dziś wyłącznie skrypty; `load("res://assets/…png")` wymaga
   wygenerowanych artefaktów importu (`godot --headless --import`) i katalogu
   `.godot/`, którego nie ma w `.gitignore`. Pierwszy plasterek assetów musi to
   udowodnić w bramce, zanim ktokolwiek zacznie podmieniać widoki.
8. **Teren istnieje tylko w warstwie bitwy — mapa strategiczna go nie zna.**
   `tbb.terrain` (`PLAINS`/`FOREST`/`HILLS`) obsługuje `Battlefield.terrain_at`,
   a most wystawia `terrain` wyłącznie per heks bitwy. `tbb.world.Region` ma samo
   `name`, więc `map_state` daje na region `name`, `col`, `row`, `owner`,
   `settlement`, `party`. Skutek dla kierunku: kafle mapy teksturujemy po
   właścicielu i obecności osady, a **teren regionu to osobna zmiana rdzenia i
   mostu** — świadomie odłożona, bo brief żąda prawdziwych assetów, nie
   bogatszej mapy. Klientowi nie wolno wymyślić terenu regionu u siebie: rdzeń
   jest jedynym źródłem reguł.

## Klimat, ton, kierunek wizualny
Średniowiecze **bez magii i fantastyki**, surowy i realistyczny ton. **[W]**
Interfejs i teksty po polsku (tak jest w kliencie i tak zostaje). **[P]**

Wizualnie: prosta grafika 2D w Godocie — mapa regionów/osad/party oraz siatka
heksów z jednostkami i terenem. Nie celujemy w AAA ani dźwięk; celem jest
czytelność stanu gry na ekranie. **[W]** dla istnienia obu widoków **oraz dla
tego, że niosą prawdziwe tekstury**; **[P]** dla stylu i doboru paczki.

Kierunek doboru assetów: płaskie, czytelne kafle terenu i sylwetki jednostek w
średniowiecznej, nie-fantastycznej stylistyce (bez smoków, magów, elfów) —
spójna paczka bije zlepek najładniejszych pojedynczych obrazków. **[P]**

## Sugestie autora briefu
- `godot-notes.md` (przykładowe node'y, szkic API, podział scen, kolejność prac)
  jest **niewiążące** — inspiracja, nie specyfikacja.
- Klient HTML/SVG `tbbui` zostaje jako narzędzie diagnostyczne; nie rozwijamy go
  jako produktu (patrz wstrzymany K62).
- Autor prosi też o **posprzątanie repo gry** — sondy testowe wymieszane z kodem
  produkcyjnym w `game/scripts/`, wersjonowane artefakty w `out/`. **[P]**
  *(zrobione: R82.1)*
- **Assety i tekstury przesądzają o tym, czy MVP jest prawdziwe** (feedback
  2026-07-27). Autor nie żąda bogactwa treści — „nie musi być dużo budynków /
  rodzajów jednostek / terenu" — tylko żeby to, co jest, było narysowane
  sensownymi, prawdziwymi assetami. Traktujemy to jako **[W]**, nie sugestię.

## Kolejne prawdopodobne etapy
1. ~~Start bez terminala~~ (K82), ~~czytelny układ ekranu~~ (K83), ~~widok mapy~~
   (K84) i ~~widok bitwy~~ (K85) — **zrobione**.
2. **Zapis/odczyt z UI**: dokończyć K86 — przyciski „Zapisz"/„Wczytaj" w scenie
   i ich wiązanie. Zostały dwa cienkie zadania; przerywanie kamienia w połowie
   zostawiłoby save/load podpięty w kliencie, ale nieosiągalny dla gracza.
3. **Prawdziwe assety** (K87) — nowy priorytet z briefu: paczka CC0 w repo z
   atrybucją, kafle mapy i heksy bitwy rysowane teksturą zamiast `ColorRect`.
   Geometria z K84/K85 zostaje, zmienia się nośnik. Zakres trzymany po stronie
   `game/`: mapa różnicuje właściciela i osadę, teren teksturujemy tam, gdzie
   most go niesie — na polu bitwy (wniosek 8).
4. **Pakiet na Linuksa**: preset eksportu, dołączony/wykryty runtime Pythona i
   `src/`, uruchomienie jedną ikoną — domknięcie kryterium sukcesu. Zakłada
   ponowną weryfikację startu bez terminala (wniosek 4) oraz spakowanie assetów.
5. **Klik na cel na mapie** zamiast globalnych przycisków „Rozwiń/Szturmuj" —
   czeka na większą mapę (dziś rozkaz celowany daje ten sam skutek co
   automatyczny; patrz nota przy K86 w `BACKLOG.md`).

## Świadomie odłożone
- Scenariuszowa kampania/fabuła, multiplayer, magia, oddziały masowe, grafika
  AAA i dźwięk, edytor map — **poza zakresem** (brief).
- Rozbudowa alertu gospodarczego w HTML (K62) — **wstrzymana**, klient HTML jest
  tylko diagnostyką.
- Bogatszy model ran/terenu/budynków, więcej typów jednostek, balans i strojenie
  AI, pełna maszyna faz `StrategicTurn` — po domknięciu widocznej, grywalnej gry.
- Podział przerośniętych dokumentów (`ARCHITECTURE.md` ~119 KB, `DECISIONS.md`
  ~74 KB, `DESIGN.md` ~28 KB) — dług dokumentacji, nie blokuje celu.
