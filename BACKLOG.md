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

## Kamień milowy 9 — rozwój jednostek w turze (§6 pkt 2: „trenuj i wyposażaj")
> Krzywa malejącego zysku `progression.pillar_level`/`investment_for_level` (U3.2)
> jest zbudowana, ale **nigdzie nie wpięta** w rozgrywkę. Ten kamień spina ją z
> `Unit` i z miesięcznym przejściem osady, tak by garnizon obserwowalnie mocniał
> (trening = czas; uzbrojenie = złoto + czynna kuźnia), zanim AI wystawi party.
> `training`/`equipment` pozostają autorytatywnymi poziomami (zgodność wsteczna),
> a reszta nakładu żyje w nowych polach `*_progress`. Bramkowanie treningu budynkiem
> i strojenie tempa/kosztów są świadomie poza tym kamieniem (balans).
- [ ] **U9.1** Trening jednostki jako czyste przejście z malejącym zyskiem. *(task-017)*
  - AC: `Unit.train(months)` + pole `training_progress`; poziom rośnie po krzywej
    trójkątnej U3.2; `months==0` no-op, `<0` błąd; wejście niemutowane; bez RNG.
- [ ] **U9.2** Uzbrojenie jednostki jako czyste przejście z malejącym zyskiem. *(task-018)*
  - AC: `Unit.equip(investment)` + pole `equipment_progress`; symetryczne do U9.1;
    `damage`/`defense` odzwierciedlają nowy `equipment`; wejście niemutowane.
- [ ] **U9.3** Miesięczny trening garnizonu w osadzie. *(task-019)*
  - AC: `Settlement.tick_training()` daje każdemu żołnierzowi
    `TRAINING_MONTHS_PER_TURN` miesięcy; pusty garnizon no-op; reszta osady bez
    zmian; niemutowalne; bez RNG.
- [ ] **U9.4** Miesięczne uzbrajanie garnizonu przez kuźnię. *(task-020)*
  - AC: `Settlement.tick_equipment()` — czynny `Smith` + `gold≥EQUIP_GOLD_COST`
    uzbraja jednego żołnierza (najniższy `equipment`, remis → najwcześniejszy)
    i pobiera złoto; brak kuźni/złota/garnizonu = no-op; deterministyczne.
- [ ] **U9.5** Rozwój garnizonu w `tick_settlements` i driverze. *(task-021)*
  - AC: łańcuch `economy→growth→immigration→training→equipment`; headless partia
    obserwowalnie rozwija jednostki i nadal kończy się rozstrzygnięciem;
    determinizm end-to-end; cały pakiet testów zielony.

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
