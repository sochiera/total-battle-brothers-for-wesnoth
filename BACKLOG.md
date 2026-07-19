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
- [x] **G10.1** Osada wchłania ocalałych obrońców po bitwie. *(task-022)* →
      `BACKLOG-ARCHIVE.md`
- [x] **G10.2a** Straty garnizonu obrońcy przy `DEFENDER_WIN`/`DRAW`. *(task-027)*
      → `BACKLOG-ARCHIVE.md`
- [x] **G10.2b** Garnizon zdobytej osady przy `ATTACKER_WIN`. *(task-028)*
      → `BACKLOG-ARCHIVE.md`
- [x] **G10.3** Koszt złota rekrutacji. *(task-029)* → `BACKLOG-ARCHIVE.md`
- [x] **G10.4** Polityka AI: otwieranie budynków ekonomii/kuźni. *(task-030)*
      → `BACKLOG-ARCHIVE.md`
- [x] **G10.5a** `take_duchy_turn`: rozwój → rekrutacja → wojsko. *(task-032)*
  - AC: `take_duchy_turn` wywołuje `develop_duchy_settlement` przed
    `recruit_duchy_unit`; test AI: po turze osada AI ma `Farm` i +1 rekruta; brak
    możliwości rozwoju nie przerywa rekrutacji/wojska; DESIGN §3.1 ROZSTRZYGNIĘTE
    G10.5; niemutowalne, deterministyczne.
  - Uwaga: rozbicie G10.5 po porażce (`.forge/failures.md`).
- [x] **G10.5b** Progresja priorytetu `Farm`→`Smith` w kolejnych turach. *(task-033)*
  - AC: na mapie bez wrogiej osady (wojsko = no-op) dwa kolejne `take_duchy_turn`
    otwierają najpierw `Farm`, potem `Smith`; rekrutacja działa; deterministyczne,
    niemutowalne.
- [x] **G10.5c** Integracja rozwoju AI w realnej partii headless. *(task-034)*
  - AC: `run_headless_game` z `create_headless_game` osiąga stan, gdzie osada AI
    ma otwarty `Farm`; determinizm end-to-end (ten sam seed → ten sam wynik);
    stany wejściowe nie mutowane. (Twarda asercja `Smith` w pełnej partii świadomie
    pominięta — progresję dowodzi G10.5b.)
- [ ] **R10.1** Refaktor: `WorldMap.with_settlement`, dedup rekonstrukcji mapy.
      *(task-035)*
  - AC: `WorldMap.with_settlement(region, settlement)` czyste przejście; `ai.py`
    (`develop`/`recruit`) i wewnętrzne miejsca `world.py` reużywają go; zero zmian
    zachowania, cały pakiet zielony.

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
