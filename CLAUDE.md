# Notatka dla agentów

`.forge/` to runtime orkiestratora Forge. Nie przeglądaj go w
poszukiwaniu ogólnego kontekstu: plik zadania i kapsułę dostajesz w promptcie.
Twój prywatny notatnik też jest w kapsule — nie czytaj go z dysku i nie
zapisuj sam; wpisy oddajesz polem `notebook` swojej decyzji, a plikiem
zarządza Forge.

Wyjątkiem jest `.forge/verdict.py`: tym skryptem zatwierdzasz werdykt
swojej tury i to jedyny plik runtime, który masz uruchamiać. Sprawdza kontrakt
od razu, więc błąd poprawisz w tej samej turze zamiast tracić całą pracę.

Zwłaszcza `.forge/tasks/archive/` zawiera zamknięte zadania; czytanie
tego archiwum zapycha kontekst i nic nie wnosi. To wyjaśnienie, nie zakaz.
