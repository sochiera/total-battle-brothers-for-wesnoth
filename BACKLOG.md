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

### Bramka planowania oprawy (brief 2026-07-30) — ODWOŁANA 2026-08-06
**[W] Do jawnego osiągnięcia progu wizualnego każde wywołanie planisty i każdy
nowy batch Forge miał dać 4–6 zadań, w tym co najmniej 4 graficzne i najwyżej 2
mechaniczne.** Próg został jawnie osiągnięty po akceptacji K106; od tej daty
bramka nie obowiązuje.
Podczas obowiązywania bramki zadanie mechaniczne wolno było dołączyć tylko jako
bezpośrednią, niezbędną zależność bieżącego efektu graficznego. Brak czterech
gotowych zadań graficznych oznaczał obowiązek dopisania małych zadań graficznych,
nie `no_more_tasks`.

Zadanie liczyło się jako graficzne tylko wtedy, gdy wskazywało konkretny asset lub
element oprawy i miejsce użycia, daje widoczną zmianę w uruchomionym Godocie,
kończy się screenshotem albo ludzkim review oraz utrzymuje per-plikowe źródło
i licencję w `game/assets/CREDITS.md`. Sam test, dokumentacja lub refaktor nie
liczył się jako grafika. K87 było wyłącznie minimum technicznym. Warunek ten
został spełniony: mapa, osady, armie, bitwa i UI są spójne i wolne od
przypadkowych placeholderów, CREDITS nie ma luk, a człowiek zaakceptował
screenshoty i stan został zapisany tutaj oraz w `docs/PROJECT.md`.

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
- [x] **G86.2a** Scena ma nazwane przyciski „Zapisz partię” / „Wczytaj partię”
      (bez wiązania). *(simple, task-481, commit ed6cf89)*
- [x] **G86.2b** Klik zapisu i wczytania przywraca zapisany stan na ekranie,
      pokazuje czytelny skutek i utrwala partię (e2e przez dwa procesy mostu).
      *(standard, task-482, commit bad91bd)*
> **Kamień 86 — UKOŃCZONY.** Gracz zapisuje i wczytuje partię z UI, bez terminala.

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
> 1 bazowy kafel heksu bitwy oraz 2 dekoracje terenu (`Forest`/`Hills`), 2 strony
> bitwy, 1 znacznik oddziału gracza. Nie dokładamy typów jednostek ani budynków,
> żeby mieć co teksturować.
> **Nota dla kodera G87.1c:** w realnej rozgrywce `world.py` tworzy
> `HexBattle(Battlefield())`, więc każdy heks zwraca `Plains`. Mapowanie
> teren→tekstura testuj na fixture snapshotu (`Forest`/`Hills` też), nie licz na
> zróżnicowany teren w e2e szturmu.
- [x] **G87.1a** Paczka assetów CC0 w repo i ładowalna z Godota: pliki w
      `game/assets/` (kafle terenu + sylwetki stron), `game/assets/CREDITS.md` z
      licencją i źródłem, `.godot/` poza gitem, a bramka headless dowodzi, że
      `load("res://assets/…")` zwraca `Texture2D` (nie `null`) po kroku importu.
      *(complex, ryzyko: import Godota w headless, brak szablonów/edytora,
      licencja assetów — bez CC0/CC-BY nie wchodzi do repo; task-485,
      commit 9fd4b0a — paczka Kenney Hexagon Pack, CC0, `game/assets/CREDITS.md`)*
- [x] **G87.1b** `MapView` rysuje kafel regionu **teksturą** zamiast
      `ColorRect`: kafel to węzeł z prawdziwą `Texture2D` z `game/assets/`,
      właściciel (`player`/`ai`/brak) nadal jednoznacznie rozróżnialny wzrokowo,
      obecność osady (klucz `settlement` z mostu) widoczna jako obrazek, oddział
      gracza oznaczony teksturą zamiast `ColorRect`, kafle nadal parami
      rozłączne. **Bez pojęcia terenu na mapie strategicznej** — most go nie
      niesie (patrz „Kontrakt terenu" wyżej); nie wolno wymyślać terenu regionu
      po stronie klienta ani zmieniać rdzenia/mostu w tym zadaniu. Testy
      rozmieszczenia z K84 przechodzą bez zmian w kryteriach. *(standard,
      task-486, commit 8424b73)*
- [x] **G87.1c-1** `BattleView` rysuje heks **teksturą terenu**: `terrain`
      z `battle.hexes` wybiera obrazek kafla, nieznany teren → kafel domyślny bez
      błędu, brak bitwy → pusty widok bez błędu. Rozmieszczenie po `(q, r)` z K85
      bez zmian. *(standard, task-487, commit 4bf7b09)*
> **Audyt assetów przy przeglądzie 2026-07-27 — G87.1c rozcięte na dwa
> plasterki.** Pliki `side_attacker.png` / `side_defender.png` z G87.1a **nie są
> sylwetkami jednostek**: wg `game/assets/CREDITS.md` to
> `PNG/Objects/castle_small.png` i `PNG/Tiles/Medieval/medieval_tower.png`, a
> obejrzane pokazują kamienny fort i kafel z wieżą. Hexagon Pack **nie zawiera
> żadnych postaci** (sprawdzone po liście plików). Bramka „`load()` zwraca
> `Texture2D`" tego nie wyłapała — patrz `docs/PROJECT.md`, wniosek 11.
> Gdyby G87.1c-2 poszło na tych plikach, pole bitwy pokazałoby dwa budynki jako
> obie walczące strony. Dlatego **najpierw wchodzą prawdziwe figurki (G87.1c-1b),
> dopiero potem widok (G87.1c-2)**.
- [x] **G87.1c-1b** Prawdziwe sylwetki jednostek w repo: `game/assets/side_attacker.png`
      i `game/assets/side_defender.png` niosą **figurę ludzką**, nie budynek, a
      `game/assets/CREDITS.md` wskazuje dla każdego z nich **konkretną ścieżkę
      pliku w paczce źródłowej** (nie samą nazwę paczki) wraz z licencją.
      Źródło rozstrzygnięte i sprawdzone przy przeglądzie: **Kenney „RTS Pack:
      Medieval" (CC0)**, `https://kenney.nl/assets/medieval-rts`, katalog
      `PNG/Default size/Unit/medievalUnit_*.png` — 24 top-downowe figurki
      piechoty, 64×64 RGBA z przezroczystym tłem, w wariantach kolorystycznych
      stron (`_01` niebieski, `_13` zielony); `License.txt` w zipie = CC0.
      Bramka headless dowodzi maszynowo: `load("res://assets/side_attacker.png")`
      i `…side_defender.png` zwracają `Texture2D`, oba mają przezroczystość
      (obraz RGBA), rozmiar **mniejszy od kafla terenu**, a oba pliki **różnią
      się bajtowo**. Człowiek ogląda oba obrazki przy review — to jedyny sposób
      sprawdzenia, że na obrazku jest postać. *(standard, ryzyko: pobranie paczki
      spoza repo, drugi krok importu Godota, styl niespójny z Hexagon Packiem —
      świadomie zaakceptowany, bo Hexagon Pack nie ma postaci; commit 1101cc1)*
- [x] **G87.1c-2** `BattleView` rysuje stronę **sylwetką jednostki** zamiast
      koloru: `side` (`attacker`/`defender`) wybiera obrazek z `game/assets/`
      (`side_attacker.png` / `side_defender.png`) nałożony na kafel terenu,
      nieznana strona → kafel bez sylwetki i bez błędu, rozróżnialność stron
      i rozmieszczenie z K85 zachowane. **Wymaga wcześniejszego G87.1c-1b** —
      przed nim te pliki są budynkami i zadanie dałoby wynik wprost sprzeczny
      z kryterium „da się grać patrząc". *(standard, commit 3df63d6)*
- [x] **R87.1 (dług techniczny)** Jedno źródło warstwy tekstury kafla w obu
      widokach + testy regresji. *(commit 6d10839)*
> **Kamień 87 — UKOŃCZONY.** Oba widoki rysują prawdziwe assety CC0: kafle mapy,
> bazowy heks bitwy oraz dekoracje drzewa/skały (Kenney Hexagon Pack), sylwetki
> stron bitwy (Kenney RTS Pack: Medieval), atrybucja per plik w
> `game/assets/CREDITS.md`. Rozróżnialność stron wzięła się z **dwóch różnych
> plików**, nie z `modulate` — tak jak przewidywał wniosek 12. Podmiana nośnika
> nie ruszyła geometrii: kryteria K84/K85 przeszły bez zmian.

## Kamień milowy 88 — natywny pakiet na Linuksa (domknięcie kryterium „gotowe") — PRIORYTET
> **Kontekst historyczny, zastąpiony zmianą briefu 2026-07-30:** po G87.1c-2
> uznawaliśmy, że znika ostatni brak treściowy, bo rdzeń, most, obie warstwy
> widoku, rozkazy, zapis/odczyt i pliki assetów były na miejscu. Nowa stała
> bramka oprawy mówi wprost, że K87 było tylko minimum technicznym. W K88 został
> jedyny nieodhaczony fragment kryterium sukcesu z briefu: *„użytkownik uruchamia
> **natywną aplikację** na Linuksie… bez terminala"*. Dziś jedyny sposób
> uruchomienia gry to `godot --path game` z konsoli — czyli dokładnie to, czego
> brief zabrania.
>
> **Zweryfikowane przy przeglądzie 2026-07-27:** `godot 4.2.2.stable` jest w
> `PATH`; katalog `~/.local/share/godot/export_templates/` **istnieje, ale jest
> pusty** — szablonów eksportu nie ma; `Godot_v4.2.2-stable_export_templates.tpz`
> na GitHubie odpowiada `200`, więc są do pobrania; `game/export_presets.cfg`
> **nie istnieje**; w systemie jest `python3` 3.14.4.
>
> **Rozstrzygnięcie zakresu (patrz `docs/PROJECT.md`):** pakiet **nie** wnosi
> własnego runtime'u Pythona — zakładamy `python3` obecny w systemie odbiorcy
> (jeden użytkownik na Linuksie x86-64). Brak Pythona ma dać czytelny komunikat
> w scenie, nie martwy ekran (ścieżka błędu istnieje od K82). Bundling CPythona
> to **[O]**, świadomie odłożone.
>
> **Ryzyko nazwane z góry:** `BridgeConfig._source_directory()`
> (`game/scripts/bridge_config.gd:27`) składa
> `ProjectSettings.globalize_path("res://") + "../src"`. Po eksporcie `res://`
> wskazuje wnętrze PCK, więc **domyślna komenda mostu przestaje działać** —
> „start bez terminala" (K82) trzeba udowodnić od nowa na wyeksportowanym
> binarium, a `src/` musi trafić obok niego.
- [x] **G88.1a** Bramka toolchainu eksportu: szablony eksportu 4.2.2 dostępne
      lokalnie (poza gitem), `game/export_presets.cfg` w repo z presetem
      „Linux/X11" x86-64, a `godot --headless --export-release` produkuje
      **wykonywalny plik** (istnieje, ma bit `+x`, niezerowy rozmiar) razem z
      `.pck`; artefakty eksportu poza gitem. Test dowodzi eksportu, nie działania
      gry. *(complex, commit 2effacd — `game/export_presets.cfg` w repo,
      szablony 4.2.2 doinstalowane lokalnie poza gitem)*
- [x] **G88.1b** Katalog źródeł mostu rozwiązywany odpornie na eksport: czysta
      funkcja w `BridgeConfig` wybiera katalog `src/` niezależnie od `res://`
      (kandydat obok wykonywalnego pliku gry, potem drzewo źródeł), pierwszy
      istniejący wygrywa, brak kandydata → ta sama czytelna ścieżka błędu co przy
      braku mostu. Domyślna komenda w drzewie źródeł zachowuje się jak dziś
      (testy K82 przechodzą bez zmian). *(standard, commit 96c3b5c)*
- [x] **G88.1c** Pakiet dystrybucyjny: `scripts/package.sh <cel>` buduje katalog
      z binarium, `.pck` i `src/` mostu obok binarium; niekompletny build →
      niezerowy kod i brak „udawanego" pakietu. *(standard, commit 398cb2b)*
- [x] **G88.1d** Pakiet bez sond testowych w `.pck`. *(task-495, commit c2a7683)*
- [x] **G88.1e** Sam start gry utrwala partię — ciągłość między uruchomieniami.
      *(task-496, commit f4a0bad)*
- [x] **G88.1f** Wyeksportowana gra startuje partię bez terminala, e2e **na
      pakiecie**. *(task-497, commit 55e5a1e)*
- [x] **G88.1g** Uruchomienie jednym kliknięciem — wpis `.desktop` w pakiecie.
      *(task-498, commit 787316c)*
> **Kamień 88 — UKOŃCZONY.** Formalne kryterium „natywna aplikacja bez terminala"
> jest odhaczone: pakiet startuje partię z binarium, `src/` mostu leży obok,
> `.pck` nie niesie sond testowych, a e2e dowodzi startu na samym pakiecie.

## Kamień milowy 89 — bitwa zawsze daje wynik, nigdy błędu rozkazu — PRIORYTET
> **Defekt sięgający gracza, potwierdzony ponownym uruchomieniem kodu przy
> przeglądzie 2026-07-28** (`serve 73`, `recruit`×2 → `muster` → `march` →
> `assault`): most odpowiada `{"ok": false, "error": "unknown battle result"}`,
> a klient pokazuje „rozkaz nie powiódł się". Kryterium sukcesu z briefu żąda,
> żeby gracz mógł **rozegrać bitwę** — dziś najbardziej naturalna sekwencja
> (dorekrutuj, zbierz, ruszaj, szturmuj) tę możliwość odbiera. Bez tego pakiet z
> K88 dowiezie grywalną-tylko-częściowo grę: wszystko widać, ale szturm w
> typowym składzie wywala rozkaz.
>
> **Mechanizm ustalony (nie zgadywany):** `HexBattle.auto_resolve` kończy 1000
> rund z `result() is None`, bo obie strony wciąż mają czynne jednostki, lecz
> atakujący **nie ma jak dojść** — jego jedyne pole skracające dystans zajmuje
> własny ogłuszony sojusznik (`hp=0`, `stunned=True`, zostaje na planszy), a
> `reachable()` pomija zajęte heksy. `WorldMap.resolve_settlement_battle_recorded`
> (`src/tbb/world.py:413-420`) podaje wtedy `None` do
> `apply_settlement_battle_result`, które na nie-`BattleResult` rzuca
> `ValueError("unknown battle result")` (`world.py:359`).
> **Fałszywe tropy sprawdzone empirycznie — nie zaczynaj od nich:** polegli NIE
> blokują pól (przy śmierci znikają z `units`), a podniesienie obrażeń bazowych
> do ≥ 1 nic nie zmienia (`result()` nadal `None`).
>
> Kolejność jest celowa: **najpierw domykamy kontrakt wyniku** (żaden szturm nie
> może dotrzeć do gracza jako błąd), dopiero potem ruszamy reguły ruchu. Odwrotna
> kolejność zostawia otwartą klasę „inny pat = znowu wyjątek".
- [x] **G89.1a** Nierozstrzygnięta bitwa jest **legalnym wynikiem rdzenia**, nie
      wyjątkiem: `resolve_settlement_battle*` i `resolve_party_battle*` na bitwie
      bez rozstrzygnięcia (`result() is None` po wyczerpaniu rund) zwracają świat
      w spójnym stanie — atakujący **zostaje w regionie źródłowym** ze
      swoimi ocalałymi, osada i jej garnizon bez zmian, właściciel bez zmian —
      zamiast `ValueError("unknown battle result")`. Test odtwarza dokładnie
      układ z repro (ogłuszeni sojusznicy blokujący dojście) na ustalonym ziarnie
      i sprawdza brak wyjątku oraz nienaruszony stan świata; dotychczasowe testy
      zwycięstwa/porażki/remisu przechodzą bez zmian w kryteriach. Walidacja
      *naprawdę* nieznanego wyniku (obiekt spoza `BattleResult`) zostaje błędem.
      *(standard, ryzyko: dotyka rdzenia — jedynego źródła reguł; nie zmieniać
      przy okazji reguł ruchu ani obrażeń, to osobny plasterek G89.2a)*
- [x] **G89.1b** Gracz widzi nierozstrzygnięty szturm jako **czytelny skutek, nie
      błąd**: most zwraca dla takiego szturmu `ok:true` z wynikiem bitwy
      odróżnialnym od zwycięstwa i porażki (dodatkowa wartość `outcome`), a
      scena Godota pokazuje polski status w rodzaju „szturm nierozstrzygnięty"
      wraz ze stratami, zamiast „rozkaz nie powiódł się". E2e na żywym moście
      odtwarza sekwencję z repro (`recruit`×2 → `muster` → `march` → `assault`,
      ziarno 73) i dowodzi, że partia zostaje utrwalona. Pozostałe teksty statusu
      bez zmian. *(standard, wymaga G89.1a)*
> **K89.1 — UKOŃCZONE** *(G89.1a: task-499…500; G89.1b: task-501…504)*: rdzeń
> traktuje bitwę bez rozstrzygnięcia jako legalny wynik (szturm i starcie
> oddziałów), most zwraca ją jako wynik z własnym `outcome`, scena pokazuje
> polski status „szturm nierozstrzygnięty" ze stratami, a e2e na żywym moście
> dowodzi, że naturalna sekwencja gracza kończy się widocznym skutkiem.
>
> **W kolejce planisty (nie planować ponownie):** G89.2a rozcięte na trzy
> plasterki — task-505 (rdzeń: jednostka przekracza własnego ogłuszonego
> sojusznika, gdy to jedyne dojście do wroga), task-506 (sekwencja z repro na
> ziarnie 73 kończy się realnym rozstrzygnięciem, świat spójny z wynikiem),
> task-507 (e2e na żywym moście: gracz widzi rozstrzygniętą bitwę, partia
> utrwalona). **Zweryfikowane prototypem 2026-07-28** na kopii repo poza gitem:
> zamiana miejsc z ogłuszonym sojusznikiem rusza pat i daje na ziarnie 73
> zwycięstwo obrońcy, a cały pythonowy zestaw testów (bez sond Godota) zostaje
> zielony. Po task-507 K89 jest domknięty.

## Kamień milowy 90 — partia da się w ogóle rozegrać (pierwsza tura, koniec gry) — PRIORYTET
> **Ustalenie z przeglądu kierunku 2026-07-28, z uruchomienia kodu, nie z
> lektury.** Po K88 i K89 wszystko *widać*, ale gry nadal **nie da się grać**:
> jedno kliknięcie „Następna tura" na starcie partii oddaje graczowi przegraną,
> a przegrana nigdy się nie kończy. Pełny pythonowy zestaw testów jest przy tym
> zielony (4 s) — to dokładnie wzorzec z wniosku 13 w `docs/PROJECT.md`.
>
> **Fakt 1 — start jest asymetryczny.** `tbb.game.create_headless_game`
> (`src/tbb/game.py:20-30`) daje AI Keep `occupied=1` i
> `garrison=(Unit(training=5, equipment=12),)`, a Player Keep **pustą załogę**.
> W pierwszej turze `ai.take_duchy_turn` robi develop → recruit → muster → march
> → assault i przejmuje bezbronną osadę gracza. Zweryfikowane na `seed=73`:
> po jednym `next_turn` `player lands` ma `owner_id="ai"`, a księstwo gracza ma
> 0 osad i 0 oddziałów **do końca partii** (150 tur symulacji — nic się już nie
> zmienia, każdy rozkaz gracza to no-op).
> **Fałszywy trop:** „gracz po prostu ma najpierw rekrutować". Sprawdzone dla 1,
> 2 i 3 rekrutów przed turą — osada pada tak samo, bo rekrut ma `equipment=0`,
> a `Unit.damage == equipment` (`src/tbb/unit.py:102`), czyli zadaje **zero**
> obrażeń weteranowi AI.
> **Prototyp rozwiązania sprawdzony (poza gitem):** gdy Player Keep startuje z
> takim samym garnizonem jak AI Keep, osada gracza stoi ≥10 tur biernej gry, a
> AI traci przy tym własny garnizon na kolejnych szturmach — czyli powstaje
> realna sytuacja do rozegrania (AI Keep zostaje bez obrony i da się je wziąć).
>
> **Fakt 2 — koniec gry jest nieosiągalny dla gracza.**
> `driver.resolve_hero_survival` (`src/tbb/driver.py:23-33`) jest wołane
> **tylko dla księstw AI**: pętla drivera robi `continue` dla `player_duchy_id`
> przed akcją militarną (`driver.py:96`), a `session.apply_command` po rozkazach
> gracza robi wyłącznie `sync_from_world`. Bohater gracza nigdy nie ginie →
> `Duchy.is_defeated` (brak osad **i** brak bohatera) nigdy nie zachodzi →
> `game.is_over` zostaje `False`. Klient pokazuje wtedy w nieskończoność
> `Wynik: ongoing` — na dodatek surowym tokenem angielskim
> (`game/scripts/main.gd:164`, wartości `_player_result`: `ongoing`/`victory`/
> `defeat`/`draw`).
>
> **Kolejność wobec kolejki K89:** najpierw kończymy K89 (task-506, task-507) —
> te zadania stoją na `seed=73` i są o krok od domknięcia. Dopiero potem G90.1a,
> bo zmiana startu zmienia skład oddziału z repro (3 jednostki zamiast 2).
> Sprawdzone: sekwencja repro na symetrycznym starcie **nadal się rozstrzyga**
> (`BattleResult.DEFENDER_WIN`), więc kryterium K89 zostaje w mocy — zmienić może
> się liczba jednostek w oczekiwaniach testu, nie sam fakt rozstrzygnięcia.
> **To nie jest odłożony „balans" z sekcji „Później"** — to warunek, żeby pętla
> sandboxa miała jak się zacząć (patrz `docs/PROJECT.md`, wnioski 15 i 16).
- [x] **G90.1a** Start partii jest **symetryczny**: `create_headless_game` daje
      osadzie gracza garnizon startowy równy garnizonowi AI (ta sama jednostka i
      ta sama `occupied`), a nie pustą załogę. Test dowodzi na `seed=73`, że po
      **jednej** turze (`Session.next_turn`) `player lands` nadal ma
      `owner_id="player"`, a księstwo gracza ma ≥1 osadę w snapshocie; testy
      startu/ekonomii/AI, które zakładały pusty garnizon gracza, aktualizowane
      świadomie (zmiana pozycji startowej, nie reguły). *(standard, ryzyko:
      dotyka rdzenia i fixture'ów wielu testów; nie zmieniać przy okazji reguł
      bitwy, obrażeń ani polityki AI)*
- [x] **G90.1b** Gracz **widzi**, że przetrwał pierwszą turę: e2e na żywym moście
      (dwa procesy, jak w K89.1b) klika „Następna tura" na świeżej partii i
      sprawdza, że kafel `player lands` w `MapView` nadal jest kafelkiem gracza,
      a status księstwa pokazuje ≥1 osadę; partia zostaje utrwalona. *(standard,
      wymaga G90.1a; wniosek 13 — kamień domykamy sekwencją gracza, nie samym
      `pytest`)*
- [x] **G90.2a** Przegrana gracza jest **osiągalna**: utrata oddziału na ścieżce
      rozkazów gracza rozstrzyga los bohatera tak samo jak u AI (reużycie
      `driver.resolve_hero_survival`, sukcesja przez dziedzica bez zmian), więc
      gracz bez osad, bez oddziałów i bez następcy dostaje
      `result.player_result == "defeat"` i `is_over == true` w snapshocie.
      Zwycięstwo (`victory`) po tej samej regule dla AI zostaje bez zmian; testy
      K89 (bitwa nierozstrzygnięta) przechodzą bez zmian w kryteriach.
      *(standard, wymaga G90.1a; ryzyko: reguła rdzenia współdzielona z driverem
      — jedno źródło, nie kopia w moście)*
- [x] **G90.2b** Koniec gry jest **czytelny po polsku**: scena pokazuje wynik
      partii jako polski tekst (np. „gra trwa" / „zwycięstwo" / „porażka" /
      „remis") zamiast surowego tokenu `ongoing`, a stan zakończonej gry jest
      wyróżniony na ekranie. Pozostałe teksty statusu bez zmian; e2e przez dwa
      procesy mostu. *(simple, wymaga G90.2a)*
> **Kamień 90 — UKOŃCZONY** *(task-508…512)*: symetryczny start, gracz widzi, że
> przetrwał pierwszą turę, los bohatera gracza rozstrzygany tą samą regułą co u
> AI, koniec partii osiągalny i czytelny po polsku.
> **Kamień 89 — UKOŃCZONY** *(task-505…507)*: reguła ruchu przez własnego
> ogłuszonego sojusznika, szturm z repro kończy się rozstrzygnięciem, e2e na
> żywym moście.

## Kamień milowy 91 — naturalne ruchy gracza mają sens (rekrutacja, koniec partii) — UKOŃCZONY
> **Ustalenie z przeglądu planowania 2026-07-28, z uruchomienia kodu.** Po K90
> partię da się przegrać **i wygrać** (zmierzone: bierny gracz przez 3 tury,
> potem `muster`→`march`→`assault` → `victory` na ziarnach 73 i 1). Ale dwa
> naturalne zachowania gracza wciąż kłócą się z grą:
>
> **Fakt 1 — rekrutacja karze.** `Settlement.recruit()` daje `Unit()`, czyli
> `damage == equipment == 0` i `defense == 0`. Sam dodatek takiej jednostki do
> garnizonu odwraca wynik obrony: na zestawie ziaren `73,1,2,7,11,42,5,9` gracz
> utrzymuje osadę po pierwszej turze w **4/8** partii bez rekrutacji i tylko w
> **1/8** po jednym `recruit`. Aktywna sekwencja (`recruit`×2 → `muster` →
> `march` → `assault`) daje dziś **3/8 zwycięstw**; z rekrutem o niezerowym
> wyposażeniu (prototyp poza gitem, `training=2, equipment=4`) — **7/8**.
>
> **Fakt 2 — zakończona partia udaje trwającą.** Po `is_over` sesja jest
> no-opem (poprawnie), ale most odpowiada `{"kind":"order","changed":false}` i
> `{"kind":"turn"}` z niezmienioną datą — nieodróżnialnie od rozkazu bez skutku.
> Gracz klika dalej i widzi „bez zmian" (sprawdzone 25 tur po przegranej).
>
> **Rozstrzygnięte pomiarem, nie planowane:** pozycja „`muster` zabiera cały
> garnizon" — zostawienie ostatniego obrońcy w osadzie **nie poprawia** wyniku
> gracza (identyczne rezultaty na tym samym zestawie ziaren, a przy silniejszym
> rekrucie wręcz osłabia wypad). Plasterek niepotrzebny.
- [x] **G91.1a** Rekrutacja wzmacnia obronę, zamiast ją osłabiać: jednostka z
      rekrutacji ma dodatnie obrażenia i obronę, dorekrutowanie obrońcy nie
      obniża liczby utrzymanych osad na ustalonym zestawie ziaren, koszt i
      ograniczenia rekrutacji bez zmian, jedna reguła dla gracza i AI.
      *(standard, task-513, commit 42ed7f9)*
- [x] **R91.1 (dług techniczny)** Jedno źródło reguły „rozkaz gracza → los
      bohatera → synchronizacja stanu gry" w `tbbbridge.session` (dziś powtórzone
      w ścieżce bez bitwy i z bitwą) + testy regresji obu ścieżek.
      *(simple, task-514, commit fdeb26b)*
- [x] **G91.1b** Gracz wygrywa partię, patrząc na ekran: e2e na żywym moście
      doprowadza partię do zwycięstwa, klient pokazuje je po polsku, stan
      utrwalony. *(standard, task-515, commit afb2dfd)*
- [x] **G91.2a** Most odróżnia zakończoną partię od rozkazu bez skutku (rozkaz i
      tura po `is_over`); reguły i snapshot bez zmian.
      *(simple, task-516, commit 3698741)*
- [x] **G91.2b** Klient mówi po polsku, że partia jest zakończona — zamiast „bez
      zmian" po każdym kliknięciu; e2e przez dwa procesy. *(simple, task-517,
      commit 113f36b)*
> **Kamień 91 — UKOŃCZONY** *(task-513…517)*: rekrut wzmacnia oddział, wspólna
> ścieżka rozkazu synchronizuje los bohatera, a zwycięstwo i próba dalszej gry
> są widoczne po polsku oraz trwałe.
> Po K91 nadal nie ma w scenie wejścia `new_game`; przycisk nowej partii wraca
> do oceny po powiększeniu świata, gdy regularne zakończenie gry ujawni jego
> faktyczną wartość.

## Kamień milowy 92 — obrona własnej osady i minimalny wieloosadowy świat — UKOŃCZONY
> **Stan 2026-07-30:** G92.1 jest domknięte w rdzeniu i na żywym moście.
> Poniższa diagnoza zakleszczenia zostaje jako uzasadnienie wykonanej reguły;
> G92.2a domknęło też minimalną skalę świata.
> **Defekt sięgający gracza, znaleziony przez uruchomienie gry obronnej przy
> przeglądzie kierunku 2026-07-28.** Gracz klika „Zbierz oddział", potem
> „Następna tura" — i partia **zakleszcza się na amen**. Most odpowiada
> `{"ok": false, "error": "destination is already occupied by a party"}`
> (sprawdzone na żywym `serve 73` przez stdio), klient pokazuje „rozkaz nie
> powiódł się", a kalendarz stoi: **20/20 kolejnych kliknięć „Następna tura"
> daje ten sam błąd**, rok 1 miesiąc 1, na 3/3 sprawdzonych ziarnach. Trafienie
> w **50/50 ziaren** w turze 1, także gdy gracz nie rekrutuje, tylko zbiera
> oddział. To jest dziś najkrótsza droga gracza do zepsutej gry — krótsza niż
> jakikolwiek wpis w K91.
>
> **Mechanizm ustalony przez uruchomienie kodu, nie z lektury.** Po `muster`
> oddział gracza stoi w regionie własnej osady. AI szturmuje ten region,
> **wygrywa** z garnizonem — i `WorldMap.apply_settlement_battle_result`
> (`src/tbb/world.py:375-379`) rzuca `ValueError("destination is already
> occupied by a party")`, bo zwycięski atakujący ma wejść na pole zajęte przez
> oddział obrońcy. Ślad wyjątku: `session.next_turn` → `driver.run_headless_game`
> → `ai.take_duchy_turn` → `ai.assault_nearest_enemy_settlement` →
> `world.resolve_settlement_battle` → `apply_settlement_battle_result`. Świat po
> nieudanej turze zostaje niezmieniony, więc kolejne kliknięcia powtarzają błąd
> w nieskończoność.
>
> **Sedno rozgrywkowe, nie tylko kontraktowe:** oddział stojący w regionie
> bronionej osady **nie bierze udziału w jej obronie** — patrzy, jak pada jego
> własna stolica, i przy okazji blokuje kod. Reguła do domknięcia jest ta sama,
> którą gracz zakłada intuicyjnie: armia w domu broni domu.
>
> **Korekta poprzedniego przeglądu (patrz `docs/PROJECT.md`, wniosek 18):**
> zapisano tam, że ten `ValueError` jest dziś nieosiągalny („200 ziaren × 12
> tur, 0 trafień") i czeka na większy świat. Tamta sonda chodziła **wyłącznie
> grą agresywną** (`muster`→`march`→`assault`), która wyprowadza oddział z domu.
> Gra obronna to osobne zachowanie i trafia w defekt natychmiast.
>
> **Zmierzone przy przeglądzie także dla skalowania świata** (prototyp poza
> gitem: pięć regionów w linii, dwie osady na stronę, garnizony jak dziś): przy
> aktywnej grze **ten sam `ValueError` wywala turę AI na 8/8 ziaren**
> (`73,1,2,7,11,42,5,9`) w turze 1–2. Czyli kolejność jest wymuszona pomiarem:
> **najpierw reguła obrony, potem druga osada** — odwrotnie dowozimy grę, która
> się wywala.
- [x] **G92.1a** Oddział stojący w regionie bronionej osady **bierze udział w
      jej obronie**, a zwycięski szturm na taki region przestaje być wyjątkiem:
      `resolve_settlement_battle*` z obcym oddziałem w regionie docelowym
      zwraca świat w spójnym stanie zamiast
      `ValueError("destination is already occupied by a party")` — jednostki
      broniącego oddziału walczą po stronie obrońcy razem z garnizonem, a po
      zwycięstwie atakującego oddział broniącego znika ze świata (jego ocalali
      rozstrzygnięci tą samą regułą co garnizon). Test odtwarza układ z repro
      (oddział gracza w regionie własnej osady, szturm AI kończący się
      `ATTACKER_WIN`) na ustalonym ziarnie i sprawdza brak wyjątku oraz spójny
      świat; przy porażce i przy bitwie nierozstrzygniętej (K89) oddział
      broniącego **zostaje** w regionie ze swoimi ocalałymi. Jedna reguła dla
      gracza i AI. Dotychczasowe testy zwycięstwa/porażki/remisu i testy K89
      przechodzą bez zmian w kryteriach. *(standard, ryzyko: dotyka rdzenia —
      jedynego źródła reguł; nie zmieniać przy okazji reguł ruchu, obrażeń ani
      polityki AI, i nie skalować przy tym świata — to osobny plasterek)*
- [x] **G92.1b** Gracz **widzi**, że gra obronna działa: e2e na żywym moście
      (dwa procesy, jak w K90.1b) wydaje `muster` i klika „Następna tura" — most
      odpowiada `ok:true`, kalendarz przesuwa się o miesiąc, klient pokazuje
      polski status zamiast „rozkaz nie powiódł się", a partia zostaje
      utrwalona. Test dowodzi też, że **druga** „Następna tura" znowu przechodzi
      (kalendarz idzie dalej), czyli zakleszczenie zniknęło. *(standard, wymaga
      G92.1a; wniosek 13 — kamień domykamy sekwencją gracza, nie samym
      `pytest`)*
- [ ] **G92.1c (ODŁOŻONE — brak ścieżki w bieżącej grze)** Wejścia AI
      `assault_duchy_party_recorded`,
      `assault_duchy_party_to_recorded` i `assault_nearest_enemy_settlement`
      **pomijają szturm**, gdy region docelowej osady zajmuje party **niebędące
      jej obrońcą** (inny `owner_id` niż osada). Dziś guard
      `apply_settlement_battle_result` przy `ATTACKER_WIN` rzuca
      `ValueError("destination is already occupied by a party")`, więc
      zwycięstwo na takim polu kończy turę AI nieobsłużonym wyjątkiem. Bez
      zmiany kontraktu `WorldMap` ani reguł bitwy — tylko selekcja celu AI.
      *(standard, wymaga G92.1a; nie dodawać w tym samym zadaniu czerwonego
      testu world — to plasterek AI; wrócić, gdy pojawi się trzecie księstwo
      albo reprodukcja w normalnej partii dwóch księstw)*
> **G92.1 — UKOŃCZONE** *(task-518…523)*: oddział w osadzie walczy z garnizonem,
> ocalali wracają do właściwego miejsca, zwycięski szturm nie zakleszcza świata,
> a żywy most przechodzi dwie kolejne tury po `muster`.

- [x] **G92.2a — minimalny świat, w którym utrata jednej osady nie kończy
      księstwa.** `create_headless_game` tworzy połączony świat pięciu regionów
      z pustym regionem granicznym i **dwiema osadami na stronę**; oba księstwa
      zaczynają z dwiema osadami, a każda osada zachowuje dzisiejszy mały,
      symetryczny garnizon i zasoby. Snapshot świeżej sesji wystawia wszystkie
      pięć regionów oraz po dwie osady w statusach księstw, więc istniejący
      `MapView` pokazuje większy świat bez nowej logiki klienta. Test rdzenia
      dowodzi też, że utrata jednej osady pozostawia księstwo żywe. Nie zmieniać
      przy tym AI, ekonomii, warunku zwycięstwa ani sterowania rozkazami.
      *(standard; ryzyko: startowy fixture jest konsumowany przez rdzeń, most,
      persystencję i e2e Godota; wniosek 17; commit a62af42)*
> **G92.2a — UKOŃCZONE**: snapshot świeżej sesji ma pięć regionów i po dwie
> osady, a naturalne e2e `recruit×2` → `muster` → `march×2` → `assault` na
> seedzie 73 zdobywa `ai outpost`, pozostawia partię w toku i wznawia ten sam
> stan w drugim procesie.

## Kamień milowy 93 — pierwszy rozkaz celowany z mapy — PRZEPLANOWANY JAKO K97
> **Pomiar po G92.2a i korekta po review (2026-07-30):** większy świat działa,
> ale `MapView` jest wyłącznie rysunkiem: `RegionTile_*` ignorują mysz, a scena
> wysyła `march` bez `target`. Istniejącego kontraktu celu **nie wolno jednak
> użyć jako kontraktu klikniętego kafla ani zmieniać**:
> `march_duchy_party_to` oznacza marsz o jeden krok **ku odległemu celowi**,
> obsługuje działające `src/tbbui/serve.py` oraz zrealizowane K15.1a/K49.1d.
> Sąsiedni cel jest w nim zgodnie z dotychczasową semantyką no-opem, więc nie
> nadaje się do odwrotu na kliknięty kafel; odległy cel może zaś wyznaczyć krok
> przez wrogą osadę bez szturmu. Klikana mapa potrzebuje odrębnej, węższej
> ścieżki ruchu, bez regresji istniejącego marszu i jego zaleceń.
>
> **ZMIANA PRIORYTETU PO BRIEFIE 2026-07-30 — WSTRZYMANE I DO PONOWNEGO
> PLANOWANIA.** Ukończone G93.1a-1 zostaje w kodzie: jest bezpiecznym,
> odizolowanym fundamentem. Niezaczęte task-531…535 nie tworzą prawidłowego
> batcha wizualnego (co najmniej task-531, task-532 i task-535 są mechaniczne,
> a task-533 nie ma wymaganej bramki screenshot/licencje). Wszystkie pięć
> wróciło wtedy do planisty i nie wolno ich wykonywać w pierwotnym składzie.
> K97 jest ich obowiązującym przeplanowaniem: maksymalnie dwie niezbędne
> zależności mechaniczne obok czterech efektów graficznych. Szeroki R93.1 nie
> jest niezbędną zależnością grafiki i pozostaje odłożony.
- [x] **G93.1a — bezpieczny, celowany ruch o jeden krok z mapy (ZASTĄPIONY
      I DOMKNIĘTY W K97).** Jawny
      prymityw rdzenia `move_duchy_party_to_adjacent` pozwala przenieść oddział
      wyłącznie do **wskazanego regionu sąsiedniego**, niezajętego przez party
      i niebędącego osadą wroga; dozwolone są pusty region oraz własna osada.
      Cel bieżący, odległy, zajęty albo z wrogą osadą daje bezpieczny no-op bez
      mutacji. Most wystawia go jako odrębny rozkaz `move` z wymaganym,
      rozwiązywalnym `target`; brak albo nieznany cel nie uruchamia awaryjnie
      automatycznego marszu. Kontrakty `march_duchy_party_to`, `march` z
      `target` i bez niego oraz trasa `POST /order/march?target=...` w `tbbui`
      pozostają bez zmian. Test regresji zachowuje działanie K15.1a/K49.1d:
      wskazanie odległej osady nadal przesuwa oddział o jeden krok w jej
      kierunku i zalecany marsz HTML nie staje się no-opem.
      Testy nowego prymitywu i mostu dowodzą, że odwrót z `player outpost` do
      sąsiedniego `player lands` wykonuje dokładnie jeden krok, cel odległy jest
      no-opem, a bezpośredni cel `ai outpost` pozostaje zablokowany i szturm
      nadal jest jedyną drogą wejścia do wrogiej osady.
      Następnie klik kafla emituje jego kanoniczną nazwę i daje widoczne
      zaznaczenie, a „Wyrusz w pole" przekazuje ją przez `BridgeClient` jako
      `{"type":"order","order":"move","target":...}`, odświeża scenę i zapisuje
      partię. E2e na żywym moście pokazuje marker po kroku do własnego
      `player outpost`, po odwrocie do `player lands` i po wznowieniu.
      Bez zaznaczenia zostaje obecny automatyczny `march`. Nie obejmuje szturmu,
      starcia ani celowania rozwoju/rekrutacji/zbiórki.
      *(complex; ryzyka: nowy prymityw rdzenia obok zachowanego kontraktu
      `march_duchy_party_to`, nowy rozkaz mostu, Godot input, integracja
      Godot↔Python; review wymagane)*
- [x] **G93.1a-1 — bezpieczny ruch oddziału do wskazanego sąsiada.** Prymityw
      rdzenia i testy przypadków dozwolonych/zablokowanych są gotowe; nie
      rozszerzać teraz mostu ani mechaniki. *(commit c0470da)*
> **G93.1a-2…5 — NIEAKTUALNE, ZASTĄPIONE PRZEZ K97:** task-531 (`move` w
> moście), task-532 (R93.1), task-533 (klik i zaznaczenie), task-534 (wybór
> steruje ruchem), task-535 (e2e). Zachowane jawnie, lecz nie wykonywać: K97
> rozcina tę samą wartość na dwie niezbędne zależności integracyjne i cztery
> zadania graficzne zgodne ze stałą bramką.

## Kamień milowy 94 — strategiczna mapa przestaje wyglądać jak prototyp — UKOŃCZONY
> **Najcieńszy następny plasterek po zmianie briefu: dokładnie cztery zadania
> graficzne, zero mechanicznych.** Screenshot klienta uruchomionego 2026-07-30
> w 1152×648 pokazał pięć odseparowanych ikon na szarym tle, napisy położone na
> zamkach, duży pusty obszar `BattleView` i przyciski poza dolną krawędzią.
> K87 dowiódł importu plików, lecz nie jakości kompozycji. K94 poprawia najpierw
> punkty 1–3 obowiązującego zakresu wizualnego: kafle, osady i tło mapy. Nie
> zmienia snapshotu, mostu, rdzenia ani reguł gry.
- [x] **G94.1a [GRAFIKA] — spójna, połączona siatka mapy.** `MapView` układa
      pięć istniejących `RegionTile_*` jako stykające się heksy o poprawnej
      skali i kolejności warstw, zamiast rzędu rozdzielonych kart; używa
      istniejącego `game/assets/map_ground.png` jako konkretnego nośnika i nie
      zmienia znaczenia `col`/`row`. Nazwy regionów dostają czytelne miejsce
      poza detalem budynku. Po uruchomieniu Godota cała pięcioregionowa mapa
      mieści się w panelu. Akceptacja: test geometrii + screenshot 1152×648 i
      ludzkie review czytelności; wpis źródłowy `map_ground.png` w
      `CREDITS.md` zostaje sprawdzony i zachowany. *(standard)*
- [x] **G94.1b [GRAFIKA] — spójna różnorodność podłoża strategicznego.** Do
      `game/assets/` wchodzą co najmniej trzy jawnie nazwane warianty
      `map_ground_grass.png`, `map_ground_earth.png`,
      `map_ground_stone.png` z jednej zgodnej stylistycznie paczki CC0/CC-BY.
      `MapView` wybiera je deterministycznie z `col`/`row` wyłącznie jako
      dekoracyjny wariant (bez wymyślania mechanicznego terenu), tak aby pięć
      regionów pokazało co najmniej trzy warianty. Akceptacja: import/ładowanie,
      screenshot działającej mapy i ludzkie review spójności; dokładna strona
      źródłowa, autor, licencja i ścieżka każdego pliku w `CREDITS.md`.
      *(standard; ryzyko: dobór/licencja assetów)*
- [x] **G94.1c [GRAFIKA] — keep i outpost wyglądają jak różne osady.** Zastąpić
      pojedyncze `settlement.png` dwoma konkretnymi assetami docelowymi
      `settlement_keep.png` i `settlement_outpost.png` w średniowiecznej,
      możliwie realistycznej stylistyce CC0/CC-BY. `MapView` dobiera je z
      istniejącej nazwy osady (`keep`/`outpost`), zachowuje czytelną nazwę i nie
      tintuje całego budynku kolorem właściciela. Akceptacja: oba typy są
      jednocześnie widoczne w natywnym Godocie, nie zasłaniają nazw, screenshot
      1152×648 przechodzi ludzkie review; per-plikowe źródło i licencja trafiają
      do `CREDITS.md`. *(standard; ryzyko: dobór/licencja assetów)*
- [x] **G94.1d [GRAFIKA] — tło i kompozycja strategiczna mieszczą sterowanie.**
      Dodać konkretny asset `strategic_map_background.png` (subtelna ziemia,
      płótno lub pergamin, CC0/CC-BY) jako tło panelu mapy i rozdzielić na
      ekranie mapę, status oraz rozkazy. Pusty `BattleView` nie rezerwuje
      miejsca; pojawia się dopiero, gdy istnieje bitwa. Przy 1152×648 data,
      pięć regionów, status wyniku i wszystkie obecne przyciski są widoczne bez
      przewijania i bez szarej pustki dominującej nad mapą. Akceptacja: test
      układu + screenshot uruchomionej świeżej partii oraz ludzkie review
      kompozycji/kontrastu; źródło, autor i licencja tła w `CREDITS.md`.
      *(standard; ryzyko: layout przy różnych rozdzielczościach)*

> **K94 — UKOŃCZONY** *(commity 7fa895d, ca5d274, 8f7ee0e, 1a5a7dd)*:
> mapa tworzy połączony pas pięciu heksów, ma trzy dekoracyjne podłoża,
> odrębne keep/outpost i pergaminową kompozycję, w której sterowanie mieści
> się przy 1152×648.

## Kamień milowy 95 — ikony rozkazów — UKOŃCZONY
> G95 zrealizował punkt 4 kolejności wizualnej. Wszystkie bieżące przyciski
> mają odrębne ikony z rodziny Game-icons, polskie etykiety i atrybucję CC-BY.
- [x] **G95.1a [GRAFIKA] — ikona „Następna tura” wyznacza język ikon
      rozkazów.** Przycisk używa czytelnej klepsydry `icon_next_turn.png`,
      zachowuje polską etykietę, źródło i licencję CC-BY 3.0. Test i review
      obejmują działający przycisk w natywnym Godocie. *(commit 1b4471c)*
- [x] **G95.1b [GRAFIKA] — odrębne ikony rozkazów osady.** Rozwój, rekrutacja
      i zbiórka używają `icon_develop.png`, `icon_recruit.png` oraz
      `icon_muster.png`. *(commit 4d14f6e)*
- [x] **G95.1c [GRAFIKA] — odrębne ikony rozkazów polowych.** Marsz i szturm
      używają `icon_march.png` oraz `icon_assault.png`. *(commit 6b05b41)*
- [x] **G95.1d [GRAFIKA] — odrębne ikony zapisu i odczytu.** Przyciski używają
      `icon_save.png` oraz `icon_load.png`. *(commit a80aba3)*

## Kamień milowy 96 — armie są czytelne na mapie strategicznej — UKOŃCZONY
- [x] **G96.1a [GRAFIKA] — sylwetki oddziałów gracza i AI na mapie
      strategicznej.** Zastąpić małą chorągiew `party_player.png` dwiema
      czytelnymi, różnymi sylwetkami `party_player_unit.png` i
      `party_ai_unit.png` z jednej spójnej, średniowiecznej paczki CC0/CC-BY.
      `MapView` dobiera je z istniejącego `region.party.owner`, pokazuje każdą
      obecną armię — także AI — i nie utożsamia właściciela z kontekstową rolą
      atakujący/obrońca. Bez zmian snapshotu, mostu i reguł. Akceptacja: test
      przemieszczenia znacznika wraz z danymi regionu oraz screenshot
      natywnego Godota w stanie z oddziałami obu stron; sylwetki nie zasłaniają
      osad ani nazw i przechodzą ludzkie review, a źródło, autor, licencja
      i ścieżka każdego pliku trafiają do `game/assets/CREDITS.md`.
      *(standard; ryzyko: dobór/licencja i czytelność przy małej skali)*
> **G96.1a — UKOŃCZONE** *(commity bca5c3b, 93ab69b, 22d67a9, b77eace)*:
> osobne sylwetki obu stron są przypisane z `region.party.owner`, pełny
> aktualny komplet armii jest rysowany, a kompozycja nie zasłania osad i nazw.

## Kamień milowy 97 — wybór regionu prowadzi do bezpiecznego kroku — UKOŃCZONY
> Najcieńszy interaktywny plasterek po K95/G96. Screenshot 1152×648
> potwierdził, że mapa i armie są już assetami, ale kafle nadal nie reagują na
> mysz, a „Wyrusz w pole” wysyła automatyczny `march` bez celu. K97 nie zmienia
> reguł: reużywa gotowe `move_duchy_party_to_adjacent` z G93.1a-1. Batch ma
> dokładnie dwie niezbędne zależności integracyjne i cztery zadania graficzne.
- [x] **G97.1a [MECHANIKA] — rozkaz `move` wystawia istniejący bezpieczny krok
      przez most.** `tbbbridge.session.apply_command` przyjmuje
      `{"type":"order","order":"move","target":"<kanoniczna nazwa>"}`,
      rozwiązuje cel w świecie i wywołuje wyłącznie
      `move_duchy_party_to_adjacent`. Brak/nieznany/nielegalny cel daje
      bezpieczny brak zmiany, nigdy awaryjny `march`; dotychczasowe `march`
      celowane i automatyczne pozostają bez zmian. Testy pinują dozwolony
      odwrót do sąsiedniego własnego regionu oraz blokadę celu odległego,
      zajętego i wrogiej osady. Zastępuje mechaniczny zakres task-531.
      *(commit 468fa3e; standard; ryzyko: kontrakt mostu)*
- [x] **R97.1 / G97.1b [MECHANIKA] — klient przekazuje cel bez duplikowania ścieżki
      persystencji.** `BridgeClient` dostaje minimalne API rozkazu z opcjonalnym
      `target`, buduje słownik żądania i reużywa istniejące
      `_send_persisted_sequence` oraz projekcję `OrderResult`. Rozkazy bez celu
      zachowują identyczny JSON i zachowanie. Test obejmuje dokładny request
      `move` + `save` oraz wznowienie. Zastępuje potrzebną część task-532;
      dawny szeroki R93.1 pozostaje odłożony.
      *(commit a78f6ef; standard; ryzyko: Godot↔Python)*
- [x] **G97.1c [GRAFIKA] — kliknięty region ma czytelną ramkę wyboru.**
      `MapView` emituje kanoniczną nazwę klikniętego `RegionTile_*` i rysuje
      nad nim konkretny element `map_target_frame.png`; tylko jeden region jest
      zaznaczony, ponowny klik nie mnoży warstw, a ramka nie zasłania nazwy,
      osady ani sylwetki. Akceptacja: test sygnału/nazwy + screenshot natywnego
      Godota 1152×648 i ludzkie review; źródło, autor, licencja i ścieżka
      assetu w `CREDITS.md`. Zastępuje część task-533. *(standard; ryzyko:
      Godot input i czytelność małego kafla; commit 0fcb13f)*
- [x] **G97.1d [GRAFIKA] — kafel sygnalizuje, że jest klikalny.** Wskazany
      kursorem region dostaje odrębny, subtelny stan hover (tint/obrys oparty na
      ramce K97), a kursor i kontrast odróżniają hover od trwałego zaznaczenia.
      Warstwy podłoża, osady i armii nadal nie przechwytują myszy. Akceptacja:
      test wejścia/wyjścia kursora + screenshot stanu hover i ludzkie review;
      wpis `map_target_frame.png` w `CREDITS.md` pozostaje kompletny.
      *(commit fb25682; standard; ryzyko: z-order i input)*
- [x] **G97.1e [GRAFIKA] — panel pokazuje stan wybranego celu po polsku.**
      W panelu strategicznym pojawia się nazwany element „Wybrany region” z
      nazwą, właścicielem, typem osady/brakiem osady i obecnością/stroną armii,
      wyłącznie z danych już obecnych w `SnapshotModel.regions`. Brak wyboru ma
      jednoznaczny pusty stan; nie dopisywać snapshotu ani reguł. Akceptacja:
      test renderu celów własnego, neutralnego i AI + screenshot 1152×648,
      ludzkie review czytelności i weryfikacja, że panel nie wypycha przycisków
      poza ekran. *(commit a93aed2; standard; ryzyko: kompozycja)*
- [x] **G97.1f [GRAFIKA] — zaznaczenie steruje widocznym bezpiecznym ruchem.**
      Przy wyborze przycisk pokazuje kontekst „Wyrusz: <region>” i wysyła
      `move` z tą nazwą; bez wyboru zachowuje dotychczasowy automatyczny
      `march`. Po legalnym kroku sylwetka gracza przenosi się na wskazany kafel,
      panel i ramka odświeżają się bez zdublowania, a cel zablokowany daje
      czytelny polski status bez fałszywego ruchu. Akceptacja: e2e na żywym
      moście obejmuje legalny krok, blokadę wrogiej osady, zapis/wznowienie,
      screenshot obu skutków i ludzkie review; użyte assety zachowują kompletne
      wpisy w `CREDITS.md`. Zastępuje task-534/535. *(complex; ryzyka:
      integracja Godot↔Python, persystencja i feedback)*

> **K97 — UKOŃCZONY** *(commity 468fa3e…ea369ee)*: most i klient niosą
> `move(target)`, mapa daje ramkę, hover, polski panel i kontekstowy przycisk,
> a e2e pokazuje legalny krok, blokadę wrogiej osady i tę samą pozycję po
> wznowieniu.

## Kamień milowy 98 — widok bitwy dorównuje mapie strategicznej — UKOŃCZONY
> **Najcieńszy kolejny plasterek wartości, bez nowej mechaniki:** istniejący
> `BattleView` pokazuje tylko zajęte heksy z obecnego snapshotu, lecz układa je
> jak prostokątną tabelę, tintuje całe podłoże kolorem strony i przykrywa je
> angielską nazwą terenu. Audyt assetów koryguje założenie K87: tylko
> `terrain_plains.png` jest heksagonalnym kaflem 120×140; pliki
> `terrain_forest.png` (drzewo 26×40) i `terrain_hills.png` (skała 74×92) są
> dekoracjami, których nie wolno rozciągać do rozmiaru heksu. K98 poprawia
> wyłącznie czytelność danych już wystawionych (`q`, `r`, `terrain`, `side`,
> `hp`, `result`). Nie dodaje pustych heksów, wymiarów pola, sterowania jednostką
> ani zmian mostu. Batch ma cztery zadania graficzne i zero mechanicznych.
- [x] **G98.1a [GRAFIKA] — bazowy heks buduje spójną siatkę osiową.**
      `BattleView` rysuje `terrain_plains.png` jako nieodkształcony bazowy heks
      każdego istniejącego pola i układa te bazy jako stykającą się siatkę
      pointy-top według `(q, r)`, z poprawnym z-orderem i bez prostokątnych
      odstępów. `terrain_forest.png` ani `terrain_hills.png` nie mogą uczestniczyć
      w wyznaczaniu rozmiaru lub styku heksów. Nie wolno dorysować nieistniejących
      pól. Akceptacja: test geometrii dla co najmniej trzech rzędów, który
      potwierdza wspólny rozmiar baz 120×140 niezależnie od `terrain`, screenshot
      natywnego Godota 1152×648 i ludzkie review; wpis źródłowy bazowego assetu
      w `game/assets/CREDITS.md` pozostaje kompletny. *(standard; ryzyko:
      geometria i clipping)*
- [x] **G98.1b [GRAFIKA] — drzewo i skała są dekoracjami terenu, nie
      rozciągniętymi heksami.** `Plains` pozostawia sam bazowy
      `terrain_plains.png`, `Forest` nakłada na niego `terrain_forest.png`
      (drzewo 26×40), a `Hills` — `terrain_hills.png` (skała 74×92), z
      zachowaniem proporcji i czytelnym zakotwiczeniem wewnątrz heksu. Usunąć
      angielskie etykiety `Plains/Forest/Hills` z powierzchni oraz tint strony
      z całej kompozycji terenu. Jeśli potrzebna jest legenda, używa polskich
      nazw poza kaflami. Akceptacja: fixture i screenshot pokazują jednocześnie
      trzy tereny na identycznych bazach oraz obie strony; test pinujący role,
      rozmiary i brak rozciągania dekoracji, ludzkie review i kompletna
      atrybucja trzech plików. *(standard; ryzyko: z-order i czytelność)*
- [x] **G98.1c [GRAFIKA] — jednostka, strona i żywotność są jedną czytelną
      kompozycją heksu.** `side_attacker.png` i `side_defender.png` pozostają
      sylwetkami na terenie, a właściciela wskazuje mały obrys/podstawka, nie
      kolor całego podłoża. Każdy zajęty heks pokazuje istniejące `hp` jako
      zwarty znacznik „PŻ”, bez zasłaniania sylwetki. Akceptacja: fixture obu
      stron z różnym `hp`, screenshot 1152×648, ludzkie review w małej skali
      oraz kompletne źródła/licencje użytych plików. *(standard; ryzyko:
      czytelność i z-order)*
- [x] **G98.1d [GRAFIKA] — bitwa ma własną ramę i jednoznaczny polski wynik.**
      Dodać `battle_panel_background.png` jako spójne z mapą tło/ramę
      `BattleView` oraz wyeksponować istniejący `BattleResultLabel` jako nagłówek
      „Bitwa” i baner zwycięstwo/porażka/remis. Gdy bitwa jest widoczna, panel
      nie może być ściśnięty przez mapę ani wypchnąć sterowania poza 1152×648.
      Akceptacja: screenshot każdego wyniku w natywnym Godocie, ludzkie review
      hierarchii i kontrastu, test układu oraz źródło, autor, licencja i ścieżka
      nowego assetu w `game/assets/CREDITS.md`. *(standard; ryzyko: kompozycja)*

> **K98 — UKOŃCZONY** *(commity 4ce8ad2…ed52d79)*: zajęte pola tworzą siatkę
> pointy-top ze wspólnego heksu, drzewo i skała są dekoracjami, jednostki mają
> odrębne strony i znaczniki PŻ, a bitwa własną ramę oraz polski baner wyniku.

## Kamień milowy 99 — ekran strategiczny dostaje spójną hierarchię — UKOŃCZONY
> **UKOŃCZONE.** K99 dał większą i wyśrodkowaną mapę, polskie tabliczki
> regionów z lekkim znacznikiem własności, pergaminową kartę statusu bez
> zdublowanej listy regionów oraz kontrastowy pasek rozkazów z jasnymi
> stanami przycisków. Kanoniczne nazwy, snapshot, most i reguły bez zmian.
> Screenshoty 1152×648 (`task-565-fresh-order-states`,
> `task-565-visible-battle`) potwierdzają hierarchię, lecz ujawniają następną
> lukę: angielskie tokeny w statusie/panelu/przycisku oraz pas mapy unoszący
> się w pustym pergaminie — to zakres K100.
- [x] **G99.1a [GRAFIKA] — mapa wykorzystuje swoją scenę i ma czytelną skalę.**
      *(commit 4b04687)*
- [x] **G99.1b [GRAFIKA] — polskie tabliczki regionów i lekki znacznik
      własności.** *(commit 5a70bd0)*
- [x] **G99.1c [GRAFIKA] — średniowieczna karta statusu księstwa.**
      *(commit f5898ae)*
- [x] **G99.1d [GRAFIKA] — kontrastowy pasek rozkazów.**
      *(commit 2772826)*
> **K99 — UKOŃCZONY** *(commity 4b04687…2772826)*: hierarchia ekranu
> strategicznego (mapa, status, rozkazy) jest spójna wizualnie; próg wizualny
> nadal nieosiągnięty z powodu angielskich etykiet poza kaflem i pustej
> scenografii mapy.

## Kamień milowy 100 — polska warstwa prezentacji i teatr mapy — UKOŃCZONY
> **UKOŃCZONE.** K100 domknął residualny prototyp po K99 bez ruszania
> snapshotu/mostu/reguł: jedno źródło PL (`WorldPresentation`), teatr mapy
> pod pasem heksów, hierarchiczna karta wyboru i pełnoekranowe tło bez
> szarego chrome. Screenshoty 1152×648 (`task-569-*`) potwierdzają teatr
> i polskie etykiety, lecz ujawniają następną lukę: `ColorRect` znaczniki
> własności, ściana tekstu w statusie i goły baner bitwy — to zakres K101.
- [x] **G100.1a [GRAFIKA] — wszystkie widoczne nazwy świata są po polsku.**
      *(commit f5477db)*
- [x] **G100.1b [GRAFIKA] — pas mapy stoi na teatrze, nie w pustce.**
      `map_theater_frame.png` pod pasem heksów. *(commit 27d12f7)*
- [x] **G100.1c [GRAFIKA] — karta wybranego regionu ma hierarchię, nie
      pusty blok.** *(commit 1ff23fa)*
- [x] **G100.1d [GRAFIKA] — pełny ekran bez pozostałego chrome prototypu.**
      *(commit e6ec556)*
> **K100 — UKOŃCZONY** *(commity f5477db…e6ec556)*: PL poza kaflem, teatr
> mapy, karta wyboru i tło okna; próg wizualny nadal nieosiągnięty.

## Kamień milowy 101 — herby, status i baner bitwy bez residualnych prostokątów — UKOŃCZONY
> **UKOŃCZONE.** K101 domknął residualne `ColorRect` własności, ścianę
> tekstu statusu i goły wynik bitwy — bez reguł/mostu. Screenshoty
> `task-572-*` (status) i kod banera bitwy potwierdzają przyrost, lecz
> ujawniają następną warstwę: ciemne `StyleBoxFlat` tabliczek nazw i PŻ
> oraz flat panel wyboru / goły status rozkazu — zakres K102.
- [x] **G101.1a [GRAFIKA] — znaczniki własności na mapie to herby, nie
      kolorowe kwadraty.** `owner_mark_{player,neutral,ai}.png` (Game-icons
      shields, CC-BY 3.0) zamiast `ColorRect`. *(commit 2ab5a81)*
- [x] **G101.1b [GRAFIKA] — legenda właścicieli spójna z herbami.**
      Te same pieczęcie, pergaminowa rama, polskie etykiety.
      *(commit 36a8ed1)*
- [x] **G101.1c [GRAFIKA] — karta statusu księstwa ma hierarchię, nie
      ścianę tekstu.** Wiersze etykieta/wartość, wyróżniony wynik; screenshoty
      `task-572-status-{fresh,finished}-1152x648.png`. *(commit 4204bfa)*
- [x] **G101.1d [GRAFIKA] — wynik bitwy to baner, nie goły napis.**
      `battle_result_banner.png` pod nagłówkiem i polskim wynikiem.
      *(commit 4efd0ca)*
> **K101 — UKOŃCZONY** *(commity 2ab5a81…4efd0ca)*: herby, legenda, hierarchia
> statusu, baner bitwy; próg wizualny nadal nieosiągnięty.

## Kamień milowy 102 — tabliczki, PŻ i feedback bez ciemnego HUD — UKOŃCZONY
> **UKOŃCZONE.** K102 domknął residualne ciemne `StyleBoxFlat` tabliczek nazw
> i PŻ, flat panel wyboru oraz goły status rozkazu — bez reguł/mostu.
> Wspólny nośnik plakietki: `LabelTextureCarrier` (R102.1). Screenshot
> `task-575-battle-hp-badges-1152x648` potwierdza plakietki PŻ; pełny ekran
> ujawnia następną warstwę: jasne `StyleBoxFlat` przycisków rozkazów i
> legendy właścicieli oraz jaskrawy zielony obrys Kenney na kaflach —
> zakres K103.
- [x] **G102.1a [GRAFIKA] — tabliczki nazw regionów to pergaminowe plakietki,
      nie ciemny HUD.** `region_name_plate.png` pod polskimi etykietami.
      *(commit d1fef4f)*
- [x] **G102.1b [GRAFIKA] — znaczniki PŻ w bitwie to plakietki, nie ciemne
      chipy.** `battle_hp_badge.png`; screenshot
      `task-575-battle-hp-badges-1152x648.png`. *(commit 09ef2fa)*
- [x] **G102.1c [GRAFIKA] — panel wybranego regionu ma teksturowaną ramę,
      nie `StyleBoxFlat`.** `selected_region_panel.png`. *(commit f504a54)*
- [x] **G102.1d [GRAFIKA] — feedback rozkazu to wstęga, nie goły napis.**
      `order_status_banner.png` pod `LastOrderStatusLabel`. *(commit 2f57877)*
- [x] **R102.1 (dług techniczny)** Jedno źródło nośnika plakietki teksturowej
      (`label_texture_carrier.gd`) + regresja tabliczek/PŻ. *(commit 1141bb4)*
> **K102 — UKOŃCZONY** *(commity d1fef4f…1141bb4)*: pergaminowe tabliczki,
> plakietki PŻ, rama panelu wyboru, wstęga feedbacku; próg wizualny nadal
> nieosiągnięty.

## Kamień milowy 103 — sterowanie, legenda i podłoże bez residualnego flat — UKOŃCZONY
> **UKOŃCZONE.** K103 domknął residualne jasne `StyleBoxFlat` sterowania
> i legendy oraz jaskrawy obrys Kenney na podłożu mapy/bitwy — bez reguł
> /mostu. Screenshoty `task-579-fresh-order-states`,
> `task-579-visible-battle`, `task-581-map-grounds` (1152×648) potwierdzają
> przyrost; pełny ekran ujawnia następną warstwę: plastyczne keep/outpost,
> kreskówkowe dekoracje bitwy i top-downowe sylwetki Kenney na pergaminie
> — zakres K104.
- [x] **G103.1a [GRAFIKA] — przyciski rozkazów mają teksturowany nośnik, nie
      `StyleBoxFlat`.** `order_button_panel.png` jako `StyleBoxTexture` +
      `modulate` stanów normal/hover/pressed na całym pasku.
      *(commit 0f781f3; screenshoty `task-579-*`)*
- [x] **G103.1b [GRAFIKA] — legenda właścicieli ma teksturowaną ramę, nie
      `StyleBoxFlat`.** `owner_legend_panel.png`; herby i etykiety PL bez
      zmian treści. *(commit dd01e96)*
- [x] **G103.1c [GRAFIKA] — podłoża mapy strategicznej bez kreskówkowego
      obrysu Kenney.** Trzy stonowane `map_ground_{grass,earth,stone}.png`
      w tonie pergaminu; deterministyczny wybór z `col`/`row` bez zmian.
      *(commit 5d33cc4; screenshot `task-581-map-grounds-1152x648`)*
- [x] **G103.1d [GRAFIKA] — bazowy heks bitwy spójny z podłożem mapy.**
      `terrain_plains.png` 120×140 pointy-top z tej samej rodziny; dekoracje
      drzewa/skały bez rozciągania. *(commit 9871482)*
> **K103 — UKOŃCZONY** *(commity 0f781f3…9871482)*: teksturowane przyciski
> i legenda, stonowane podłoże mapy i bitwy; próg wizualny nadal
> nieosiągnięty (residualny Kenney na osadach/dekoracjach/sylwetkach +
> brak ludzkiej akceptacji).

## Kamień milowy 104 — residualny Kenney w tonie pergaminu — UKOŃCZONY
> **UKOŃCZONE.** K104 domknął residualny Kenney na pergaminie bez reguł/mostu:
> keep/outpost w tonie pergaminu (G104.1a), drzewo/skała spójne z
> `terrain_plains` (G104.1b), recolor sylwetek mapy/bitwy (G104.1c) oraz cue
> strony PŻ jako para plakietek zamiast `StyleBoxFlat` (G104.1d). Screenshoty
> `task-585-map-armies` i `task-585-battle-sides` (1152×648) potwierdzają
> przyrost; pełny ekran ujawnia następną lukę: **kształt** top-down RTS nadal
> kłóci się z isometrią osad (recolor ≠ rodzina), a panel wyboru i klaster
> bitwy zostawiają dużo pustego pergaminu — zakres K105.
- [x] **G104.1a [GRAFIKA] — keep i outpost w tonie pergaminu, nie plastiku
      Kenney.** *(commit 6b6691a)*
- [x] **G104.1b [GRAFIKA] — drzewo i skała bitwy w tej samej rodzinie co
      podłoże.** *(commit 274c616)*
- [x] **G104.1c [GRAFIKA] — sylwetki armii i stron w jednej, czytelnej
      rodzinie (recolor).** *(commit 56aa4a7; screenshoty `task-585-*`)*
- [x] **G104.1d [GRAFIKA] — cue strony w bitwie bez residualnego
      `StyleBoxFlat`.** `battle_hp_badge_{attacker,defender}.png`.
      *(commit da1bd29)*
> **K104 — UKOŃCZONY** *(commity 6b6691a…da1bd29)*: ton pergaminu na
> osadach/dekoracjach/cue PŻ; próg wizualny nadal nieosiągnięty (kształt
> figur + kompozycja chrome + brak ludzkiej akceptacji).

## Kamień milowy 105 — figury w rodzinie mapy i kompozycja chrome — UKOŃCZONY
> **UKOŃCZONE w kodzie.** K105 domknął zaplanowany zakres oprawy przed progiem:
> armie mapy i strony bitwy w isometrii/¾ (nie top-down RTS), centrowanie
> klastra heksów bitwy bez dorysowywania pustych pól, ornament pustego
> wyboru + gęstsze dzielniki statusu. Bez reguł/mostu. **Brak** screenshotów
> `task-*` w `game/screenshots/` po tej serii — pakiet dowodowy i jawna
> ludzka akceptacja progu to **K106**, nie kolejna warstwa inventowanej oprawy.
- [x] **G105.1a [GRAFIKA] — armie na mapie w rodzinie isometrii, nie top-down
      RTS.** `party_player_unit.png` / `party_ai_unit.png` — standing ¾,
      48×56, CC0 project art. *(commit d054581)*
- [x] **G105.1b [GRAFIKA] — strony bitwy z tej samej rodziny co armie mapy.**
      `side_attacker.png` / `side_defender.png` — ta sama rodzina. *(commit
      67eb63e)*
- [x] **G105.1c [GRAFIKA] — klaster bitwy ma skalę i kotwiczenie, nie unosi
      się w pustce.** Centrowanie AABB zajętych heksów w panelu. *(commit
      b9c80c9)*
- [x] **G105.1d [GRAFIKA] — panel wyboru i karta statusu bez dominującej
      pustki.** `selected_region_empty_ornament.png` + HSeparators statusu.
      *(commit 1ebbbd4)*
> **K105 — UKOŃCZONY** *(commity d054581…1ebbbd4)*: figury + chrome; pakiet
> screenshotów i ludzka akceptacja progu należały do K106.

## Kamień milowy 106 — próg wizualny: pakiet dowodowy i jawna akceptacja — UKOŃCZONY 2026-08-06
> **K106 — UKOŃCZONY.** Człowiek zaakceptował 2026-08-06 trzy stany dowodowe
> G106.1a–c na screenshotach 1152×648: świeżą partię
> `task-591-fresh-post-k105-1152x648.png`, pusty i wybrany region
> (`task-592-selected-region-{empty,selected}-1152x648.png`) oraz bitwę
> (`task-593-visible-battle-post-k105-1152x648.png`). Audyt G106.1d nie
> wskazał residualnego chrome, angielskich tokenów, top-downowych figur ani
> pustego panelu bez ornamentu; `game/assets/CREDITS.md` nie ma luk. Nie ma
> wskazanego residualu do follow-upu. Pakiet świadomie domknięto trzema stanami;
> status i zakończenie pokrywają dowody świeżej partii i bitwy. Próg wizualny
> jest osiągnięty, a bramka 4 graficzne / batch została odwołana tą akceptacją.
- [x] **G106.1a [GRAFIKA] — świeża partia strategiczna po K105.** Dowód:
      `task-591-fresh-post-k105-1152x648.png`; przegląd zaakceptowany
      2026-08-06.
- [x] **G106.1b [GRAFIKA] — wybrany region (pusty → wybrany).** Dowody:
      `task-592-selected-region-empty-1152x648.png` oraz
      `task-592-selected-region-selected-1152x648.png`; polski UI,
      ornament i ramka wyboru zaakceptowane 2026-08-06.
- [x] **G106.1c [GRAFIKA] — bitwa z figurami isometrii/¾ i wycentrowanym
      klastrem.** Dowód: `task-593-visible-battle-post-k105-1152x648.png`;
      strony, PŻ, dekoracje i polski wynik zaakceptowane 2026-08-06.
- [x] **G106.1d [GRAFIKA] — audyt residualnego chrome i jawna akceptacja.**
      Pełne ekrany G106.1a–c przejrzane; brak wskazanego residualnego chrome
      i brak luk w CREDITS. Wpis progu znajduje się w `docs/PROJECT.md` oraz
      tutaj. *(2026-08-06)*

## Kamień milowy 107 — nowa partia z UI (po zakończonej grze) — W TOKU
> Pierwszy kamień po odwołaniu bramki oprawy. Most ma komendę `new_game` od K65,
> a klient nie ma jak jej wydać: po zakończonej partii („zwycięstwo"/„porażka")
> ekran zostaje na martwym stanie, a jedyny sposób zaczęcia od nowa to skasowanie
> pliku stanu z terminala — dokładnie to, czego brief zabrania. Rdzeń bez zmian.
- [x] **G107.1a** Nowa partia z klienta: `BridgeClient` wydaje `new_game`
      i utrwala świeży stan w pliku stanu (kolejny proces widzi nową partię).
      *(commit 2c4ace0)*
> **G107.1b–d zaplanowane poza tym plikiem** *(task-596: przycisk „Nowa partia"
> w pasku rozkazów bez wiązania; task-597: klik zaczyna grę od nowa, także po
> zakończonej partii; task-598: dowód wizualny paska sterowania)* — dopisane tu
> dla ciągłości, **nie planować ich ponownie**.
- [x] **G107.1d [GRAFIKA] — dowód rozszerzonego paska po task-597.** Wygenerowany
      z uruchomionej gry pełny screenshot
      `game/screenshots/task-598-new-game-order-bar-1152x648.png` (1152×648) pokazuje
      „Nowa partia” oraz komplet
      dziewięciu przycisków. Ludzka akceptacja obrazu 2026-08-06: brak
      przycięcia, nachodzenia etykiet i residualnego chrome.

## Kamień milowy 108 — przeciwnik, który nie roztrwania armii, i gracz, który ma czym go uderzyć
> **Zwrot kierunku (przegląd bootstrap-diff 2026-08-06).** Próg wizualny jest
> osiągnięty, formalne kryterium „gotowe" odhaczone — więc pierwszy raz od K87
> patrzymy na **samą rozgrywkę**. Uruchomienie rdzenia przy tym przeglądzie
> (nie lektura) pokazuje, że pętla sandboxa domyka się, ale jest pusta:
>
> **Zmierzone na `new_session(73)`:**
> 1. Partia jest do wygrania w **trzy miesiące gry**: `recruit`×5 → `muster` →
>    (`march`+`assault`)×2 daje `result.player_result = "victory"`,
>    księstwo AI schodzi do `settlements=0, parties=0` w roku 1, miesiącu 3.
> 2. Gdy gracz **nic nie robi** przez 20 tur, na mapie **nigdy nie pojawia się
>    wojsko wroga** — `duchies[ai].parties` zostaje `0`, a morale AI spada do
>    `-8`. Powód jest w rdzeniu: `ai.take_duchy_military_action`
>    (`src/tbb/ai.py:536`) co turę bezwarunkowo robi `muster` → `march` →
>    `assault`, więc AI wystawia oddział (bohater + 1 rekrut z garnizonu
>    posterunku) i **traci go w tej samej turze** szturmując „Posterunek gracza"
>    broniony przez jednostkę `training=5, equipment=12`. Wróg nigdy nie stoi na
>    mapie dłużej niż wnętrze własnej tury; gracz nie widzi przeciwnika.
> 3. Klient **nie ma rozkazu `engage`** — pasek to `next_turn`, `develop`,
>    `recruit`, `muster`, `march`/`move`, `assault`, `save`, `load`. Most
>    obsługuje `engage` od K65 (`src/tbbbridge/session.py:347`), gracz nie ma jak
>    go wydać.
>
> **Kolejność jest celowa i wynika z reguły przegranej:**
> `Duchy.is_defeated` (`src/tbb/duchy.py:72`) wymaga **braku osad *i* braku
> oddziałów**. Gdyby najpierw wszedł powściągliwy AI (1c), oddział wroga
> przeżywałby tury, a gracz — bez `engage` — **nie mógłby wygrać partii wcale**.
> Dlatego najpierw gracz dostaje odpowiedź na wojsko w polu, dopiero potem
> wojsko zaczyna w polu zostawać. Żaden commit nie zostawia gry niewygrywalnej.
- [x] **G108.1a** `order_result.gd` — tekst statusu rozróżnia rozkaz `engage`
      (starcie z wojskiem wroga: wynik bitwy + straty, po polsku), pozostałe
      statusy bez zmian. Scena ma nazwany przycisk „Uderz na wojsko wroga"
      w pasku rozkazów, spójny z teksturowanym nośnikiem K103 (bez wiązania).
      *(simple)*
- [x] **G108.1b** Klik „Uderz na wojsko wroga" wydaje rozkaz `engage` przez
      most, pokazuje skutek bitwy na ekranie (baner wyniku + widok bitwy) i
      utrwala partię — e2e przez dwa procesy mostu na układzie, w którym oddział
      wroga **stoi w sąsiednim regionie**. Rozkaz bez sąsiedniego wroga daje
      czytelny „bez zmian", nie pusty status ani błąd. *(standard)*
- [x] **G108.1c** **Rdzeń: AI nie rzuca oddziału na osadę bez szans.**
      `ai.take_duchy_military_action` szturmuje dopiero, gdy wystawiony oddział
      ma realną szansę wobec garnizonu celu (jawne, deterministyczne kryterium
      siły — nie losowanie); w przeciwnym razie oddział **zostaje w polu albo w
      osadzie** i księstwo go nie traci. Test odtwarza układ z repro (`seed=73`,
      oddział AI = bohater + rekrut, „Posterunek gracza" z jednostką
      `training=5, equipment=12`) i sprawdza, że po 5 turach bez ruchu gracza AI
      **wciąż ma oddział** (`duchies[ai].parties == 1`), a jego morale nie
      spada przez samobójcze szturmy. Dotychczasowe testy AI przechodzą albo
      zmieniają kryterium **jawnie**, z powodem w commicie. *(standard, ryzyko:
      dotyka rdzenia — jedynego źródła reguł; nie zmieniać przy okazji reguł
      ruchu, obrażeń ani ekonomii)*
- [x] **R108.1 (dług techniczny)** Żaden przycisk paska rozkazów nie jest martwy
      ani nieoprawiony — jedno źródło definicji przycisków + testy regresji.
      *(commit 21a2a3f; zaplanowane poza tym plikiem)*
- [x] **G108.1e [GRAFIKA]** Ikona rozkazu „Uderz na wojsko wroga" w pasku.
      *(commit d4de6e1; zaplanowane poza tym plikiem)*
- [x] **G108.1d** Widoczny skutek: po kilku turach bez akcji gracza **wojsko
      wroga stoi na mapie strategicznej** i jest rozpoznawalne jako wrogie
      (figura `party_ai_unit.png` w regionie AI), a klik „Uderz na wojsko wroga"
      na sąsiednim wrogim oddziale kończy się bitwą z wynikiem na ekranie.
      Dowód: screenshot 1152×648 mapy z wojskiem wroga oraz screenshot bitwy
      po `engage`. **Zamknięte i zaakceptowane wizualnie** na żywym moście:
      `task-606-live-enemy-army-1152x648.png` oraz
      `task-607-live-engage-battle-1152x648.png`; layout zachowuje mapę,
      legendę, status i pasek rozkazów w viewport 1152×648. *(standard)*
> **K108 — ZMIERZONY 2026-08-06 (uruchomienie rdzenia na `seed=73`, nie
> lektura):** cel kamienia jest osiągnięty. Wojsko AI **stoi na mapie od
> miesiąca 2** (`border` → `player outpost` → `player lands`, oddział 3 jednostek
> utrzymywany turami), a gracz bierny **przegrywa partię w 13 turach**:
> AI zdobywa obie osady gracza, snapshot daje
> `result = {"is_over": true, "winner": "ai", "player_result": "defeat"}`.
> Poprzedni objaw (AI traci oddział co turę, morale `-8`) nie występuje.
> Dowody wizualne K108 zostały zaakceptowane: ekran bitwy nie wypycha mapy
> poza okno, a oba kadry z żywej sesji (`task-606` i `task-607`) pokazują
> odpowiednio wojsko AI na mapie i rozstrzygnięte starcie po `engage`.

## Kamień milowy 109 — rozkaz wojskowy kosztuje miesiąc (pętla tura po turze)
> **Zwrot kierunku (przegląd bootstrap-diff 2026-08-06, po K108).** K108 dał
> przeciwnika, który zostaje na planszy i naciska. Ten sam pomiar odsłonił
> **głębszy, wcześniej niewidoczny brak: rozkazy wojskowe nic nie kosztują**.
> Zmierzone na `new_session(73)` **bez ani jednego `next_turn`**:
> `recruit`×5 → `muster` → (`march` + `assault`)×3 kończy się
> `player_result = "victory"` w **roku 1, miesiącu 1**. Kalendarz nie drgnął, AI
> nigdy nie dostało tury, wojsko wroga nie zdążyło się pojawić. Gra nie ma
> ekonomii tury: `march`/`move`/`assault`/`engage` można wydać dowolną liczbę
> razy w jednym miesiącu, a rozkazy gospodarcze ogranicza tylko złoto/pszenica.
> Cała presja z K108 istnieje wyłącznie dla gracza, który dobrowolnie klika
> „Następna tura".
>
> **Kierunek zweryfikowany symulacją tej samej reguły przy przeglądzie:** przy
> **jednej akcji wojskowej oddziału na miesiąc** partia zostaje wygrywalna
> (zwycięstwo w roku 1, miesiącu 4) i **po drodze pojawia się realne starcie w
> polu** — w miesiącu 2 oddział AI stoi na `border` i gracz sięga po
> „Uderz na wojsko wroga". Żaden commit nie zostawia gry niewygrywalnej ani
> nie odbiera graczowi odpowiedzi na wojsko w polu (wniosek 33).
>
> **Reguła obowiązuje także oddziały AI (wniosek 16), a znacznik ustawia
> WYŁĄCZNIE akcja, która zmieniła świat.** To nie jest detal implementacyjny,
> tylko warunek, żeby K109 nie odwrócił po cichu K108.
> `ai.take_duchy_military_action` (`src/tbb/ai.py:553`) wykonuje w **jednej
> turze AI** `muster_duchy_party` → `march_toward_nearest_enemy` →
> `assault_duchy_party_to`, czyli dwie z czterech blokowanych akcji pod rząd.
> Obie interpretacje zmierzono przy przeglądzie, emulując regułę dla AI na
> `seed=73`:
> - odczyt „pierwsza akcja ustawia znacznik" **dosłownie** (bezskuteczny `march`
>   też liczy się jako akcja) → AI po turze 11 **nigdy już nie szturmuje**, a
>   bierny gracz **nie przegrywa nawet po 20 turach** — czyli K109 cofnąłby
>   efekt K108, ogłoszony w tym samym przeglądzie jako zmierzony i skuteczny;
> - odczyt „znacznik ustawia tylko akcja, która zmieniła świat" → przegrana
>   biernego gracza wypada **w turze 13**, dokładnie jak dziś.
>
> Bierzemy odczyt drugi. Mechanizm: `march_toward_nearest_enemy` na oddziale
> **już sąsiadującym** z celem zwraca świat bez zmian (`next_march_step` daje
> `None`), więc nie ustawia znacznika i szturm w tej samej turze AI przechodzi;
> marsz, który realnie przesunął oddział, znacznik ustawia i wtedy szturmu w tym
> miesiącu nie ma — ale w tym układzie oddział i tak nie sąsiadował jeszcze z
> celem. Wyjmowanie AI spod reguły jest **wykluczone**: kolidowałoby z wnioskiem
> 16 („gracz i AI przez te same reguły świata"). Symulacja z wniosku 35 objęła
> wyłącznie stronę gracza i tego przypadku nie wykluczała.
>
> Zakres celowo wąski: **licznik akcji, nie balans**. Nie ruszamy punktów ruchu
> w bitwie, kosztów rozkazów gospodarczych, tempa AI ani `muster`.
- [x] **G109.1a [RDZEŃ]** Oddział niesie stan „działał w tym miesiącu", a nowy
      miesiąc go zeruje: `Party` ma jawny znacznik akcji, `WorldMap.tick_parties`
      (uruchamiane raz na turę w `run_headless_game`) czyści go dla wszystkich
      oddziałów, a `tbbbridge.persist.dump/load_party` przenosi go round-trip
      (zapis partii nie może rozdawać darmowej akcji). Znacznik jest polem
      **każdego** oddziału — gracza i AI tak samo (wniosek 16); nie ma pola
      „czyj oddział" ani wyjątku po właścicielu. Sam znacznik jeszcze
      niczego nie blokuje — istniejące testy rdzenia, mostu i klienta przechodzą
      bez zmian w kryteriach. *(simple, ryzyko: dotyka rdzenia i kontraktu
      persystencji — nie zmieniać przy okazji reguł ruchu ani walki)*
- [x] **G109.1b [RDZEŃ + MOST]** Druga akcja wojskowa w tym samym miesiącu nie
      robi nic: `move`/`march`/`assault`/`engage` oddziału ze znacznikiem
      zostawia świat bez zmian (pozycja, osady, garnizony, morale i RNG jak
      przed rozkazem). **Znacznik ustawia wyłącznie akcja, która naprawdę
      zmieniła świat** — rozkaz zakończony bez zmiany (np. `march` oddziału już
      sąsiadującego z celem, gdzie `next_march_step` daje `None`) znacznika
      **nie** ustawia i nie zużywa miesiąca. Most odpowiada wtedy
      `{"ok": true, ...,"changed": false}` — **nie błędem** (wniosek 14).
      **Reguła obejmuje tak samo oddziały AI** (wniosek 16): nie wolno dodawać
      wyjątku dla `ai.*` ani sprawdzać właściciela oddziału.
      Test dowodzi na `seed=73` trzech rzeczy: (a) `muster` → `march` → drugi
      `march` bez skutku, `next_turn` → `march` znowu działa; (b) `march`
      bezskuteczny nie blokuje kolejnej akcji w tym samym miesiącu; (c)
      **regresja K108: bierny gracz (same `next_turn`) nadal przegrywa w 13
      turach** — `result = {"is_over": true, "winner": "ai",
      "player_result": "defeat"}`, bo `ai.take_duchy_military_action`
      (`src/tbb/ai.py:553`) łączy `march` i `assault` w jednej turze AI i przy
      błędnym odczycie znacznika przestałby szturmować (zmierzone: brak
      przegranej nawet po 20 turach). Rozkazy
      gospodarcze (`develop`/`recruit`) i `muster` bez zmian; testy e2e klienta,
      które łączyły kilka akcji wojskowych w jednym miesiącu, dostają
      `next_turn` między nimi — **jawnie, z powodem w commicie**. *(standard,
      ryzyko: dotyka rdzenia, przechodzi przez wszystkie ścieżki rozkazów
      klienta i może po cichu odwrócić K108 — patrz kryterium (c))*
- [x] **G109.1c** Gracz widzi, dlaczego rozkaz nic nie dał: klik akcji wojskowej
      oddziałem, który już działał w tym miesiącu, pokazuje czytelny polski
      status w rodzaju „Oddział już działał w tym miesiącu — zakończ turę"
      (nie puste pole i nie „rozkaz nie powiódł się"), a po „Następna tura" ten
      sam rozkaz znowu zmienia stan na ekranie. E2e przez dwa procesy mostu +
      dowód wizualny 1152×648 stanu po zablokowanym rozkazie. *(standard)*
> **Kamień 109 — UKOŃCZONY** (`53d6d98`, `9bb7686`, `dd0f67e`, `af80dcc`,
> `0fc0819`, `6d6946a`). Zmierzone ponownie przy przeglądzie 2026-08-07 na
> uruchomionym rdzeniu (`new_session(73)`, nie z lektury):
> - `Party.acted_this_month` istnieje (`src/tbb/party.py:16`), reguła obejmuje
>   oddziały obu stron, a znacznik ustawia tylko akcja zmieniająca świat;
> - **regresja K108 stoi**: bierny gracz (same `next_turn`) przegrywa w **13
>   turach** (`{"is_over": true, "winner": "ai", "player_result": "defeat"}`,
>   rok 2, miesiąc 1) — dokładnie jak przed K109;
> - partia jest wygrywalna: przy jednej akcji wojskowej na miesiąc sekwencja
>   priorytetów `assault` → `engage` → `march` daje `player_result="victory"`
>   w **roku 1, miesiącu 4**, po drodze z realnymi starciami w polu.
> Ekonomia tury działa — i dopiero ona odsłoniła defekt z K110.

## Kamień milowy 110 — armia stojąca w regionie wrogiej osady potrafi ją zdobyć
> **Zwrot kierunku (przegląd bootstrap-diff 2026-08-07, po K109).** Odkąd tura
> kosztuje, partia toczy się miesiącami i **wchodzi w stan, z którego nie ma
> wyjścia**. Zmierzone na uruchomionym moście (`new_session(73)`, sekwencja
> wyłącznie z rozkazów, jakie ma klient): gracz robi `recruit`×5, `muster`,
> a potem co miesiąc jedną akcję z priorytetem `engage` → `assault` → `march`.
> Wygrywa **każde** starcie w polu (miesiące 2–4) i ląduje oddziałem 3 jednostek
> (hp 89, atak 24) w regionie `ai lands`, **czyli tam, gdzie stoi AI Keep**
> (garnizon 2). Od tej chwili wszystkie trzy rozkazy wojskowe zwracają
> `{"kind":"order","changed":false}` **na zawsze**: sprawdzone do roku 7,
> miesiąca 3 (80 tur) — `is_over: false`, po 2 osady na stronę, oba księstwa
> żywe, nic się nie rusza. Gra nie da się ani wygrać, ani przegrać.
>
> **Mechanizm ustalony w kodzie, nie zgadnięty:**
> `nearest_enemy_settlement` (`src/tbb/ai.py:134`) liczy `distances[start] = 0`,
> więc dla oddziału stojącego **w** regionie wrogiej osady zwraca **ten sam
> region**. `assault_nearest_enemy_settlement` (`ai.py:510`) odrzuca go zaraz
> potem warunkiem `target not in world.neighbors(start)` → `return world`.
> Ta sama para blokuje wariant z jawnym celem
> (`assault_duchy_party_to`, `ai.py:445`) i ścieżkę AI
> (`take_duchy_military_action`, `ai.py:553`). Niżej `next_march_step`
> (`ai.py:196`) zwraca `None` dla `start == target`, a fundament rdzenia mówi to
> wprost: `start_settlement_battle` (`src/tbb/world.py:378-381`) podnosi
> `ValueError` na `source == destination` i na brak sąsiedztwa. **Szturm istnieje
> wyłącznie „z sąsiedniego regionu"; szturm „spod murów" nie istnieje.**
>
> **Do stanu bez wyjścia prowadzi zwykła gra, nie egzotyka.** Wejście daje
> `engage`: wygrane starcie przesuwa zwycięzcę do regionu pokonanego, także gdy
> stoi tam wroga osada (`_can_enter_adjacent_region`, `ai.py:225`, blokuje takie
> wejście tylko marszowi). Klient wysyła `assault` **bez celu**
> (`game/scripts/main.gd:300`; cel dostaje wyłącznie „Wyrusz w pole",
> `main.gd:323-325`), więc gracz nie ma nawet obejścia — sprawdzone: ten sam
> stan z jawnym `target="ai outpost"` rozstrzyga się normalnie
> (`{"kind":"battle","outcome":"zwycięstwo"}`), tylko klient nie umie takiego
> rozkazu wysłać. Reguła jest symetryczna, więc AI zakleszcza się tak samo.
>
> **Pokrewny, ale osobny od G92.1c.** G92.1c dotyczy szturmu na osadę
> **sąsiedniego** regionu, w którym stoi party niebędące jej obrońcą; K110
> dotyczy oddziału stojącego **w regionie samej osady**. Wspólny jest guard
> `apply_settlement_battle_result` (`src/tbb/world.py:494-499`): przy
> `ATTACKER_WIN` obecność w regionie docelowym oddziału, który nie broni osady,
> podnosi `ValueError("destination is already occupied by a party")` — a w
> układzie K110 tym oddziałem jest **sam atakujący**. Ścieżka z G110.1a musi
> więc jawnie rozstrzygnąć, gdzie ląduje zwycięzca, zamiast przechodzić przez
> ten guard. Warunek podjęcia G92.1c (reprodukcja w normalnej partii) nadal
> **nie** został spełniony — K110 go nie zastępuje i nie zamyka.
>
> Zakres celowo wąski: **jedna brakująca reguła zdobycia osady**. Nie ruszamy
> `muster`, tempa AI, balansu ani reguł ruchu w bitwie.
- [x] **G110.1a [RDZEŃ]** *(rozcięte na trzy plasterki: `b9682a5` rozstawienie,
      `f434804` skutek w świecie, `86aaceb` koszt miesiąca)* Rdzeń umie rozstrzygnąć szturm oddziału stojącego
      **w tym samym regionie** co wroga osada: nowa ścieżka obok
      `start_settlement_battle` / `resolve_settlement_battle*` (`source ==
      destination` przestaje być `ValueError` **tylko** w tej nowej ścieżce —
      istniejący kontrakt sąsiedztwa zostaje nietknięty). Rozstawienie jak w
      szturmie z sąsiedztwa: oddział jako `ATTACKER` od `Hex(0, row)`, garnizon
      jako `DEFENDER` od `Hex(2, row)`. Zwycięstwo → osada **i** region zmieniają
      właściciela, ocalali atakującego zostają w regionie; porażka → właściciel
      bez zmian, ocalali zostają w regionie (nie ma dokąd się wycofać);
      bitwa nierozstrzygnięta to **legalny wynik**, nie wyjątek (wniosek 14,
      kontrakt z G89.1a). Znacznik miesiąca z K109 obowiązuje tak samo jak przy
      szturmie z sąsiedztwa, dla oddziałów obu stron (wniosek 16). Wszystkie
      dotychczasowe testy szturmu przechodzą bez zmian w kryteriach.
      *(standard, ryzyko: dotyka rdzenia — jedynego źródła reguł; nie zmieniać
      przy okazji reguł ruchu, `muster` ani warunku siły z K108)*
- [x] **G110.1b [RDZEŃ + MOST]** *(rozcięte: `1580ca5` rdzeń kieruje rozkaz,
      `f7c1e88` most daje wynik bitwy i zakleszczenie znika)* `assault` przestaje być martwy pod murami:
      gdy oddział stoi w regionie wrogiej osady, `assault` **bez celu** oraz
      `assault` z celem równym własnemu regionowi kierują do ścieżki z G110.1a
      zamiast zwracać świat bez zmian; most odpowiada `{"kind":"battle", …}`
      z wynikiem i stratami, a nie `changed: false`. **Reguła obejmuje tak samo
      AI** (`take_duchy_military_action`) — bez wyjątku po właścicielu.
      Test dowodzi na `seed=73` czterech rzeczy: (a) oddział w regionie wrogiej
      osady szturmuje ją i przy zwycięstwie region zmienia właściciela;
      (b) **regresja K108/K109: bierny gracz nadal przegrywa w 13 turach**
      (`{"is_over": true, "winner": "ai", "player_result": "defeat"}`);
      (c) **regresja K109: sekwencja priorytetów `assault` → `engage` → `march`
      nadal wygrywa w roku 1, miesiącu 4**; (d) **zakleszczenie znika** —
      sekwencja `engage` → `assault` → `march` (ta z diagnozy, dziś martwa przez
      80 tur) kończy partię rozstrzygnięciem. Rozkazy gospodarcze i `muster`
      bez zmian. *(standard, ryzyko: te same funkcje `ai.*` obsługują gracza i
      AI; łatwo po cichu odwrócić K108 — patrz kryteria (b) i (c))*
- [x] **G110.1c** *(commit `d81cb79`)* Gracz widzi zdobycie osady, pod którą stoi: klik „Szturmuj
      osadę" oddziałem stojącym w regionie wrogiej osady pokazuje wynik bitwy
      i straty w statusie, a region **na mapie** zmienia stronę (herb/kolor
      właściciela) bez ręcznego odświeżania. E2e przez dwa procesy mostu +
      dowód wizualny 1152×648 pary kadrów „przed / po" szturmu spod murów.
      *(standard)*
> **Kamień 110 — UKOŃCZONY.** Zweryfikowane ponownym uruchomieniem mostu przy
> przeglądzie 2026-08-07 (`new_session(73)`, sekwencje wyłącznie z rozkazów
> klienta): zakleszczenie z diagnozy **zniknęło** — sekwencja `engage` →
> `assault` → `march`, martwa przez 80 tur, kończy się teraz zwycięstwem gracza
> w **roku 1, miesiącu 7**. Regresje stoją: bierny gracz przegrywa w **13
> turach** (rok 2, miesiąc 1), a priorytet `assault` → `engage` → `march`
> wygrywa w **roku 1, miesiącu 4**.

## Kamień milowy 111 — czytelny powód, gdy marsz blokuje wroga armia
> Zaplanowany poza tym plikiem jako **task-621…624** (G111.1a rdzeń wskazuje
> blokujący oddział, G111.1b most nazywa blokujący region w bezskutecznym
> rozkazie ruchu, G111.1c polski status w kliencie, G111.1d dowód z żywej
> sesji) — dopisane tu dla ciągłości, **nie planować ich ponownie**.
> Diagnoza (pomiar 2026-08-07, potwierdzony po K110): sekwencja `assault` →
> `march` bez `engage` stoi w miejscu od miesiąca 3 przez ≥25 tur, bo wroga
> armia okupuje `border`, a klient mówi wyłącznie „bez zmian". Odpowiedź w grze
> **istnieje** („Uderz na wojsko wroga"), więc to defekt czytelności, nie reguł.
- [x] **R111.1 (dług techniczny)** Znacznik akcji miesiąca pochodzi z rdzenia,
      nie ze zgadywania w kliencie (+ testy regresji). *(commit `24f5a4a`)*
- [x] **G111.1a [RDZEŃ]** Rdzeń wskazuje obcy oddział blokujący marsz.
      *(commit `e82a078`)*
- [x] **G111.1b [MOST]** Bezskuteczny rozkaz ruchu niesie nazwę blokującego
      regionu (`blocked_region`). *(commit `22b99c0`)*
- [x] **G111.1c [KLIENT]** Status marszu mówi po polsku, kto zagradza drogę
      i co z tym zrobić. *(commit `1afc76d`)*
- [x] **G111.1d [POMIAR]** Gracz w żywej sesji widzi, że drogę zagradza wojsko
      wroga. *(commit `5baf330`)*
> **Kamień 111 — UKOŃCZONY 2026-08-08.** Wzorzec „rozkaz bez skutku niesie
> powód" (pole diagnostyczne w `command_result` → projekcja w `order_result.gd`
> → polski tekst statusu) jest gotowy do reużycia — bierze go **K114**.

## Kamień milowy 112 — wojsko z garnizonu trafia w pole (koniec martwej partii bez armii) — UKOŃCZONY
> **Zwrot kierunku (przegląd bootstrap-diff 2026-08-07, po K110).** K110 usunął
> zakleszczenie „armia pod murami", więc partia toczy się dalej — i za jego
> horyzontem (wniosek 36) leży **kolejny stan bez wyjścia, tym razem po stronie
> AI**. Zmierzone na uruchomionym moście, nie z lektury (`new_session(73)`,
> wyłącznie rozkazy dostępne w kliencie):
>
> 1. **Rekruci nie docierają do pola.** `recruit` (`src/tbb/ai.py:101`) obsadza
>    *pierwszą* osadę z wolną ludnością, a `muster` (`ai.py:116`) zbiera garnizon
>    *pierwszej* osady bez oddziału — obie po kolejności `world.regions`, obie
>    bez celu. Gracz „rozwojowy" (`develop`×10 → `recruit`×10 → `muster`) dostaje
>    oddział **1 jednostki** (hero, hp 25), bo `develop` wyczerpało `free`
>    w „player lands", więc rekruci wylądowali w „player outpost" — i tam
>    **zostają**. Gracz „wojenny" (`recruit`×10 → `muster`) dostaje oddział
>    **5 jednostek** (hp 73) i wygrywa w roku 1, miesiącu 4. Ta sama sekwencja
>    rozkazów, dwa różne wyniki, a klient nie mówi o tym ani słowa.
> 2. **Po utracie oddziału partia zamiera na 10 lat gry.** Gracz „rozwojowy"
>    traci jedynkę w pierwszym szturmie (miesiąc 3) — i od tej chwili **nic się
>    nie dzieje**: sprawdzone do tury 120 (rok 10, miesiąc 4), `is_over: false`,
>    po 2 osady na stronę. Armia AI (3 jednostki) stoi na `border` **bez ruchu**,
>    bo `take_duchy_military_action` (`ai.py:630`) szturmuje wyłącznie przy
>    przewadze 2:1 z K108, a siły rosną równolegle: `str_att` 78 → 108,
>    `str_def` 40 → 63 przez 120 tur. Ratio nigdy nie osiąga progu, więc AI
>    **nigdy** nie zaatakuje. Jednocześnie własne osady AI trzymają **4 + 3
>    jednostki garnizonu**, których nie ma jak wprowadzić do pola.
>
> **Wspólny brak jest jeden i nie jest strojeniem AI:** w rdzeniu **nie istnieje
> reguła wzmocnienia stojącego oddziału garnizonem osady**. `muster_party`
> tworzy oddział raz, jedno księstwo ma jeden oddział, a garnizon zrekrutowany
> później zostaje w murach na zawsze. Progu 2:1 z K108 **nie ruszamy** — po
> wzmocnieniu AI spełni go własną, niezmienioną regułą.
>
> Zakres celowo wąski: **jedna brakująca reguła** + jej widoczny skutek.
> Nie ruszamy progu z K108, tempa AI, balansu, celowanego `develop`/`recruit`
> ani reguły „ile garnizonu wolno zabrać" (nadal odłożona — wzmocnienie zabiera
> cały garnizon, symetrycznie do `muster`).
>
> **Nota kolejności (przegląd 2026-08-07, po K110/R111.1):** „licznik oddziału"
> z G112.1d **nie istnieje dziś w kliencie** — panel wybranego regionu mówi
> wyłącznie „Armia: twoja armia" / „brak armii", bez jednej liczby
> (`game/scripts/main.gd:654-667`). Wzrost oddziału po `reinforce` da się więc
> dziś pokazać tylko figurą i statusem rozkazu. Liczby daje **K113**; wykonawca
> G112.1d albo bierze K113 wcześniej i pokazuje wzrost licznikiem, albo
> ogranicza kryterium do statusu i figury i **nie wymyśla własnego licznika**
> obok tego z K113.
- [x] **G112.1a [RDZEŃ]** Oddział stojący w regionie **własnej** osady wciąga jej
      garnizon: nowa reguła obok `muster_party`, oddział rośnie o wszystkie
      jednostki garnizonu, osada zostaje z garnizonem 0, hero i rany bez zmian.
      Brak osady w regionie, cudza osada, pusty garnizon albo brak oddziału →
      świat **bez zmian** (`changed=false`, nie wyjątek — wniosek 14). Znacznik
      akcji miesiąca z K109 obowiązuje tak samo jak przy `march`/`assault`, dla
      oddziałów obu stron (wniosek 16). Dotychczasowe testy `muster` przechodzą
      bez zmian w kryteriach. *(standard, ryzyko: dotyka rdzenia — jedynego
      źródła reguł; nie zmieniać przy okazji `muster`, progu 2:1 z K108 ani reguł
      ruchu)*
- [x] **G112.1b [MOST]** Rozkaz `reinforce` w `apply_command`: kieruje do reguły
      z G112.1a dla księstwa gracza, odpowiada `{"kind":"order","changed":…}`,
      nieskuteczny (brak własnej osady pod oddziałem, pusty garnizon, akcja już
      wykonana w tym miesiącu) → `changed:false` przy `ok:true`, nigdy błąd.
      Test na `seed=73` dowodzi: `recruit`×10 → `muster` → `move("player
      outpost")` → `next_turn` → `reinforce` daje oddział większy o garnizon
      outpostu, a **regresje stoją**: bierny gracz przegrywa w 13 turach,
      priorytet `assault` → `engage` → `march` wygrywa w roku 1, miesiącu 4.
      *(standard)*
- [x] **G112.1c [RDZEŃ]** AI bez przewagi 2:1 nie stoi bezczynnie: gdy
      `take_duchy_military_action` odrzuci szturm warunkiem siły, oddział AI
      stojący w regionie własnej osady wzmacnia się jej garnizonem zamiast
      kończyć turę bez ruchu. Test odtwarza zmierzony stan (gracz bez oddziału,
      armia AI na `border`, garnizony AI 4 + 3) i dowodzi, że partia
      **rozstrzyga się** zamiast trwać 120 tur bez zmiany; regresje K108/K109
      z G112.1b przechodzą bez zmian. **Progu 2:1 nie wolno tknąć.**
      *(standard, ryzyko: te same funkcje obsługują gracza i AI)*
- [x] **G112.1d [KLIENT]** Gracz widzi, jak oddział rośnie: przycisk „Wzmocnij
      oddział" w pasku rozkazów wydaje `reinforce`, status po polsku mówi
      o wzmocnieniu albo o jego braku (np. „oddział nie stoi w twojej osadzie"),
      a licznik/figura oddziału na mapie zmienia się bez ręcznego odświeżania.
      E2e przez dwa procesy mostu + dowód wizualny 1152×648 pary kadrów
      „przed / po" wzmocnienia. *(standard)*

> **Pomiar zamykający K112 (2026-08-08, żywy most `seed=73`):** po sekwencji
> `develop`×10 → `recruit`×10 → `muster` partia kończy się po **6 turach**;
> `result` ma `winner: "ai"` i `player_result: "defeat"`. Przebieg
> wzmocnienia AI: oddział na `border` rośnie z 2 jednostek, po dojściu do
> `ai outpost` nadal ma 2, a następnie **oddział AI rośnie 2 → 4**, pobierając
> garnizon osady **1 → 0**. To potwierdza, że partia rozstrzyga się dzięki
> wzmocnieniu, a nie samemu upływowi czasu.

## Kamień milowy 113 — siła widoczna liczbą: oddział i garnizon w panelu regionu
> **Zmierzone przy przeglądzie bootstrap-diff 2026-08-07** (uruchomiony
> `tbbbridge`, `new_session(73)`, wyłącznie rozkazy dostępne w kliencie) — nie
> z lektury: most niesie na region komplet liczb siły od K63/K74, a klient
> **nie pokazuje ani jednej**.
>
> - `snapshot.map.regions[*].party` ma `size`, `hp`, `attack`, `defense`,
>   `wounded`, `acted_this_month` (`src/tbbbridge/snapshot.py:61-88`);
>   `…[*].settlement` ma `garrison`, `population`, `free`, zapasy i produkcję
>   (`snapshot.py:23-58`). `SnapshotModel._placeable_regions` przepuszcza cały
>   słownik regionu (`game/scripts/snapshot_model.gd:32-50`), więc dane **są
>   już w kliencie**.
> - Panel wybranego regionu renderuje z tego cztery wiersze, z czego dwa gubią
>   całą treść: `_settlement_text` daje samą nazwę osady, a `_party_text` samo
>   „twoja armia" / „wroga armia" / „brak armii"
>   (`game/scripts/main.gd:654-667`). Karta statusu pokazuje morale i **liczbę**
>   osad/oddziałów, nie ich siłę (`main.gd:523-552`); mapa pokazuje obecność
>   figury, nie jej wielkość. PŻ widać dopiero w widoku bitwy (K98) — czyli
>   **po** decyzji.
> - Dwa przebiegi różniące się **wyłącznie** dziesięcioma `develop` przed
>   rekrutacją: `recruit`×10 → `muster` daje oddział `size 5, hp 73, atk 29`,
>   a `develop`×10 → `recruit`×10 → `muster` daje `size 1, hp 25` (bohater sam).
>   **Na ekranie oba wyglądają identycznie**: ta sama figura, ten sam wiersz
>   „Armia: twoja armia". Gracz nie ma jak zauważyć, że idzie na szturm
>   jedynką — a to dokładnie pułapka z wniosku 39, którą K112 usuwa w regułach,
>   ale nie w widoku.
> - To samo dotyczy strony wroga: przed `assault`/`engage` gracz nie widzi ani
>   garnizonu osady (`AI Keep`: 1 na starcie, rośnie z turami), ani siły armii
>   AI stojącej na `border`. Decyzja „bić czy nie" jest dziś **ślepa**, choć
>   rdzeń AI podejmuje ją po jawnym stosunku sił 2:1 (K108).
>
> Kryterium z briefu **[W]** brzmi „da się grać patrząc, a nie czytając logi";
> tu nie da się grać nawet czytając — liczby nie docierają na ekran w ogóle.
> Zakres celowo wąski: **wyłącznie klient**. Bez zmian w rdzeniu, moście,
> kontrakcie snapshotu i bez nowego rozkazu. To nie jest balans ani nowa
> warstwa oprawy — to brakująca projekcja danych, które już przychodzą.
- [x] **G113.1a [KLIENT]** Czysty polski tekst siły w kliencie: funkcja
      projekcji zamienia słownik `party` na tekst z **liczbą jednostek i PŻ**
      (np. „twoja armia: 5 jednostek, 73 PŻ"), a słownik `settlement` na tekst
      z **garnizonem** (np. „Twierdza gracza · garnizon 2"). Brakujące,
      niepoprawne lub nieliczbowe pola → dotychczasowy tekst zastępczy
      („brak armii" / „brak osady" / sama nazwa) bez błędu i bez „0" wziętego
      z powietrza. Testy headless na fixture'ach snapshotu, bez uruchamiania
      mostu; dotychczasowe testy panelu przechodzą bez zmian w kryteriach.
      *(simple, commit `0235b89`)*
- [x] **G113.1b [KLIENT]** Panel wybranego regionu pokazuje te liczby dla
      **obu stron**: wybór regionu z własnym oddziałem daje jego siłę, wybór
      regionu z wrogą osadą daje jej garnizon, a wartości odświeżają się po
      rozkazie i po turze **bez ręcznego odświeżania** (szturm zmniejsza
      garnizon, straty zmniejszają oddział). E2e przez dwa procesy mostu na
      `seed=73` dowodzi rozróżnienia zmierzonego wyżej: po `recruit`×10 →
      `muster` panel pokazuje oddział 5 jednostek, a po `develop`×10 →
      `recruit`×10 → `muster` — oddział 1 jednostki. Dowód wizualny 1152×648:
      kadr z zaznaczonym regionem własnego oddziału i kadr z zaznaczonym
      regionem wrogiej osady. *(standard, commit `a1643fe`)*
> **Kamień 113 — UKOŃCZONY 2026-08-08.** `WorldPresentation.party_strength_text`
> / `settlement_strength_text` dają liczbę jednostek, PŻ i garnizon; panel
> wybranego regionu pokazuje je dla obu stron.

## Kamień milowy 114 — rozkaz gospodarczy mówi, dlaczego nic nie zrobił (koniec ślepego klikania)
> **Zmierzone przy przeglądzie bootstrap-diff 2026-08-08 na uruchomionym
> moście** (`new_session(73)`, wyłącznie rozkazy dostępne w kliencie), nie
> z lektury. `pytest` w całości zielony (3m06s).
> **SPROSTOWANE po recenzji tego przeglądu — pierwsza wersja diagnozy wskazała
> zły mechanizm.** Odtworzono ją i obalono na tym samym ziarnie; niżej stoją
> wyłącznie liczby, które daje uruchomiony kod. Nie planować pod poprzednią
> wersję (współdzielona pula jako przyczyna trwałego zastoju) — to **nie** jest
> to, co się dzieje.
>
> 1. **Blokada nr 1 — chwilowa, w obrębie tury.** `develop_duchy_settlement`
>    (`src/tbb/ai.py:26-45`) wymaga `settlement.free >= building.staff`,
>    a `recruit_duchy_unit` (`ai.py:112`) wymaga `free > 0` i złota — to **ta
>    sama** wolna ludność. Przebieg: `recruit`×8 na świeżej partii daje **osiem
>    razy `changed:true`** (`free` obu osad 4 → 0, złoto 10 → 6, garnizon
>    1 → 5), a **następne osiem `develop` w tej samej turze daje osiem razy
>    `changed:false`**. Odwrotna kolejność jest symetryczna: `develop`×8 buduje
>    `Farm/Smith/Barracks/Market` w obu osadach, zjada `free` do 0 i następny
>    `recruit` zwraca `changed:false`.
>    **Ta blokada sama z siebie mija.** Po jednej turze `free` odrasta, więc
>    klikanie `develop` **raz na turę** po `recruit`×8 daje **`changed:true`
>    w turach 2–6** (w turze 1 jeszcze `false`, pula dopiero co zeszła do 0),
>    a `changed:false` dopiero od tury 7: Farm/Smith/Barracks/Market w Player
>    Keep, Farm/Smith w Player Outpost, `wheat_production` 0 → 3 w obu.
>    „`buildings: []` i produkcja 0/0 na zawsze" zachodzi **wyłącznie** wtedy,
>    gdy gracz już nigdy nie kliknie „Rozwiń osadę".
> 2. **Gracz nie dostaje ani powodu, ani liczby.** Most odpowiada
>    `{"kind":"order","order":"develop","changed":false}` — bez przyczyny;
>    klient pokazuje samo „bez zmian" (`order_result.gd`). Panel wybranego
>    regionu po K113 pokazuje nazwę osady i **garnizon**, a `free`, złoto i
>    budynki są w snapshocie (`snapshot.py:23-58`) i **nie trafiają na ekran**.
>    Gracz nie ma jak odróżnić „kliknij za turę" od „nigdy już nie zadziała".
> 3. **Blokada nr 2 — trwała, i to ona zabija gospodarkę: głód.** Konsumpcja
>    osady = jej ludność (`settlement.py:62`), a Farm daje `wheat=3`
>    (`building.py:22`), więc saldo jest ujemne od startu: zapas pszenicy
>    spada 10 → 0 w 2–4 turach, `free` zamarza na 0 i rozkaz gospodarczy
>    odmawia turę po turze (zmierzone: `recruit` co turę → `changed:false`
>    od tury 5 w nieskończoność, partia wciąż `is_over: false`).
> 4. **Próg głodu leży PRZED pustym spichlerzem — to poprawka po drugiej
>    recenzji i najważniejsza liczba tej diagnozy.** `tick_settlements`
>    (`src/tbb/world.py:133-145`) woła `tick_economy()` **przed**
>    `tick_growth()`, a `tick_growth` (`settlement.py:72-76`) patrzy na zapas
>    **po ticku** i dodatkowo na `below_capacity`. Ludność rośnie więc dokładnie
>    wtedy, gdy `wheat + production − consumption > 0` **i** `capacity is None
>    or population < capacity` — nie wtedy, gdy `storage.wheat > 0`.
>    Te dwa warunki **rozjeżdżają się na progu**, i to zmierzone na `seed=73`
>    zwykłym graniem (co turę `develop` i `recruit` do odmowy): w turze 3 obie
>    osady mają `free=0` i **niezerowy** zapas (Keep 5, Outpost 4), więc test
>    `wheat > 0` orzekłby „poczekaj, ludność przybędzie", a saldo wynosi już
>    **0** (Keep) i **−2** (Outpost) — w turze 4 ludność stoi (Keep 8 → 8,
>    Outpost 9 → 9) i zapas jest 0. Naiwny predykat kłamie **dokładnie w turze
>    wejścia w stan pochłaniający**, czyli w jedynym momencie, w którym rada
>    jeszcze cokolwiek zmienia. Uwaga na `saldo == 0`: zero **nie** rośnie,
>    warunek jest ostry.
> 5. **Z tego stanu nie ma wyjścia żadnym rozkazem klienta.** Sprawdzone
>    empirycznie: `muster` opróżnia garnizon i zbija ludność Keep 8 → 3
>    (konsumpcja 8 → 3), ale przy produkcji 3 saldo wynosi **0**, zapas zostaje
>    **0** i ludność nadal nie przybywa — 9 kolejnych tur bez zmiany. Dlatego
>    rada „poczekaj na przyrost ludności albo wydaj rozkaz w drugiej osadzie"
>    jest w tym stanie **pusta**: druga osada jest równie głodna.
>
> To ten sam kształt defektu co K111 (rozkaz bez skutku milczy o powodzie),
> tylko po stronie gospodarki, i ten sam wzorzec wniosku 40 (reguła wymaga
> stanu, którego gracz nie widzi). **K114 zostaje defektem czytelności** —
> mówi prawdę o stanie, w tym prawdę „tego się nie doczekasz". Naprawa samego
> głodu (produkcja / próg wzrostu / zapas) to **osobny plasterek po K114**,
> patrz „Kolejne kierunki" i wniosek 43 w `docs/PROJECT.md`.
>
> **Zakres celowo wąski.** Nie ruszamy kosztów rozkazów gospodarczych, progu
> 2:1 z K108, tempa AI, balansu ani reguły „ile garnizonu wolno zabrać".
> **Nie otwieramy pełnego panelu ekonomii osady** (nadal odłożony): na ekran
> wchodzi **wyłącznie wolna ludność**, bo to ona rozstrzyga, czy kliknięcie
> cokolwiek zrobi. Zapasy, produkcja i konsumpcja zostają poza kadrem.
> **Wybór osady dla rozkazu gospodarczego to osobny, późniejszy plasterek** —
> K114 tłumaczy odmowę, nie zmienia kontraktu rozkazu.
>
> **Wzorzec do reużycia, nie do wymyślania:** K111 przeprowadził diagnostykę
> rozkazu przez wszystkie warstwy — pole w `command_result`
> (`protocol.py:35-71`), projekcja w `order_result.gd:162`, polski tekst
> w `order_result.gd:21-29`. K114 idzie tą samą ścieżką.
> **Uwaga na dług:** `_blocked_region_name` z K111 **powiela guardy rdzenia**
> w moście (komentarz „Mirror the core's…" w `protocol.py:41`). Powtórzenie
> tego byłoby złamaniem „[W] rdzeń jedynym źródłem reguł" — dlatego powód
> odmowy liczy **rdzeń** (G114.1a), a most go wyłącznie przenosi.
- [ ] **G114.1a [RDZEŃ]** Rdzeń umie powiedzieć, **dlaczego** rozkaz
      gospodarczy nie zmieni świata: czysta funkcja obok
      `develop_duchy_settlement` / `recruit_duchy_unit` zwraca jawny, skończony
      powód dla księstwa albo `None`, gdy rozkaz się powiedzie. Zbiór powodów
      **rozróżnia dwie blokady zmierzone w diagnozie**: `brak wolnej ludności`
      (przejściowa — ludność przybędzie w kolejnej turze) oraz `brak wolnej
      ludności — osada nie wyżywi przyrostu` (trwała), a obok nich `brak
      złota`, `komplet budynków`, `limit garnizonu`, `brak własnej osady`.
      **Predykat rozróżnienia jest przesądzony pomiarem (pkt 4 diagnozy) i nie
      wolno go upraszczać do `storage.wheat > 0`:** powód jest przejściowy
      wtedy i tylko wtedy, gdy `storage.wheat + production.wheat −
      consumption.wheat > 0` (saldo **po** `tick_economy`, warunek ostry — zero
      nie rośnie) **oraz** `capacity is None or population < capacity` (ta sama
      bramka, co w `tick_growth`); w każdym innym przypadku powód jest trwały.
      Wartości wyliczane z tych samych progów, co sama reguła
      (`building.staff`, `RECRUIT_GOLD_COST`, warunek wzrostu z `tick_growth`
      czytany po `tick_economy`, limit 12) — **bez drugiej kopii warunków**.
      Testy odtwarzają zmierzony układ na `seed=73`: świeża partia → `None`;
      `recruit`×8 w pierwszej turze → powód `develop` = brak wolnej ludności
      **przejściowy** (zapas 10, saldo +5); **oraz — test, który obala naiwny
      predykat — tura 3 przebiegu „co turę `develop` i `recruit` do odmowy":
      zapas jeszcze niezerowy (Keep 5, Outpost 4), a powód `recruit` już
      trwały**, bo saldo wynosi 0 i −2; ten sam przebieg dwie tury dalej
      (zapas 0) → nadal trwały. Reguły `develop`/`recruit` **bez zmian
      zachowania** i bez zmian samej ekonomii — to zapytanie, nie naprawa głodu
      (naprawa = osobny plasterek po K114). *(standard, ryzyko: dotyka rdzenia
      — jedynego źródła reguł; nie zmieniać przy okazji kosztów, produkcji,
      progu wzrostu ani kolejności osad)*
- [ ] **G114.1b [MOST]** Bezskuteczny `develop`/`recruit`/`muster` niesie ten
      powód: `command_result` dokłada pole diagnostyczne obok
      `{"kind":"order","changed":false}`, **wyłącznie** gdy rdzeń go zwrócił;
      skuteczny rozkaz i wszystkie dotychczasowe kształty wyniku bez zmian,
      nigdy `ok:false`. Most **nie powiela** warunków rdzenia — pyta funkcję
      z G114.1a. Test na `seed=73` odtwarza `recruit`×8 → `develop`.
      *(standard)*
- [ ] **G114.1c [KLIENT]** Gracz widzi powód i pulę: status rozkazu mówi po
      polsku, czego zabrakło, a panel wybranego regionu dokłada do wiersza
      osady **wolną ludność** obok garnizonu z K113 (np. „Twierdza gracza,
      garnizon: 5, wolni mieszkańcy: 0").
      **Twardy warunek, z recenzji tego przeglądu: tekst nie może obiecywać
      wyjścia, którego w danym stanie nie ma.** Powód przejściowy z G114.1a
      może radzić czekanie (np. „Brak wolnych mieszkańców — ludność przybędzie
      w kolejnej turze."), ale powód **trwały** ma nazwać stan bez fałszywej
      rady (np. „Osada nie wyżywi więcej ludzi — ludność nie przybywa.").
      Tekst **nie może odwoływać się do pustego spichlerza**: pkt 4 diagnozy
      pokazuje, że stan zaczyna się przy zapasie jeszcze niezerowym (5 i 4),
      więc „pusty spichlerz" byłby na progu nieprawdą widoczną na ekranie.
      Kryterium testowe: dla powodu trwałego status **nie zawiera** zachęty do
      czekania ani do wydania rozkazu w drugiej osadzie — bo zmierzono
      (pkt 4–5 diagnozy), że w tym stanie obie osady stoją i żaden rozkaz go
      nie odwraca. Gdyby G114.1a nie dowiozło rozróżnienia, G114.1c **nie
      narzuca żadnej treści rady** i poprzestaje na nazwaniu braku.
      Brakujące/nieliczbowe pole → dotychczasowy tekst bez „0" wziętego
      z powietrza; nieznany powód → dotychczasowe „bez zmian" (nigdy pusty
      status). Bez nowego rozkazu, bez zmian rdzenia i mostu, bez dokładania
      zapasów/produkcji/konsumpcji do panelu — stan trwały niesie **tekst
      powodu**, nie liczba pszenicy (tym bardziej, że na progu ta liczba jest
      jeszcze dodatnia i sama w sobie myli). Testy headless na fixture'ach + dowód
      wizualny 1152×648: kadr z osadą o zerowej wolnej ludności i widocznym
      powodem odmowy. *(standard)*
- [ ] **G114.1d [POMIAR]** Dowód na żywym moście przez dwa procesy
      (`seed=73`), **trzy stany, nie dwa** — trzeci dopisany po recenzji, bo
      dwa pierwsze mierzą wyłącznie skrajności i przepuszczają błąd predykatu:
      (a) `recruit`×8 → `develop` w tej samej turze kończy się na ekranie
      powodem **przejściowym** zamiast „bez zmian" (zapas 10, saldo +5);
      (b) **tura wejścia w głód przy zapasie jeszcze niezerowym** — przebieg
      „co turę `develop` i `recruit` do odmowy", tura 3: obie osady mają
      `free=0`, zapas **5 i 4**, saldo **0 i −2**, więc odmowa `recruit`
      pokazuje powód **trwały**, a status **nie** radzi czekać; kolejna tura
      potwierdza pomiarem, że ludność faktycznie nie urosła (Keep 8 → 8,
      Outpost 9 → 9); (c) ten sam przebieg przy zapasie 0 — powód nadal trwały.
      Stan (b) jest kryterium **rozstrzygającym**: sam (a) i (c) przechodzą
      także dla błędnego predykatu `storage.wheat > 0`.
      **Regresje stoją**: bierny gracz przegrywa w **roku
      1, miesiącu 7** (6× „Następna tura"), a gracz aktywny (`recruit`×10 →
      `muster` → `assault`/`engage`/`march`) wygrywa w **roku 1, miesiącu 4**.
      Zapis pomiaru trafia tutaj, do sekcji K114. *(standard)*

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

## Kolejne kierunki (po odwołaniu bramki oprawy)
> Kolejność wynika z kryterium „gotowe" w `docs/PROJECT.md`. Próg wizualny
> został osiągnięty 2026-08-06; niezależne przyciski, reguły rdzenia, AI,
> ekonomia, walka, ruch, protokół i porządki nie są już wstrzymywane przez
> bramkę oprawy.
- ~~K94: spójność kafli, keep/outpost, tło i kompozycja~~ — **wykonane**.
- ~~K95: ikony wszystkich bieżących rozkazów~~ — **wykonane**.
- ~~G96.1a: sylwetki armii obu stron na mapie~~ — **wykonane**.
- ~~K97: wybór regionu, bezpieczny krok, blokada i wznowienie~~ — **wykonane**.
- ~~K98: osiowa siatka bitwy, dekoracje, jednostki z PŻ i polski wynik~~ —
  **wykonane**.
- ~~K99: hierarchia ekranu strategicznego (mapa, status, rozkazy)~~ —
  **wykonane**.
- ~~K100: polskie etykiety, teatr mapy, karta wyboru, tło okna~~ —
  **wykonane**.
- ~~K101: herby, hierarchia statusu, baner bitwy~~ — **wykonane**.
- ~~K102: tabliczki, PŻ, panel wyboru, feedback rozkazu~~ — **wykonane**.
- ~~K103: przyciski/legenda teksturowane, podłoże mapy/bitwy bez obrysu
  Kenney~~ — **wykonane**.
- ~~K104: residualny Kenney na pergaminie (keep/outpost, dekoracje, recolor
  sylwetek, cue PŻ)~~ — **wykonane** (`task-585-*`).
- ~~K105: figury isometrii/¾ + centrowanie bitwy + ornament pustego wyboru~~
  — **wykonane** (commity `d054581`…`1ebbbd4`; bez `task-*` w
  `game/screenshots/`).
- ~~**K106:** pakiet dowodowy 1152×648 po K105 (świeża partia, wybór regionu,
  bitwa) + jawna ludzka akceptacja progu wizualnego~~ — **wykonane 2026-08-06**;
  brak wskazanego residualu, nie otwarto nowej serii polish.
- ~~Zapis/odczyt z UI: jawne „Zapisz”/„Wczytaj”~~ — rozplanowane jako K86.
- ~~Prawdziwe assety i tekstury zamiast `ColorRect`~~ — rozplanowane jako K87.
- Assety / próg — K87–K105 dały nośnik, mapę, bitwę, hierarchię, PL/teatr,
  herby, plakietki, sterowanie, stonowane podłoże, ton pergaminu, rodzinę
  kształtów figur i residualny chrome; **K106 domknął 2026-08-06 dowód i
  akceptację progu**, bez inventowania kolejnej warstwy oprawy.
- **Mechaniczny teren regionu na mapie strategicznej — ODŁOŻONY DO PROGU
  WIZUALNEGO.** `tbb.world.Region` ma dziś tylko
  `name`, więc `snapshot.map_state` nie ma czego wystawić i kafel mapy w K87
  różnicuje wyłącznie właściciela i osadę. Jeśli zróżnicowana mapa okaże się
  potrzebna, idzie to jako **osobny cienki plasterek dotykający rdzenia i
  mostu**: pole terenu w `Region` (reuse `tbb.terrain`) → `map_state` →
  `SnapshotModel` → wybór tekstury w `MapView`. K94.1b daje różnorodność
  wyłącznie dekoracyjną, bez fałszywego znaczenia mechanicznego. Zmiana rdzenia
  nie jest teraz niezbędna do tego efektu i pozostaje wykluczona.
- ~~Pakiet na Linuksa x86-64: preset eksportu, uruchomienie jedną ikoną~~ —
  **wykonane w całości jako K88** (G88.1a–g).
- ~~Gra jest przegrana po pierwszym kliknięciu „Następna tura", a przegrana
  nigdy się nie kończy~~ — **rozplanowane jako K90** (start symetryczny,
  osiągalny koniec gry, polski tekst wyniku). Pełna diagnoza w sekcji K90.
- ~~Gra obronna („Zbierz oddział" + „Następna tura") zakleszcza partię na amen~~
  — **naprawione jako G92.1** w rdzeniu i na żywym moście. Pełna diagnoza
  zostaje w sekcji K92.
- ~~Druga osada na stronę i większy świat startowy~~ — **wykonane jako
  G92.2a**: pięć regionów, dwie osady na stronę i trwająca partia po zdobyciu
  pierwszej osady.
- ~~Nowa partia z UI po zakończonej grze~~ — rozplanowane jako **K107**
  (G107.1a zrobione, G107.1b–d w kolejce jako task-596…598).
- ~~**Pusty sandbox: da się wygrać w trzy miesiące, a wroga nie widać**~~ —
  rozplanowane jako **K108** i **zmierzone jako naprawione 2026-08-06**: wojsko
  AI stoi na mapie od miesiąca 2, a bierny gracz przegrywa w 13 turach. Zostały
  dowody wizualne (task-605…607) zostały zaakceptowane. Diagnoza zostaje w
  sekcji K108.
- ~~**Rozkaz wojskowy nic nie kosztuje: partię da się wygrać bez ani jednej
  tury**~~ — rozplanowane jako **K109** i **zmierzone jako naprawione
  2026-08-07**: przy jednej akcji wojskowej na miesiąc bierny gracz nadal
  przegrywa w 13 turach, a aktywny wygrywa w roku 1, miesiącu 4. Diagnoza
  zostaje w sekcji K109.
- ~~**Zakleszczenie: armia stojąca w regionie wrogiej osady nie potrafi jej
  zdobyć**~~ — rozplanowane jako **K110** i **zmierzone jako naprawione
  2026-08-07**: martwa dotąd sekwencja `engage` → `assault` → `march` kończy
  partię w roku 1, miesiącu 7, a regresje K108/K109 stoją. Diagnoza zostaje
  w sekcji K110.
- **Marsz zablokowany przez wrogą armię nie mówi o tym graczowi** —
  rozplanowane jako **K111** (task-621…624), diagnoza w sekcji K111.
- **Wojsko z garnizonu nie ma jak trafić w pole, a partia bez armii zamiera** —
  rozplanowane jako **K112** po pomiarze 2026-08-07 (120 tur bez zmiany, AI
  nieruchome przy `str_att` 78→108 vs `str_def` 40→63). Pełna diagnoza w sekcji
  K112; nie powtarzać jej tutaj.
- **Siły nie widać liczbą: gracz decyduje o szturmie na ślepo** —
  rozplanowane jako **K113** po pomiarze 2026-08-07 (ten sam ekran dla oddziału
  5 jednostek i dla jedynki). Pełna diagnoza w sekcji K113; klient-only,
  bez zmian rdzenia i mostu.
- **Rozkaz gospodarczy odmawia bez powodu, a wolnej ludności nie widać** —
  rozplanowane jako **K114** po pomiarze 2026-08-08, **sprostowanym po
  recenzji**: w jednej turze `recruit`×8 → osiem `develop` z `changed:false`
  (blokada chwilowa), a od tury 6 `develop` odmawia przez 25 kolejnych tur,
  bo osady głodują i ludność nie rośnie (blokada trwała). Pełna diagnoza
  w sekcji K114; nie powtarzać jej tutaj.
- **Głód jest ślepą uliczką: ujemne saldo pszenicy zatrzymuje ludność na
  zawsze** — **nie planowane, kandydat nr 1 po K114**. Zmierzone 2026-08-08
  przy recenzjach tego przeglądu (`seed=73`): konsumpcja osady równa się jej
  ludności (`settlement.py:62`), Farm daje `wheat=3` (`building.py:22`), więc
  zapas spada 10 → 0 w 2–4 turach. **Próg leży wcześniej, niż widać:**
  `tick_settlements` (`world.py:133-145`) puszcza `tick_growth` **po**
  `tick_economy`, więc ludność rośnie tylko przy saldzie
  `wheat + production − consumption > 0` — zmierzona tura 3 ma zapas 5 i 4,
  saldo 0 i −2, i ludność już nie rośnie. Dalej `free` stoi na 0, a **żaden
  rozkaz dostępny w kliencie tego nie odwraca** — `muster` zbija konsumpcję
  8 → 3, ale przy produkcji 3 saldo wynosi 0 i zapas zostaje 0 (9 tur bez
  zmiany). To defekt rozgrywki, nie balans: „koniec wzrostu na zawsze" blokuje
  pętlę, natomiast **wartości** produkcji i konsumpcji pozostają odłożone jako
  strojenie. K114 tego **nie** naprawia — tylko nazywa stan graczowi.
  Kolejność wobec „wyboru osady" rozstrzygnie pomiar po K114.
- **Rozkazy osadowe bez wyboru osady** (`develop`/`recruit`/`muster` biorą
  *pierwszą* pasującą osadę, cel jest po cichu ignorowany) — **potwierdzone
  ponownie pomiarem 2026-08-08**: `recruit` z jawnym `target: "Player Outpost"`
  obsadza mimo to Player Keep, dopóki starczy tam wolnej ludności. Nadal
  **nie planowane**; blokada „po K112" wygasła (K112 domknięty), więc to
  kandydat **po K114** — nie razem z nim, żeby nie mieszać wyjaśnienia odmowy
  ze zmianą kontraktu rozkazu. Mapa ma już wybór regionu (K97, używany przez
  `move`). **Korekta wartości po recenzji 2026-08-08:** argument „gracz zobaczy
  pustą pulę i wskaże drugą osadę" jest słabszy, niż zakładano — w zmierzonym
  stanie trwałym **obie** osady mają `free` 0, więc wybór osady niczego tam nie
  odblokowuje. Wciąż ma wartość w turach 1–5 (pule są wtedy różne: Outpost ma
  2 wolnych, gdy Keep 0), ale przed nim stoi kandydat „głód".
- **`muster` zabiera cały garnizon osady** — obserwacja z przeglądu 2026-07-28,
  nadal **nie planowana**: po zbiórce osada zostaje pusta, więc każde wyjście
  w pole odsłania dom. K112 świadomie powiela tę regułę we wzmocnieniu
  (symetria z `muster`), żeby nie strojić dwóch rzeczy naraz. „Ile garnizonu
  wolno zabrać" podejmować dopiero, gdy pętla stoi — to strojenie, nie defekt.
- ~~**Po K108: presja ze strony AI** („czy AI kiedykolwiek naciera")~~ —
  **odpowiedziane pomiarem 2026-08-06**, bez osobnego plasterka: po G108.1c AI
  maszeruje do osad gracza i je zdobywa, więc naciera. Otwarte zostaje pytanie
  o *tempo* tej presji, a tego nie da się sensownie ocenić przed K109 —
  dziś gracz może wyprzedzić AI dowolną liczbą darmowych rozkazów.
- Pełne pole bitwy (teren pustych heksów, wymiary pola) — wymaga rozszerzenia
  `tbbbridge.snapshot.battle_state`; dopiero gdy sam widok bitwy (K85) stoi.
- Sterowanie pojedynczą jednostką w bitwie — po K85.
- ~~Szturm potrafi się nie rozstrzygnąć i wywala rozkaz~~ — **rozplanowane jako
  K89** (G89.1a kontrakt wyniku, G89.1b widoczny skutek, G89.2a reguła ruchu).
  Pełna diagnoza zostaje niżej, bo koder jej potrzebuje.
- **Szturm potrafi się nie rozstrzygnąć i wywala rozkaz — przyczyną jest ruch,
  nie obrażenia.** Odtwarzalne na `serve 73` (recruit ×2 → muster → march →
  assault): gracz dostaje `unknown battle result`. Zweryfikowane przez
  uruchomienie kodu 2026-07-28, nie z lektury: `auto_resolve` kończy 1000 rund z
  `result() is None`, bo z trzech atakujących dwaj są **ogłuszeni** (`hp=0`,
  `stunned=True`) i **zostają na planszy jako przeszkoda**, a jedyny czynny
  atakujący stoi na `Hex(0,2)`. Jego jedyny sąsiad skracający dystans do
  obrońcy na `Hex(2,0)` to `Hex(1,1)` — zajęty przez własnego ogłuszonego. Skoro
  `reachable()` pomija zajęte heksy, `take_unit_turn` co rundę zwraca `self`,
  obrońca sam nie naciera, a `result()` nie widzi czynnej strony po stronie
  atakującej (ogłuszeni się nie liczą). Dwie rzeczy do rozdzielenia na osobne
  plasterki, **żadna nie jest „obrażenia bazowe ≥ 1"**: (a) jednostka musi umieć
  ominąć sojusznika albo ogłuszony przestaje blokować pole; (b)
  `apply_settlement_battle_result` na nierozstrzygniętej bitwie rzuca
  `ValueError("unknown battle result")` zamiast potraktować remis/przerwanie jako
  legalny wynik — dlatego defekt dociera do gracza jako błąd rozkazu.
  **Uwaga na fałszywy trop:** polegli NIE blokują (przy śmierci znikają z
  `units`, tu `_fallen` jest puste), a podniesienie obrażeń bazowych do ≥ 1
  sprawdzono empirycznie — wynik identyczny, `result()` nadal `None`. Zerowe
  obrażenia ma rekrut z `settlement.recruit()`, bohater ma `equipment=1`.
  *(Ustalenie z recenzji przeglądu kierunku 2026-07-28, którą przerwał
  zatrzymany przebieg; zapisane ręcznie, żeby nie zginęło.)*

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
- Dług dokumentacji: `docs/PROJECT.md` ma 20 KB — zaplanuj podział pliku.
