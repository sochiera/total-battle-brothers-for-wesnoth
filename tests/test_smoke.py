"""Smoke test — potwierdza, że framework testów i pakiet rdzenia działają."""

import tbb


def test_package_imports_and_has_version():
    assert isinstance(tbb.__version__, str)
    assert tbb.__version__  # niepusta wersja


def test_headless_main_returns_zero():
    from tbb.__main__ import main

    assert main() == 0
