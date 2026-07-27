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
- `tbbui` (HTML/SVG) — **wyłącznie narzędzie diagnostyczne**, nie docelowy klient.

**Czego brakuje do celu (nazwane wprost, bo tu jest cała reszta pracy):**
klient startuje tylko ze zmiennymi `TBB_*` (czyli z terminala); kontrolki sceny
leżą jedna na drugiej bez layoutu; nie ma widoku mapy ani żadnej wizualizacji
bitwy w Godocie; nie ma zapisu/odczytu z poziomu UI; nie ma presetu eksportu ani
pakietu na Linuksa.

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
- **[P]** Gotowe assety open source (CC0: Kenney, OpenGameArt) zamiast rysowania
  własnych. Grafika ma być czytelna, nie ładna.
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

## Klimat, ton, kierunek wizualny
Średniowiecze **bez magii i fantastyki**, surowy i realistyczny ton. **[W]**
Interfejs i teksty po polsku (tak jest w kliencie i tak zostaje). **[P]**

Wizualnie: prosta, schematyczna grafika 2D w Godocie — mapa regionów/osad/party
oraz siatka heksów z jednostkami i terenem. Nie celujemy w AAA ani dźwięk; celem
jest czytelność stanu gry na ekranie. **[W]** dla istnienia obu widoków,
**[P]** dla ich stylu.

## Sugestie autora briefu
- `godot-notes.md` (przykładowe node'y, szkic API, podział scen, kolejność prac)
  jest **niewiążące** — inspiracja, nie specyfikacja.
- Klient HTML/SVG `tbbui` zostaje jako narzędzie diagnostyczne; nie rozwijamy go
  jako produktu (patrz wstrzymany K62).
- Autor prosi też o **posprzątanie repo gry** — sondy testowe wymieszane z kodem
  produkcyjnym w `game/scripts/`, wersjonowane artefakty w `out/`. **[P]**

## Kolejne prawdopodobne etapy
1. **Start bez terminala**: domyślna konfiguracja mostu i pliku stanu, gdy nie ma
   `TBB_*` (kolejka: K82).
2. **Czytelny układ ekranu**: kontenery Godota zamiast kontrolek w punkcie (0,0);
   panel osady/księstwa oddzielony od panelu rozkazów.
3. **Widok mapy**: regiony, osady i party rysowane w 2D zamiast `ItemList` nazw;
   klik na region/osadę zamiast globalnych przycisków „Rozwiń/Szturmuj".
4. **Widok bitwy**: `battle_state` z mostu na siatce heksów w Godocie — teren,
   jednostki, wynik; potem sterowanie pojedynczą jednostką w bitwie.
5. **Zapis/odczyt z UI**: jawne „Zapisz"/„Wczytaj" (most ma to od K68/K69).
6. **Pakiet na Linuksa**: preset eksportu, dołączony/wykryty runtime Pythona,
   uruchomienie jedną ikoną — domknięcie kryterium sukcesu.

## Świadomie odłożone
- Scenariuszowa kampania/fabuła, multiplayer, magia, oddziały masowe, grafika
  AAA i dźwięk, edytor map — **poza zakresem** (brief).
- Rozbudowa alertu gospodarczego w HTML (K62) — **wstrzymana**, klient HTML jest
  tylko diagnostyką.
- Bogatszy model ran/terenu/budynków, więcej typów jednostek, balans i strojenie
  AI, pełna maszyna faz `StrategicTurn` — po domknięciu widocznej, grywalnej gry.
- Podział przerośniętych dokumentów (`ARCHITECTURE.md` ~119 KB, `DECISIONS.md`
  ~74 KB, `DESIGN.md` ~28 KB) — dług dokumentacji, nie blokuje celu.
