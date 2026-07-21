"""Tests for the order-log presentation primitive (tbbui)."""

import html
from xml.etree import ElementTree as ET

from tbb.turn import Calendar
from tbbui.orderlog import format_log_entry, render_order_log


def test_format_log_entry_prefixes_notice_with_calendar_date():
    """``format_log_entry(notice, calendar)`` returns exactly
    ``f"Rok {calendar.year}, miesiąc {calendar.month} — {notice}"``.
    """
    assert format_log_entry("Marsz: wykonano", Calendar()) == (
        "Rok 1, miesiąc 1 — Marsz: wykonano"
    )
    assert format_log_entry("rekrutacja", Calendar(year=3, month=7)) == (
        "Rok 3, miesiąc 7 — rekrutacja"
    )
    assert format_log_entry("", Calendar(year=2, month=13)) == (
        "Rok 2, miesiąc 13 — "
    )


def test_format_log_entry_is_pure_deterministic_and_does_not_escape():
    """Helper is pure and deterministic: does not escape special characters
    (escaping is ``render_order_log``'s job), does not mutate ``calendar`` or
    ``notice``, and yields the same string for the same arguments.
    """
    notice = 'szturm <Keep> & "hold"'
    calendar = Calendar(year=4, month=2)
    year_before, month_before = calendar.year, calendar.month
    notice_before = notice

    first = format_log_entry(notice, calendar)
    second = format_log_entry(notice, calendar)

    assert first == second
    assert first == 'Rok 4, miesiąc 2 — szturm <Keep> & "hold"'
    assert "<" in first and "&" in first and '"' in first
    assert "&lt;" not in first and "&amp;" not in first and "&quot;" not in first
    assert calendar.year == year_before and calendar.month == month_before
    assert notice == notice_before


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


def test_render_order_log_first_child_is_visible_header_h2():
    """Root's first child is exactly one ``<h2 data-order-log-header="">``
    with body ``Dziennik rozkazów``, before any ``data-order-log-entry``;
    present for empty sequence as well (K44.2a).
    """
    for entries in ((), ("solo",), ("first", "second")):
        xml = render_order_log(entries)
        root = ET.fromstring(xml)
        children = list(root)

        headers = [
            c
            for c in children
            if c.tag == "h2" and c.attrib.get("data-order-log-header") == ""
        ]
        assert len(headers) == 1
        assert children[0] is headers[0]
        assert "".join(headers[0].itertext()) == "Dziennik rozkazów"
        assert (
            '<h2 data-order-log-header="">Dziennik rozkazów</h2>' in xml
        )
        # Header precedes every entry child in document order.
        entry_children = [
            c
            for c in children
            if c.attrib.get("data-order-log-entry") == ""
        ]
        if entry_children:
            assert children.index(headers[0]) < children.index(entry_children[0])


def test_render_order_log_one_child_per_entry_in_order_with_escaped_body():
    """One ``<div data-order-log-entry="">`` per entry in reverse input order
    (K45.1a newest-first); body in the raw fragment is
    ``html.escape(entry, quote=True)``. Empty sequence → ``data-count="0"`` and
    no entry children (header still present, K44.2a).
    """
    empty_xml = render_order_log(())
    empty_root = ET.fromstring(empty_xml)
    assert empty_root.tag == "div"
    assert empty_root.attrib == {"data-order-log": "", "data-count": "0"}
    empty_entries = [
        c
        for c in empty_root
        if c.attrib.get("data-order-log-entry") == ""
    ]
    assert empty_entries == []

    entries = ("march north", "assault Keep", "recruit")
    xml = render_order_log(entries)
    root = ET.fromstring(xml)
    children = [
        c for c in root if c.attrib.get("data-order-log-entry") == ""
    ]
    expected_order = tuple(reversed(entries))
    assert len(children) == len(entries)
    for index, (child, entry) in enumerate(
        zip(children, expected_order, strict=True)
    ):
        assert child.tag == "div"
        assert child.attrib.get("data-order-log-entry") == ""
        # Raw source body is escaped; ElementTree surfaces the human-readable form.
        # Newest (index 0) carries K45.2a badge before the escaped body.
        escaped = html.escape(entry, quote=True)
        if index == 0:
            assert (
                f'<div data-order-log-entry="" data-order-log-latest="">'
                f'<span data-order-log-latest-badge="">najnowszy</span>'
                f"{escaped}</div>"
            ) in xml
            assert "".join(child.itertext()) == f"najnowszy{entry}"
        else:
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
    # Escaped bodies appear in the raw fragment (newest has K45.2a badge wrap).
    for escaped in expected_bodies:
        assert escaped in first

    root = ET.fromstring(first)
    children = [
        c for c in root if c.attrib.get("data-order-log-entry") == ""
    ]
    assert len(children) == 3
    for index, (child, entry) in enumerate(
        zip(children, reversed(entries), strict=True)
    ):
        # After XML parse, text content is the original entry (entities decoded).
        # Display order is newest-first (K45.1a); newest also has K45.2a badge.
        if index == 0:
            assert "".join(child.itertext()) == f"najnowszy{entry}"
        else:
            assert "".join(child.itertext()) == entry


def test_render_order_log_empty_embeds_empty_state_paragraph_after_header():
    """K44.2b: empty ``entries`` → after the K44.2a header exactly one
    ``<p data-order-log-empty="">Brak rozkazów w tej kampanii</p>`` and zero
    ``data-order-log-entry`` children; ``data-count="0"``.
    """
    xml = render_order_log(())
    root = ET.fromstring(xml)
    children = list(root)

    assert root.attrib.get("data-count") == "0"

    headers = [
        c
        for c in children
        if c.tag == "h2" and c.attrib.get("data-order-log-header") == ""
    ]
    assert len(headers) == 1
    assert children[0] is headers[0]

    empty_msgs = [
        c
        for c in children
        if c.tag == "p" and c.attrib.get("data-order-log-empty") == ""
    ]
    assert len(empty_msgs) == 1
    assert children[1] is empty_msgs[0]
    assert "".join(empty_msgs[0].itertext()) == "Brak rozkazów w tej kampanii"
    assert (
        '<p data-order-log-empty="">Brak rozkazów w tej kampanii</p>' in xml
    )

    entry_children = [
        c for c in children if c.attrib.get("data-order-log-entry") == ""
    ]
    assert entry_children == []
    assert len(children) == 2


def test_render_order_log_nonempty_has_no_empty_state_and_renders_entries():
    """K44.2b: non-empty ``entries`` → root has no ``data-order-log-empty``;
    still K44.2a shape: header first, ``len(entries)`` entry children,
    ``data-count`` equals ``len(entries)``.
    """
    entries = ("Marsz: wykonano", "Rekrutacja: ok")
    xml = render_order_log(entries)
    root = ET.fromstring(xml)
    children = list(root)

    assert root.attrib.get("data-count") == str(len(entries))
    assert root.find(".//*[@data-order-log-empty]") is None
    assert 'data-order-log-empty' not in xml

    headers = [
        c
        for c in children
        if c.tag == "h2" and c.attrib.get("data-order-log-header") == ""
    ]
    assert len(headers) == 1
    assert children[0] is headers[0]
    assert "".join(headers[0].itertext()) == "Dziennik rozkazów"

    entry_children = [
        c for c in children if c.attrib.get("data-order-log-entry") == ""
    ]
    assert len(entry_children) == len(entries)
    for index, (child, entry) in enumerate(
        zip(entry_children, reversed(entries), strict=True)
    ):
        # Display order is newest-first (K45.1a); newest has K45.2a badge text.
        visible = "".join(child.itertext())
        if index == 0:
            assert visible == f"najnowszy{entry}"
        else:
            assert visible == entry


def test_render_order_log_entries_newest_first_with_escaped_bodies():
    """K45.1a: non-empty ``entries`` → ``data-order-log-entry`` children appear
    in reverse input order (first child = last entry = newest, last child =
    ``entries[0]``); each body is still ``html.escape(entry, quote=True)``.
    """
    entries = ("oldest", 'mid <Keep> & "x"', "newest")
    xml = render_order_log(entries)
    root = ET.fromstring(xml)
    entry_children = [
        c for c in root if c.attrib.get("data-order-log-entry") == ""
    ]

    expected_order = tuple(reversed(entries))
    assert len(entry_children) == len(entries)
    assert "".join(entry_children[0].itertext()) == f"najnowszy{entries[-1]}"
    assert "".join(entry_children[-1].itertext()) == entries[0]
    for index, (child, entry) in enumerate(
        zip(entry_children, expected_order, strict=True)
    ):
        assert child.tag == "div"
        assert child.attrib.get("data-order-log-entry") == ""
        escaped = html.escape(entry, quote=True)
        if index == 0:
            assert "".join(child.itertext()) == f"najnowszy{entry}"
            assert (
                f'<div data-order-log-entry="" data-order-log-latest="">'
                f'<span data-order-log-latest-badge="">najnowszy</span>'
                f"{escaped}</div>"
            ) in xml
        else:
            assert "".join(child.itertext()) == entry
            assert f'<div data-order-log-entry="">{escaped}</div>' in xml


def test_render_order_log_marks_newest_entry_with_latest_attr_and_badge():
    """K45.2a: non-empty ``entries`` → exactly the first (newest)
    ``data-order-log-entry`` child carries ``data-order-log-latest=""`` and its
    body starts with ``<span data-order-log-latest-badge="">najnowszy</span>``
    before ``html.escape(entry, quote=True)``; other entry children have neither
    ``data-order-log-latest`` nor ``data-order-log-latest-badge``.
    """
    entries = ("oldest", 'mid <Keep> & "x"', "newest")
    xml = render_order_log(entries)
    root = ET.fromstring(xml)
    entry_children = [
        c for c in root if c.attrib.get("data-order-log-entry") == ""
    ]
    assert len(entry_children) == len(entries)

    newest = entry_children[0]
    assert newest.attrib.get("data-order-log-entry") == ""
    assert newest.attrib.get("data-order-log-latest") == ""
    badge = list(newest)
    assert len(badge) == 1
    assert badge[0].tag == "span"
    assert badge[0].attrib.get("data-order-log-latest-badge") == ""
    assert "".join(badge[0].itertext()) == "najnowszy"
    # Badge is a literal (not taken from entry text); escaped body follows.
    newest_escaped = html.escape(entries[-1], quote=True)
    assert (
        f'<div data-order-log-entry="" data-order-log-latest="">'
        f'<span data-order-log-latest-badge="">najnowszy</span>'
        f"{newest_escaped}</div>"
    ) in xml
    # Visible text is badge + entry (XML parse joins them).
    assert "".join(newest.itertext()) == f"najnowszy{entries[-1]}"

    for older in entry_children[1:]:
        assert "data-order-log-latest" not in older.attrib
        assert older.find(".//*[@data-order-log-latest-badge]") is None
        assert older.find("span[@data-order-log-latest-badge]") is None
    assert xml.count("data-order-log-latest=") == 1
    assert xml.count("data-order-log-latest-badge") == 1
    # Older entries keep plain markup (no badge).
    for entry in entries[:-1]:
        escaped = html.escape(entry, quote=True)
        assert f'<div data-order-log-entry="">{escaped}</div>' in xml


def test_render_order_log_empty_has_no_latest_marker_or_badge():
    """K45.2a: empty ``entries`` → root has neither ``data-order-log-latest``
    nor ``data-order-log-latest-badge``; ``data-count``, header and empty-state
    paragraph are unchanged (same as K44.2a/K44.2b).
    """
    xml = render_order_log(())
    root = ET.fromstring(xml)
    children = list(root)

    assert "data-order-log-latest" not in xml
    assert "data-order-log-latest-badge" not in xml
    assert root.find(".//*[@data-order-log-latest]") is None
    assert root.find(".//*[@data-order-log-latest-badge]") is None

    assert root.attrib == {"data-order-log": "", "data-count": "0"}
    assert len(children) == 2
    assert children[0].tag == "h2"
    assert children[0].attrib.get("data-order-log-header") == ""
    assert "".join(children[0].itertext()) == "Dziennik rozkazów"
    assert children[1].tag == "p"
    assert children[1].attrib.get("data-order-log-empty") == ""
    assert "".join(children[1].itertext()) == "Brak rozkazów w tej kampanii"
    assert (
        '<h2 data-order-log-header="">Dziennik rozkazów</h2>'
        '<p data-order-log-empty="">Brak rozkazów w tej kampanii</p>'
    ) in xml
