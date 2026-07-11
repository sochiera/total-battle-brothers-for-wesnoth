# BACKLOG — Total Battle Brothers

> **Kolejka zadań.** Każde zadanie = jeden mały, testowalny przyrost (TDD).
> Statusy: `[ ]` do zrobienia, `[~]` w toku, `[x]` zrobione.
> Bierz zadania z góry. Nie łącz wielu przyrostów w jeden. Aktualizuj status i
> dopisuj nowe zadania, gdy wizja się doprecyzowuje. Detale mechaniki → `docs/DESIGN.md`.

## Legenda
Każde zadanie ma **kryteria akceptacji** (co musi przejść jako test). Rdzeń przed
prezentacją. Determinizm (seedowalny RNG) jest wymogiem przekrojowym.

---

## Kamień milowy 0 — szkielet (bootstrap)
- [x] **B0.1** Szkielet projektu + pytest + jeden trywialny zielony test.
  - AC: `bash scripts/test.sh` przechodzi; `import tbb` działa; `python -m tbb` kończy 0.

## Kamień milowy 1 — fundament rdzenia
- [x] **C1.1** Seedowalny RNG (`tbb/rng.py`).
  - AC: ten sam seed → ta sama sekwencja; `randint`, `chance(p)` deterministyczne;
    dwa RNG z tym samym seedem dają identyczne wyniki, z różnym — różne.
- [x] **C1.2** `Resources` (pszenica, złoto) — dodawanie, odejmowanie, walidacja.
  - AC: nie da się zejść poniżej zera bez jawnej zgody; arytmetyka pokryta testami.
- [x] **C1.3** Współrzędne heksów (`tbb/hex.py`, axial/cube).
  - AC: dystans heksowy, sąsiedzi, konwersje axial↔cube; testy na znanych przypadkach.

## Kamień milowy 2 — osada i ekonomia
- [x] **E2.1** `Settlement` z pulą populacji (wolna vs zajęta).
  - AC: rekrutacja/obsada zajmuje populację; brak wolnej populacji blokuje akcję.
- [x] **E2.2** Budynki: uruchomienie wymaga wolnej populacji; zamknięcie ją zwalnia.
  - AC: za mała populacja → nie można uruchomić kowala; zamknięcie oddaje 1 pop.
- [x] **E2.3** Produkcja surowców per tura (pszenica/złoto z budynków) + konsumpcja.
  - AC: bilans miesięczny liczony deterministycznie; testy na przykładowej osadzie.
- [x] **E2.4a** Wzrost populacji — urodzenia + sufit (`capacity`).
  - AC: najedzona osada (nadwyżka pszenicy) rośnie o 1/turę; sufit blokuje wzrost;
    głodująca nie rośnie; faza wzrostu osobna od `tick_economy` (DESIGN §10 kolejność).
- [x] **E2.4b** Wzrost populacji — imigranci (dopływ zależny od dobrobytu).
  - AC: dobrobyt (nadwyżka złota) przyciąga +1 imigranta/turę do puli wolnej;
    sufit respektowany; głodująca/bez złota nie przyciąga; determinizm; osobne
    przejście `tick_immigration()` w fazie wzrostu (po urodzeniach).

## Kamień milowy 3 — jednostki i progresja
- [x] **U3.1** `Unit` z trzema filarami (trening/uzbrojenie/doświadczenie).
  - AC: statystyki pochodne = funkcja filarów; niezależność filarów pokryta testem.
    Mapowanie liniowe (placeholder, DESIGN §5); krzywe malejącego zysku → U3.2.
- [x] **U3.2** Malejący zysk treningu i uzbrojenia (czas/surowce → poziom filaru).
  - AC: przyrost maleje z poziomem; parametry z DESIGN; monotoniczność w teście.
    Wzór `level(inv) = (isqrt(8·inv+1)−1)//2` (progi trójkątne), deterministyczny.
- [~] **U3.3** Rekrutacja jednostki z populacji osady.
  - AC: rekrutacja zdejmuje pop z puli; brak pop blokuje; jednostka trafia do osady.

## Kamień milowy 4 — bitwa heksowa
- [ ] **B4.1** Plansza heksowa + teren z modyfikatorami.
  - AC: pola mają typ terenu; modyfikatory (ruch/obrona/celność) odczytywalne.
- [ ] **B4.2** Rozstawienie jednostek i ruch po punktach ruchu z kosztem terenu.
  - AC: legalne ruchy respektują koszt i zasięg; nielegalne odrzucone.
- [ ] **B4.3** Walka wręcz: trafienie (celność+teren+morale) i obrażenia.
  - AC: rozstrzyganie deterministyczne przy ustalonym seedzie; morale zmienia celność.
- [ ] **B4.4** Atak dystansowy (model Wesnoth/BB).
  - AC: zasięg, brak kontrataku poza zasięgiem, trafienie wg wzoru.
- [ ] **B4.5** Śmierć permanentna oraz ogłuszenie + rana (czasowa/trwała).
  - AC: 0 HP → śmierć lub (wg reguły) ogłuszenie+rana; rana modyfikuje statystyki.
- [ ] **B4.6** Warunek końca bitwy i wynik (kto wygrał, straty, zdobyte doświadczenie).
  - AC: bitwa kończy się gdy jedna strona wybita/wycofana; wynik raportowany.

## Kamień milowy 5 — mapa strategiczna i tura
- [ ] **M5.1** `WorldMap` z regionami/osadami i pozycjami party.
  - AC: reprezentacja mapy + zapytania o sąsiedztwo/pozycje.
- [ ] **M5.2** Party (bohater + ≤12 jednostek) i ruch po mapie z punktami ruchu.
  - AC: limit 12; party rusza się tylko z bohaterem; garnizon zostaje w osadzie.
- [ ] **M5.3** Kontakt party↔osada/party wyzwala bitwę (przejście do warstwy B4).
  - AC: kontakt tworzy `HexBattle` z właściwymi składami.
- [ ] **M5.4** Faza tury miesięcznej (produkcja → wzrost → ruch → bitwy), 13 mies./rok.
  - AC: kolejność faz z DESIGN §10; kalendarz 13×4 tyg. liczony poprawnie.

## Kamień milowy 6 — księstwa, następstwo, warunki gry
- [ ] **D6.1** `Duchy`: bohater + dziedzic + osady + party + morale.
  - AC: struktura księstwa; 1 bohater na księstwo (inwariant).
- [ ] **D6.2** Śmierć bohatera → sukcesja dziedzica + kara morale.
  - AC: dziedzic przejmuje; morale osad/wojsk spada; brak dziedzica → patrz D6.3.
- [ ] **D6.3** Warunek przegranej/wygranej (brak osad ORAZ brak bohatera).
  - AC: gra sygnalizuje koniec dokładnie w tym warunku, nie wcześniej.

## Kamień milowy 7 — AI i grywalna pętla MVP
- [ ] **A7.1** Proste AI księstwa (rozwijaj osadę → zbierz party → atakuj).
  - AC: AI wykonuje sensowną turę deterministycznie przy ustalonym seedzie.
- [ ] **A7.2** Headless przebieg całej pętli MVP (setup → tury → bitwa → wynik).
  - AC: `run.sh` symuluje partię do rozstrzygnięcia i wypisuje wynik; test smoke pętli.

## Później (poza MVP)
- [ ] Prezentacja/UI (pygame lub most do innego silnika) nad rdzeniem.
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] Balans ekonomii i krzywych progresji; strojenie AI.
