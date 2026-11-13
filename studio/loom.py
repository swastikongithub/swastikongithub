"""A small loom.

A weave is three boolean matrices (the weaving draft):

    threading  T[end]   -> shaft     which shaft each warp end is threaded on
    tie-up     U[shaft][treadle]     which shafts each treadle lifts
    treadling  P[pick]  -> treadles  which treadles are pressed for each pick

The cloth (the drawdown) is their product: warp end j is up on pick i when
the shaft it is threaded on is lifted by a treadle pressed on that pick.

    D[i][j] = OR_t ( P[i][t] AND U[T[j]][t] )

A Jacquard loom skips shafts and lifts every end independently; `jacquard`
builds a cloth directly from a per-cell rule (used for the damask lettering).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Draft:
    threading: list[int]                 # shaft per end
    tieup: list[list[int]]               # tieup[shaft] = treadles that lift it
    treadling: list[list[int]]           # treadles pressed per pick

    def drawdown(self) -> list[list[bool]]:
        lift = [set(t) for t in self.tieup]
        return [
            [bool(lift[s] & set(pressed)) for s in self.threading]
            for pressed in self.treadling
        ]


@dataclass
class Cloth:
    up: list[list[bool]]                 # up[pick][end]: warp on top
    warp: list[str] = field(default_factory=list)   # colour per end
    weft: list[str] = field(default_factory=list)   # colour per pick

    @property
    def picks(self) -> int:
        return len(self.up)

    @property
    def ends(self) -> int:
        return len(self.up[0])


def jacquard(picks: int, ends: int, rule) -> list[list[bool]]:
    return [[bool(rule(i, j)) for j in range(ends)] for i in range(picks)]


def tile(pattern: list[list[bool]], picks: int, ends: int, di: int = 0, dj: int = 0):
    h, w = len(pattern), len(pattern[0])
    return [[pattern[(i + di) % h][(j + dj) % w] for j in range(ends)] for i in range(picks)]


# --- Structures ------------------------------------------------------------

def twill(over: int, under: int, direction: int = 1) -> list[list[bool]]:
    n = over + under
    return [[((j - direction * i) % n) < over for j in range(n)] for i in range(n)]


def satin(n: int = 5, step: int = 2, warp_faced: bool = True) -> list[list[bool]]:
    """n-end satin. Warp-faced: warp on top except one interlacing per row."""
    rows = []
    for i in range(n):
        row = [warp_faced] * n
        row[(i * step) % n] = not warp_faced
        rows.append(row)
    return rows


def plain() -> list[list[bool]]:
    return [[True, False], [False, True]]


# --- Rendering -------------------------------------------------------------

def _f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def render(cloth: Cloth, x0: float, y0: float, s: float, gap: float,
           classes: dict[str, str] | None = None, row_groups: bool = False,
           row_attr=None, tiedown: float = 1.0) -> str:
    """Draw the cloth as floats: one stroke per run of the thread on top.

    Each colour becomes one <path>; strokes have round caps and are inset so
    every interlacing shows as a small gap between floats. `classes` maps a
    colour key to a CSS class (colours are themed in CSS, not baked in).
    With row_groups, every pick is its own <g> so it can be animated.
    """
    w = s - gap
    r = w / 2
    classes = classes or {}

    def vrun(j, a, b):  # warp end j visible on picks a..b
        x = x0 + j * s + s / 2
        ya = y0 + a * s + gap / 2 + r
        yb = y0 + (b + 1) * s - gap / 2 - r
        return f"M{_f(x)} {_f(ya)}V{_f(yb)}"

    def hrun(i, a, b):  # pick i visible on ends a..b
        y = y0 + i * s + s / 2
        xa = x0 + a * s + gap / 2 + r
        xb = x0 + (b + 1) * s - gap / 2 - r
        return f"M{_f(xa)} {_f(y)}H{_f(xb)}"

    up = cloth.up
    P, E = cloth.picks, cloth.ends
    # warp floats: they may cross pick boundaries, so they are drawn per end.
    warp_paths: dict[str, list[str]] = {}
    for j in range(E):
        i = 0
        while i < P:
            if up[i][j]:
                k = i
                while k + 1 < P and up[k + 1][j]:
                    k += 1
                key = cloth.warp[j] if (k > i or tiedown == 1.0) else cloth.warp[j] + "."
                warp_paths.setdefault(key, []).append((i, vrun(j, i, k)))
                i = k + 1
            else:
                i += 1
    weft_paths: dict[str, list[str]] = {}
    for i in range(P):
        j = 0
        while j < E:
            if not up[i][j]:
                k = j
                while k + 1 < E and not up[i][k + 1]:
                    k += 1
                weft_paths.setdefault(cloth.weft[i], []).append((i, hrun(i, j, k)))
                j = k + 1
            else:
                j += 1

    def cls(col):
        return classes.get(col.rstrip("."), col.rstrip("."))

    def sw(col):  # tie-down points (single-cell warp floats) may be drawn smaller
        return f' stroke-width="{_f(w * tiedown)}"' if col.endswith(".") else ""

    out = []
    if not row_groups:
        for col, items in list(weft_paths.items()) + list(warp_paths.items()):
            d = "".join(p for _, p in items)
            out.append(f'<path class="{cls(col)}" stroke-width="{_f(w * (tiedown if col.endswith(".") else 1))}" d="{d}"/>')
        return "".join(out)

    # Animated: group by the pick where each float starts.
    for i in range(P):
        parts = []
        for col, items in list(weft_paths.items()) + list(warp_paths.items()):
            d = "".join(p for k, p in items if k == i)
            if d:
                parts.append(f'<path class="{cls(col)}"{sw(col)} d="{d}"/>')
        attr = row_attr(i) if row_attr else ""
        out.append(f"<g{attr}>{''.join(parts)}</g>")
    return f'<g stroke-width="{_f(w)}">{"".join(out)}</g>'
