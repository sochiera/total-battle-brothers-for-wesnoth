"""Stdlib PNG helpers for Godot map/asset alpha checks (no Pillow).

Decodes non-interlaced 8-bit RGBA PNGs as used by Kenney hex tiles and
samples hex-floor rim alphas for owner-ground occlusion contracts.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


def png_rgba8(path: Path) -> tuple[int, int, bytes]:
    """Decode a non-interlaced 8-bit RGBA PNG via stdlib."""
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
            assert bit_depth == 8 and color_type == 6, (
                f"expected 8-bit RGBA PNG, got bit={bit_depth} color={color_type} "
                f"for {path}"
            )
        elif chunk_type == b"IDAT":
            idat.extend(chunk)
        elif chunk_type == b"IEND":
            break
    assert width is not None and height is not None, f"missing IHDR in {path}"
    raw = zlib.decompress(bytes(idat))
    stride = width * 4
    out = bytearray(height * stride)
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
                left = scan[i - 4] if i >= 4 else 0
                scan[i] = (scan[i] + left) & 0xFF
        elif filter_type == 2:  # Up
            for i in range(stride):
                scan[i] = (scan[i] + prev[i]) & 0xFF
        elif filter_type == 3:  # Average
            for i in range(stride):
                left = scan[i - 4] if i >= 4 else 0
                scan[i] = (scan[i] + ((left + prev[i]) // 2)) & 0xFF
        elif filter_type == 4:  # Paeth
            for i in range(stride):
                a = scan[i - 4] if i >= 4 else 0
                b = prev[i]
                c = prev[i - 4] if i >= 4 else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                scan[i] = (scan[i] + pr) & 0xFF
        else:
            raise AssertionError(f"unsupported PNG filter {filter_type} in {path}")
        out[row * stride : (row + 1) * stride] = scan
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
