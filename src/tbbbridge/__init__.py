"""Pakiet-most tbbbridge — serializacja stanu rdzenia gry do JSON.

Konsumuje wyłącznie publiczne API rdzenia `tbb`. Rdzeń nigdy nie importuje
tego pakietu; patrz docs/ARCHITECTURE.md (sekcja `tbbbridge`).
"""

from tbbbridge.snapshot import settlement_state

__all__ = ["settlement_state"]
