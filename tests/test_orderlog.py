"""Tests for the order-log presentation primitive (tbbui)."""

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
