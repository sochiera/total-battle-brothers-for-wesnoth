# BACKLOG — Total Battle Brothers

> **Kolejka zadań.** Każde zadanie = jeden mały, testowalny przyrost (TDD).
> Statusy: `[ ]` do zrobienia, `[~]` w toku, `[x]` zrobione.
> Bierz zadania z góry. Nie łącz wielu przyrostów w jeden. Aktualizuj status i
> dopisuj nowe zadania, gdy wizja się doprecyzowuje. Detale mechaniki → `docs/DESIGN.md`.
> Ukończone milestony przeniesione do `BACKLOG-ARCHIVE.md` (kamienie 0–8 oraz
> A7.1*/A7.2*) — tu zostaje wyłącznie żywy tail w stronę grywalnego MVP.

## Legenda
Każde zadanie ma **kryteria akceptacji** (co musi przejść jako test). Rdzeń przed
prezentacją. Determinizm (seedowalny RNG) jest wymogiem przekrojowym.

---

## Kamienie 7–8 — UKOŃCZONE (headless pętla MVP + ekonomia/kalendarz w driverze)
> `python -m tbb` uruchamia pełną, deterministyczną partię end-to-end: żywa
> miesięczna ekonomia i wzrost osad, płynący kalendarz, wypisany zwycięzca/remis
> wraz z końcową datą (kod wyjścia 0). Wszystkie pozycje w `BACKLOG-ARCHIVE.md`.
> To domyka **minimalną** pętlę z DESIGN §6 pkt 1,3,4,5. Otwarty zostaje pkt 2:
> jednostki są rekrutowane z filarami 0 i nigdy się nie „trenują ani wyposażają"
> — to domyka Kamień milowy 9.

## Kamień milowy 9 — rozwój jednostek w turze — UKOŃCZONE
> Krzywa malejącego zysku (U3.2) wpięta w `Unit` i miesięczne przejście osady:
> garnizon obserwowalnie mocnieje (trening = czas; uzbrojenie = złoto + kuźnia)
> w realnej headless partii. Wszystkie pozycje w `BACKLOG-ARCHIVE.md`.

## Kamień milowy 10 — realne straty i koszty w pętli strategicznej
> Headless pętla MVP działa end-to-end, ale trzy placeholdery czynią warstwę
> strategiczną płytką: (a) garnizon osady **nigdy nie ponosi strat** — po obronie
> zostaje pełny, a po podboju obrońcy zostają garnizonem zdobywcy (BW.3c/BM.2
> świadomie odłożone); (b) rekrutacja jest **darmowa** poza 1 populacją, więc AI
> spamuje żołnierzy bez związku z ekonomią (§7 „koszt … dochodzi później");
> (c) AI **nigdy nie otwiera budynków**, więc ekonomia jest statyczna, a uzbrojenie
> garnizonu (wymaga kuźni) w realnej partii nie postępuje. Ten kamień domyka te
> trzy luki, spinając straty, koszt rekrutacji i rozwój ekonomii AI z pętlą.
> Strojenie wartości (balans) pozostaje poza kamieniem.
- [ ] **G10.1** Osada wchłania ocalałych obrońców po bitwie. *(task-022)*
  - AC: `Settlement.absorb_defenders(survivors)` — czyste przejście zastępujące
    garnizon ocalałymi (w kolejności), a polegli (różnica liczności) zmniejszają
    `population` i `occupied`; ocalali muszą być podzbiorem liczności garnizonu;
    pusta sekwencja czyści garnizon; niemutowalne, bez RNG.
- [ ] **G10.2** Straty garnizonu w `apply_settlement_battle_result`. *(task-023)*
  - AC: przy podanym `battle` garnizon `destination` jest odtwarzany z
    `battle.side_survivors(DEFENDER)` dla **każdego** wyniku; `ATTACKER_WIN` →
    zdobyta osada ma ocalałych obrońców pod nowym `owner_id`; `DEFENDER_WIN`/`DRAW`
    → osada traci poległych obrońców; `battle is None` zachowuje zgodność wsteczną;
    walidacja bez zmian; niemutowalne.
- [ ] **G10.3** Koszt złota rekrutacji. *(task-024)*
  - AC: `Settlement.recruit()` pobiera `RECRUIT_GOLD_COST` ze `storage`; brak złota
    → `ValueError` (blokada, jak przy braku populacji); AI `recruit_duchy_unit`
    pomija osady bez dość złota; niemutowalne, deterministyczne.
- [ ] **G10.4** Polityka AI: otwieranie budynków ekonomii/kuźni. *(task-025)*
  - AC: czyste `ai.develop_duchy_settlement(world, duchy)` otwiera pierwszy brakujący
    korzystny budynek (priorytet `Farm` → `Smith` → `Market`) w pierwszej wg
    kolejności regionów własnej osadzie z dość wolną populacją; brak kandydata =
    no-op; niemutowalne, bez RNG.
- [ ] **G10.5** Wpięcie rozwoju budynków w turę AI + integracja. *(task-026)*
  - AC: `take_duchy_turn` wywołuje `develop_duchy_settlement` przed rekrutacją;
    test drivera pokazuje, że w realnej partii AI otwiera `Farm` (ekonomia
    samowystarczalna) i `Smith` (uzbrojenie garnizonu postępuje); determinizm
    end-to-end; cały pakiet testów zielony.

## Później (poza MVP)
- [ ] Prezentacja/UI (pygame lub most do innego silnika) nad rdzeniem.
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] **Bramkowanie treningu budynkiem (§5 „odpowiednie budynki"):** katalog
      budynku treningowego i wymóg jego czynności w `tick_training` (dziś trening
      jest bezwarunkową funkcją czasu). Analogicznie polityka AI otwierania
      kuźni/budynków treningowych.
- [ ] Balans ekonomii, tempa rozwoju jednostek i krzywych progresji; strojenie AI.
- [ ] Pełna maszyna faz `StrategicTurn` w headless driverze (routing akcji AI przez
      fazy ruch/bitwy zamiast bezpośredniego `take_duchy_turn`). M8 reużywa tylko
      prymitywów `tick_settlements`/`end_turn`, bez wciągania phase-gatingu.
