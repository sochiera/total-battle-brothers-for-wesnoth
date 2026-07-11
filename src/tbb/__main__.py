"""Headless entry point (placeholder).

Na teraz tylko wypisuje banner i kończy się kodem 0, żeby komenda `run`
działała od zera. Docelowo uruchomi headless przebieg pętli MVP (BACKLOG A7.2).
"""

from tbb import __version__


def main() -> int:
    print(f"Total Battle Brothers — rdzeń v{__version__} (headless placeholder)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
