"""The plates for github.com/swastikongithub.

    cd studio && npm install && pip install -r requirements.txt && python build.py

Every image on the profile is computed cloth. Nothing is drawn by hand:
each plate is a weave (a weaving draft, or a Jacquard rule) rendered thread
by thread, plus a few lines of type set as outlines.

System
  Width      every plate is 1048 units wide (262 ends at the base pitch of 4)
             and is shown at the README's full width.
  Type       Libre Caslon. On the loom it is quantised onto the thread grid
             (the masthead); on the plates it is set as vector outlines,
             because images in a README cannot load fonts.
  Colour     warp ink, weft ink, and madder for the one thread that
             explains something. Two themes, chosen by <picture>.
  Narrow     below 560 px rendered width, small labels hide and larger
             ones take their place (each SVG answers to its own width).
  Motion     two animations, both explanatory: the masthead is woven once,
             and the draft steps through its own arithmetic.
             prefers-reduced-motion removes both and leaves a finished,
             legible still.
"""
from __future__ import annotations

import io
import random
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

from loom import Cloth, Draft, render, satin, tile, twill
from typeset import Face

HERE = Path(__file__).resolve().parent
NM = HERE / "node_modules" / "@fontsource" / "libre-caslon-text" / "files"
OUT = HERE.parent / "assets"

W = 1048
PITCH = 4

THEMES = {
    "light": dict(warp="#1b2550", weft="#b9bfd6", tint="#e3e6ef", accent="#b3321f",
                  ink="#1b2550", quiet="#6b7190", rule="#c9cde0"),
    "dark": dict(warp="#e7dfca", weft="#454b5b", tint="#2a303c", accent="#ec6a4f",
                 ink="#e7dfca", quiet="#9a9fae", rule="#3a404d"),
}

roman = Face(str(NM / "libre-caslon-text-latin-400-normal.woff2"))
italic = Face(str(NM / "libre-caslon-text-latin-400-italic.woff2"))


def _ttf_bytes(path: Path) -> bytes:
    f = TTFont(str(path))
    f.flavor = None
    b = io.BytesIO()
    f.save(b)
    return b.getvalue()


BOLD_TTF = _ttf_bytes(NM / "libre-caslon-text-latin-700-normal.woff2")


def f1(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


# --------------------------------------------------------------------------
# shared output
# --------------------------------------------------------------------------
def write(name: str, theme: str, h: float, title: str, body: str, css: str = "") -> None:
    t = THEMES[theme]
    style = (
        f".W{{stroke:{t['warp']}}}.F{{stroke:{t['weft']}}}.T{{stroke:{t['tint']}}}"
        f".A{{stroke:{t['accent']}}}"
        "path.W,path.F,path.T,path.A{fill:none;stroke-linecap:round}"
        f".i{{fill:{t['ink']}}}.q{{fill:{t['quiet']}}}.af{{fill:{t['accent']}}}"
        f".r{{fill:none;stroke:{t['rule']};stroke-width:1}}"
        f".ra{{fill:none;stroke:{t['accent']};stroke-width:2.5}}"
        ".n{display:none}"
        "@media (max-width:560px){.w{display:none}.n{display:inline}}"
        + css
        + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    doc = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {f1(h)}" '
        f'width="{W}" height="{f1(h)}"><title>{title}</title>'
        f"<style>{style}</style>{body}</svg>\n"
    )
    OUT.mkdir(exist_ok=True)
    (OUT / f"{name}-{theme}.svg").write_text(doc, encoding="utf-8")


def text(face: Face, s: str, x: float, y: float, size: float, cls: str = "i",
         anchor: str = "start", tracking: float = 0.0, extra: str = "") -> str:
    return f'<path class="{cls}{extra}" d="{face.path(s, x, y, size, tracking, anchor)}"/>'


def cloth_colours(cloth: Cloth) -> dict:
    return {"W": "W", "F": "F", "T": "T", "A": "A"}


# --------------------------------------------------------------------------
# 1. Masthead: the name woven as damask
# --------------------------------------------------------------------------
def name_mask(ends: int, picks: int):
    """Quantise the name onto the thread grid, as a Jacquard designer would
    on point paper. Returns mask[pick][end] and the letter box."""
    S = 8
    probe = ImageFont.truetype(io.BytesIO(BOLD_TTF), 1000)
    track = 0.045
    def width(word, em):
        f = ImageFont.truetype(io.BytesIO(BOLD_TTF), int(em * S))
        return (sum(f.getlength(c) for c in word) + track * em * S * (len(word) - 1)) / S
    margin = 20
    target = ends - 2 * margin
    em = 60.0
    em = em * target / width("SWASTIK", em)
    cap = 0.77 * em
    top = 21
    lead = cap + 0.30 * em
    base1 = top + cap
    base2 = base1 + lead
    font = ImageFont.truetype(io.BytesIO(BOLD_TTF), int(em * S))
    im = Image.new("L", (ends * S, picks * S), 0)
    d = ImageDraw.Draw(im)
    for word, bl in (("SWASTIK", base1), ("SINGH", base2)):
        x = margin * S
        for ch in word:
            d.text((x, bl * S), ch, font=font, fill=255, anchor="ls")
            x += font.getlength(ch) + track * em * S
    px = im.resize((ends, picks), Image.BOX).load()
    return [[px[j, i] >= 128 for j in range(ends)] for i in range(picks)], base2


def masthead_picks() -> int:
    em = 60.0
    S = 8
    f = ImageFont.truetype(io.BytesIO(BOLD_TTF), int(em * S))
    w = (sum(f.getlength(c) for c in "SWASTIK") + 0.045 * em * S * 6) / S
    em = em * (W // PITCH - 40) / w
    cap = 0.77 * em
    return round(21 + cap + cap + 0.30 * em + 21)


def masthead(theme: str) -> None:
    ends = W // PITCH
    picks = masthead_picks()
    mask, base2 = name_mask(ends, picks)
    figure = tile(satin(8, 3, True), picks, ends)
    ground = tile(satin(8, 3, False), picks, ends)

    up = []
    for i in range(picks):
        row = []
        for j in range(ends):
            if j < 4 or j >= ends - 4:          # selvedge: plain weave
                row.append((i + j) % 2 == 0)
            elif mask[i][j]:
                row.append(figure[i][j])
            else:
                row.append(ground[i][j])
        up.append(row)
    cloth = Cloth(up, ["W"] * ends, ["F"] * picks)

    per = 0.018
    body = render(
        cloth, 0, 0, PITCH, 1.1, cloth_colours(cloth), row_groups=True,
        row_attr=lambda i: f' class="p" style="animation-delay:{i * per:.3f}s"',
        tiedown=0.62,
    )
    total = picks * per
    # The beater: a madder line that rides the fell of the cloth, then goes.
    beater = (
        f'<path class="A b" stroke-width="2.4" d="M0 0H{W}" '
        f'style="animation-duration:{total + 0.5:.2f}s"/>'
    )
    css = (
        ".p{animation:p .45s cubic-bezier(.2,.7,.2,1) both}"
        "@keyframes p{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}"
        ".b{opacity:0;animation-name:b;animation-timing-function:linear;animation-fill-mode:both}"
        f"@keyframes b{{0%{{opacity:1;transform:translateY(0)}}"
        f"92%{{opacity:1;transform:translateY({picks * PITCH}px)}}"
        f"100%{{opacity:0;transform:translateY({picks * PITCH}px)}}}}"
    )
    write("masthead", theme, picks * PITCH, "Swastik Singh",
          body + beater, css)


# --------------------------------------------------------------------------
# 2. The draft: notation on the left, the same draft woven on the right
# --------------------------------------------------------------------------
def diamond_draft(ends: int, picks: int) -> Draft:
    shafts = 8
    point = list(range(shafts)) + list(range(shafts - 2, 0, -1))   # 0..7..1
    threading = [point[j % len(point)] for j in range(ends)]
    tieup = [[] for _ in range(shafts)]
    for t in range(shafts):                 # treadle t lifts a 3/1/1/3 twill line
        for k in (0, 1, 2, 4):
            tieup[(t + k) % shafts].append(t)
    treadling = [[point[i % len(point)]] for i in range(picks)]
    return Draft(threading, tieup, treadling)


def draft_plate(theme: str) -> None:
    c = 13                       # notation cell
    n = 28                       # ends and picks shown (two repeats)
    shafts = 8
    d = diamond_draft(n, n)
    D = d.drawdown()
    ox, oy = 0, 40
    thr_y = oy
    dd_y = oy + shafts * c + c
    tre_x = ox + n * c + c

    cells, grid = [], []

    def block(x0, y0, cols, rows, filled):
        grid.append(f"M{x0} {y0}h{cols * c}v{rows * c}h{-cols * c}z")
        for k in range(1, cols):
            grid.append(f"M{x0 + k * c} {y0}v{rows * c}")
        for k in range(1, rows):
            grid.append(f"M{x0} {y0 + k * c}h{cols * c}")
        for (r, q) in filled:
            cells.append(f"M{x0 + q * c + 2} {y0 + r * c + 2}h{c - 4}v{c - 4}h{-(c - 4)}z")

    # threading: row = shaft (shaft 1 at the bottom, as drafts are read)
    block(ox, thr_y, n, shafts, [(shafts - 1 - s, j) for j, s in enumerate(d.threading)])
    # tie-up: rows = shafts, columns = treadles (rising shed)
    block(tre_x, thr_y, shafts, shafts,
          [(shafts - 1 - s, t) for s in range(shafts) for t in d.tieup[s]])
    # treadling: rows = picks, columns = treadles
    block(tre_x, dd_y, shafts, n, [(i, t) for i, ts in enumerate(d.treadling) for t in ts])
    # drawdown
    block(ox, dd_y, n, n, [(i, j) for i in range(n) for j in range(n) if D[i][j]])

    t = THEMES[theme]
    notation = (
        f'<path class="r" d="{"".join(grid)}"/>'
        f'<path class="i" d="{"".join(cells)}"/>'
    )

    # the same draft, woven
    cx, cs = 560, 8          # coarse enough not to alias on 1x screens
    ce, cp = (W - cx) // cs, (dd_y + n * c - oy) // cs
    big = diamond_draft(ce, cp)
    cloth = Cloth(big.drawdown(), ["W"] * ce, ["F"] * cp)
    woven = render(cloth, cx, oy, cs, 2.0, cloth_colours(cloth))

    # walking the arithmetic, one pick at a time
    step = 0.6
    cycle = n * step
    marks = []
    for i in range(n):
        tr = d.treadling[i][0]
        lifted = [s for s in range(shafts) if tr in d.tieup[s]]
        g = [
            f'<rect class="ra" x="{tre_x + tr * c}" y="{dd_y + i * c}" width="{c}" height="{c}"/>',
            f'<rect class="ra" x="{tre_x + tr * c}" y="{thr_y}" width="{c}" height="{shafts * c}"/>',
            f'<rect class="ra" x="{ox}" y="{dd_y + i * c}" width="{n * c}" height="{c}"/>',
        ]
        for k in range(i, cp, n):
            g.append(f'<rect class="af" x="{cx - 14}" y="{oy + k * cs + 1}" width="8" height="{cs - 2}"/>')
        delay = i * step - cycle
        marks.append(f'<g class="k" id="k{i}" style="animation-delay:{delay:.2f}s">{"".join(g)}</g>')
    slot = 100 / n
    css = (
        f".k{{opacity:0;animation:k {cycle:.1f}s infinite}}#k0{{opacity:1}}"
        f"@keyframes k{{0%,{slot - 0.4:.2f}%{{opacity:1}}{slot:.2f}%,100%{{opacity:0}}}}"
    )

    y_lab = oy - 14
    labels = (
        text(italic, "threading", ox, y_lab, 17, "q", extra=" w")
        + text(italic, "tie-up", tre_x, y_lab, 17, "q", extra=" w")
        + text(italic, "drawdown", ox, dd_y + n * c + 30, 17, "q", extra=" w")
        + text(italic, "treadling", tre_x, dd_y + n * c + 30, 17, "q", extra=" w")
        + text(italic, "the same draft, woven", cx, y_lab, 17, "q", extra=" w")
    )
    H = dd_y + n * c + 44
    write("draft", theme, H,
          "A weaving draft and the cloth it produces", notation + woven + "".join(marks) + labels, css)


# --------------------------------------------------------------------------
# 3. Sample card: four swatches that index the selected work
# --------------------------------------------------------------------------
def herringbone(p, e):
    base = twill(2, 2, 1)
    out = []
    for i in range(p):
        row = []
        for j in range(e):
            block, k = divmod(j, 8)
            jj = k if block % 2 == 0 else 7 - k
            row.append(base[i % 4][(jj + (2 if block % 2 else 0)) % 4])
        out.append(row)
    return out


def swatch(kind: str, p: int, e: int) -> Cloth:
    if kind == "herringbone":
        return Cloth(herringbone(p, e), ["W"] * e, ["F"] * p)
    if kind == "houndstooth":
        order = lambda k: "W" if (k // 4) % 2 == 0 else "F"   # 4 dark, 4 light
        warp = [order(j) for j in range(e)]
        weft = [order(i) for i in range(p)]
        return Cloth(tile(twill(2, 2, 1), p, e), warp, weft)
    if kind == "basket":   # 3/3 basket: threads work in threes, as if one
        b = [[(i // 3 + j // 3) % 2 == 0 for j in range(6)] for i in range(6)]
        return Cloth(tile(b, p, e), ["W"] * e, ["F"] * p)
    if kind == "tartan":
        sett = [("W", 10), ("F", 2), ("W", 3), ("A", 2), ("W", 3), ("F", 2), ("W", 10), ("F", 8)]
        seq = [col for col, k in sett for _ in range(k)]
        return Cloth(tile(twill(2, 2, 1), p, e), [seq[j % len(seq)] for j in range(e)],
                     [seq[i % len(seq)] for i in range(p)])
    raise ValueError(kind)


def pinked(x, y, w, h, tooth=8):
    pts = []
    k = int(w // tooth)
    for q in range(k + 1):
        pts.append((x + q * w / k, y + (0 if q % 2 == 0 else tooth / 2)))
    k2 = int(h // tooth)
    for q in range(k2 + 1):
        pts.append((x + w - (0 if q % 2 == 0 else tooth / 2), y + q * h / k2))
    for q in range(k + 1):
        pts.append((x + w - q * w / k, y + h - (0 if q % 2 == 0 else tooth / 2)))
    for q in range(k2 + 1):
        pts.append((x + (0 if q % 2 == 0 else tooth / 2), y + h - q * h / k2))
    return " ".join(f"{f1(a)},{f1(b)}" for a, b in pts)


LABEL = {"herringbone": "Herringbone 2/2", "houndstooth": "Houndstooth 4 and 4",
         "basket": "Basket 3/3", "tartan": "Tartan, 2/2 twill"}

SAMPLES = [
    ("01", "LPU Reserve", "herringbone"),
    ("02", "Tenora", "houndstooth"),
    ("03", "SyncSpace", "basket"),
    ("04", "VulnTrack", "tartan"),
]


def sample_card(theme: str) -> None:
    size, gap, cs = 238, 32, 6
    parts, defs = [], []
    for k, (num, name, kind) in enumerate(SAMPLES):
        x = k * (size + gap)
        n_ = size // cs + 1
        cl = swatch(kind, n_, n_)
        defs.append(f'<clipPath id="c{k}"><polygon points="{pinked(x, 0, size, size)}"/></clipPath>')
        parts.append(f'<g clip-path="url(#c{k})">{render(cl, x, 0, cs, 1.5, cloth_colours(cl))}</g>')
        parts.append(text(roman, num, x, size + 40, 26, "i", extra=" w"))
        parts.append(text(roman, name, x + 42, size + 40, 20, "i", extra=" w"))
        parts.append(text(italic, LABEL[kind], x + 42, size + 66, 17, "q", extra=" w"))
        parts.append(text(roman, num, x, size + 84, 64, "i", extra=" n"))
    H = size + 92
    write("samples", theme, H, "Four woven samples numbered 01 to 04",
          f"<defs>{''.join(defs)}</defs>" + "".join(parts))


# --------------------------------------------------------------------------
# 4. Composition: a shadow-stripe whose stripes are the measured languages
# --------------------------------------------------------------------------
COMPOSITION = [  # share of non-blank lines, seven public repositories
    ("Python", 33.8, lambda p, e: tile(twill(2, 2, 1), p, e)),
    ("JavaScript", 31.0, lambda p, e: tile(satin(5, 2, True), p, e)),
    ("TypeScript", 24.8, lambda p, e: tile(twill(3, 1, -1), p, e)),
    ("HTML & CSS", 6.6, lambda p, e: tile([[True, True, False, False]] * 2 + [[False, False, True, True]] * 2, p, e)),
    ("Java", 3.4, lambda p, e: tile([[True, False], [False, True]], p, e)),
]


def composition(theme: str) -> None:
    ends = W // PITCH
    picks = 30
    total = sum(s for _, s, _ in COMPOSITION)
    widths = [round(ends * s / total) for _, s, _ in COMPOSITION]
    widths[0] += ends - sum(widths)
    y0 = 64
    up = [[False] * ends for _ in range(picks)]
    warp = ["W"] * ends
    starts = []
    j0 = 0
    for (name, share, weave), w in zip(COMPOSITION, widths):
        cl = weave(picks, w)
        for i in range(picks):
            for j in range(w):
                up[i][j0 + j] = cl[i][j]
        if j0:
            warp[j0] = "A"          # one madder end marks each change of stripe
        starts.append((j0, w))
        j0 += w
    cloth = Cloth(up, warp, ["F"] * picks)
    body = render(cloth, 0, y0, PITCH, 1.1, cloth_colours(cloth))

    labels = []
    above = y0 - 18
    below = y0 + picks * PITCH + 34
    for k, ((name, share, _), (j, w)) in enumerate(zip(COMPOSITION, starts)):
        x = j * PITCH
        pct = f"{round(share)}"
        if k < 3:
            labels.append(text(roman, pct, x, above, 30, "i", extra=" w"))
            labels.append(text(italic, name, x + roman.measure(pct, 30) + 8, above, 18, "q", extra=" w"))
            labels.append(text(roman, f"{pct}%", x, above, 54, "i", extra=" n"))
        else:
            right = (j + w) * PITCH if k == 3 else W - 6
            ylab = below if k == 3 else above
            nw = italic.measure(name, 18)
            labels.append(text(italic, name, right, ylab, 18, "q", "end", extra=" w"))
            labels.append(text(roman, pct, right - nw - 8, ylab, 30, "i", "end", extra=" w"))
    H = below + 14
    write("composition", theme, H, "Composition by language", body + "".join(labels))


# --------------------------------------------------------------------------
# 5. Fringe: the cloth ends, the warp hangs loose
# --------------------------------------------------------------------------
def fringe(theme: str) -> None:
    """The last picks of plain weave, then the warp, gathered and knotted."""
    ends = W // PITCH
    hem = 8
    up = [[(i + j) % 2 == 0 for j in range(ends)] for i in range(hem)]
    cloth = Cloth(up, ["W"] * ends, ["F"] * hem)
    body = render(cloth, 0, 0, PITCH, 1.1, cloth_colours(cloth))
    rng = random.Random(262)
    y_top = hem * PITCH - 1
    n_groups = 24                              # 262 ends: 22 bundles of 11, 2 of 10
    sizes = [11] * 22 + [10] * 2
    rng.shuffle(sizes)
    threads, wraps = [], []
    j0 = 0
    for size in sizes:
        g = list(range(j0, j0 + size))
        j0 += size
        cxk = (g[0] + g[-1] + 1) / 2 * PITCH
        ky = y_top + 52
        half = size * 0.55
        for j in g:
            x = j * PITCH + PITCH / 2
            t = (x - cxk) / (size * PITCH / 2)          # -1 .. 1 across the bundle
            xin = cxk + t * half
            threads.append(f"M{f1(x)} {f1(y_top)}C{f1(x)} {f1(y_top + 30)} {f1(xin)} {f1(ky - 20)} {f1(xin)} {f1(ky)}")
            ln = 96 + 26 * rng.random() - 10 * abs(t)
            drift = rng.uniform(-3, 3)
            threads.append(
                f"M{f1(xin)} {f1(ky + 12)}C{f1(xin)} {f1(ky + 40)} {f1(xin + t * 6 + drift)} "
                f"{f1(ky + ln * 0.7)} {f1(xin + t * 9 + drift)} {f1(ky + 12 + ln)}"
            )
        # the knot: a wrapped band around the bundle
        wraps.append(f'<rect class="kn" x="{f1(cxk - half - 2.5)}" y="{f1(ky - 1)}" '
                     f'width="{f1(2 * half + 5)}" height="12" rx="5"/>')
    t = THEMES[theme]
    css = f".kn{{fill:{t['warp']}}}"
    fr = f'<path class="W" stroke-width="1.2" d="{"".join(threads)}"/>'
    H = y_top + 52 + 12 + 122 + 6
    write("fringe", theme, H, "The end of the cloth", body + fr + "".join(wraps), css)


if __name__ == "__main__":
    for old in OUT.glob("*.svg"):
        old.unlink()
    for theme in THEMES:
        masthead(theme)
        draft_plate(theme)
        sample_card(theme)
        composition(theme)
        fringe(theme)
    files = sorted(OUT.glob("*.svg"))
    for f in files:
        print(f"{f.name:28} {f.stat().st_size / 1024:6.1f} KB")
