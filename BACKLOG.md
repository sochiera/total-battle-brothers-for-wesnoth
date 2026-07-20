# BACKLOG — Total Battle Brothers

> **Kolejka zadań.** Każde zadanie = jeden mały, testowalny przyrost (TDD).
> Statusy: `[ ]` do zrobienia, `[~]` w toku, `[x]` zrobione.
> Bierz zadania z góry. Nie łącz wielu przyrostów w jeden. Aktualizuj status i
> dopisuj nowe zadania, gdy wizja się doprecyzowuje. Detale mechaniki → `docs/DESIGN.md`.
> Ukończone milestony przeniesione do `BACKLOG-ARCHIVE.md` (kamienie 0–10 oraz
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

## Kamień milowy 10 — realne straty i koszty w pętli strategicznej — UKOŃCZONE
> Garnizon ponosi straty po bitwie (G10.1–G10.2), rekrutacja kosztuje złoto
> (G10.3), AI otwiera budynki i rozwija ekonomię w pełnej polityce tury
> (G10.4–G10.5), a rekonstrukcja mapy po podmianie osady jest zdeduplikowana
> w `WorldMap.with_settlement` (R10.1). Wszystkie pozycje (task-022…035)
> w `BACKLOG-ARCHIVE.md`. Strojenie wartości pozostaje balansem.

## Kamień milowy 11 — regeneracja i ciągłość władzy
> Trzy luki czynią długą partię zdegenerowaną: (a) **rany czasowe nigdy nie
> mijają** (B4.5a odkłada upływ czasu ran) — kary `Bruise` są de facto trwałe;
> (b) **ogłuszenie wychodzi z bitwy na mapę** — ocalały ze `stunned=True` nigdy
> więcej nie zaatakuje ani się nie ruszy w żadnej kolejnej bitwie; (c) księstwo
> **bez bohatera i dziedzica jest wiecznie bierne**, mimo że warunek przegranej
> (D6.3a) zakłada możliwość wystawienia nowego bohatera z osady. Ten kamień
> domyka leczenie, zdjęcie ogłuszenia przy powrocie na mapę i odrodzenie
> bohatera w pętli headless. Balans kosztów/czasów pozostaje poza kamieniem.
- [ ] **W11.1** Leczenie ran czasowych: `Unit.tick_wounds(months=1)`. *(task-036)*
  - AC: rana czasowa traci `months` miesięcy i znika przy `<= 0`; trwałe bez
    zmian; kolejność ran i reszta jednostki zachowane; `0` no-op, ujemne błąd;
    czyste, bez RNG; DESIGN B4.5a ROZSTRZYGNIĘTE (W11.1).
- [ ] **W11.2** Ogłuszenie nie przenosi się na warstwę strategiczną. *(task-037)*
  - AC: `Party.reconstruct` i `Settlement.absorb_defenders` zdejmują
    `stunned` (rany/XP zachowane); po `resolve_*_battle` nikt na mapie nie jest
    ogłuszony; walidacje bez zmian; DESIGN ROZSTRZYGNIĘTE (W11.2).
- [ ] **W11.3** Miesięczne leczenie garnizonu w łańcuchu osady. *(task-038)*
  - AC: `Settlement.tick_healing()` = `tick_wounds(1)` dla garnizonu;
    `tick_settlements` kończy łańcuch `…→training→equipment→healing`; `Bruise`
    znika po 2 turach mapy; driver dziedziczy bez zmian; DESIGN/ARCHITECTURE.
- [ ] **D11.4a** Wystawienie nowego bohatera z osady. *(task-039)*
  - AC: `Settlement.raise_hero() -> (Settlement, Unit)`: świeży `Unit`, −1
    wolnej populacji, −`HERO_GOLD_COST` (placeholder `2`) złota; niedobór →
    `ValueError`; czyste, bez RNG; DESIGN §7 ROZSTRZYGNIĘTE (D11.4a).
- [ ] **D11.4b** Bezhetmańskie księstwo wystawia bohatera w turze. *(task-040)*
  - AC: `ai.raise_duchy_hero(world, duchy) -> (WorldMap, Duchy)` — pierwsza
    własna osada stać na koszt, no-op gdy `has_hero`/brak kandydata; driver
    wpina przed akcją księstwa (`_replace_duchy` + sync); test: po stracie
    bohatera bez dziedzica księstwo z osadą odzyskuje `has_hero`; determinizm.

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
