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
- **Start bez terminala działa w drzewie źródeł** (K82): bez żadnej zmiennej
  `TBB_*` klient sam składa komendę mostu, ścieżkę stanu i ziarno, a gdy most nie
  wstanie — pokazuje komunikat zamiast martwej sceny. Repo gry posprzątane
  (R82.1); układ ekranu czytelny, kontrolki w kontenerach (K83).
- **Oba widoki działają** (K84/K85): `MapView` rysuje kafel na region po
  `col`/`row` z rozróżnialnym właścicielem i przesuwającym się oddziałem gracza;
  `BattleView` rysuje heksy po `(q, r)` z rozróżnialnymi stronami i czytelnym
  wynikiem po kliknięciu „Szturmuj osadę".
- **Zapis/odczyt z UI działa** (K86): konfiguracja niesie `save_path`, scena ma
  przyciski „Zapisz partię"/„Wczytaj partię", a klik przywraca zapisany stan na
  ekranie i utrwala partię między procesami.
- **Prawdziwe assety w repo — DOMKNIĘTE** (K87): `game/assets/` niesie 10 plików
  PNG z dwóch paczek CC0 — kafle mapy i terenu z Kenney Hexagon Pack, sylwetki
  stron bitwy z Kenney „RTS Pack: Medieval" — z atrybucją **per plik** w
  `CREDITS.md`; `.godot/` poza gitem. `MapView` rysuje grunt/osadę/oddział
  teksturami, `BattleView` teren heksu (`Plains`/`Forest`/`Hills`) i sylwetkę
  strony. Rozróżnialność stron wzięła się z dwóch różnych plików, nie z
  `modulate` (wniosek 12 potwierdzony w praktyce). R87.1 scalił warstwę tekstury
  kafla w jedno źródło dla obu widoków.
- **Pakiet na Linuksa — w toku** (K88, 3 z 7 plasterków): `game/export_presets.cfg`
  z presetem „Linux/X11" x86-64 jest w repo, szablony 4.2.2 doinstalowane lokalnie
  poza gitem, `godot --headless --export-release` produkuje wykonywalne binarium
  + `.pck` (G88.1a); `BridgeConfig` szuka `src/` odpornie na eksport — najpierw
  obok binarium, potem w drzewie źródeł (G88.1b); `scripts/package.sh <cel>`
  składa katalog dystrybucyjny z binarium, `.pck` i `src/` mostu (G88.1c).
- `tbbui` (HTML/SVG) — **wyłącznie narzędzie diagnostyczne**, nie docelowy klient.

**Czego brakuje do celu (nazwane wprost, bo tu jest cała reszta pracy):**
1. **Pakiet nie jest jeszcze dowiedziony jako grywalny.** Zbudować się buduje,
   ale nikt nie uruchomił *wyeksportowanej* gry i nie pokazał, że startuje partię
   bez terminala — a to jedyny nieodhaczony fragment kryterium sukcesu. W kolejce:
   czysty `.pck` (bez sond testowych), ciągłość partii przy samym starcie, e2e na
   pakiecie i uruchomienie jednym kliknięciem (`.desktop`). Szczegóły ryzyka:
   wniosek 4.
2. **Szturm potrafi zwrócić graczowi błąd zamiast wyniku bitwy.** Odtworzone
   uruchomieniem kodu **ponownie 2026-07-28** (`serve 73`, recruit ×2 → muster →
   march → assault): most odpowiada `{"ok": false, "error": "unknown battle
   result"}`, klient pokazuje „rozkaz nie powiódł się". Bitwa nie rozstrzyga się
   w 1000 rundach, bo ogłuszeni sojusznicy zostają na planszy i blokują jedyne
   pole skracające dystans do obrońcy; `resolve_settlement_battle_recorded` podaje
   wtedy `None` do `apply_settlement_battle_result`, a to rzuca `ValueError`.
   Przyczyną jest **ruch, nie obrażenia** — podniesienie obrażeń bazowych do ≥ 1
   sprawdzono i nic nie zmienia. Rozplanowane jako **K89**; nie planować nic
   ponad to bez przeczytania diagnozy w `BACKLOG.md`, bo pierwszy nasuwający się
   trop jest fałszywy. To **drugi warunek „gotowe"**, obok pakietu: kryterium
   mówi wprost „rozegrać bitwę", a najbardziej naturalna sekwencja gracza tę
   możliwość dziś odbiera.

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
- **[P]** Pakiet na Linuksa zakłada **systemowy `python3`**; nie wnosimy własnego
  runtime'u Pythona (patrz wniosek 10). Bundling CPythona: **[O]**.
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
   komenda mostu składa `PYTHONPATH=res://../src python3 -m tbbbridge`
   (`game/scripts/bridge_config.gd:27`); po eksporcie `res://` wskazuje wnętrze
   PCK, więc K88 musi *od nowa* udowodnić start bez terminala i położyć `src/`
   obok binarium. Stan toolchainu sprawdzony 2026-07-27: `godot 4.2.2` jest w
   `PATH`, katalog szablonów eksportu istnieje, ale jest **pusty**; paczka
   `.tpz` na GitHubie odpowiada `200`, więc da się ją pobrać;
   `game/export_presets.cfg` nie istnieje. To prerekwizyt toolchainu i pierwszy
   plasterek K88, nie zaskoczenie na koniec.
5. Snapshot bitwy (`battle.hexes`) niesie **wyłącznie heksy zajęte przez
   jednostki**, bez wymiarów pola i terenu pustych heksów. Pierwszy widok bitwy
   rysuje więc jednostki, nie całą planszę; pełna siatka to osobna, późniejsza
   zmiana mostu.
6. **Kolorowy prostokąt wystarczył na „widać stan gry", ale nie na MVP.** K84 i
   K85 domknęły kryterium „da się grać patrząc" *strukturalnie* (kafle, siatka,
   rozróżnialne strony), lecz autor briefu nazwał brakujący element wprost:
   assety. Kolejny kamień podmienia `ColorRect` na tekstury — geometria i testy
   rozmieszczenia z K84/K85 zostają, zmienia się nośnik.
7. **Import tekstur w Godocie to był prerekwizyt toolchainu, nie detal — i to
   się potwierdziło.** G87.1a rozstrzygnęło całą ścieżkę import→tekstura w
   osobnej bramce (`godot --headless --import`, `.godot/` w `.gitignore`,
   `load("res://assets/…")` → `Texture2D`), zanim ktokolwiek ruszył widoki.
   Dwa kolejne plasterki widoków poszły potem bez niespodzianek. **Ten wzorzec
   powtarzamy w K88: najpierw bramka eksportu, dopiero potem treść pakietu.**
8. **Teren istnieje tylko w warstwie bitwy — mapa strategiczna go nie zna.**
   `tbb.terrain` (`PLAINS`/`FOREST`/`HILLS`) obsługuje `Battlefield.terrain_at`,
   a most wystawia `terrain` wyłącznie per heks bitwy. `tbb.world.Region` ma samo
   `name`, więc `map_state` daje na region `name`, `col`, `row`, `owner`,
   `settlement`, `party`. Skutek dla kierunku: kafle mapy teksturujemy po
   właścicielu i obecności osady, a **teren regionu to osobna zmiana rdzenia i
   mostu** — świadomie odłożona, bo brief żąda prawdziwych assetów, nie
   bogatszej mapy. Klientowi nie wolno wymyślić terenu regionu u siebie: rdzeń
   jest jedynym źródłem reguł.
9. **Podmiana nośnika nie kosztowała czytelności.** Kafle są dziś teksturą
   przyciemnianą `modulate` w kolorze właściciela/strony, więc kryteria
   rozróżnialności z K84/K85 przeszły bez jednej zmiany. Wniosek na przyszłość:
   warstwa tekstury + tint zamiast osobnego assetu na każdy wariant — mała
   paczka wystarcza, a testy geometrii zostają w mocy.
10. **Pakiet nie wnosi własnego Pythona.** Odbiorcą jest jeden użytkownik na
    Linuksie x86-64, który ma `python3` w systemie (zweryfikowane: 3.14.4).
    Bundling CPythona podwoiłby zakres K88 i nie wynika z briefu, więc pakiet
    zakłada systemowy `python3`, a jego brak daje czytelny komunikat w scenie
    (ścieżka błędu istnieje od K82). To decyzja zakresowa, nie ograniczenie
    techniczne — jeśli okaże się za wąska, wraca jako osobny plasterek.
11. **Bramka „plik się ładuje" nie sprawdza, *co* jest na obrazku — i to nas
    kosztowało plasterek.** G87.1a przyjęło jako „sylwetki stron" dwa budynki z
    Hexagon Packa tylko dlatego, że nazwa pliku brzmiała `side_*.png`, a `load()`
    zwracał `Texture2D`. **Wniosek na każdy kolejny plasterek assetowy:**
    kryterium akceptacji wiąże plik z jego *źródłem* w `CREDITS.md` (konkretna
    ścieżka w paczce, nie sama nazwa paczki) i z maszynowo sprawdzalnym kształtem
    (przezroczyste tło, rozmiar mniejszy od kafla, obie strony różne bajtowo), a
    człowiek ogląda obrazek przy review. Dobór paczki sprawdzamy po **liście
    plików**, zanim wejdzie do repo. To szczególny przypadek wniosku 13.
12. **Jedna paczka nie wystarczy — i to jest świadome odstępstwo od [P].**
    Hexagon Pack nie ma postaci, więc sylwetki jednostek muszą przyjść z drugiej
    paczki CC0 (RTS Pack: Medieval). Preferencja „spójna paczka bije zlepek"
    zostaje w mocy jako domyślna, ale ustępuje wymaganiu: lepiej mieszany styl
    z prawdziwą figurą niż spójny styl z budynkiem udającym żołnierza. Praktyczny
    skutek dla G87.1c-2: figurki RTS Packa **są już kolorowe per strona**
    (`medievalUnit_01` niebieski, `_13` zielony), więc rozróżnialność stron może
    wziąć się z **wyboru dwóch różnych plików**, a nie z `modulate` — tint na już
    pokolorowanej figurce może ją zaszarzeć. Wzorzec „tekstura + tint" z wniosku
    9 zostaje dla kafli terenu, gdzie wariant koloru nie istnieje w paczce.
    *(Potwierdzone wykonaniem: K87 domknięty właśnie tak.)*
13. **Zielony zestaw testów nie znaczy, że dało się zagrać — defekt szturmu
    znalazło dopiero uruchomienie gry ręką.** Rdzeń jest pokryty TDD, most też,
    klient ma e2e przez dwa procesy — a mimo to najbardziej naturalna sekwencja
    gracza (dorekrutuj → zbierz → wyrusz → szturmuj) kończy się błędem rozkazu.
    Testy bitwy sprawdzały składy, które *rozstrzygają się*; pat, w którym własny
    ogłuszony blokuje jedyne dojście, nie miał testu, bo nikt go nie wymyślił
    przy biurku. **Wniosek na kierunek:** od teraz każdy przegląd (i najlepiej
    każdy plasterek domykający kamień) kończy się **przejściem pełnej sekwencji
    gracza na żywym moście**, nie samym `pytest`. Po K88 ta sekwencja idzie na
    wyeksportowanym pakiecie, nie w drzewie źródeł — bo to jest artefakt, który
    dostaje odbiorca.
14. **Kontrakt „wynik bitwy" był niepełny, nie tylko zabugowany.** `HexBattle`
    dopuszcza stan „nikt nie wygrał po wyczerpaniu rund" (`result() is None`), a
    `WorldMap` nie ma dla niego przypadku i rzuca `ValueError`. Naprawa reguły
    ruchu (żeby akurat ten pat nie występował) **nie zamyka klasy problemu** —
    inny pat wróci tą samą ścieżką. Dlatego K89 najpierw domyka kontrakt
    (nierozstrzygnięta bitwa = legalny wynik, świat spójny, gracz widzi tekst),
    a dopiero potem rusza reguły ruchu. Kolejność jest tu decyzją, nie wygodą.

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
   (K84), ~~widok bitwy~~ (K85) i ~~zapis/odczyt z UI~~ (K86) — **zrobione**.
2. ~~Prawdziwe assety~~ (K87) — **domknięte**: obie paczki CC0 z atrybucją per
   plik, kafle mapy, teren heksów i sylwetki stron rysowane teksturami. Zakres
   został po stronie `game/`: mapa różnicuje właściciela i osadę, teren
   teksturujemy tam, gdzie most go niesie — na polu bitwy (wniosek 8).
3. **Pakiet na Linuksa** (K88) — **w toku**, 3 z 7 plasterków. Zrobione: bramka
   eksportu (szablony + `export_presets.cfg` + wykonywalny artefakt), odporne na
   eksport rozwiązywanie ścieżki `src/`, `scripts/package.sh` kładący `src/` obok
   binarium. Zostają: czysty `.pck` bez sond testowych, ciągłość partii przy samym
   starcie, ponowny dowód startu bez terminala **na wyeksportowanej grze**
   (wniosek 4) i uruchomienie jednym kliknięciem. Bez własnego runtime'u Pythona
   (wniosek 10).
4. **Bitwa zawsze daje wynik** (K89) — drugi warunek „gotowe" obok pakietu:
   nierozstrzygnięty szturm ma być legalnym wynikiem widocznym jako tekst, nie
   `ValueError` docierającym do gracza jako „rozkaz nie powiódł się" (wniosek 14).
   Dopiero po tym reguła ruchu, która ten konkretny pat likwiduje.
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
