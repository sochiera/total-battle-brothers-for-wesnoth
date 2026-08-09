"""Stdlib PNG helpers for Godot map/asset alpha checks (no Pillow).

Decodes non-interlaced 8-bit RGBA PNGs as used by Kenney hex tiles and
samples hex-floor rim alphas for owner-ground occlusion contracts.

Also hosts shared CREDITS.md attribution checks used by asset/icon gates.
"""

from __future__ import annotations

import re
import struct
import zlib
from pathlib import Path

# License tokens accepted next to an attributed asset row in CREDITS.md.
LICENSE_RE = re.compile(r"\bCC0\b|\bCC-BY\b|\bCC BY\b", re.IGNORECASE)

# Default: page URL, pack-relative path, or an explicit project-original
# source/path. Original assets use prose plus game/assets/… rather than a
# third-party pack path.
_DEFAULT_SOURCE_RE = re.compile(
    r"https?://\S+|PNG/|original artwork\b|game/assets/",
    re.IGNORECASE,
)


def assert_asset_credited(
    credits_path: Path,
    asset_name: str,
    *,
    source_re: re.Pattern[str] | None = None,
    author: str | None = None,
) -> None:
    """Assert CREDITS.md attributes *asset_name* with license + source nearby.

    Looks up the first line containing the file name, then requires a CC0/CC-BY
    token and a source marker within a ±3 line window (row or adjacent prose).
    When supplied, ``author`` must also appear in that attribution window.
    """
    credits = credits_path.read_text(encoding="utf-8")
    credit_lines = credits.splitlines()
    credit_idx = next(
        (i for i, line in enumerate(credit_lines) if asset_name in line),
        None,
    )
    assert credit_idx is not None, (
        f"CREDITS.md must attribute {asset_name} with source/author/license"
    )
    credit_window = "\n".join(
        credit_lines[max(0, credit_idx - 3) : credit_idx + 4]
    )
    assert LICENSE_RE.search(credit_window), (
        f"CREDITS.md must state CC0 or CC-BY next to {asset_name}"
    )
    pattern = source_re if source_re is not None else _DEFAULT_SOURCE_RE
    assert pattern.search(credit_window), (
        f"CREDITS.md must give a source page or pack-relative path for {asset_name}"
    )
    if author is not None:
        assert re.search(rf"\b{re.escape(author)}\b", credit_window), (
            f"CREDITS.md must name author {author!r} for {asset_name}"
        )


def png_rgba8(path: Path) -> tuple[int, int, bytes]:
    """Decode a non-interlaced 8-bit RGB/RGBA PNG as RGBA via stdlib."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"not a PNG: {path}"
    pos = 8
    width = height = None
    color_type = None
    bit_depth = None
    idat = bytearray()
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _comp, _filt, inter = struct.unpack(
                ">IIBBBBB", chunk
            )
            assert inter == 0, f"interlaced PNG unsupported: {path}"
            assert bit_depth == 8 and color_type in (2, 6), (
                f"expected 8-bit RGB/RGBA PNG, got bit={bit_depth} color={color_type} "
                f"for {path}"
            )
        elif chunk_type == b"IDAT":
            idat.extend(chunk)
        elif chunk_type == b"IEND":
            break
    assert width is not None and height is not None, f"missing IHDR in {path}"
    raw = zlib.decompress(bytes(idat))
    channels = 4 if color_type == 6 else 3
    stride = width * channels
    out = bytearray(height * width * 4)
    prev = bytearray(stride)
    offset = 0
    for row in range(height):
        filter_type = raw[offset]
        offset += 1
        scan = bytearray(raw[offset : offset + stride])
        offset += stride
        if filter_type == 0:
            pass
        elif filter_type == 1:  # Sub
            for i in range(stride):
                left = scan[i - channels] if i >= channels else 0
                scan[i] = (scan[i] + left) & 0xFF
        elif filter_type == 2:  # Up
            for i in range(stride):
                scan[i] = (scan[i] + prev[i]) & 0xFF
        elif filter_type == 3:  # Average
            for i in range(stride):
                left = scan[i - channels] if i >= channels else 0
                scan[i] = (scan[i] + ((left + prev[i]) // 2)) & 0xFF
        elif filter_type == 4:  # Paeth
            for i in range(stride):
                a = scan[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                scan[i] = (scan[i] + pr) & 0xFF
        else:
            raise AssertionError(f"unsupported PNG filter {filter_type} in {path}")
        if channels == 4:
            out[row * width * 4 : (row + 1) * width * 4] = scan
        else:
            for column in range(width):
                source = column * 3
                target = (row * width + column) * 4
                out[target : target + 4] = scan[source : source + 3] + b"\xff"
        prev = scan
    return width, height, bytes(out)


def hex_floor_sample_alphas(path: Path) -> list[int]:
    """Alpha at hex-floor rim points (outside a typical building footprint).

    Kenney pointy-top hex tiles paint terrain across the whole hex; a settlement
    overlay that keeps that baked floor fully opaque covers Ground.modulate.
    """
    width, height, rgba = png_rgba8(path)
    points = (
        (max(1, width // 8), height // 2),
        (width - 1 - max(1, width // 8), height // 2),
        (width // 2, height - 1 - max(1, height // 8)),
        (width // 4, (3 * height) // 4),
        ((3 * width) // 4, (3 * height) // 4),
    )
    alphas: list[int] = []
    for x, y in points:
        alphas.append(rgba[(y * width + x) * 4 + 3])
    return alphas
