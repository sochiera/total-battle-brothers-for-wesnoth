# BACKLOG — Total Battle Brothers

> **Kolejka zadań.** Każde zadanie = jeden mały, testowalny przyrost (TDD).
> Statusy: `[ ]` do zrobienia, `[~]` w toku, `[x]` zrobione.
> Bierz zadania z góry. Nie łącz wielu przyrostów w jeden. Aktualizuj status i
> dopisuj nowe zadania, gdy wizja się doprecyzowuje. Detale mechaniki → `docs/DESIGN.md`.
> Ukończone milestony (kamienie 0–53 oraz A7.1*/A7.2*) przeniesione do
> `BACKLOG-ARCHIVE.md` — tu zostaje wyłącznie żywy tail w stronę grywalnego MVP.

## Legenda
Każde zadanie ma **kryteria akceptacji** (co musi przejść jako test). Rdzeń przed
prezentacją. Determinizm (seedowalny RNG) jest wymogiem przekrojowym.
Planista przypisuje każdemu zadaniu trudność `simple|standard|complex` oraz
flagi ryzyka; bootstrap klienta przechodzi dodatkowo obowiązkowe review pętli
agentowej. Bootstrap, toolchain i integracja Godot↔Python są routowane jako
`complex`.

---

> **Kamienie 0–53 — UKOŃCZONE.** Pełne streszczenia w `BACKLOG-ARCHIVE.md`
> (headless pętla MVP, ekonomia/kalendarz, rozwój jednostek, straty/koszty,
> regeneracja/sukcesja, morale, warstwa wizualna `tbbui` i cała seria rady
> w jeden klik K41–K52, trening party K53). Żywy tail zaczyna się od K54.

> **Kamienie 54–55 — UKOŃCZONE.** Bramkowanie treningu garnizonu Koszarami
> (katalog `BARRACKS`, AI otwierające je przed Market, no-op `tick_training`
> bez Koszar) oraz czytelna gotowość treningu w panelu osad (flaga
> `data-training-ready` + sufiks ` · trening: …`). Szczegóły w
> `BACKLOG-ARCHIVE.md`.

> **Kamień 56 — UKOŃCZONE.** Czytelna gotowość uzbrojenia garnizonu (Kuźnia) w
> panelu osady (flaga `data-equip-ready` + sufiks ` · uzbrojenie: …`) oraz
> refaktor R56.1 (wspólny helper gotowości bramkowanej budynkiem). Szczegóły w
> `BACKLOG-ARCHIVE.md`.

> **Kamień 57 — UKOŃCZONE.** Czytelny bilans ekonomiczny osady w panelu:
> atrybuty `data-wheat-production` / `data-gold-production` /
> `data-wheat-consumption` + flaga `data-wheat-surplus` i czytelne sufiksy
> ` · produkcja/mies.: … · konsumpcja: …` oraz ` · bilans pszenicy:
> nadwyżka|deficyt`. Szczegóły w `BACKLOG-ARCHIVE.md`.

> **Kamień 58 — UKOŃCZONE.** Zbiorcza gospodarka pszenicy księstwa w
> podsumowaniu gracza (`data-wheat-production` / `data-wheat-consumption` /
> `data-wheat-surplus` / `data-wheat-net` + czytelne sufiksy produkcji,
> konsumpcji, bilansu i salda). Szczegóły w `BACKLOG-ARCHIVE.md`.

> **Kamień 59 — UKOŃCZONE.** Zbiorcza produkcja złota księstwa w podsumowaniu
> gracza (`data-gold-production` + grupa tekstu `produkcja/mies.: +Pw pszenicy,
> +Pg złota`). Szczegóły w `BACKLOG-ARCHIVE.md`.

> **Kamień 60 — UKOŃCZONE.** Alert gospodarczy głodujących osad
> (`tbbui.economyalert.render_economy_alert`: korzeń `data-economy-alert` +
> `data-starving-settlements="N"`, tekst `Osady na deficycie pszenicy: N`,
> osadzenie w `render_game_page` po `data-player-summary`). Szczegóły w
> `BACKLOG-ARCHIVE.md`.

> **Kamień 61 — UKOŃCZONE.** Alert gospodarczy: wiersze per głodująca osada
> (`data-starving-settlement` / `data-wheat-deficit` + tekst `<name>: deficyt D
> pszenicy/mies.`), łączny deficyt księstwa (`data-total-wheat-deficit` + sufiks
> nagłówka) oraz flaga i nota krytyczności (`data-economy-critical` /
> `data-economy-caution`). Szczegóły w `BACKLOG-ARCHIVE.md`.

## Kamień milowy 63 — most stanu gry do klienta Godota (snapshot JSON) — PRIORYTET
> **Zmiana zakresu (brief, DECISIONS G63.0):** docelowy klient to natywna gra
> Godot 4 na Linux, a komunikacja z rdzeniem idzie przez testowalny snapshot
> JSON. HTML/SVG `tbbui` degradowane do narzędzia diagnostycznego. Zanim powstaną
> sceny Godota, budujemy w TDD **kontrakt danych**: nowy pakiet-most `tbbbridge`
> serializujący publiczny stan rdzenia do json-serializowalnych słowników. To
> fundament, którego Godot będzie konsumentem; rdzeń `tbb` pozostaje jedynym
> źródłem reguł i nie zależy od mostu. Szczegóły `[x]` G63.1a–2a → `BACKLOG-ARCHIVE.md`.
> **Kamienie 63–64 — UKOŃCZONE.** Most snapshotu JSON (`tbbbridge.snapshot`:
> `settlement_state`/`party_state`/`map_state`/`game_state`/`battle_state`,
> `save_state` + CLI `python -m tbbbridge`, osadzenie bitwy w `game_state`).
> Pełne streszczenia w `BACKLOG-ARCHIVE.md`.

> **Kamień 65 — UKOŃCZONE.** Most poleceń kanał IN (`tbbbridge.session`):
> `Session` (world/game/calendar/rng/player_duchy_id/seed/last_battle),
> `new_session`, `Session.next_turn()`, `apply_command` z komendami sterującymi
> (`next_turn`/`new_game`) i pełnym zestawem rozkazów gracza (`develop`/
> `recruit`/`muster`/`march`/`assault`/`engage` — reużycie prymitywów `ai.*`,
> morale z `game.duchies`, współdzielony RNG, `last_battle`). Szczegóły w
> `BACKLOG-ARCHIVE.md`.

> **Kamień 66 — UKOŃCZONE.** Proces-most stdio (JSON Lines): czysta
> `tbbbridge.protocol.handle_command_line` (parse → `apply_command` → `{"ok",
> "snapshot"|"error", "result"?}`), reużywalna pętla `serve_stream` (pomija
> puste linie, `flush`, EOF → końcowa sesja), CLI `python -m tbbbridge serve
> [seed]` (ścieżka snapshot-do-pliku zachowana) oraz `command_result`
> (`turn`/`new_game`/`order` z `changed`, `battle` z outcome i stratami dla
> `assault`/`engage`). Szczegóły w `docs/ARCHITECTURE.md` i `docs/DECISIONS.md`
> (`G66.0`…`G66.2b`). *(task-319…323)*

## Kamień milowy 67 — persystencja partii: round-trip serializacja (fundament save/load) — PRIORYTET
> DESIGN §11: gracz ma móc **zapisać/wczytać stan**. Dziś `save_state` daje tylko
> stratny snapshot (widok OUT), bez odczytu. Budujemy w TDD round-trippowalną
> serializację w nowym module `tbbbridge.persist` — **oddolnie**, od typów
> liściowych ku kompozytom (osada/party/świat/sesja w kolejnych wsadach). Rdzeń
> `tbb` bez zmian; most reużywa wyłącznie publiczne API i konstruktory rdzenia.
> **G67.1 liście — UKOŃCZONE.** Round-trip typów liściowych w `tbbbridge.persist`:
> `dump/load_resources` (G67.1a), `dump/load_wound` (G67.1b, w tym
> `duration_months=None`), `dump/load_unit` (G67.1c), `dump/load_building`
> (G67.1d), `dump/load_calendar` (G67.1e). Szczegóły w `docs/ARCHITECTURE.md`
> (sekcja „Persystencja round-trip") i `docs/DECISIONS.md`. *(task-324…328)*

> **Kamień 67 — UKOŃCZONE.** Round-trip serializacja w `tbbbridge.persist`
> oddolnie aż do sesji: kompozyty (`dump/load_party` G67.2a, `settlement`
> G67.2b, `region` G67.2c, `world` G67.2d, `duchy` G67.2e, `gamestate` G67.2f),
> seam RNG w rdzeniu (`Rng.state`/`from_state` G67.3a) i jego most
> (`dump/load_rng` G67.3b) oraz sesja (`dump/load_session` G67.4a; `last_battle`
> nietrwałe, `None` po wczytaniu). Szczegóły w `docs/ARCHITECTURE.md` i
> `docs/DECISIONS.md`. *(task-329…337)*

> **Kamień 68 — UKOŃCZONE.** Save/load w protokole JSON Lines: `handle_command_line`
> obsługuje `{"type":"save"|"load","path":...}` w warstwie protokołu (reużycie
> `persist.save_session`/`read_session`, IO poza `apply_command`), `command_result`
> daje `{"kind":"save"|"load","path":...}`, błędy (`path`/`OSError`/`JSONDecodeError`)
> → `{"ok":false,"error":...}`; e2e round-trip po stdio (`order`→`save`→`new_game`
> →`load`) odtwarza snapshot i dalszą sekwencję RNG. *(task-339…341)*

> **Kamień 69 — UKOŃCZONE.** Dopełnienie pętli gracza: komenda protokołu
> `snapshot` (czysty odczyt bez mutacji/RNG, `command_result`→`{"kind":"snapshot"}`;
> G69.1a) oraz wznowienie zapisanej partii z pliku — CLI `serve --resume <path>`
> (`read_session` zamiast `new_session`; G69.2a), błędy wznowienia
> (brak/niepoprawny plik → `stderr` + kod `1`, bez startu pętli; G69.2b) i e2e
> zapis-w-jednym / wznowienie-w-drugim procesie z ciągłością RNG przez plik
> (G69.2c). Szczegóły w `docs/ARCHITECTURE.md`, `docs/DESIGN.md` §11 i
> `docs/DECISIONS.md` (`G69.1a`…`G69.2b`). *(task-342…345)*

> **Kamień 70 — UKOŃCZONY.** Round-trip `HexBattle`, trwałe `last_battle` i
> weryfikacja protokołu e2e `save`→`new_game`→`load` są gotowe. Szczegóły
> przeniesione do `BACKLOG-ARCHIVE.md`. *(task-346…351)*

## Kamień milowy 71 — bootstrap natywnego klienta Godot — PRIORYTET
> Po domknięciu mostu zaczynamy widoczny klient w `game/`. Bootstrap, toolchain
> i integracja z procesem Python są zadaniami `complex` i przechodzą review
> agent-loop. Godot konsumuje JSON Lines z istniejącego `tbbbridge`; nie
> duplikuje reguł `tbb`.
> **G71.0 — UKOŃCZONE.** Minimalny projekt Godot 4 ma główną scenę `Control`
> i stabilną strukturę `game/`; szczegóły przeniesione do
> `BACKLOG-ARCHIVE.md`. *(task-352)*
> **G71.1a2a — UKOŃCZONE.** Bramka headless rozróżnia sukces i celową porażkę
> skryptu Godota także z `SceneTree._init()`. Szczegóły w
> `BACKLOG-ARCHIVE.md`. *(task-361)*
> **G71.1a2b — PONOWNIE ROZCIĘTE PO `coder_red` task-362.** Porzucona próba
> pomyliła liść `snapshot.result.player_result` z całym `snapshot.result`;
> projekcja idzie teraz po jednym polu/grupie pól, a mutacja tego liścia osobno.
- [x] **G71.1a2b1…G71.1a3** `SnapshotModel` po jednym polu/grupie pól: `year`+
      `month`, `regions`, liść `player_result`, bramka mutacyjna liścia oraz
      atomowe odrzucanie błędnych/niepełnych odpowiedzi → `null`.
      *(task-366…370)*
- [x] **G71.1b1…G71.1b2** Nazwane kontrolki daty/regionów/wyniku w głównej scenie
      i render fixture przez `SnapshotModel` (pierwotne task-364/365 porzucone po
      porażce task-362; wykonane w serii task-406…419).
> **G71.1a2b1…G71.2a — UKOŃCZONE.** `SnapshotModel` (kalendarz, regiony, liść
> `player_result`, atomowa walidacja → `null`), nazwane kontrolki i idempotentne
> `apply_model` w głównej scenie, bramka na żywym snapshocie mostu oraz klient
> procesu JSON Lines (`bridge_client.gd`: `request_line`/`first_response`,
> `send`, `snapshot_model`) wpięty w scenę przez `main.gd.refresh_from_bridge`.
> *(task-366…369, task-406…419)*

## Kamień milowy 72 — trwała partia w kliencie Godota (sekwencje komend + plik stanu)
> Godot 4.2.2 nie ma `OS.execute_with_pipe`, więc most wołamy jedno-strzałowo,
> a partia musi przeżyć między wywołaniami. Droga: wiele komend w jednym
> uruchomieniu procesu (`next_turn` + `save`) i wznowienie przez
> `serve --resume <plik stanu>` — oba mechanizmy istnieją już w `tbbbridge`
> (K68/K69) i zostały zweryfikowane empirycznie przy planowaniu.
- [x] **G72.1a** `BridgeClient.request_lines` / `all_responses` — czysta warstwa
      wielolinijkowego JSON Lines (bez procesu). *(task-420)*
- [x] **G72.1b** `BridgeClient.send_many()` — sekwencja komend do żywego mostu
      w jednym uruchomieniu procesu. *(task-421)*
- [x] **G72.2a** Komenda startowa mostu zależna od pliku stanu (świeże ziarno vs
      `serve --resume`) + `create_persistent`. *(task-422)*
- [x] **G72.2b** `BridgeClient.advance_turn()` — tura utrwalona w pliku stanu;
      dwa procesy = dwie kolejne tury tej samej partii. *(task-423)*
- [x] **G72.3** Wejście gracza w scenie: przycisk „Następna tura” (G72.3a),
      `advance_turn_from_bridge` (G72.3b), `bind_client` (G72.3c) i e2e trwałej
      partii przez dwa procesy mostu (G72.3d).

## Kamień milowy 73 — samodzielny start klienta Godota (konfiguracja + autostart)
> Dziś partię składa wyłącznie sonda testowa: nikt nie tworzy klienta przy
> starcie gry. K73 daje klientowi jawne wejście uruchomieniowe (komenda mostu,
> plik stanu, ziarno ze zmiennych `TBB_*`), granicę startu w scenie i autostart
> w `_ready()`, który bez konfiguracji jest bezpiecznym no-opem (sceny są
> instancjonowane też przez istniejące sondy — zweryfikowane empirycznie:
> `_ready()` odpala się przy `root.add_child`).
- [x] **G73.1a** `bridge_config.gd`: czysta `from_values` (atomowa walidacja
      komendy, ścieżki stanu i ziarna). *(task-428)*
- [x] **G73.1b** `BridgeConfig.from_environment()` — `TBB_BRIDGE_COMMAND` /
      `TBB_STATE_PATH` / `TBB_SEED`; brak lub błąd → `null`. *(task-429)*
- [x] **G73.2a** `main.gd.start_session(config)` — trwały klient, `bind_client`
      i render bieżącego stanu bez przesuwania tury. *(task-430)*
- [x] **G73.2b** Autostart w `_ready()` + e2e ciągłości partii (no-op bez
      konfiguracji). *(task-431)*

## Kamień milowy 74 — stan księstwa gracza w kliencie Godota
> Klient pokazuje datę, regiony i wynik, ale nie wie, **które księstwo jest
> gracza** — snapshot niesie listę `duchies` bez wskaźnika na gracza
> (zweryfikowane empirycznie na `seed=73`). K74 dokłada ten wskaźnik w moście,
> projekcję statusu w `SnapshotModel` i render w scenie, aż do odświeżenia po
> naciśnięciu „Następna tura".
- [x] **G74.1a** Snapshot wskazuje księstwo gracza (`player_duchy`, `None` bez
      gracza; sesja i protokół niosą ten sam klucz). *(task-433)*
- [x] **G74.1b** `SnapshotModel` wystawia status księstwa gracza (morale, osady,
      oddziały) albo jednoznaczny brak; atomowa walidacja bez zmian. *(task-434)*
- [x] **G74.2a** Scena renderuje status księstwa gracza i odświeża go po turze
      (e2e autostartu i ciągłości partii). *(task-435)*

## Kamień milowy 75 — rozkazy gracza w kliencie Godota (pierwszy rozkaz: rozwój)
> Klient umie dziś tylko czytać snapshot i przesuwać turę. Most (`tbbbridge`)
> obsługuje pełen zestaw rozkazów gracza od K65 — zweryfikowane empirycznie:
> sekwencja `order:develop` + `save` w jednym uruchomieniu daje `changed=true`
> i utrwala stan, a `serve --resume` startuje po rozkazie bez przesunięcia
> kalendarza. K75 doprowadza tę ścieżkę do przycisku w scenie.
- [x] **G75.1a** `BridgeClient.send_order()` — rozkaz + zapis stanu w jednym
      uruchomieniu procesu; `SnapshotModel` albo `null`. *(task-436)*
- [x] **R75.1 (dług techniczny)** Jeden prymityw sekwencji „komenda + zapis"
      reużyty przez `advance_turn` i `send_order`. *(task-437)*
- [x] **G75.1b** Scena ma nazwany przycisk „Rozwiń osadę" (bez wiązania).
      *(task-438)*
- [x] **G75.1c** Klik rozwoju wydaje rozkaz przez most, odświeża scenę i
      utrwala partię (e2e przez dwa procesy). *(task-439)*

## Kamień milowy 76 — informacja zwrotna o rozkazie w kliencie Godota
> Klik „Rozwiń osadę" wydaje rozkaz i odświeża scenę, ale gracz nie wie, czy
> rozkaz cokolwiek zmienił — most niesie to w `result.changed`, a klient je
> wyrzuca. Zweryfikowane empirycznie (`serve 73`): cztery pierwsze `develop`
> dają `changed:true`, piąty `changed:false` przy `ok:true`.
- [x] **G76.1a** `order_result.gd` — czysta, atomowa projekcja `result` rozkazu
      (albo `null`). *(task-440)*
- [x] **G76.1b** `BridgeClient` wystawia wynik ostatniego rozkazu obok modelu.
      *(task-441)*
- [x] **G76.2a** Scena ma nazwaną kontrolkę statusu rozkazu (bez wiązania).
      *(task-442)*
- [x] **G76.2b** Klik rozwoju pokazuje „zmieniono"/„bez zmian" (e2e przez dwa
      procesy). *(task-443)*

## Kamień milowy 77 — drugi rozkaz gracza w kliencie Godota (rekrutacja)
> Klient wydaje dziś tylko `develop`, a ścieżka rozkazu jest zaszyta pod tę
> jedną nazwę (`develop_from_bridge` + własna gałąź tekstu statusu). K77
> uogólnia ścieżkę i dokłada drugi rozkaz — rekrutację. Most obsługuje
> `recruit` od K65; zweryfikowane empirycznie (`serve 73`): pięć pierwszych
> `recruit` daje `changed:true`, szósty i dalsze `false` przy `ok:true`,
> a nieznany rozkaz → `ok:false`.
- [x] **G77.1a** `order_result.gd` — czysty polski tekst statusu rozkazu
      (zmieniono / bez zmian / brak wyniku), rozróżniający rozkazy. *(task-444)*
- [x] **G77.1b** `main.gd` wydaje dowolny rozkaz jedną, parametryzowaną
      ścieżką; `develop_from_bridge` zostaje cienkim wrapperem. *(task-445)*
- [x] **G77.2a** Scena ma nazwany przycisk „Rekrutuj jednostkę" (bez wiązania).
      *(task-446)*
- [x] **G77.2b** Klik rekrutacji wydaje rozkaz, pokazuje skutek i utrwala
      partię (e2e przez dwa procesy). *(task-447)*

## Kamień milowy 78 — trzeci rozkaz gracza (zbiórka) i czytelna porażka rozkazu
> Ścieżka rozkazu jest od K77 parametryzowana, więc kolejny rozkaz to już tylko
> tekst statusu, przycisk i wiązanie. Osobno domykamy cichą lukę: gdy most nie
> zwróci modelu, klient czyści status do pustego tekstu i gracz nie wie, że
> rozkaz się nie powiódł. Zweryfikowane empirycznie (`serve 73`): pierwszy
> `muster` → `changed:true`, kolejne → `false` przy `ok:true`; nieznany rozkaz →
> `{"ok":false,"error":"Unknown order: …"}`.
- [x] **G78.1a** `order_result.gd` — tekst statusu rozróżnia rozkaz `muster`.
      *(task-448)*
- [x] **G78.1b** Scena ma nazwany przycisk „Zbierz oddział" (bez wiązania).
      *(task-449)*
- [x] **G78.1c** Klik zbiórki wydaje rozkaz, pokazuje skutek i utrwala partię
      (e2e przez dwa procesy). *(task-450)*
- [x] **G78.2a** Nieudany rozkaz pokazuje czytelny komunikat zamiast pustego
      statusu. *(task-451)*

## Kamień milowy 79 — czwarty rozkaz gracza (marsz) w kliencie Godota
> Ścieżka rozkazu jest parametryzowana od K77, więc marsz to tekst statusu,
> przycisk i wiązanie. Najpierw jednak spłacamy dług: scena szuka wyniku
> ostatniego rozkazu skanując `get_property_list()` klienta — ukryty kontrakt
> po nazwie pola. Zweryfikowane empirycznie (`serve 73`): sam `march` na
> świeżej partii → `changed:false`; `muster` → `march` → `changed:true`,
> kolejne `march` → `false`.
- [x] **R79.1 (dług techniczny)** Jawne API wyniku ostatniego rozkazu w
      `BridgeClient` zamiast skanowania `get_property_list` w `main.gd`
      + testy regresji statusu rozkazu. *(task-452)*
- [x] **G79.1a** `order_result.gd` — tekst statusu rozróżnia rozkaz `march`.
      *(task-453)*
- [x] **G79.1b** Scena ma nazwany przycisk „Wyrusz w pole" (bez wiązania).
      *(task-454)*
- [x] **G79.1c** Klik marszu wydaje rozkaz, pokazuje skutek i utrwala partię
      (e2e przez dwa procesy). *(task-455)*

## Kamień milowy 80 — piąty rozkaz gracza (szturm) i wynik bitwy w kliencie
> Szturm to pierwszy rozkaz, który zwraca **inny kształt wyniku**: most daje
> `result.kind == "battle"` (outcome + straty stron), a nie
> `{"kind":"order","changed":…}`. Klient dziś taki wynik odrzuca i zostawia
> pusty status. Zweryfikowane empirycznie (`serve 73`, trzy procesy na wspólnym
> pliku stanu): `muster`→`march`→`save`; po `--resume` `assault` →
> `{"kind":"battle","outcome":"porażka","attacker_losses":0,
> "defender_losses":0}`; kolejny `assault` → `{"kind":"order","changed":false}`.
- [x] **G80.1a** `order_result.gd` — atomowa projekcja wyniku bitwy
      (`kind:"battle"`) obok projekcji rozkazu. *(task-456)*
- [x] **G80.1b** `order_result.gd` — polski tekst statusu szturmu i skutku
      bitwy (wynik + straty), bez zmian pozostałych statusów. *(task-457)*
- [x] **G80.2a** Scena ma nazwany przycisk „Szturmuj osadę" (bez wiązania).
      *(task-458)*
- [x] **G80.2b** Klik szturmu wydaje rozkaz, pokazuje skutek bitwy i utrwala
      partię (e2e przez procesy `serve` + `--resume`). *(task-459)*

## Kamień milowy 81 — położenie oddziału gracza w kliencie — UKOŃCZONY
> **UKOŃCZONE.** `SnapshotModel.player_party_region` (G81.1a), render położenia
> w scenie (G81.1b), e2e „rozkazy przesuwają widoczny oddział" przez dwa procesy
> (G81.2a) oraz refaktor jednej ścieżki wydawania rozkazu (R81.1). Zaplanowane i
> wykonane poza tym plikiem — dopisane tu dla ciągłości numeracji.

## Kamień milowy 82 — klient startuje bez terminala (domyślna konfiguracja) — PRIORYTET
> **Zwrot kierunku (przegląd bootstrap-diff).** K75–K81 to była seria „kolejny
> przycisk rozkazu"; ścieżka rozkazu jest już sparametryzowana, więc szósty
> przycisk nie zbliża do celu z briefu. Kryterium „gotowe" mówi: gracz uruchamia
> **natywną aplikację na Linuksie i bez terminala** zarządza osadą, przemieszcza
> armię, rozgrywa bitwę, zapisuje i wczytuje stan. Dziś `_ready()` startuje partię
> **wyłącznie** przy ustawionych `TBB_BRIDGE_COMMAND`/`TBB_STATE_PATH`/`TBB_SEED`
> — bez nich `BridgeConfig.from_environment()` daje `null` i scena jest martwa.
> K82 usuwa terminal ze ścieżki startu. Rdzeń `tbb` i most bez zmian.
- [x] **G82.1a** `BridgeConfig.default_values()` — czysta funkcja dająca
      kompletną, poprawną konfigurację bez środowiska (komenda mostu, ścieżka
      stanu w katalogu danych użytkownika, domyślne ziarno); wynik przechodzi
      `is_valid_session_config`. *(simple)*
- [x] **G82.1b** `from_environment()` uzupełnia **brakujące lub niepoprawne**
      zmienne wartościami domyślnymi zamiast zwracać `null`; jawnie ustawione
      `TBB_*` nadal nadpisują domyślne. Testy regresji dotychczasowych odrzuceń
      przenoszą się na `from_values` (kontrakt walidacji bez zmian). *(standard)*
- [x] **G82.2a** Scena po `_ready()` w środowisku **bez żadnych `TBB_*`** startuje
      partię i renderuje datę oraz status księstwa (sonda headless na tymczasowym
      katalogu stanu). *(standard)*
- [x] **G82.2b** Most daje się uruchomić z katalogu projektu Godota bez ręcznego
      `PYTHONPATH` z terminala: domyślna komenda rozwiązuje interpreter i pakiet
      `tbbbridge` względem lokalizacji gry, a e2e w czystym środowisku daje dwa
      kolejne snapshoty tej samej partii. *(complex, ryzyko: ścieżki `res://` vs
      katalog roboczy procesu, brak Pythona → czytelny komunikat w scenie zamiast
      cichej martwej sceny)*

## Kamień milowy 83 — czytelny układ ekranu — UKOŃCZONY
> **UKOŃCZONE.** K83.1: kontrolki sceny w kontenerach zamiast wspólnego punktu
> (0,0) — prostokąty parami rozłączne, `RegionList` o niezerowym rozmiarze,
> grupa stanu oddzielona od grupy rozkazów, nazwy kontrolek bez zmian.
> *(task-471)*

## Kamień milowy 84 — widok mapy 2D w kliencie Godota — UKOŃCZONY
> Następny punkt kryterium „da się grać patrząc, a nie czytając logi": mapa
> istnieje w kliencie wyłącznie jako `ItemList` nazw. Most niesie siatkę od
> dawna — zweryfikowane empirycznie (`serve 73`): `map.regions` ma `name`,
> `col`, `row`, `owner` (`"player"`/`"ai"`/`null`), a po `muster`→`march`
> oddział gracza stoi w regionie `border`. Rdzeń `tbb` i most bez zmian.
- [x] **R83.1 (dług techniczny)** Jedno miejsce walidacji regionów: model
      wystawia regiony gotowe do pokazania, scena nie powtarza sprawdzeń
      surowych słowników + testy regresji. *(simple, task-472)*
- [x] **G84.1a** Model niesie `col`, `row` i właściciela regionu; region bez
      poprawnych współrzędnych odpada. *(simple, task-473, commit d666192)*
- [x] **G84.1b** Widok mapy `MapView`: jeden kafel na region, rozmieszczenie po
      siatce, kafle rozłączne, właściciel rozróżnialny wzrokowo. *(standard,
      task-474, commit bcad83c)*
- [x] **G84.1c** Kafel oddziału gracza oznaczony i przesuwający się po rozkazach
      (e2e przez dwa procesy mostu). *(standard, task-475, commit 4af2b79)*

## Kamień milowy 85 — widok bitwy w kliencie Godota (pierwszy plasterek) — PRIORYTET
> Po mapie zostaje **jedyna całkowicie niewidoczna faza gry**: szturm daje dziś
> wyłącznie jedną linię tekstu („porażka, straty 0/0"), choć most niesie pełną
> bitwę. Kryterium z briefu wymaga obu widoków — mapy **i** bitwy. Zweryfikowane
> empirycznie (`serve 73`, sekwencja `muster`→`march`→`assault`): snapshot dostaje
> klucz `battle` z `hexes` (`q`, `r`, `terrain`: `"Plains"`, `side`:
> `"attacker"`/`"defender"`, `hp`, `stunned`) oraz `result` (`"defender_win"`);
> przed pierwszą bitwą klucza `battle` w snapshocie **nie ma**. Ograniczenie
> znane z góry: snapshot niesie tylko heksy **zajęte przez jednostki**, więc ten
> plasterek rysuje jednostki, a nie całe pole bitwy — pełna siatka terenu
> wymagałaby rozszerzenia mostu i jest świadomie odłożona. Rdzeń `tbb` bez zmian;
> wzorzec kafla i rozmieszczenia reużywamy z `MapView` (K84).
- [x] **G85.1a** `SnapshotModel` wystawia stan ostatniej bitwy: lista heksów
      gotowych do pokazania (`q`, `r`, `terrain`, `side`, `hp`) i wynik bitwy
      albo jednoznaczny brak, gdy snapshot nie ma klucza `battle`; heks bez
      poprawnych współrzędnych lub strony odpada; atomowa walidacja modelu bez
      zmian. *(simple, task-476)*
- [x] **G85.1b** Widok bitwy `BattleView`: jeden kafel na heks bitwy,
      rozmieszczenie po współrzędnych osiowych `(q, r)`, kafle parami rozłączne,
      strona (atakujący/broniący) rozróżnialna wzrokowo; brak bitwy → pusty
      widok bez błędu. *(standard, task-477)*
- [x] **G85.1c** Klik „Szturmuj osadę” pokazuje bitwę na siatce zamiast samego
      tekstu: po rozkazie widok ma kafle obu stron, wynik bitwy jest czytelny na
      ekranie, a partia zostaje utrwalona (e2e przez dwa procesy mostu).
      *(standard, task-478, commit a4966d4)*

## Kamień milowy 86 — zapis i odczyt partii z UI — PRIORYTET
> Po widoku mapy (K84) i bitwy (K85) zostaje punkt kryterium „gotowe”, który
> gracz dziś **w ogóle nie ma jak wykonać**: zapisać i wczytać stan bez
> terminala. Protokół ma `save`/`load` od K68/K69, klient ich nie używa i nie
> zna żadnej ścieżki zapisu. Zweryfikowane empirycznie (`serve 73`, trzy procesy
> na wspólnym pliku stanu): `save SLOT` → `{"kind":"save"}`; po `--resume`
> `next_turn` → `rok 1, miesiąc 2`; `load SLOT` → `{"kind":"load"}` i kalendarz
> z powrotem `rok 1, miesiąc 1`; kolejny proces to potwierdza, o ile po `load`
> poszedł `save` do pliku stanu; `load` nieistniejącego pliku → `ok:false`.
> Rdzeń `tbb` i most bez zmian.
> **Odłożone świadomie:** „rozkaz klikiem na cel na mapie” (następny punkt listy
> kierunków) — most przyjmuje `target` w `march`/`assault`, ale w obecnym
> trzyregionowym świecie (`player lands` — `border` — `ai lands`) rozkaz celowany
> daje **ten sam** skutek co automatyczny (`next_march_step` zwraca `None`, gdy
> cel sąsiaduje). Nie da się dziś napisać kryterium, które odróżnia klik od
> automatu; wraca po większej mapie albo po zmianie semantyki celu.
- [x] **G86.1a** Konfiguracja niesie ścieżkę zapisu partii gracza (`save_path`
      w katalogu danych użytkownika, `TBB_SAVE_PATH` nadpisuje, walidacja sesji
      jej wymaga). *(simple, task-479, commit 65dd536)*
- [x] **G86.1b** `BridgeClient` zapisuje partię do pliku i wczytuje ją z
      utrwaleniem w pliku stanu (kolejny proces widzi wczytany stan); błąd →
      `null`. *(standard, task-480, commit 9ebf1be)*
- [ ] **G86.2a** Scena ma nazwane przyciski „Zapisz partię” / „Wczytaj partię”
      (bez wiązania). *(simple, task-481)*
- [ ] **G86.2b** Klik zapisu i wczytania przywraca zapisany stan na ekranie,
      pokazuje czytelny skutek i utrwala partię (e2e przez dwa procesy mostu).
      *(standard, task-482)*

## Kamień milowy 87 — prawdziwe assety zamiast kolorowych prostokątów — PRIORYTET
> **Nowe wymaganie z briefu (feedback autora, 2026-07-27):** *„prawdziwe MVP
> będzie wtedy, kiedy będą assety i tekstury. Nie musi być dużo budynków /
> rodzajów jednostek / terenu itp, ale żeby były jakieś sensowne prawdziwe
> assety."* Stan faktyczny: w repo **nie ma ani jednego pliku graficznego** —
> `MapView` i `BattleView` rysują `ColorRect` w jednolitym kolorze z `Label`
> pośrodku. K84/K85 domknęły geometrię (siatka, współrzędne osiowe, rozłączne
> kafle, rozróżnialne strony); K87 podmienia **nośnik**, nie układ — istniejące
> testy rozmieszczenia zostają w mocy.
> **Zweryfikowane przy przeglądzie:** sieć działa (`kenney.nl`, `opengameart.org`
> odpowiadają `200`), więc paczka CC0 jest do pobrania; `godot` jest w `PATH`.
> Rdzeń `tbb` i most bez zmian — to zadanie wyłącznie po stronie `game/`.
> **Ryzyko nazwane z góry:** sondy headless ładują dziś tylko skrypty. Tekstura
> wymaga artefaktów importu Godota (`godot --headless --import`) i katalogu
> `.godot/`, którego **nie ma w `.gitignore`** — pierwszy plasterek musi to
> rozstrzygnąć w bramce, zanim ktokolwiek ruszy widoki.
>
> **Kontrakt terenu — sprawdzony w kodzie przy tym przeglądzie (poprawka po
> recenzji):** teren istnieje **wyłącznie w warstwie bitwy**. `tbb.terrain`
> (`PLAINS`/`FOREST`/`HILLS`) konsumuje `Battlefield.terrain_at`, a
> `snapshot.battle_state` (`src/tbbbridge/snapshot.py:229`) daje `terrain` per
> heks. Na mapie strategicznej terenu **nie ma**: `tbb.world.Region` ma tylko
> `name`, a `snapshot.map_state` (`snapshot.py:103-130`) wystawia na region
> `name`, `col`, `row`, `owner`, `settlement`, `party`. Dlatego G87.1b **nie
> rysuje terenu regionu** — kafel mapy dobiera teksturę po tym, co most naprawdę
> niesie (`owner`, obecność osady). Rozszerzenie `Region`/`map_state` o teren
> regionu to osobny plasterek dotykający rdzenia i mostu — **świadomie odłożony**
> (patrz „Kolejne kierunki"), żeby K87 pozostał zadaniem po stronie `game/`.
> Zakres treści trzymamy mały: 1 kafel gruntu mapy + rozróżnienie właściciela,
> 3 tekstury terenu bitwy (`Plains`/`Forest`/`Hills` — tyle zna rdzeń), 2 strony
> bitwy, 1 znacznik oddziału gracza. Nie dokładamy typów jednostek ani budynków,
> żeby mieć co teksturować.
> **Nota dla kodera G87.1c:** w realnej rozgrywce `world.py` tworzy
> `HexBattle(Battlefield())`, więc każdy heks zwraca `Plains`. Mapowanie
> teren→tekstura testuj na fixture snapshotu (`Forest`/`Hills` też), nie licz na
> zróżnicowany teren w e2e szturmu.
- [ ] **G87.1a** Paczka assetów CC0 w repo i ładowalna z Godota: pliki w
      `game/assets/` (kafle terenu + sylwetki stron), `game/assets/CREDITS.md` z
      licencją i źródłem, `.godot/` poza gitem, a bramka headless dowodzi, że
      `load("res://assets/…")` zwraca `Texture2D` (nie `null`) po kroku importu.
      *(complex, ryzyko: import Godota w headless, brak szablonów/edytora,
      licencja assetów — bez CC0/CC-BY nie wchodzi do repo)*
- [ ] **G87.1b** `MapView` rysuje kafel regionu **teksturą** zamiast
      `ColorRect`: kafel to węzeł z prawdziwą `Texture2D` z `game/assets/`,
      właściciel (`player`/`ai`/brak) nadal jednoznacznie rozróżnialny wzrokowo,
      obecność osady (klucz `settlement` z mostu) widoczna jako obrazek, oddział
      gracza oznaczony teksturą zamiast `ColorRect`, kafle nadal parami
      rozłączne. **Bez pojęcia terenu na mapie strategicznej** — most go nie
      niesie (patrz „Kontrakt terenu" wyżej); nie wolno wymyślać terenu regionu
      po stronie klienta ani zmieniać rdzenia/mostu w tym zadaniu. Testy
      rozmieszczenia z K84 przechodzą bez zmian w kryteriach. *(standard)*
- [ ] **G87.1c** `BattleView` rysuje heks **teksturą terenu** i stronę
      **sylwetką jednostki** zamiast koloru: `terrain` z `battle.hexes` (jedyne
      miejsce, gdzie most niesie teren) wybiera obrazek kafla, `side` wybiera
      sylwetkę, nieznany teren → kafel domyślny bez błędu, brak bitwy → pusty
      widok bez błędu. Rozmieszczenie po `(q, r)` z K85 bez zmian. *(standard)*

## Dług/refaktor
- [x] **R82.1 (dług, prośba autora briefu)** Porządek w repo gry: sondy testowe
      poza kodem produkcyjnym klienta (R82.1a) i wygenerowane artefakty `out/`
      poza gitem (R82.1b). *(task-469, task-470)*
- [x] **R73.1 (dług techniczny)** Jedno źródło reguł poprawnej konfiguracji
      startowej: `main.gd._is_valid_session_config` duplikował warunki
      `BridgeConfig.from_values`; scalone w `BridgeConfig` + testy regresji.
      *(task-432)*
- [x] **R33.1 (refaktor)** Kompaktacja DESIGN.md §11: usunięcie bloków narracyjnych „PLAN K14…K33" (historia → git/DECISIONS.md); tylko stan obecny. *(task-169)*
- [x] **R21.1 (refaktor)** Wspólny emiter formularzy celu marsz/szturm/starcie w `serve.py`. *(task-113)*
- [x] **R15.1 (refaktor)** Kompaktacja DESIGN.md do stanu obecnego; historia → DECISIONS.md. *(task-094)*
- [x] **R16.1 (refaktor)** Wspólny generator formularzy celu marsz/szturm w `serve.py`. *(task-098)*

## Kolejne kierunki (po K87, do rozplanowania na kamienie)
> Kolejność wynika z kryterium „gotowe" w `docs/PROJECT.md`. **Nie dokładamy
> kolejnych przycisków rozkazu ani reguł rdzenia, dopóki te punkty stoją** —
> most obsługuje więcej rozkazów, niż klient potrafi pokazać. Od 2026-07-27
> dochodzi twarde: **bez assetów nie ma MVP**, więc rozbudowa treści (typy
> jednostek, budynki, tereny) czeka na to, aż istniejąca treść będzie narysowana.
- Rozkaz wybierany klikiem na cel na mapie, nie globalnym przyciskiem — czeka na
  większą mapę (w obecnym trzyregionowym świecie klik nie różni się skutkiem od
  automatu; uzasadnienie przy K86).
- ~~Zapis/odczyt z UI: jawne „Zapisz”/„Wczytaj”~~ — rozplanowane jako K86.
- ~~Prawdziwe assety i tekstury zamiast `ColorRect`~~ — rozplanowane jako K87.
- Assety pozostałych elementów sceny (osady/budynki na mapie, tło, ikony
  rozkazów) — dopiero gdy K87 dowiedzie, że ścieżka import→tekstura stoi.
- **Teren regionu na mapie strategicznej** — `tbb.world.Region` ma dziś tylko
  `name`, więc `snapshot.map_state` nie ma czego wystawić i kafel mapy w K87
  różnicuje wyłącznie właściciela i osadę. Jeśli zróżnicowana mapa okaże się
  potrzebna, idzie to jako **osobny cienki plasterek dotykający rdzenia i
  mostu**: pole terenu w `Region` (reuse `tbb.terrain`) → `map_state` →
  `SnapshotModel` → wybór tekstury w `MapView`. Świadomie odłożone przy
  przeglądzie 2026-07-27: nie jest warunkiem „prawdziwych assetów" z briefu, a
  wpuszczone do K87 rozsadziłoby plasterek deklarowany jako „tylko `game/`".
- Pakiet na Linuksa x86-64: preset eksportu + runtime Pythona, uruchomienie
  jedną ikoną — domknięcie kryterium „gotowe". **Uwaga z przeglądu:** domyślna
  komenda mostu składa ścieżkę `res://../src`, co działa wyłącznie w drzewie
  źródeł — po eksporcie „start bez terminala" (K82) trzeba zweryfikować od nowa,
  a `src/` dołączyć do pakietu. W środowisku brak zainstalowanych szablonów
  eksportu Godota — to prerekwizyt toolchainu tego kamienia. Po K87 dochodzi
  dołączenie assetów i pliku atrybucji do pakietu.
- Pełne pole bitwy (teren pustych heksów, wymiary pola) — wymaga rozszerzenia
  `tbbbridge.snapshot.battle_state`; dopiero gdy sam widok bitwy (K85) stoi.
- Sterowanie pojedynczą jednostką w bitwie — po K85.

## Później (poza MVP)
- [ ] **K62 (WSTRZYMANE — DECISIONS G63.0)** Rozbudowa alertu gospodarczego HTML
      (osada priorytetowa + remedium: `data-priority-settlement` /
      `data-priority-hint` / `data-priority-remedy`). Zaplanowane task-292…295
      **zdjęte z kolejki i usunięte** — to dalsza polish diagnostycznego klientu
      HTML, którą brief degraduje na rzecz klienta Godota. Podjąć dopiero, jeśli
      wróci realna potrzeba tej podpowiedzi (najpewniej już jako element klienta
      Godota, nie HTML).
- [ ] **R12.1 (opcjonalny dług)** Wspólna kwerenda własnych osad w `ai.py`:
      generator `_owned_settlements(world, duchy_id)` reużyty przez
      `develop_duchy_settlement`/`raise_duchy_hero`/`recruit_duchy_unit`/
      `muster_duchy_party`. Zdjęty z K12 po dwóch micro-cap porażkach refaktorów
      w pętli — duplikacja ~4 linii × 4 funkcje nie blokuje MVP. Podjąć tylko
      gdy pojawi się kolejny konsument tego wzorca.
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] Balans ekonomii, tempa rozwoju jednostek i krzywych progresji; strojenie AI.
- [ ] Pełna maszyna faz `StrategicTurn` w headless driverze (routing akcji AI przez
      fazy ruch/bitwy zamiast bezpośredniego `take_duchy_turn`). M8 reużywa tylko
      prymitywów `tick_settlements`/`end_turn`, bez wciągania phase-gatingu.
- Dług dokumentacji: `docs/ARCHITECTURE.md` ma 116 KB — zaplanuj podział pliku.
- Dług dokumentacji: `docs/DESIGN.md` ma 27 KB — zaplanuj podział pliku.
- Dług dokumentacji: `docs/DECISIONS.md` ma 74 KB — zaplanuj podział pliku.
