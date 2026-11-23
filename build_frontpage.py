#!/usr/bin/env python3
"""news-image-20261123 — Monday 23 November 2026 in one image.

Renders entry.png (1024x1024) from stories.json with Pillow. Written from
scratch in this session. All illustrations are flat-vector scenes drawn in
code; no raster assets, no network, deterministic output.

P0 rules enforced BY CONSTRUCTION (build FAILS on any violation):
  * In-art labels: red banner top-left = caps phrase only (no numeral);
    story-number badge = dark square bottom-left; a big numeral lives in
    its OWN box (heroes, top-right) with >=6px clearance from every other
    text box. Every text box is measured (textbbox) and registered; the
    builder asserts pairwise non-intersection inside each card and that no
    text crosses a card edge.
  * DATE CHECK height is computed from wrapped text; last baseline >=4px
    above the bottom border; text >=11px, black on cream.
  * Briefs: <=24, >=10px, each a single measured line; last brief >=4px
    above the DATE CHECK box.
  * Map: smooth Natural Earth 110m land polygons (public-domain data,
    simplified in-code); pins de-collided to >=15px centre distance with
    white outlines and leader lines to true positions.
  * 3 heroes / 10 mediums / 35 stories; type floors: hero headline 26px,
    hero deck 11px, medium headline 13px, medium deck 11px, briefs 10px,
    strip numerals 34px.
"""
import json
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.expanduser("~/workspace/custom-skills/canvas-design/canvas-fonts")
SYS_FONTS = "/usr/share/fonts/truetype"

W, H = 1024, 1024
MARGIN = 12

# --- palette -------------------------------------------------------------
PAPER = (246, 241, 227)
INK = (22, 19, 14)
NAVY = (22, 35, 63)
RED = (179, 38, 30)
RED_DK = (140, 28, 22)
TEAL = (14, 107, 92)
GOLD = (200, 155, 60)
BLUE = (31, 78, 121)
GREEN = (46, 107, 52)
ORANGE = (194, 94, 16)
PURPLE = (91, 45, 142)
SEA = (214, 228, 238)
LAND = (233, 222, 196)
RULE = (180, 168, 140)
GREY = (110, 104, 90)

# --- fonts ---------------------------------------------------------------
def _font(*names, size=12):
    for n in names:
        for base in (FONT_DIR, SYS_FONTS + "/liberation", SYS_FONTS + "/dejavu"):
            p = os.path.join(base, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def f_gloock(s):
    return _font("Gloock-Regular.ttf", "DejaVuSerif-Bold.ttf", size=s)


def f_serif_b(s):
    return _font("CrimsonPro-Bold.ttf", "LiberationSerif-Bold.ttf",
                 "DejaVuSerif-Bold.ttf", size=s)


def f_serif_i(s):
    return _font("CrimsonPro-Italic.ttf", "LiberationSerif-Italic.ttf",
                 "DejaVuSerif.ttf", size=s)


def f_sans(s):
    return _font("LiberationSans-Regular.ttf", "DejaVuSans.ttf", size=s)


def f_sans_b(s):
    return _font("LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf", size=s)


def f_disp(s):
    return _font("BigShoulders-Bold.ttf", "LiberationSans-Bold.ttf", size=s)


def f_mono_b(s):
    return _font("GeistMono-Bold.ttf", "LiberationMono-Bold.ttf",
                 "DejaVuSansMono-Bold.ttf", size=s)


# --- text helpers --------------------------------------------------------
class Ctx:
    """A drawing context that measures every text box and can prove that
    no two text boxes in a scope intersect and none leaves its card."""

    def __init__(self, draw):
        self.d = draw
        self.boxes = []          # (x0, y0, x1, y1, label) in current scope
        self.scope = "global"

    def reset_scope(self, name):
        self.boxes = []
        self.scope = name

    def _reg(self, x, y, w, h, label):
        self.boxes.append((x, y, x + w, y + h, label))

    def text_w(self, s, font):
        return self.d.textlength(s, font=font)

    def text_h(self, font):
        b = self.d.textbbox((0, 0), "Ag", font=font)
        return b[3] - b[1]

    def wrap(self, s, font, width):
        """Greedy wrap; returns list of lines. Raises if a word is wider
        than the column (caller must shorten the text, never clip)."""
        words = s.split()
        lines, cur = [], ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if self.text_w(trial, font) <= width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                if self.text_w(wd, font) > width:
                    raise AssertionError(
                        "word %r too wide for column (%s)" % (wd, self.scope))
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def draw_text(self, x, y, s, font, fill, label, anchor_left=True):
        """Draw one line; register its exact bbox. Returns (w, h)."""
        w = self.text_w(s, font)
        b = self.d.textbbox((0, 0), s, font=font)
        h = b[3] - b[1]
        # textbbox y-offset: PIL draws from the anchor baseline area; use
        # the measured top so the registered box matches the glyphs.
        self.d.text((x, y - b[1]), s, font=font, fill=fill)
        self._reg(x, y, w, h, label)
        return w, h

    def draw_wrapped(self, x, y, lines, font, fill, label, leading=1.28):
        """Draw wrapped lines; returns total height used."""
        lh = int(round(self.text_h(font) * leading))
        yy = y
        for ln in lines:
            self.draw_text(x, yy, ln, font, fill, "%s: %r" % (label, ln[:24]))
            yy += lh
        return yy - y

    def assert_scope(self, card, what):
        """No two text boxes intersect; every box inside the card rect."""
        cx0, cy0, cx1, cy1 = card
        for (x0, y0, x1, y1, lab) in self.boxes:
            if x0 < cx0 - 0.5 or y0 < cy0 - 0.5 or x1 > cx1 + 0.5 or y1 > cy1 + 0.5:
                raise AssertionError(
                    "%s: text %r escapes card %s (box %s)" % (what, lab, card,
                                                             (x0, y0, x1, y1)))
        for i in range(len(self.boxes)):
            for j in range(i + 1, len(self.boxes)):
                a = self.boxes[i]
                b = self.boxes[j]
                ox = min(a[2], b[2]) - max(a[0], b[0])
                oy = min(a[3], b[3]) - max(a[1], b[1])
                if ox > 1 and oy > 1:
                    raise AssertionError(
                        "%s: text overlap %r vs %r (%.1f x %.1f px)"
                        % (what, a[4], b[4], ox, oy))


def spaced(s):
    """Letterspaced caps eyebrow."""
    return " ".join(list(s.replace(" ", "   "))).replace("      ", "   ")


# --- data ----------------------------------------------------------------
def load_json(name):
    with open(os.path.join(HERE, name)) as fh:
        return json.load(fh)


DATA = load_json("stories.json")
LAND_POLYS = load_json("land_polys.json")

# --- structural assertions (P0-5 / P2-14) --------------------------------
HEROES = DATA["heroes"]
MEDIUMS = DATA["mediums"]
BRIEFS = DATA["briefs"]
assert len(HEROES) == 3, "heroes must be 3, got %d" % len(HEROES)
assert len(MEDIUMS) == 10, "mediums must be 10, got %d" % len(MEDIUMS)
assert len(BRIEFS) <= 24, "briefs must be <=24, got %d" % len(BRIEFS)
TOTAL = len(HEROES) + len(MEDIUMS) + len(BRIEFS)
assert 35 <= TOTAL <= 39, "total stories must be 35-39, got %d" % TOTAL
assert sum(r["n"] for r in DATA["regions"]) == TOTAL, "region counts must sum to stories"
assert max(r["n"] for r in DATA["regions"]) <= 9, "no region above 9"
assert len(DATA["numbers"]) == 6, "numbers strip must be 6"
assert len(DATA["timeline"]) == 6, "timeline must be 6"
NUMS = [s["n"] for s in HEROES + MEDIUMS + BRIEFS]
assert NUMS == list(range(1, TOTAL + 1)), "story numbers must run 1..%d" % TOTAL

# --- illustrations -------------------------------------------------------
# Every scene draws >=3 distinct elements plus the card renderer's banner /
# badge / numeral box. No text is drawn inside these functions.

def _rr(d, box, rad, **kw):
    d.rounded_rectangle(box, radius=rad, **kw)


def _rot_text(base, x, y, s, font, fill, angle=-8):
    """Render text on its own tile, rotate, paste — used for stamps."""
    w = int(base.textlength(s, font=font)) + 16
    b = base.textbbox((0, 0), s, font=font)
    h = b[3] - b[1] + 12
    tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    td.text((8, 6 - b[1]), s, font=font, fill=fill)
    tile = tile.rotate(angle, expand=True, resample=Image.BICUBIC)
    return tile, x, y


def art_cop31(d, x, y, w, h):
    # Dusk plenary hall: sky bands, skyline, long table, 7 delegates, globe.
    d.rectangle([x, y, x + w, y + h], fill=(24, 68, 74))
    d.rectangle([x, y + int(h * 0.42), x + w, y + h], fill=(46, 96, 84))
    d.rectangle([x, y + int(h * 0.62), x + w, y + h], fill=(58, 44, 30))
    # distant skyline
    for i, bh in enumerate([18, 26, 14, 30, 20, 24, 16]):
        bx = x + 8 + i * (w // 8)
        d.rectangle([bx, y + int(h * 0.62) - bh, bx + 16, y + int(h * 0.62)],
                    fill=(30, 52, 58))
    # globe, centre-left above the table
    gx, gy, gr = x + int(w * 0.20), y + int(h * 0.30), 20
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=(52, 130, 90),
              outline=(240, 230, 200), width=2)
    d.ellipse([gx - 12, gy - 6, gx - 2, gy + 8], fill=(38, 110, 170))
    d.ellipse([gx + 4, gy + 4, gx + 14, gy + 14], fill=(38, 110, 170))
    # long table
    ty = y + int(h * 0.66)
    d.rectangle([x + 6, ty, x + w - 6, ty + 12], fill=(120, 84, 50))
    d.rectangle([x + 6, ty + 12, x + w - 6, ty + 16], fill=(90, 62, 36))
    # 7 delegates behind the table
    cols = [(178, 60, 50), (60, 110, 170), (200, 170, 60), (90, 160, 110),
            (150, 90, 160), (210, 120, 40), (70, 130, 130)]
    for i, c in enumerate(cols):
        cx = x + 22 + i * ((w - 44) // 6)
        d.ellipse([cx - 7, ty - 26, cx + 7, ty - 12], fill=(232, 200, 170))
        d.polygon([(cx - 12, ty - 10), (cx + 12, ty - 10), (cx + 8, ty + 2),
                   (cx - 8, ty + 2)], fill=c)
    # flags on the table
    for i, c in enumerate([(179, 38, 30), (31, 78, 121), (46, 107, 52),
                           (200, 155, 60), (91, 45, 142)]):
        fx = x + 30 + i * 52
        d.line([fx, ty - 14, fx, ty], fill=(220, 210, 190), width=1)
        d.polygon([(fx, ty - 14), (fx + 14, ty - 11), (fx, ty - 8)], fill=c)
    # red NO DEAL stamp, rotated, bottom-right (clear of the numeral box
    # and of the tag pill below the art)
    tile, tx, ty2 = _rot_text(d, x + w - 92, y + h - 44, "NO DEAL",
                              f_sans_b(13), (255, 255, 255))
    stamp = Image.new("RGBA", (tile.width + 12, tile.height + 8), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp)
    sd.rectangle([0, 0, stamp.width - 1, stamp.height - 1], fill=RED,
                 outline=RED_DK, width=2)
    stamp.paste(tile, (6, 4), tile)
    return stamp, tx, ty2


def art_dymer(d, x, y, w, h):
    # Night strike: sky, stars, three blocks, collapsed middle, searchlight.
    d.rectangle([x, y, x + w, y + h], fill=(16, 24, 46))
    rnd = random.Random(7)
    for _ in range(26):
        sx = x + rnd.randint(4, w - 4)
        sy = y + rnd.randint(4, int(h * 0.4))
        d.ellipse([sx, sy, sx + 2, sy + 2], fill=(230, 225, 190))
    # searchlight beam from bottom-right
    d.polygon([(x + w - 30, y + h), (x + w - 70, y + 8), (x + w - 46, y + 8)],
              fill=(250, 240, 180))
    blocks = [(0.06, 0.30, 52), (0.38, 0.46, 66), (0.72, 0.30, 52)]
    for fx, fw, bh in blocks:
        bx, bw = x + int(w * fx), int(w * fw)
        by = y + h - bh
        d.rectangle([bx, by, bx + bw, y + h], fill=(38, 46, 70))
        for r in range(4):
            for c in range(max(2, bw // 18)):
                wx = bx + 6 + c * 16
                wy = by + 8 + r * 13
                if wx + 8 < bx + bw - 4:
                    lit = (r * 3 + c) % 3 != 0
                    d.rectangle([wx, wy, wx + 8, wy + 7],
                                fill=(250, 210, 90) if lit else (20, 28, 50))
    # collapsed middle block: jagged top + rubble + dust
    bx, bw = x + int(w * 0.38), int(w * 0.46)
    by = y + h - 66
    d.polygon([(bx, by + 22), (bx + 18, by + 6), (bx + 40, by + 18),
               (bx + 62, by + 2), (bx + 84, by + 16), (bx + bw, by + 10),
               (bx + bw, by + 66), (bx, by + 66)], fill=(24, 30, 52))
    for i, (rx, rr_) in enumerate([(6, 10), (26, 14), (52, 11), (76, 13)]):
        d.polygon([(bx + rx, y + h), (bx + rx + rr_, y + h - 16),
                   (bx + rx + 2 * rr_, y + h)], fill=(58, 60, 78))
    for cx, cy, cr in [(bx + 20, by + 26, 12), (bx + 60, by + 20, 15),
                       (bx + 44, by + 34, 10)]:
        d.ellipse([cx - cr, cy - cr // 2, cx + cr, cy + cr // 2],
                  fill=(150, 145, 130))
    # three drones
    for dx, dy in [(0.16, 0.16), (0.55, 0.10), (0.84, 0.22)]:
        px, py = x + int(w * dx), y + int(h * dy)
        d.polygon([(px, py - 5), (px + 9, py + 4), (px - 9, py + 4)], fill=(10, 12, 22))
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=RED)


def art_gulf(d, x, y, w, h):
    # Strait at night: sea bands, tanker ablaze, radar arcs, patrol boat.
    d.rectangle([x, y, x + w, y + h], fill=(18, 50, 79))
    d.rectangle([x, y, x + w, y + int(h * 0.30)], fill=(24, 38, 66))
    d.ellipse([x + w - 52, y + 10, x + w - 22, y + 40], fill=(240, 220, 170))
    for i in range(4):
        yy = y + int(h * (0.42 + i * 0.13))
        d.line([x + 6, yy, x + w - 6, yy], fill=(90, 140, 175), width=2)
    # tanker
    hx, hy, hw = x + int(w * 0.14), y + int(h * 0.52), int(w * 0.60)
    d.rectangle([hx, hy, hx + hw, hy + 22], fill=(20, 22, 30))
    d.rectangle([hx + hw - 52, hy - 26, hx + hw - 8, hy], fill=(40, 44, 56))
    d.rectangle([hx + 14, hy - 14, hx + 26, hy], fill=(40, 44, 56))
    d.line([hx + 20, hy - 30, hx + 20, hy - 14], fill=(200, 200, 190), width=2)
    # flames on tanker + on the water
    for fx, fh_ in [(hx + 30, 26), (hx + 90, 32), (hx + 150, 22),
                    (x + int(w * 0.84), 24)]:
        d.polygon([(fx - 10, hy + 2), (fx, hy - fh_), (fx + 10, hy + 2)],
                  fill=(240, 120, 20))
        d.polygon([(fx - 5, hy + 2), (fx, hy - fh_ // 2), (fx + 5, hy + 2)],
                  fill=(250, 200, 60))
    # radar arcs top-left (kept inside the art rect)
    for r in (8, 13, 18):
        d.arc([x + 14 - r, y + 20 - r, x + 14 + r, y + 20 + r],
              start=300, end=60, fill=(240, 240, 230), width=2)
    d.ellipse([x + 11, y + 17, x + 17, y + 23], fill=(240, 240, 230))
    # missile streak
    d.line([x + int(w * 0.62), y + 16, x + int(w * 0.78), y + 34],
           fill=(255, 255, 255), width=2)
    d.ellipse([x + int(w * 0.78) - 3, y + 31, x + int(w * 0.78) + 3, y + 37],
              fill=(255, 220, 120))
    # patrol boat
    bx, by = x + int(w * 0.80), y + int(h * 0.80)
    d.polygon([(bx, by), (bx + 34, by), (bx + 28, by + 8), (bx + 6, by + 8)],
              fill=(200, 200, 195))
    d.rectangle([bx + 12, by - 8, bx + 22, by], fill=(200, 200, 195))


def art_ballot(d, x, y, w, h):
    # Hong Kong: skyline, red ballot box, flying ballot papers.
    d.rectangle([x, y, x + w, y + h], fill=(72, 48, 110))
    d.rectangle([x, y, x + w, y + int(h * 0.34)], fill=(110, 84, 160))
    for i, bh in enumerate([20, 30, 16, 26, 22, 34, 18]):
        bx = x + 4 + i * (w // 8)
        d.rectangle([bx, y + h - bh, bx + 14, y + h], fill=(30, 22, 52))
        d.rectangle([bx + 5, y + h - bh - 6, bx + 9, y + h - bh], fill=(250, 210, 90))
    # ballot box (fits inside the art rect)
    bx, by, bw, bh = x + int(w * 0.36), y + int(h * 0.28), 54, 28
    d.rectangle([bx, by, bx + bw, by + bh], fill=RED)
    d.rectangle([bx + 8, by - 6, bx + bw - 8, by], fill=RED_DK)
    d.rectangle([bx + 16, by - 3, bx + bw - 16, by], fill=(20, 16, 12))
    d.rectangle([bx + 18, by + 8, bx + bw - 18, by + 20], fill=(255, 255, 255))
    d.line([bx + 22, by + 14, bx + 27, by + 18], fill=RED, width=2)
    d.line([bx + 27, by + 18, bx + 36, by + 10], fill=RED, width=2)
    # flying papers
    for px, py, a in [(0.12, 0.30, -14), (0.72, 0.22, 12), (0.82, 0.52, -8)]:
        cx, cy = x + int(w * px), y + int(h * py)
        d.polygon([(cx, cy), (cx + 16, cy - 4), (cx + 18, cy + 8), (cx + 2, cy + 12)],
                  fill=(250, 248, 240))
        d.line([cx + 4, cy + 3, cx + 14, cy + 1], fill=(120, 110, 100), width=1)


def art_cricket(d, x, y, w, h):
    # Wellington: green outfield, brown pitch, stumps, batsman, red ball.
    d.rectangle([x, y, x + w, y + h], fill=(52, 130, 66))
    d.ellipse([x - 30, y + int(h * 0.55), x + w + 30, y + h + 40], fill=(44, 112, 56))
    d.rectangle([x + int(w * 0.42), y + 4, x + int(w * 0.58), y + h - 4],
                fill=(196, 164, 110))
    d.line([x + int(w * 0.42), y + int(h * 0.5), x + int(w * 0.58), y + int(h * 0.5)],
           fill=(255, 255, 255), width=1)
    # stumps
    sx = x + int(w * 0.47)
    for i in range(3):
        d.line([sx + i * 5, y + 10, sx + i * 5, y + 22], fill=(250, 220, 90), width=2)
    d.line([sx, y + 9, sx + 10, y + 9], fill=(250, 220, 90), width=2)
    # batsman silhouette (fits inside the art rect)
    bx, by = x + int(w * 0.68), y + int(h * 0.44)
    d.ellipse([bx - 6, by - 18, bx + 6, by - 8], fill=(24, 24, 28))
    d.polygon([(bx - 8, by - 8), (bx + 8, by - 8), (bx + 10, by + 10),
               (bx - 10, by + 10)], fill=(24, 24, 28))
    d.polygon([(bx - 4, by + 10), (bx + 2, by + 10), (bx + 6, by + 20),
               (bx - 2, by + 20)], fill=(24, 24, 28))
    d.polygon([(bx + 4, by + 10), (bx + 12, by + 10), (bx + 16, by + 20),
               (bx + 8, by + 20)], fill=(24, 24, 28))
    d.line([bx + 6, by - 6, bx + 22, by + 8], fill=(24, 24, 28), width=3)
    d.rectangle([bx + 20, by + 4, bx + 26, by + 18], fill=(210, 180, 120))
    # red ball + crowd dots
    d.ellipse([x + int(w * 0.20) - 4, y + 12, x + int(w * 0.20) + 4, y + 20],
              fill=(200, 40, 30))
    for i in range(9):
        cx = x + 8 + i * 20
        d.ellipse([cx, y + h - 8, cx + 4, y + h - 4], fill=(240, 235, 220))


def art_tennis(d, x, y, w, h):
    # Turin: blue court, white lines, net, ball, crossed rackets, trophy.
    d.rectangle([x, y, x + w, y + h], fill=(38, 96, 168))
    d.rectangle([x, y + int(h * 0.62), x + w, y + h], fill=(52, 130, 96))
    d.line([x + 8, y + int(h * 0.30), x + w - 8, y + int(h * 0.30)],
           fill=(255, 255, 255), width=2)
    d.line([x + 8, y + int(h * 0.30), x + 8, y + h - 6], fill=(255, 255, 255), width=2)
    d.line([x + w - 8, y + int(h * 0.30), x + w - 8, y + h - 6],
           fill=(255, 255, 255), width=2)
    # net
    ny = y + int(h * 0.52)
    d.rectangle([x + 10, ny, x + w - 10, ny + 10], fill=(240, 240, 235))
    for i in range(12):
        nx = x + 14 + i * ((w - 28) // 12)
        d.line([nx, ny, nx, ny + 10], fill=(160, 160, 155), width=1)
    # ball
    bx, by = x + int(w * 0.24), y + int(h * 0.20)
    d.ellipse([bx - 8, by - 8, bx + 8, by + 8], fill=(200, 220, 60))
    d.arc([bx - 8, by - 8, bx + 8, by + 8], start=300, end=120, fill=(255, 255, 255),
          width=2)
    # crossed rackets
    for cx, cy, ang in [(0.68, 0.30, -28), (0.82, 0.34, 28)]:
        rx, ry = x + int(w * cx), y + int(h * cy)
        d.ellipse([rx - 11, ry - 14, rx + 11, ry + 6], outline=(250, 240, 220), width=3)
        d.line([rx - 4, ry + 6, rx + 2, ry + 22], fill=(120, 80, 40), width=4)
    # trophy
    tx, ty = x + int(w * 0.50), y + int(h * 0.16)
    d.polygon([(tx - 8, ty), (tx + 8, ty), (tx + 5, ty + 12), (tx - 5, ty + 12)],
              fill=GOLD)
    d.rectangle([tx - 3, ty + 12, tx + 3, ty + 17], fill=GOLD)
    d.rectangle([tx - 8, ty + 17, tx + 8, ty + 20], fill=GOLD)


def art_ship(d, x, y, w, h):
    # Gulf of Finland: grey sea, burning cargo ship, lifeboat, gulls.
    d.rectangle([x, y, x + w, y + h], fill=(96, 118, 138))
    d.rectangle([x, y, x + w, y + int(h * 0.34)], fill=(150, 168, 186))
    for i in range(3):
        yy = y + int(h * (0.44 + i * 0.16))
        d.line([x + 4, yy, x + w - 4, yy], fill=(210, 220, 228), width=2)
    # hull + superstructure
    hx, hy, hw = x + int(w * 0.12), y + int(h * 0.52), int(w * 0.66)
    d.polygon([(hx, hy), (hx + hw, hy), (hx + hw - 12, hy + 16), (hx + 8, hy + 16)],
              fill=(30, 34, 40))
    d.rectangle([hx + hw - 46, hy - 18, hx + hw - 10, hy], fill=(52, 58, 66))
    d.rectangle([hx + 10, hy - 10, hx + 22, hy], fill=(52, 58, 66))
    # smoke + flames (kept inside the art rect)
    for cx, cy, cr in [(hx + 18, hy - 8, 6), (hx + 30, hy - 12, 8),
                       (hx + 44, hy - 16, 6)]:
        d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(120, 120, 118))
    for fx, fh_ in [(hx + 60, 16), (hx + 110, 20)]:
        d.polygon([(fx - 8, hy + 1), (fx, hy - fh_), (fx + 8, hy + 1)],
                  fill=(240, 120, 20))
        d.polygon([(fx - 4, hy + 1), (fx, hy - fh_ // 2), (fx + 4, hy + 1)],
                  fill=(250, 200, 60))
    # lifeboat + gulls
    bx, by = x + int(w * 0.84), y + int(h * 0.74)
    d.polygon([(bx, by), (bx + 22, by), (bx + 18, by + 7), (bx + 4, by + 7)],
              fill=(230, 110, 20))
    for gx, gy in [(0.30, 0.16), (0.44, 0.10)]:
        px, py = x + int(w * gx), y + int(h * gy)
        d.arc([px - 7, py - 5, px, py + 5], start=200, end=340, fill=(40, 40, 40),
              width=2)
        d.arc([px, py - 5, px + 7, py + 5], start=200, end=340, fill=(40, 40, 40),
              width=2)


def art_aidvan(d, x, y, w, h):
    # Gaza: sandy ground, road, white aid truck, scattered boxes, olive branch.
    d.rectangle([x, y, x + w, y + h], fill=(214, 190, 148))
    d.rectangle([x, y, x + w, y + int(h * 0.30)], fill=(232, 214, 178))
    d.ellipse([x + w - 34, y + 6, x + w - 12, y + 28], fill=(250, 220, 140))
    d.rectangle([x, y + int(h * 0.58), x + w, y + h], fill=(120, 116, 108))
    d.line([x, y + int(h * 0.58), x + w, y + int(h * 0.58)],
           fill=(255, 255, 255), width=2)
    for i in range(6):
        dx = x + 8 + i * 32
        d.line([dx, y + int(h * 0.78), dx + 16, y + int(h * 0.78)],
               fill=(255, 255, 255), width=2)
    # truck (fits inside the art rect)
    tx, ty = x + int(w * 0.30), y + int(h * 0.20)
    d.rectangle([tx, ty, tx + 62, ty + 20], fill=(250, 248, 242))
    d.rectangle([tx + 62, ty + 6, tx + 84, ty + 20], fill=(200, 60, 50))
    d.rectangle([tx + 68, ty + 9, tx + 78, ty + 15], fill=(180, 220, 240))
    d.ellipse([tx + 10, ty + 20, tx + 22, ty + 30], fill=(24, 24, 26))
    d.ellipse([tx + 66, ty + 20, tx + 78, ty + 30], fill=(24, 24, 26))
    d.rectangle([tx + 8, ty + 5, tx + 22, ty + 16], fill=(240, 230, 200))
    # scattered aid boxes
    for bx, by in [(0.10, 0.66), (0.82, 0.40), (0.88, 0.62)]:
        px, py = x + int(w * bx), y + int(h * by)
        d.rectangle([px, py, px + 14, py + 11], fill=(176, 138, 84))
        d.line([px, py + 5, px + 14, py + 5], fill=(120, 92, 54), width=1)
    # olive branch
    ox, oy = x + int(w * 0.14), y + int(h * 0.18)
    d.line([ox, oy + 14, ox + 22, oy - 6], fill=(70, 110, 60), width=2)
    for i in range(3):
        lx, ly = ox + 4 + i * 7, oy + 10 - i * 6
        d.ellipse([lx - 4, ly - 2, lx + 4, ly + 2], fill=(90, 140, 80))


def art_card(d, x, y, w, h):
    # Washington: navy field, big credit card, scissors, coins, down arrow.
    d.rectangle([x, y, x + w, y + h], fill=(22, 35, 63))
    for i in range(5):
        d.ellipse([x + 10 + i * 34, y + 6, x + 20 + i * 34, y + 12],
                  fill=(60, 80, 120))
    # card (fits inside the art rect)
    cx, cy, cw, ch = x + int(w * 0.16), y + int(h * 0.16), 110, 26
    _rr(d, [cx, cy, cx + cw, cy + ch], 6, fill=(245, 242, 235))
    d.rectangle([cx + 10, cy + 6, cx + 26, cy + 14], fill=GOLD)
    d.rectangle([cx, cy + 18, cx + cw, cy + 21], fill=RED)
    d.rectangle([cx + 62, cy + 6, cx + cw - 10, cy + 9], fill=(180, 175, 165))
    # scissors cutting the corner
    sx, sy = cx + cw - 6, cy + ch - 4
    d.ellipse([sx - 2, sy - 12, sx + 8, sy - 2], outline=(220, 220, 215), width=2)
    d.ellipse([sx - 2, sy + 2, sx + 8, sy + 12], outline=(220, 220, 215), width=2)
    d.line([sx + 6, sy - 7, sx + 24, sy - 12], fill=(220, 220, 215), width=2)
    d.line([sx + 6, sy + 7, sx + 24, sy + 12], fill=(220, 220, 215), width=2)
    # coins + down arrow
    for i, (px, py) in enumerate([(0.10, 0.70), (0.20, 0.76), (0.86, 0.68)]):
        qx, qy = x + int(w * px), y + int(h * py)
        d.ellipse([qx - 7, qy - 7, qx + 7, qy + 7], fill=GOLD,
                  outline=(160, 120, 40), width=1)
    ax, ay = x + int(w * 0.86), y + int(h * 0.16)
    d.line([ax, ay, ax, ay + 16], fill=(240, 90, 70), width=3)
    d.polygon([(ax - 6, ay + 10), (ax + 6, ay + 10), (ax, ay + 20)], fill=(240, 90, 70))


def art_measles(d, x, y, w, h):
    # Virginia: pale field, spiky virus orbs, thermometer, rash dots.
    d.rectangle([x, y, x + w, y + h], fill=(248, 232, 226))
    rnd = random.Random(11)
    for _ in range(40):
        px = x + rnd.randint(4, w - 4)
        py = y + rnd.randint(4, h - 4)
        d.ellipse([px, py, px + 2, py + 2], fill=(200, 90, 80))
    # virus orbs
    for cx, cy, cr, col in [(0.24, 0.42, 14, (200, 60, 50)),
                            (0.62, 0.30, 11, (180, 50, 44)),
                            (0.80, 0.62, 9, (210, 80, 60))]:
        px, py = x + int(w * cx), y + int(h * cy)
        for a in range(0, 360, 45):
            ex = px + int((cr + 6) * math.cos(math.radians(a)))
            ey = py + int((cr + 6) * math.sin(math.radians(a)))
            d.line([px, py, ex, ey], fill=col, width=2)
            d.ellipse([ex - 2, ey - 2, ex + 2, ey + 2], fill=col)
        d.ellipse([px - cr, py - cr, px + cr, py + cr], fill=col)
        d.ellipse([px - cr // 2, py - cr // 2, px, py], fill=(240, 140, 120))
    # thermometer (fits inside the art rect)
    tx, ty = x + int(w * 0.44), y + int(h * 0.40)
    _rr(d, [tx, ty, tx + 10, ty + 16], 5, fill=(255, 255, 255),
        outline=(150, 140, 130), width=1)
    d.rectangle([tx + 4, ty + 6, tx + 6, ty + 14], fill=RED)
    d.ellipse([tx - 2, ty + 12, tx + 12, ty + 24], fill=RED)


def art_robot(d, x, y, w, h):
    # Geneva: dark slate, robot head, red prohibition ring, drone, circuits.
    d.rectangle([x, y, x + w, y + h], fill=(40, 44, 56))
    for i in range(4):
        d.line([x + 6, y + 8 + i * 12, x + 26, y + 8 + i * 12],
               fill=(90, 100, 120), width=1)
        d.ellipse([x + 26, y + 6 + i * 12, x + 30, y + 10 + i * 12],
                  fill=(120, 200, 180))
    # robot head (fits inside the art rect)
    hx, hy, hw, hh = x + int(w * 0.36), y + int(h * 0.20), 52, 32
    _rr(d, [hx, hy, hx + hw, hy + hh], 8, fill=(200, 205, 212))
    d.line([hx + hw // 2, hy - 6, hx + hw // 2, hy], fill=(200, 205, 212), width=2)
    d.ellipse([hx + hw // 2 - 3, hy - 9, hx + hw // 2 + 3, hy - 4], fill=RED)
    d.ellipse([hx + 10, hy + 11, hx + 20, hy + 19], fill=(30, 180, 160))
    d.ellipse([hx + hw - 20, hy + 11, hx + hw - 10, hy + 19], fill=(30, 180, 160))
    d.line([hx + 12, hy + 25, hx + hw - 12, hy + 25], fill=(120, 125, 135), width=2)
    # prohibition ring over the head
    cx, cy, cr = hx + hw // 2, hy + hh // 2, 18
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], outline=RED, width=4)
    d.line([cx - 13, cy + 13, cx + 13, cy - 13], fill=RED, width=4)
    # small drone
    dx, dy = x + int(w * 0.84), y + int(h * 0.24)
    d.ellipse([dx - 8, dy - 4, dx + 8, dy + 4], fill=(180, 185, 195))
    d.ellipse([dx - 14, dy - 8, dx - 6, dy - 2], fill=(140, 145, 155))
    d.ellipse([dx + 6, dy - 8, dx + 14, dy - 2], fill=(140, 145, 155))


def art_roadblock(d, x, y, w, h):
    # Sinaloa: desert bands, road, burning tyre, mountains, helicopter.
    d.rectangle([x, y, x + w, y + h], fill=(224, 170, 96))
    d.rectangle([x, y, x + w, y + int(h * 0.30)], fill=(240, 200, 140))
    d.ellipse([x + w - 30, y + 6, x + w - 10, y + 26], fill=(250, 220, 140))
    for mx, mh_ in [(0.06, 22), (0.30, 30), (0.62, 20)]:
        px = x + int(w * mx)
        d.polygon([(px, y + int(h * 0.34)), (px + 26, y + int(h * 0.34) - mh_),
                   (px + 52, y + int(h * 0.34))], fill=(150, 100, 60))
    d.rectangle([x, y + int(h * 0.58), x + w, y + h], fill=(90, 88, 84))
    for i in range(6):
        dx = x + 8 + i * 32
        d.line([dx, y + int(h * 0.78), dx + 16, y + int(h * 0.78)],
               fill=(255, 255, 255), width=2)
    # burning tyre
    tx, ty = x + int(w * 0.42), y + int(h * 0.64)
    d.ellipse([tx - 11, ty - 6, tx + 11, ty + 10], fill=(20, 20, 22))
    d.ellipse([tx - 4, ty - 1, tx + 4, ty + 5], fill=(90, 88, 84))
    d.polygon([(tx - 7, ty - 4), (tx, ty - 20), (tx + 7, ty - 4)], fill=(240, 120, 20))
    d.polygon([(tx - 3, ty - 4), (tx, ty - 12), (tx + 3, ty - 4)], fill=(250, 200, 60))
    # helicopter
    hx, hy = x + int(w * 0.72), y + int(h * 0.16)
    d.ellipse([hx - 12, hy - 5, hx + 12, hy + 5], fill=(30, 30, 34))
    d.rectangle([hx + 12, hy - 3, hx + 26, hy + 1], fill=(30, 30, 34))
    d.line([hx - 20, hy - 8, hx + 20, hy - 8], fill=(30, 30, 34), width=2)
    # cactus
    cx, cy = x + int(w * 0.10), y + int(h * 0.40)
    d.line([cx, cy, cx, cy + 16], fill=(60, 130, 70), width=4)
    d.line([cx, cy + 6, cx - 8, cy + 6], fill=(60, 130, 70), width=3)
    d.line([cx - 8, cy + 6, cx - 8, cy - 2], fill=(60, 130, 70), width=3)


def art_swim(d, x, y, w, h):
    # Hormuz: blue bands, swimmer, waves, cliffs, distant tanker, sun.
    d.rectangle([x, y, x + w, y + h], fill=(36, 110, 160))
    d.rectangle([x, y, x + w, y + int(h * 0.30)], fill=(90, 160, 200))
    d.ellipse([x + 12, y + 6, x + 30, y + 24], fill=(250, 220, 140))
    for i in range(3):
        yy = y + int(h * (0.44 + i * 0.16))
        d.line([x + 4, yy, x + w - 4, yy], fill=(200, 225, 240), width=2)
    # cliffs left + right
    d.polygon([(x, y + int(h * 0.34)), (x + 26, y + int(h * 0.34)),
               (x + 14, y + h)], fill=(140, 100, 60))
    d.polygon([(x + w, y + int(h * 0.34)), (x + w - 26, y + int(h * 0.34)),
               (x + w - 14, y + h)], fill=(140, 100, 60))
    # distant tanker
    tx, ty = x + int(w * 0.68), y + int(h * 0.36)
    d.rectangle([tx, ty, tx + 34, ty + 8], fill=(30, 34, 40))
    d.rectangle([tx + 24, ty - 6, tx + 30, ty], fill=(30, 34, 40))
    # swimmer: head + arms + wake
    sx, sy = x + int(w * 0.46), y + int(h * 0.58)
    d.ellipse([sx - 6, sy - 6, sx + 6, sy + 6], fill=(24, 24, 28))
    d.arc([sx - 16, sy - 12, sx + 2, sy + 6], start=180, end=340, fill=(24, 24, 28),
          width=4)
    d.arc([sx - 2, sy - 4, sx + 16, sy + 12], start=200, end=20, fill=(24, 24, 28),
          width=4)
    for i in range(3):
        wx = sx - 22 + i * 8
        d.arc([wx, sy + 8, wx + 14, sy + 18], start=180, end=360,
              fill=(255, 255, 255), width=2)


ART = {
    "cop31": art_cop31, "dymer": art_dymer, "gulf": art_gulf,
    "ballot": art_ballot, "cricket": art_cricket, "tennis": art_tennis,
    "ship": art_ship, "aidvan": art_aidvan, "card": art_card,
    "measles": art_measles, "robot": art_robot, "roadblock": art_roadblock,
    "swim": art_swim,
}

# --- card rendering ------------------------------------------------------
TAG_FILL = {"CONFIRMED": GREEN, "REPORTED": (140, 110, 20), "CLAIM": RED,
            "FORECAST": BLUE, "ONGOING": TEAL}


def draw_banner(ctx, d, x, y, phrase, size=11):
    """Red banner, top-left of the art. Phrase only — never a numeral."""
    assert not any(ch.isdigit() for ch in phrase), \
        "banner must not contain a numeral: %r" % phrase
    f = f_sans_b(size)
    tw = d.textlength(phrase, font=f)
    bw, bh = int(tw) + 12, size + 6
    d.rectangle([x, y, x + bw, y + bh], fill=RED)
    ctx.draw_text(x + 6, y + 3, phrase, f, (255, 255, 255), "banner %r" % phrase)
    return bw, bh


def draw_badge(ctx, d, x, y, n, size=18):
    """Dark story-number square, bottom-left of the art."""
    d.rectangle([x, y, x + size, y + size], fill=INK)
    f = f_sans_b(11)
    s = str(n)
    tw = d.textlength(s, font=f)
    ctx.draw_text(x + (size - tw) / 2, y + 3, s, f, (255, 255, 255),
                  "badge %d" % n)
    return size, size


def draw_numeral_box(ctx, d, x, y, numeral, size=22):
    """The big numeral in its OWN white box (heroes only), numeral only."""
    f = f_disp(size)
    tw = d.textlength(numeral, font=f)
    bw, bh = int(tw) + 14, size + 10
    d.rectangle([x, y, x + bw, y + bh], fill=(255, 255, 255),
                outline=INK, width=1)
    ctx.draw_text(x + 7, y + 4, numeral, f, RED, "numeral %r" % numeral)
    return bw, bh


def _check_clearance(ctx, what):
    """Numeral box must clear every other text box by >=6px (P0-1)."""
    nums = [b for b in ctx.boxes if b[4].startswith("numeral ")]
    others = [b for b in ctx.boxes if not b[4].startswith("numeral ")]
    for nb in nums:
        for ob in others:
            dx = max(ob[0] - nb[2], nb[0] - ob[2])
            dy = max(ob[1] - nb[3], nb[1] - ob[3])
            gap = max(dx, dy) if (dx > 0 or dy > 0) else 0
            if dx <= 0 and dy <= 0:
                raise AssertionError("%s: numeral box touches %r" % (what, ob[4]))
            if gap < 6:
                raise AssertionError(
                    "%s: numeral box only %.1fpx from %r (need >=6)"
                    % (what, gap, ob[4]))


def draw_hero_card(ctx, d, img, x, y, w, art_h, text_h, st):
    """One hero card. Art on top, text below. Returns card height."""
    ctx.reset_scope("hero %d" % st["n"])
    card = (x, y, x + w, y + art_h + text_h)
    d.rectangle([x, y, x + w, y + art_h + text_h], fill=PAPER,
                outline=RULE, width=1)
    # --- art: drawn on its own tile, so no element can ever leave the art
    # rect and touch the text below (P0-1, by construction) ---
    tile = Image.new("RGB", (w - 2, art_h - 2), PAPER)
    td = ImageDraw.Draw(tile)
    res = ART[st["art"]](td, 0, 0, w - 2, art_h - 2)
    img.paste(tile, (x + 1, y + 1))
    stamp = None
    if res is not None:
        stamp, sx, sy = res
    draw_banner(ctx, d, x + 5, y + 5, st["banner"], size=11)
    # numeral box: measure first so its right edge sits 5px inside the card.
    nf = f_disp(22)
    nbw = int(d.textlength(st["numeral"], font=nf)) + 14
    draw_numeral_box(ctx, d, x + w - 5 - nbw, y + 5, st["numeral"], size=22)
    draw_badge(ctx, d, x + 5, y + art_h - 23, st["n"])
    if stamp is not None:
        img.paste(stamp, (x + 1 + sx, y + 1 + sy), stamp)
    _check_clearance(ctx, "hero %d" % st["n"])
    # --- text ---
    tx = x + 8
    tw = w - 16
    ty = y + art_h + 6
    # kicker + tag pill
    kick = "%d  %s · %s" % (st["n"], st["place"], st["topic"])
    kf = f_sans_b(9)
    ctx.draw_text(tx, ty, kick, kf, INK, "kicker %d" % st["n"])
    tag = st["tag"]
    tf = f_sans_b(8)
    twd = d.textlength(tag, font=tf)
    px = x + w - 8 - (twd + 10)
    py = ty - 1
    d.rectangle([px, py, px + twd + 10, py + 12], fill=TAG_FILL[tag])
    ctx.draw_text(px + 5, py + 2, tag, tf, (255, 255, 255), "tag %d" % st["n"])
    ty += 15
    # headline, 26px serif bold
    hf = f_serif_b(26)
    hl = ctx.wrap(st["headline"], hf, tw)
    assert len(hl) <= 3, "hero %d headline wraps to %d lines" % (st["n"], len(hl))
    used = ctx.draw_wrapped(tx, ty, hl, hf, INK, "headline %d" % st["n"],
                            leading=1.04)
    ty += used + 3
    # deck, 11px
    df = f_sans(11)
    dl = ctx.wrap(st["deck"], df, tw)
    assert len(dl) <= 3, "hero %d deck wraps to %d lines" % (st["n"], len(dl))
    used = ctx.draw_wrapped(tx, ty, dl, df, (50, 46, 38), "deck %d" % st["n"],
                            leading=1.28)
    ty += used + 3
    # sources
    sf = f_sans(8)
    ctx.draw_text(tx, ty, st["src"], sf, GREY, "src %d" % st["n"])
    ctx.assert_scope(card, "hero %d" % st["n"])
    return art_h + text_h


def draw_medium_card(ctx, d, img, x, y, w, art_h, text_h, st):
    """One medium card. Art strip on top, text below."""
    ctx.reset_scope("medium %d" % st["n"])
    card = (x, y, x + w, y + art_h + text_h)
    d.rectangle([x, y, x + w, y + art_h + text_h], fill=PAPER,
                outline=RULE, width=1)
    # art on its own tile: nothing can leave the art rect (P0-1).
    tile = Image.new("RGB", (w - 2, art_h - 2), PAPER)
    td = ImageDraw.Draw(tile)
    ART[st["art"]](td, 0, 0, w - 2, art_h - 2)
    img.paste(tile, (x + 1, y + 1))
    draw_banner(ctx, d, x + 4, y + 4, st["banner"], size=9)
    draw_badge(ctx, d, x + 4, y + art_h - 20, st["n"], size=16)
    tx = x + 7
    tw = w - 14
    ty = y + art_h + 5
    kick = "%d  %s · %s" % (st["n"], st["place"], st["topic"])
    kf = f_sans_b(8)
    ctx.draw_text(tx, ty, kick, kf, INK, "kicker %d" % st["n"])
    tag = st["tag"]
    tf = f_sans_b(7)
    twd = d.textlength(tag, font=tf)
    px = x + w - 7 - (twd + 8)
    py = ty - 1
    d.rectangle([px, py, px + twd + 8, py + 10], fill=TAG_FILL[tag])
    ctx.draw_text(px + 4, py + 1, tag, tf, (255, 255, 255), "tag %d" % st["n"])
    ty += 13
    hf = f_serif_b(13)
    hl = ctx.wrap(st["headline"], hf, tw)
    assert len(hl) <= 3, "medium %d headline wraps to %d lines" % (st["n"], len(hl))
    used = ctx.draw_wrapped(tx, ty, hl, hf, INK, "headline %d" % st["n"],
                            leading=1.06)
    ty += used + 2
    df = f_sans(11)
    dl = ctx.wrap(st["deck"], df, tw)
    assert len(dl) <= 2, "medium %d deck wraps to %d lines" % (st["n"], len(dl))
    used = ctx.draw_wrapped(tx, ty, dl, df, (50, 46, 38), "deck %d" % st["n"],
                            leading=1.26)
    ty += used + 2
    sf = f_sans(8)
    ctx.draw_text(tx, ty, st["src"], sf, GREY, "src %d" % st["n"])
    ctx.assert_scope(card, "medium %d" % st["n"])
    return art_h + text_h


# --- map -----------------------------------------------------------------
LAT_TOP, LAT_BOT = 83.0, -58.0


def draw_map(d, x0, y0, w, h, stories):
    """Smooth-polygon world map with de-collided numbered pins (P0-4)."""
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=SEA)
    for poly in LAND_POLYS:
        pts = [(x0 + (lon + 180.0) / 360.0 * w,
                y0 + (LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * h)
               for lon, lat in poly]
        d.polygon(pts, fill=LAND)

    def proj(lat, lon):
        return (x0 + (lon + 180.0) / 360.0 * w,
                y0 + (LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * h)

    pins = []   # (n, true_x, true_y, major)
    for s in stories:
        if s.get("lat") is None:
            continue
        px, py = proj(s["lat"], s["lon"])
        pins.append((s["n"], px, py, s["n"] <= 13))
    # Two-pass placement: majors first (15px apart), then brief dots only
    # kept clear of majors (9px) — dots may sit close together, which keeps
    # the Europe cluster from turning into a leader-line spiderweb.
    placed = []  # (n, fx, fy, major)

    def settle(px, py, min_d, others):
        fx, fy = px, py
        ang, rad = 0.0, 0.0
        for _ in range(150):
            if all(math.hypot(fx - qx, fy - qy) >= min_d
                   for (_, qx, qy, _) in others):
                return fx, fy
            ang += 1.0
            rad += 1.0
            fx = px + rad * math.cos(ang)
            fy = py + rad * math.sin(ang)
        raise AssertionError("pin at (%.0f, %.0f) could not be de-collided"
                             % (px, py))

    for n, px, py, major in pins:
        if major:
            fx, fy = settle(px, py, 15, placed)
            placed.append((n, fx, fy, major))
    for n, px, py, major in pins:
        if not major:
            # Dots avoid majors (>=9px) AND other dots (>=6px): without the
            # dot-vs-dot rule the whole London/Brussels cluster stacked on
            # one spot (6 stories -> 1 visible dot).
            fx, fy = px, py
            ang, rad = 0.0, 0.0
            for _ in range(200):
                ok_m = all(math.hypot(fx - qx, fy - qy) >= 9
                           for (_, qx, qy, m) in placed if m)
                ok_d = all(math.hypot(fx - qx, fy - qy) >= 6
                           for (_, qx, qy, m) in placed if not m)
                if ok_m and ok_d:
                    break
                ang += 1.0
                rad += 1.0
                fx = px + rad * math.cos(ang)
                fy = py + rad * math.sin(ang)
            else:
                raise AssertionError(
                    "dot %d could not be de-collided" % n)
            placed.append((n, fx, fy, major))
    placed.sort(key=lambda p: p[0])
    # final distance assertion (P0-4: >=14px centre distance, majors)
    majors = [p for p in placed if p[3]]
    for i in range(len(majors)):
        for j in range(i + 1, len(majors)):
            dd = math.hypot(majors[i][1] - majors[j][1],
                            majors[i][2] - majors[j][2])
            assert dd >= 14, "pins %d and %d only %.1fpx apart" % (
                majors[i][0], majors[j][0], dd)
    pin_by_n = {n: (px, py) for n, px, py, _ in pins}
    for (n, fx, fy, major) in placed:
        px, py = pin_by_n[n]
        if math.hypot(fx - px, fy - py) > 3:
            d.line([px, py, fx, fy], fill=(170, 165, 155), width=1)
        if major:
            r = 7
            d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=RED,
                      outline=(255, 255, 255), width=2)
            f = f_sans_b(8)
            s = str(n)
            tw = d.textlength(s, font=f)
            b = d.textbbox((0, 0), s, font=f)
            d.text((fx - tw / 2, fy - (b[3] - b[1]) / 2 - b[1]), s, font=f,
                   fill=(255, 255, 255))
        else:
            d.ellipse([fx - 2.5, fy - 2.5, fx + 2.5, fy + 2.5],
                      fill=(90, 85, 75), outline=(255, 255, 255), width=1)
    return placed

# --- layout constants (tuned so the page fits 1024 with all floors) -------
TOPBAR_H = 19
TITLE_SIZE = 46
NUM_H = 48
REGION_H = 19
TL_H = 19
HERO_ART_H = 92
MED_ART_H = 44
MED_GAP = 6
HERO_GAP = 8


def measure_text_heights(ctx):
    """Measure hero/medium text blocks so card heights are exact."""
    hero_th = 0
    for st in HEROES:
        hf = f_serif_b(26)
        hl = ctx.wrap(st["headline"], hf, 328 - 16)
        df = f_sans(11)
        dl = ctx.wrap(st["deck"], df, 328 - 16)
        th = 6 + 15 + len(hl) * 28 + 3 + len(dl) * 14 + 3 + 11
        hero_th = max(hero_th, th)
    med_th = 0
    for st in MEDIUMS:
        hf = f_serif_b(13)
        hl = ctx.wrap(st["headline"], hf, 195 - 14)
        df = f_sans(11)
        dl = ctx.wrap(st["deck"], df, 195 - 14)
        th = 5 + 13 + len(hl) * 15 + 2 + len(dl) * 14 + 2 + 10
        med_th = max(med_th, th)
    return hero_th, med_th


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    ctx = Ctx(d)
    y = 0

    # --- top bar ---
    d.rectangle([0, y, W, y + TOPBAR_H], fill=NAVY)
    ctx.draw_text(12, y + 4, "THE WORLD IN ONE DAY", f_sans_b(10),
                  (255, 255, 255), "topbar-left")
    rt = DATA["page_date"].upper()
    tw = d.textlength(rt, font=f_sans_b(10))
    ctx.draw_text(W - 12 - tw, y + 4, rt, f_sans_b(10), (255, 255, 255),
                  "topbar-right")
    y += TOPBAR_H

    # --- masthead ---
    y += 3
    eb = spaced(DATA["eyebrow"])
    ef = f_sans_b(10)
    ew = d.textlength(eb, font=ef)
    ctx.draw_text((W - ew) / 2, y, eb, ef, (90, 82, 66), "eyebrow")
    y += 14
    tf = f_gloock(TITLE_SIZE)
    title = DATA["page_date"]
    tw = d.textlength(title, font=tf)
    ctx.draw_text((W - tw) / 2, y, title, tf, INK, "masthead")
    y += TITLE_SIZE + 10
    df = f_serif_i(13)
    dw = d.textlength(DATA["deck"], font=df)
    ctx.draw_text((W - dw) / 2, y, DATA["deck"], df, RED, "deck-line")
    y += 15
    d.line([MARGIN, y, W - MARGIN, y], fill=INK, width=2)
    y += 5

    # --- numbers strip ---
    ctx.draw_text(MARGIN, y, DATA["numbers_label"], f_sans_b(10), INK,
                  "numbers-label")
    y += 13
    nbw = (W - 2 * MARGIN) // 6
    for i, num in enumerate(DATA["numbers"]):
        bx = MARGIN + i * nbw
        if i:
            d.line([bx - 3, y, bx - 3, y + NUM_H - 4], fill=RULE, width=1)
        bf = f_disp(34)
        bw = d.textlength(num["big"], font=bf)
        ctx.draw_text(bx + (nbw - bw) / 2, y, num["big"], bf, RED,
                      "num %r" % num["big"])
        lf = f_sans_b(9)
        lw = d.textlength(num["label"], font=lf)
        ctx.draw_text(bx + (nbw - lw) / 2, y + 33, num["label"], lf, INK,
                      "numlabel %r" % num["label"][:12])
        sf = f_sans(7)
        sw = d.textlength(num["src"], font=sf)
        ctx.draw_text(bx + (nbw - sw) / 2, y + 43, num["src"], sf, GREY,
                      "numsrc %r" % num["src"][:12])
    y += NUM_H
    d.line([MARGIN, y, W - MARGIN, y], fill=RULE, width=1)
    y += 4

    # --- region bar (widths proportional to counts; sums to stories) ---
    rx = MARGIN
    total_w = W - 2 * MARGIN
    for r in DATA["regions"]:
        rw = int(round(total_w * r["n"] / TOTAL))
        d.rectangle([rx, y, rx + rw, y + REGION_H], fill=r["color"])
        lab = "%s %d" % (r["name"], r["n"])
        lf = f_sans_b(9)
        lw = d.textlength(lab, font=lf)
        assert lw <= rw - 4, "region label %r too wide for segment" % lab
        ctx.draw_text(rx + (rw - lw) / 2, y + 5, lab, lf, (255, 255, 255),
                      "region %s" % r["name"])
        rx += rw
    y += REGION_H + 3

    # --- UTC timeline ---
    d.rectangle([MARGIN, y, W - MARGIN, y + TL_H], fill=NAVY)
    lab = DATA["timeline_label"]
    lf = f_sans_b(9)
    ctx.draw_text(MARGIN + 6, y + 5, lab, lf, (255, 210, 90), "tl-label")
    tx = MARGIN + 6 + d.textlength(lab, font=lf) + 12
    for it in DATA["timeline"]:
        tf2 = f_mono_b(10)
        ctx.draw_text(tx, y + 5, it["t"], tf2, (255, 120, 100), "tl-time")
        tx += d.textlength(it["t"], font=tf2) + 4
        wf = f_sans(10)
        ctx.draw_text(tx, y + 5, it["what"], wf, (255, 255, 255), "tl-what")
        tx += d.textlength(it["what"], font=wf) + 10
    assert tx <= W - MARGIN, "timeline overflows: ends at %d" % tx
    y += TL_H + 6

    # --- heroes ---
    hero_th, med_th = measure_text_heights(ctx)
    hw = (W - 2 * MARGIN - 2 * HERO_GAP) // 3
    hero_card_h = HERO_ART_H + hero_th
    for i, st in enumerate(HEROES):
        hx = MARGIN + i * (hw + HERO_GAP)
        draw_hero_card(ctx, d, img, hx, y, hw, HERO_ART_H, hero_th, st)
    y += hero_card_h + 6

    # --- mediums, 5 across x 2 rows ---
    mw = (W - 2 * MARGIN - 4 * MED_GAP) // 5
    med_card_h = MED_ART_H + med_th
    for i, st in enumerate(MEDIUMS):
        row, col = divmod(i, 5)
        mx = MARGIN + col * (mw + MED_GAP)
        my = y + row * (med_card_h + MED_GAP)
        draw_medium_card(ctx, d, img, mx, my, mw, MED_ART_H, med_th, st)
    y += 2 * med_card_h + MED_GAP + 6

    # --- map + briefs ---
    sec_y = y
    ctx.draw_text(MARGIN, y, "WHERE IT HAPPENED — PINS MATCH STORY NUMBERS",
                  f_sans_b(10), INK, "map-header")
    y += 14
    map_x, map_w, map_h = MARGIN, 330, 140
    draw_map(d, map_x, y, map_w, map_h, HEROES + MEDIUMS + BRIEFS)
    cap = ctx.wrap(DATA["map_caption"], f_sans(8), map_w)
    cy = y + map_h + 3
    ctx.draw_wrapped(map_x, cy, cap, f_sans(8), GREY, "map-caption",
                     leading=1.25)
    # briefs, 2 columns x 11, each a single measured line (P0-3)
    bx0 = map_x + map_w + 10
    col_w = (W - MARGIN - bx0 - 10) // 2
    bf = f_sans(10)
    bh = f_sans_b(10)
    for i, b in enumerate(BRIEFS):
        col, row = divmod(i, 11)
        bx = bx0 + col * (col_w + 10)
        by = y + row * 13
        num_s = "%d  " % b["n"]
        nw = d.textlength(num_s, font=bh)
        tw = d.textlength(b["text"], font=bf)
        assert nw + tw <= col_w, "brief %d too wide (%.0f > %d): %r" % (
            b["n"], nw + tw, col_w, b["text"])
        ctx.draw_text(bx, by, num_s, bh, RED, "briefnum %d" % b["n"])
        ctx.draw_text(bx + nw, by, b["text"], bf, INK, "brief %d" % b["n"])
    briefs_bottom = y + 11 * 13
    y = max(sec_y + 14 + map_h + 3 + len(cap) * 10 + 4, briefs_bottom) + 4

    # --- DATE CHECK (height computed from wrapped text, P0-2) ---
    dc_y = y
    dcf = f_sans(11)
    dchead = f_sans_b(11)
    inner_w = W - 2 * MARGIN - 20
    lines = ctx.wrap(DATA["datecheck"], dcf, inner_w)
    notyet = ctx.wrap(DATA["datecheck_notyet"], f_sans_b(11), inner_w)
    dc_h = 8 + 13 + len(lines) * 13 + 3 + len(notyet) * 13 + 8
    d.rectangle([MARGIN, dc_y, W - MARGIN, dc_y + dc_h], fill=PAPER,
                outline=RED, width=2)
    ctx.draw_text(MARGIN + 10, dc_y + 8, DATA["datecheck_label"], dchead, RED,
                  "dc-label")
    ty = dc_y + 8 + 13
    used = ctx.draw_wrapped(MARGIN + 10, ty, lines, dcf, INK, "dc-body",
                            leading=1.18)
    ty += used + 3
    used2 = ctx.draw_wrapped(MARGIN + 10, ty, notyet, f_sans_b(11), INK,
                             "dc-notyet", leading=1.18)
    last_bottom = ty + used2
    assert dc_y + dc_h - last_bottom >= 4, \
        "DATE CHECK last line %.0fpx from border" % (dc_y + dc_h - last_bottom)
    y = dc_y + dc_h + 6

    # --- legend + footer ---
    lf = f_sans(8)
    lw = d.textlength(DATA["legend"], font=lf)
    assert lw <= W - 2 * MARGIN, "legend too wide"
    ctx.draw_text((W - lw) / 2, y, DATA["legend"], lf, (70, 64, 52), "legend")
    y += 10
    fl = ctx.wrap(DATA["footer"], f_sans(8), W - 2 * MARGIN)
    assert len(fl) <= 2, "footer wraps to %d lines" % len(fl)
    ctx.draw_wrapped(MARGIN, y, fl, f_sans(8), (70, 64, 52), "footer",
                     leading=1.25)
    y += len(fl) * 10 + 2
    assert y <= H, "page overflows by %dpx (y=%d)" % (y - H, y)

    # --- QA: 512px downscale + crops ---
    img.save(os.path.join(HERE, "entry.png"))
    img.resize((512, 512), Image.LANCZOS).save(
        os.path.join(HERE, "entry_512.png"))
    print("QA PASS: %d stories (3 heroes, 10 mediums, %d briefs); "
          "final y=%d/1024" % (TOTAL, len(BRIEFS), y))
    print("hero text h=%d, medium text h=%d, datecheck h=%d (%d+%d lines)"
          % (hero_th, med_th, dc_h, len(lines), len(notyet)))


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print("BUILD FAILED: %s" % e, file=sys.stderr)
        sys.exit(1)
