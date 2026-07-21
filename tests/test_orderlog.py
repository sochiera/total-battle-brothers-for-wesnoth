"""Tests for the order-log presentation primitive (tbbui)."""

import html
from xml.etree import ElementTree as ET

from tbbui.orderlog import render_order_log


def test_render_order_log_root_is_div_with_data_order_log_and_data_count():
    """``render_order_log(entries)`` returns a parsable XML fragment whose root
    is ``<div data-order-log="">`` carrying ``data-count="<len(entries)>"``.
    """
    for entries in ((), ("a",), ("first", "second", "third")):
        xml = render_order_log(entries)
        root = ET.fromstring(xml)

        assert root.tag == "div"
        assert root.attrib.get("data-order-log") == ""
        assert root.attrib.get("data-count") == str(len(entries))


def test_render_order_log_one_child_per_entry_in_order_with_escaped_body():
    """One ``<div data-order-log-entry="">`` per entry in input order; body in
    the raw fragment is ``html.escape(entry, quote=True)``. Empty sequence →
    bare root ``<div data-order-log="" data-count="0"></div>`` with no children.
    """
    empty_xml = render_order_log(())
    empty_root = ET.fromstring(empty_xml)
    assert empty_root.tag == "div"
    assert empty_root.attrib == {"data-order-log": "", "data-count": "0"}
    assert list(empty_root) == []
    assert empty_xml == '<div data-order-log="" data-count="0"></div>'

    entries = ("march north", "assault Keep", "recruit")
    xml = render_order_log(entries)
    root = ET.fromstring(xml)
    children = list(root)
    assert len(children) == len(entries)
    for child, entry in zip(children, entries, strict=True):
        assert child.tag == "div"
        assert child.attrib.get("data-order-log-entry") == ""
        # Raw source body is escaped; ElementTree surfaces the human-readable form.
        escaped = html.escape(entry, quote=True)
        assert f'<div data-order-log-entry="">{escaped}</div>' in xml
        assert "".join(child.itertext()) == entry


def test_render_order_log_is_pure_deterministic_and_escapes_special_chars():
    """Pure and deterministic: does not mutate ``entries``; two calls with the
    same sequence yield the identical string; ``<``, ``&``, ``"`` in entry text
    are safely escaped via ``html.escape(..., quote=True)`` in the raw fragment.
    """
    entries = ['strike <Keep>', 'gold & iron', 'say "hold"']
    snapshot = list(entries)

    first = render_order_log(entries)
    second = render_order_log(entries)
    assert first == second
    assert list(entries) == snapshot

    expected_bodies = [html.escape(entry, quote=True) for entry in entries]
    assert expected_bodies == [
        "strike &lt;Keep&gt;",
        "gold &amp; iron",
        'say &quot;hold&quot;',
    ]
    for escaped in expected_bodies:
        assert f'<div data-order-log-entry="">{escaped}</div>' in first

    root = ET.fromstring(first)
    children = list(root)
    assert len(children) == 3
    for child, entry in zip(children, entries, strict=True):
        # After XML parse, text content is the original entry (entities decoded).
        assert "".join(child.itertext()) == entry
