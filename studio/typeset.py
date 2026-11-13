"""Text to SVG outlines.

GitHub serves README images through <img>, where web fonts cannot load.
Every piece of display type is therefore shaped with HarfBuzz and written
out as vector outlines, so the typography is identical on every device.
"""
from __future__ import annotations

import io
from functools import lru_cache

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer


class Face:
    def __init__(self, path: str, axes: dict | None = None):
        font = TTFont(path)
        if axes and "fvar" in font:
            font = instancer.instantiateVariableFont(font, axes, inplace=False)
        font.flavor = None
        buf = io.BytesIO()
        font.save(buf)
        self.tt = TTFont(io.BytesIO(buf.getvalue()))
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upm = self.tt["head"].unitsPerEm
        self.hb = hb.Font(hb.Face(buf.getvalue()))
        os2 = self.tt["OS/2"]
        self.cap = getattr(os2, "sCapHeight", 0) or self.upm * 0.7
        self.xh = getattr(os2, "sxHeight", 0) or self.upm * 0.5

    @lru_cache(maxsize=4096)
    def _shape(self, text: str, features: tuple):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, dict(features))
        return [
            (self.order[i.codepoint], p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)
        ]

    def measure(self, text: str, size: float, tracking: float = 0.0, features=()) -> float:
        run = self._shape(text, tuple(features))
        s = size / self.upm
        return sum(a for _, a, _, _ in run) * s + tracking * size * max(len(run) - 1, 0)

    def path(self, text: str, x: float, y: float, size: float, tracking: float = 0.0,
             anchor: str = "start", features=()) -> str:
        """Outline `text` with its baseline at (x, y). tracking is in em."""
        run = self._shape(text, tuple(features))
        s = size / self.upm
        width = self.measure(text, size, tracking, features)
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        out = []
        cx = x
        for name, adv, xo, yo in run:
            pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
            tp = TransformPen(pen, (s, 0, 0, -s, cx + xo * s, y - yo * s))
            self.glyphs[name].draw(tp)
            d = pen.getCommands()
            if d:
                out.append(d)
            cx += adv * s + tracking * size
        return "".join(out)
