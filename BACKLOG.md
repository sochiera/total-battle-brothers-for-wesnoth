# BACKLOG — Total Battle Brothers

## US-001 — Gracz widzi bitwę przed jej rozstrzygnięciem  [do weryfikacji]

Jako gracz chcę po rozpoczęciu szturmu lub starcia zobaczyć rozmieszczenie
walczących na planszy, żeby bitwa nie sprowadzała się do samego wyniku.

- Dostarczone w migracji K119: plansza bitwy jest widoczna przed wynikiem.
- Sprawdzenie: uruchom grę, doprowadź do szturmu lub starcia i potwierdź, że przed wynikiem pojawia się plansza z rozmieszczeniem jednostek.
- Poza zakresem: wybór celu, ręczny ruch jednostek, zmiany reguł walki i zmiany zachowania AI.

## US-002 — Gracz przechodzi jedną rundę bitwy  [gotowe]

Jako gracz chcę przejść następną rundę trwającej bitwy, żeby obserwować jej
przebieg krok po kroku.

- Dostarczone w migracji K119: gracz może przejść następną rundę bitwy.
- Sprawdzenie: na widoku trwającej bitwy wybierz następną rundę i potwierdź widoczną zmianę pozycji, PŻ lub ogłuszenia jednostek.
- Poza zakresem: wybór celu, ręczne wskazywanie ruchu, nowe obrażenia i nowe zasady tur jednostek.

## US-003 — Gracz może od razu dokończyć trwającą bitwę  [gotowe]

Jako gracz chcę zlecić automatyczne rozegranie pozostałych rund, żeby nie
musieć krokować walki, której dalszy przebieg chcę tylko poznać.

- Dostarczone w migracji K119: automatyczne dokończenie zachowuje dotychczasowy skutek bitwy.
- Sprawdzenie: rozpocznij bitwę, wybierz rozstrzygnięcie od razu i potwierdź, że gra pokazuje końcowy baner oraz skutki bitwy w świecie.
- Poza zakresem: zmiana wyniku względem dotychczasowego automatycznego rozstrzygnięcia, balans walki i tempo AI.

## US-004 — Gracz dostaje jasną blokadę działań strategicznych podczas bitwy  [gotowe]

Jako gracz chcę wiedzieć, że najpierw muszę zakończyć trwającą bitwę, żeby nie
próbować bezskutecznie wydawać rozkazów na mapie ani przesuwać miesiąca.

- Dostarczone w migracji K119: bitwa w toku blokuje działania strategiczne i niesie powód.
- Sprawdzenie: podczas trwającej bitwy spróbuj wydać rozkaz strategiczny i przejść do następnej tury; potwierdź brak zmiany świata i komunikat o bitwie w toku.
- Poza zakresem: nowe rozkazy strategiczne, zmiana kosztów akcji i równoległe rozgrywanie mapy oraz bitwy.

## US-005 — Gracz wznawia zapisaną bitwę w tym samym stanie  [gotowe]

Jako gracz chcę zapisać grę podczas bitwy i po wczytaniu kontynuować ją od
tego samego układu, żeby zapis partii działał także w trakcie walki.

- Dostarczone w migracji K119: zapis i wczytanie zachowują stan bitwy w toku.
- Sprawdzenie: rozpocznij bitwę, przejdź rundę, zapisz i wczytaj grę, a następnie potwierdź ten sam układ jednostek, PŻ i możliwość przejścia kolejnej rundy.
- Poza zakresem: wiele slotów zapisu, historia powtórek i zmiana istniejącego interfejsu zapisu poza obsługą bitwy w toku.
- Dług dokumentacji: `docs/ARCHITECTURE.md` ma 142 KB — zaplanuj podział pliku.
- Dług dokumentacji: `docs/DESIGN.md` ma 28 KB — zaplanuj podział pliku.
- Dług dokumentacji: `docs/DECISIONS.md` ma 74 KB — zaplanuj podział pliku.
