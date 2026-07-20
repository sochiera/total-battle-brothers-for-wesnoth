"""CLI snapshot entry point: python -m tbbui → HTML party page (V13.4b)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find_by_attr(root: ET.Element, attr: str) -> list[ET.Element]:
    return [el for el in root.iter() if el.get(attr) is not None]


def test_main_writes_parsable_html_snapshot_with_svg_and_data_result(tmp_path: Path):
    """main(argv) runs headless party and writes render_game_page HTML to path.

    Contract (task-073 / V13.4b): optional first argv is output path; exit 0;
    non-empty parsable HTML with embedded map <svg> and data-result; two runs
    with the fixed seed produce identical file contents.
    """
    from tbbui.__main__ import main

    out = tmp_path / "subdir" / "game.html"

    code = main([str(out)])
    assert code == 0
    assert out.is_file()
    html = out.read_text(encoding="utf-8")
    assert html.strip() != ""

    root = ET.fromstring(html)
    assert _local(root.tag) == "html"

    svgs = [el for el in root.iter() if _local(el.tag) == "svg"]
    assert len(svgs) >= 1, "snapshot must embed map <svg>"

    results = _find_by_attr(root, "data-result")
    assert len(results) == 1
    assert results[0].get("data-result") is not None
    assert results[0].get("data-result") != ""

    out2 = tmp_path / "subdir" / "game2.html"
    code2 = main([str(out2)])
    assert code2 == 0
    assert out2.read_text(encoding="utf-8") == html
