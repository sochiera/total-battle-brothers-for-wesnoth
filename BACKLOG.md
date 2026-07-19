# BACKLOG — Total Battle Brothers

> **Kolejka zadań.** Każde zadanie = jeden mały, testowalny przyrost (TDD).
> Statusy: `[ ]` do zrobienia, `[~]` w toku, `[x]` zrobione.
> Bierz zadania z góry. Nie łącz wielu przyrostów w jeden. Aktualizuj status i
> dopisuj nowe zadania, gdy wizja się doprecyzowuje. Detale mechaniki → `docs/DESIGN.md`.
> Ukończone milestony przeniesione do `BACKLOG-ARCHIVE.md` (kamienie 0–6.8 oraz
> A7.1*/A7.2a) — tu zostaje wyłącznie żywy tail w stronę grywalnego MVP.

## Legenda
Każde zadanie ma **kryteria akceptacji** (co musi przejść jako test). Rdzeń przed
prezentacją. Determinizm (seedowalny RNG) jest wymogiem przekrojowym.

---

## Kamień milowy 7 — grywalna pętla MVP (headless przebieg A7.2b) — UKOŃCZONY
> Rdzeń, AI księstwa, deterministyczny setup (`A7.2a`) i cały headless driver
> (`A7.2b1`–`A7.2b4`) są gotowe: `python -m tbb` uruchamia pełną, deterministyczną
> partię end-to-end i wypisuje zwycięzcę albo remis (kod wyjścia 0). Wszystkie
> pozycje przeniesione do `BACKLOG-ARCHIVE.md`. To domknęło **minimalną** pętlę
> z DESIGN §6, ale headless partia nadal toczy się z **zamrożonymi osadami** —
> driver nie uruchamia miesięcznej ekonomii ani nie przesuwa kalendarza. To
> domyka Kamień milowy 8.

## Kamień milowy 8 — pełna tura strategiczna w driverze (ekonomia + kalendarz)
> Cała warstwa ekonomii/wzrostu (`WorldMap.tick_settlements`) i kalendarza
> (`turn.end_turn`) istnieje i jest przetestowana, ale headless driver jej **nie
> używa** — woła `take_duchy_turn` na gołej mapie. Skutek: podczas realnej partii
> osady nie produkują surowców, nie rosną i nie przyciągają imigrantów, a czas nie
> płynie. Ten kamień spina istniejące prymitywy z pętlą tury, w kolejności faz
> DESIGN §10 (produkcja → wzrost → ruch → bitwy), **bez** wciągania pełnej maszyny
> faz `StrategicTurn` (routing AI przez fazy zostaje po MVP — patrz „Później").
- [ ] **M8.1** Miesięczna ekonomia w pętli tury headless. *(task-014)*
  - AC: driver wykonuje `world.tick_settlements()` raz na początku każdej tury,
    przed przebiegiem księstw, i synchronizuje `GameState`; osada obserwowalnie
    produkuje/rośnie w trakcie headless partii; pełna pętla nadal kończy się
    zwycięzcą przed bezpiecznikiem; determinizm (ten sam seed → ten sam wynik); czyste.
- [ ] **M8.2** Kalendarz przesuwa się o miesiąc na ukończoną turę. *(task-015)*
  - AC: `run_headless_game` przyjmuje `calendar: Calendar = Calendar()` i zwraca
    trójkę `(WorldMap, GameState, Calendar)`; kalendarz przesuwa się dokładnie
    o jeden miesiąc na każdą ukończoną turę przez `turn.end_turn`; ten sam seed →
    ten sam kalendarz końcowy; wejścia niemutowane.
- [ ] **M8.3** CLI raportuje datę zakończenia partii. *(task-016)*
  - AC: `main()` wypisuje końcowy rok/miesiąc kalendarza obok wyniku (zwycięzca
    albo remis); smoke sprawdza obecność daty w wyjściu i kod wyjścia 0; cała
    logika w rdzeniu, `__main__.py` tylko I/O.

## Później (poza MVP)
- [ ] Prezentacja/UI (pygame lub most do innego silnika) nad rdzeniem.
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] **Rozwój jednostek w turze (§6 „trenuj i wyposażaj"):** model nakładu
      miesiąc/surowiec na `Unit` (śledzenie skumulowanej inwestycji → poziom filaru
      przez `progression.level`, zgodnie z U3.2) oraz przejście treningu/uzbrojenia
      w polityce AI. Świadomie odłożone: wymaga zmiany modelu `Unit` (dziś filary są
      wpisywane wprost), więc to osobny mini-kamień po M8.
- [ ] Balans ekonomii i krzywych progresji; strojenie AI.
- [ ] Pełna maszyna faz `StrategicTurn` w headless driverze (routing akcji AI przez
      fazy ruch/bitwy zamiast bezpośredniego `take_duchy_turn`). M8 reużywa tylko
      prymitywów `tick_settlements`/`end_turn`, bez wciągania phase-gatingu.
