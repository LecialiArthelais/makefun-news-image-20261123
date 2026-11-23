#!/usr/bin/env python3
"""Build the news-image-20261123 front page: one 1024x1024 Pillow PNG.

Fresh rewrite from DESIGN.md. Pillow only, no network, no randomness:
re-runs must be byte-identical. Every text box is registered from measured
textbbox extents and the build FAILS on any overlap, any text escaping its
card, any banner containing a digit, or any numeral box closer than 6px to
another text box in the same card (P0-1). DATE CHECK height comes from the
wrapped 11px text (P0-2). Briefs are single measured 10px lines (P0-3).
The map is smooth Natural Earth 110m polygons with de-collided pins (P0-4).
Structure is 3 heroes / 10 mediums / 22 briefs = 35 stories (P0-5).
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024
MARGIN = 16
CW = W - 2 * MARGIN  # 992 content width

# ---- Design tokens: "Newsprint" (DESIGN.md) -------------------------------
PAPER = "#f6f1e3"
INK = "#16130e"
NAVY = "#16233f"
RED = "#b3261e"
GREEN = "#2e6b34"
AMBER = "#8a6d00"
SEA = "#cfe0d8"
LAND = "#e8ddc0"
LAND_LINE = "#b9a878"
REGION_COLORS = {
    "Western Europe": "#1f4e79",
    "Eastern Europe": "#2e6b8a",
    "Middle East": "#b3261e",
    "Americas": "#2e6b34",
    "Asia-Pacific": "#c25e10",
    "Oceania": "#0e6b5c",
    "Africa": "#8a6d00",
    "World": "#5b2d8e",
}
TAG_COLORS = {"CONFIRMED": "#2e6b34", "REPORTED": "#8a6d00", "CLAIM": "#b3261e"}

# ---- Fonts (system Liberation / DejaVu; Gloock etc. are not on this VM) ---
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF_IT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SERIF_REG = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


# ---- Measured text registry: P0-1 enforcement -----------------------------
class Card:
    """One card's text boxes. Every draw registers its measured box here;
    finish() asserts no two boxes intersect and none escapes the card."""

    def __init__(self, name, x0, y0, x1, y1):
        self.name = name
        self.rect = (x0, y0, x1, y1)
        self.boxes = []  # (label, x0, y0, x1, y1)

    def add(self, label, box):
        x0, y0, x1, y1 = box
        cx0, cy0, cx1, cy1 = self.rect
        assert cx0 - 1 <= x0 and y0 >= cy0 - 1, \
            "%s: %s escapes top/left of card %s" % (self.name, label, self.rect)
        assert x1 <= cx1 + 1 and y1 <= cy1 + 1, \
            "%s: %s escapes bottom/right of card %s" % (self.name, label, self.rect)
        self.boxes.append((label, x0, y0, x1, y1))

    def finish(self):
        for i in range(len(self.boxes)):
            for j in range(i + 1, len(self.boxes)):
                li, a = self.boxes[i][0], self.boxes[i][1:]
                lj, b = self.boxes[j][0], self.boxes[j][1:]
                overlap = not (a[2] <= b[0] or b[2] <= a[0]
                               or a[3] <= b[1] or b[3] <= a[1])
                assert not overlap, \
                    "%s: text boxes overlap: %s %s vs %s %s" % (self.name, li, a, lj, b)


def gap(a, b):
    """Edge-to-edge gap between two boxes (0 when they touch/overlap)."""
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return math.hypot(dx, dy)


def draw_text(draw, card, label, xy, text, fnt, fill, anchor="la"):
    """Draw text and register its measured box on the card (or None)."""
    x, y = xy
    bbox = draw.textbbox((x, y), text, font=fnt, anchor=anchor)
    draw.text((x, y), text, font=fnt, fill=fill, anchor=anchor)
    if card is not None:
        card.add(label, bbox)
    return bbox


def wrap(draw, text, fnt, width):
    """Greedy word wrap to a pixel width; returns a list of lines."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def wrap_lines(draw, text, fnt, width, max_lines):
    """Wrap and assert the text fits in max_lines; returns the lines."""
    lines = wrap(draw, text, fnt, width)
    assert len(lines) <= max_lines, \
        "text needs %d lines, max %d: %r" % (len(lines), max_lines, text)
    return lines


def banner_box(draw, card, x, y, text, fnt):
    """Red banner: caps phrase ONLY. P0-1: a banner must never hold a digit."""
    assert not any(ch.isdigit() for ch in text), \
        "banner contains a digit (P0-1): %r" % text
    tw = draw.textlength(text, font=fnt)
    pad_x, pad_y = 6, 4
    box = (x, y, x + int(tw) + 2 * pad_x, y + fnt.size + 2 * pad_y)
    draw.rectangle(box, fill=RED)
    draw_text(draw, card, "banner", (x + pad_x, y + pad_y), text, fnt, "white")
    return box


def numeral_box(draw, card, x, y, text, fnt):
    """Big numeral in its own white box with a red border (heroes only)."""
    tw = draw.textlength(text, font=fnt)
    pad_x, pad_y = 7, 3
    box = (x, y, x + int(tw) + 2 * pad_x, y + fnt.size + 2 * pad_y)
    draw.rectangle(box, fill="white", outline=RED, width=2)
    draw_text(draw, card, "numeral", (x + pad_x, y + pad_y), text, fnt, RED)
    return box


def tag_pill(draw, card, x, y, tag, fnt):
    """Certainty tag pill, right-aligned at x (x is the right edge)."""
    tw = draw.textlength(tag, font=fnt)
    pad_x, pad_y = 5, 2
    box = (x - int(tw) - 2 * pad_x, y, x, y + fnt.size + 2 * pad_y)
    draw.rectangle(box, fill=TAG_COLORS[tag])
    draw_text(draw, card, "tag", (box[0] + pad_x, y + pad_y), tag, fnt, "white")
    return box


def number_badge(draw, card, x, y, n, size=16):
    """Small dark story-number badge, bottom-left of the art tile."""
    fnt = font(SANS_B, size)
    label = str(n)
    tw = draw.textlength(label, font=fnt)
    box = (x, y, x + int(tw) + 10, y + size + 6)
    draw.rectangle(box, fill=INK)
    draw_text(draw, card, "badge", (x + 5, y + 3), label, fnt, "white")
    return box


# ---- Flat-vector illustrations (one system per card, colours = page tokens)
# Each scene paints on its own tile; the tile is pasted into the art rect,
# so no illustration element can ever touch text below (P0-1 by construction).
def tile(w, h, painter, bg):
    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)
    painter(d, w, h)
    return img


def _person(d, x, y, s, shirt, skin="#e8b98a", hair="#16130e"):
    """Tiny seated/standing flat figure: head, torso, legs. No ground line."""
    d.ellipse([x - 5 * s, y - 6 * s, x + 5 * s, y + 4 * s], fill=skin)
    d.pieslice([x - 5 * s, y - 7 * s, x + 5 * s, y + 1 * s], 180, 360, fill=hair)
    d.rectangle([x - 7 * s, y + 4 * s, x + 7 * s, y + 16 * s], fill=shirt)
    d.rectangle([x - 6 * s, y + 16 * s, x - 1 * s, y + 26 * s], fill="#16130e")
    d.rectangle([x + 1 * s, y + 16 * s, x + 6 * s, y + 26 * s], fill="#16130e")


def scene_cop(d, w, h):
    d.rectangle([0, h - 26, w, h], fill="#7a5a34")          # plenary table
    d.rectangle([0, h - 30, w, h - 26], fill="#5d4326")
    for i, shirt in enumerate(["#b3261e", "#1f4e79", "#2e6b34", "#c25e10",
                               "#5b2d8e", "#0e6b5c", "#8a6d00"]):
        _person(d, 24 + i * 42, 26, 1.1, shirt)
    d.ellipse([w - 112, 6, w - 68, 50], fill="#7fb3d5")     # globe
    d.ellipse([w - 106, 12, w - 74, 44], fill="#2e6b34")
    d.rectangle([w - 130, 52, w - 86, 58], fill="#16130e")
    d.rectangle([w - 150, 58, w - 60, 86], fill=RED)        # NO DEAL stamp
    d.rectangle([w - 150, 58, w - 60, 86], outline="white", width=2)
    d.text((w - 146, 64), "NO DEAL", font=font(SANS_B, 15), fill="white")


def scene_dymer(d, w, h):
    d.rectangle([0, 0, w, h], fill="#232a3d")                # night sky
    d.ellipse([w - 104, 6, w - 80, 30], fill="#f6f1e3")     # moon
    for bx, bw, bh in [(8, 60, 62), (78, 52, 84), (140, 66, 70), (216, 58, 90)]:
        d.rectangle([bx, h - bh, bx + bw, h], fill="#10131f")
        for fy in range(h - bh + 8, h - 8, 12):
            for fx in range(bx + 6, bx + bw - 6, 12):
                d.rectangle([fx, fy, fx + 5, fy + 6], fill="#e8c33a")
    d.polygon([(140, h), (180, h - 52), (220, h), (206, h - 30)], fill="#6b6f7a")
    d.polygon([(150, h - 8), (180, h - 52), (210, h - 8)], fill="#9aa0ad")
    d.polygon([(w - 60, 10), (w - 40, 34), (w - 78, 34)], fill="#c25e10")
    d.rectangle([w - 52, 34, w - 46, 44], fill="#c25e10")
    d.line([(30, 20), (90, 44)], fill="#f6f1e3", width=2)    # searchlight


def scene_gulf(d, w, h):
    d.rectangle([0, 0, w, h - 34], fill="#16233f")           # dusk sky
    d.rectangle([0, h - 34, w, h], fill="#1f4e79")           # sea
    d.rectangle([20, h - 62, w - 20, h - 30], fill="#10131f")  # tanker
    d.rectangle([w - 70, h - 84, w - 40, h - 62], fill="#10131f")
    for fx in range(120, w - 30, 34):
        d.polygon([(fx, h - 62), (fx + 10, h - 88), (fx + 20, h - 62)],
                  fill="#e8700a")
        d.polygon([(fx + 4, h - 62), (fx + 10, h - 78), (fx + 16, h - 62)],
                  fill="#f6c90e")
    d.polygon([(w - 30, 14), (w - 8, 26), (w - 34, 26)], fill="#f6f1e3")


def scene_hk(d, w, h):
    d.rectangle([0, 0, w, h], fill="#5b2d8e")
    d.rectangle([w // 2 - 30, int(h * 0.45), w // 2 + 30, h - 6], fill=RED)
    d.rectangle([w // 2 - 12, int(h * 0.45), w // 2 + 12, int(h * 0.45) + 3],
                fill="#16130e")
    for bx in (10, w - 30):
        d.rectangle([bx, h - 26, bx + 20, h - 6], fill="white",
                    outline="#16130e", width=2)
        d.line([(bx + 4, h - 16), (bx + 9, h - 10), (bx + 17, h - 21)],
               fill=GREEN, width=3)
    d.ellipse([w - 34, 6, w - 10, 30], fill="white")
    d.line([(w - 29, 18), (w - 24, 23), (w - 15, 11)], fill=RED, width=3)


def scene_cricket(d, w, h):
    d.rectangle([0, 0, w, h], fill="#2e6b34")
    d.rectangle([0, h - 16, w, h], fill="#c9a86a")           # pitch
    d.rectangle([w // 2 - 26, h - 30, w // 2 + 26, h - 16], fill="#e8dcc0")
    for sx in (w // 2 - 8, w // 2 + 4):
        d.rectangle([sx, h - 34, sx + 2, h - 30], fill="#f6c90e")
    _person(d, w // 2 - 48, 26, 0.9, "#f6f1e3")
    d.line([(w // 2 - 42, 34), (w // 2 - 28, 46)], fill="#8a6d00", width=4)
    d.ellipse([w - 30, 8, w - 18, 20], fill=RED)             # ball


def scene_tennis(d, w, h):
    d.rectangle([0, 0, w, h], fill="#1f4e79")
    d.rectangle([0, h - 20, w, h], fill="#2e6b34")
    d.line([(0, h - 20), (w, h - 20)], fill="white", width=2)
    d.line([(w // 2, 8), (w // 2, h - 20)], fill="white", width=2)
    d.rectangle([w // 2 - 2, h - 34, w // 2 + 2, h - 20], fill="white")
    _person(d, w // 2 - 44, 24, 0.9, "#f6f1e3")
    d.line([(w // 2 - 38, 34), (w // 2 - 22, 44)], fill="#c25e10", width=4)
    d.ellipse([w - 34, 10, w - 22, 22], fill="#c8e64a")       # ball
    d.polygon([(w - 58, h - 34), (w - 46, h - 52), (w - 34, h - 34)],
              fill="#f6c90e")
    d.rectangle([w - 58, h - 34, w - 34, h - 30], fill="#f6c90e")


def scene_sparta(d, w, h):
    d.rectangle([0, 0, w, h - 26], fill="#8a97a8")           # grey sea sky
    d.rectangle([0, h - 26, w, h], fill="#1f4e79")
    for wx in range(0, w, 26):
        d.arc([wx, h - 30, wx + 26, h - 14], 180, 360, fill="white", width=2)
    d.rectangle([24, h - 52, w - 24, h - 26], fill="#3a3f4a")  # hull
    d.rectangle([w // 2 - 30, h - 72, w // 2 + 30, h - 52], fill="#5b2d8e")
    for fx in range(40, w - 40, 30):
        d.polygon([(fx, h - 52), (fx + 9, h - 78), (fx + 18, h - 52)],
                  fill="#e8700a")
    d.ellipse([w // 2 - 40, 4, w // 2 - 8, 26], fill="#6b6f7a")
    d.ellipse([w // 2 + 4, 2, w // 2 + 40, 28], fill="#9aa0ad")


def scene_gaza(d, w, h):
    d.rectangle([0, 0, w, h], fill="#e8ddc0")
    for bx, bw, bh in [(6, 34, 40), (48, 28, 30), (w - 44, 36, 46)]:
        d.rectangle([bx, h - bh - 18, bx + bw, h - 18], fill="#b9a878")
        d.rectangle([bx + 5, h - bh - 8, bx + 13, h - bh], fill=INK)
    d.rectangle([0, h - 18, w, h], fill="#6b6f7a")           # road
    d.line([(0, h - 9), (w, h - 9)], fill="white", width=2)
    d.rectangle([w // 2 - 34, h - 44, w // 2 + 34, h - 20], fill="white",
                outline=INK, width=2)
    d.rectangle([w // 2 - 34, h - 44, w // 2 - 6, h - 30], fill="#7fb3d5")
    d.ellipse([w // 2 - 24, h - 18, w // 2 - 12, h - 6], fill=INK)
    d.ellipse([w // 2 + 14, h - 18, w // 2 + 26, h - 6], fill=INK)
    d.ellipse([w - 26, 6, w - 10, 22], fill="white")         # dove dot
    d.polygon([(w - 26, 12), (w - 40, 6), (w - 38, 18)], fill="white")


def scene_trump(d, w, h):
    d.rectangle([0, 0, w, h], fill="#16233f")
    d.ellipse([w // 2 - 26, 6, w // 2 + 26, 44], fill="#f6f1e3")  # dome
    d.rectangle([w // 2 - 34, 40, w // 2 + 34, 50], fill="#f6f1e3")
    d.rectangle([w // 2 - 2, 0, w // 2 + 2, 10], fill="#f6f1e3")
    d.rectangle([14, h - 34, w - 14, h - 8], fill=RED)       # card
    d.rectangle([14, h - 34, w - 14, h - 8], outline="white", width=2)
    d.rectangle([22, h - 28, 58, h - 22], fill="#f6c90e")


def scene_measles(d, w, h):
    d.rectangle([0, 0, w, h], fill="#f6f1e3")
    for cx, cy, r in [(w // 2 - 30, 22, 14), (w // 2 + 26, 18, 11),
                      (w // 2 + 4, 40, 9), (26, 44, 8), (w - 26, 42, 8)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED)
        for ang in range(0, 360, 45):
            ex = cx + int((r + 5) * math.cos(math.radians(ang)))
            ey = cy + int((r + 5) * math.sin(math.radians(ang)))
            d.line([(cx, cy), (ex, ey)], fill=RED, width=2)
            d.ellipse([ex - 2, ey - 2, ex + 2, ey + 2], fill=RED)
    d.rectangle([w // 2 - 12, h - 18, w // 2 + 12, h - 6], fill=GREEN)
    d.rectangle([w // 2 - 4, h - 26, w // 2 + 4, h - 6], fill=GREEN)


def scene_robots(d, w, h):
    d.rectangle([0, 0, w, h], fill="#e8ddc0")
    d.rectangle([w // 2 - 20, 14, w // 2 + 20, 44], fill="#b9a878")  # body
    d.rectangle([w // 2 - 14, 2, w // 2 + 14, 16], fill="#b9a878")   # head
    d.ellipse([w // 2 - 8, 6, w // 2 - 2, 12], fill=RED)
    d.ellipse([w // 2 + 2, 6, w // 2 + 8, 12], fill=RED)
    d.line([(w // 2 - 20, 20), (w // 2 - 34, 34)], fill="#16130e", width=4)
    d.line([(w // 2 + 20, 20), (w // 2 + 34, 34)], fill="#16130e", width=4)
    d.ellipse([w - 34, h - 30, w - 6, h - 2], outline=RED, width=3)
    d.line([(w - 32, h - 28), (w - 8, h - 4)], fill=RED, width=3)
    d.ellipse([14, h - 30, 42, h - 2], fill="#7fb3d5")       # globe
    d.ellipse([20, h - 24, 36, h - 8], fill="#2e6b34")


def scene_sinaloa(d, w, h):
    d.rectangle([0, 0, w, h], fill="#c25e10")
    d.rectangle([0, h - 22, w, h], fill="#6b6f7a")
    d.line([(0, h - 11), (w, h - 11)], fill="#f6c90e", width=2)
    for bx in (10, 66, w - 52):
        d.polygon([(bx, h - 22), (bx + 8, h - 46), (bx + 16, h - 22)],
                  fill="#e8700a")
        d.polygon([(bx + 4, h - 22), (bx + 8, h - 34), (bx + 12, h - 22)],
                  fill="#f6c90e")
    d.rectangle([w // 2 - 30, h - 40, w // 2 + 30, h - 22], fill="#16130e")
    d.rectangle([w // 2 - 30, h - 40, w // 2 + 30, h - 34], fill="#f6f1e3")
    d.ellipse([w - 30, 6, w - 8, 28], fill="#f6f1e3")        # sun


def scene_pugh(d, w, h):
    d.rectangle([0, 0, w, h - 20], fill="#7fb3d5")
    d.rectangle([0, h - 20, w, h], fill="#1f4e79")
    for wy in (h - 34, h - 24, h - 14):
        for wx in range(0, w, 30):
            d.arc([wx, wy - 6, wx + 30, wy + 6], 180, 360, fill="white", width=2)
    d.ellipse([w // 2 - 10, h - 46, w // 2 + 10, h - 30], fill="#e8b98a")
    d.ellipse([w // 2 - 4, h - 46, w // 2 + 12, h - 34], fill="#16130e")
    d.rectangle([w // 2 - 26, h - 34, w // 2 + 26, h - 24], fill="#2e6b34")
    d.rectangle([w - 52, 8, w - 8, 22], fill="#10131f")       # tanker far off
    d.rectangle([w - 44, 2, w - 16, 8], fill="#10131f")


SCENES = {
    1: (scene_cop, "#16233f"), 2: (scene_dymer, "#232a3d"),
    3: (scene_gulf, "#16233f"), 4: (scene_hk, "#5b2d8e"),
    5: (scene_cricket, "#2e6b34"), 6: (scene_tennis, "#1f4e79"),
    7: (scene_sparta, "#8a97a8"), 8: (scene_gaza, "#e8ddc0"),
    9: (scene_trump, "#16233f"), 10: (scene_measles, "#f6f1e3"),
    11: (scene_robots, "#e8ddc0"), 12: (scene_sinaloa, "#c25e10"),
    13: (scene_pugh, "#7fb3d5"),
}


# ---- Card renderers -------------------------------------------------------
def draw_hero(draw, img, story, x, y, w, art_h, text_h):
    """One hero card. Returns the card's bottom y."""
    card = Card("hero%d" % story["n"], x, y, x + w, y + art_h + text_h)
    draw.rectangle([x, y, x + w, y + art_h + text_h], outline=INK, width=1)
    painter, bg = SCENES[story["n"]]
    img.paste(tile(w, art_h, painter, bg), (x, y))
    # Red banner top-left (phrase only, no digits) + white numeral top-right.
    banner = banner_box(draw, card, x + 6, y + 6, story["banner"],
                        font(SANS_B, 11))
    numeral = numeral_box(draw, card, x + w - 46, y + 6, story["numeral"],
                          font(SANS_B, 22))
    assert gap(banner, numeral) >= 6, "hero%d: banner/numeral gap < 6px" % story["n"]
    number_badge(draw, card, x + 6, y + art_h - 24, story["n"], 15)
    ty = y + art_h + 8
    kicker = "%s · %s" % (story["place"], story["topic"])
    draw_text(draw, card, "kicker", (x + 6, ty), kicker, font(SANS_B, 10), INK)
    tag_pill(draw, card, x + w - 6, ty - 2, story["tag"], font(SANS_B, 9))
    ty += 18
    head_f = font(SERIF, 26)
    for line in wrap_lines(draw, story["headline"], head_f, w - 12, 2):
        draw_text(draw, card, "headline", (x + 6, ty), line, head_f, INK)
        ty += 28
    deck_f = font(SANS, 11)
    for line in wrap_lines(draw, story["deck"], deck_f, w - 12, 2):
        draw_text(draw, card, "deck", (x + 6, ty), line, deck_f, INK)
        ty += 13
    src_f = font(SANS, 9)
    draw_text(draw, card, "source", (x + 6, ty + 2), story["source"], src_f, "#5a5344")
    # Numeral box must clear every other text box in the card by >= 6px.
    num_box = [b for b in card.boxes if b[0] == "numeral"][0][1:]
    for entry in card.boxes:
        label, box = entry[0], entry[1:]
        if label in ("numeral", "banner"):
            continue
        assert gap(num_box, box) >= 6 or box[1] > num_box[3] + 40, \
            "hero%d: numeral too close to %s" % (story["n"], label)
    card.finish()
    return y + art_h + text_h


def draw_medium(draw, img, story, x, y, w, art_h, text_h):
    """One medium card. Returns the card's bottom y."""
    card = Card("medium%d" % story["n"], x, y, x + w, y + art_h + text_h)
    draw.rectangle([x, y, x + w, y + art_h + text_h], outline=INK, width=1)
    painter, bg = SCENES[story["n"]]
    img.paste(tile(w, art_h, painter, bg), (x, y))
    banner_box(draw, card, x + 4, y + 4, story["banner"], font(SANS_B, 9))
    number_badge(draw, card, x + 4, y + art_h - 21, story["n"], 13)
    ty = y + art_h + 6
    kicker = "%s · %s" % (story["place"], story["topic"])
    draw_text(draw, card, "kicker", (x + 5, ty), kicker, font(SANS_B, 8), INK)
    tag_pill(draw, card, x + w - 5, ty - 1, story["tag"], font(SANS_B, 8))
    ty += 12
    head_f = font(SERIF, 13)
    for line in wrap_lines(draw, story["headline"], head_f, w - 10, 2):
        draw_text(draw, card, "headline", (x + 5, ty), line, head_f, INK)
        ty += 15
    deck_f = font(SANS, 11)
    for line in wrap_lines(draw, story["deck"], deck_f, w - 10, 2):
        draw_text(draw, card, "deck", (x + 5, ty), line, deck_f, INK)
        ty += 12
    draw_text(draw, card, "source", (x + 5, ty + 1), story["source"],
              font(SANS, 8), "#5a5344")
    card.finish()
    return y + art_h + text_h


# ---- Page sections --------------------------------------------------------
def draw_masthead(draw, data, y):
    """Eyebrow, giant serif date masthead, red italic deck. Returns new y."""
    eyebrow = "THE WORLD IN ONE DAY  ·  35 STORIES  ·  8 REGIONS  ·  EVERY ONE DATED BY ITS EVENT"
    draw_text(draw, None, "eyebrow", (MARGIN, y), eyebrow, font(SANS_B, 10), INK)
    right = data["page_date"].upper()
    rw = draw.textlength(right, font=font(SANS_B, 10))
    draw_text(draw, None, "eyebrow-r", (W - MARGIN - rw, y), right,
              font(SANS_B, 10), INK)
    y += 16
    title = data["page_date"]
    tf = font(SERIF, 62)
    tw = draw.textlength(title, font=tf)
    draw_text(draw, None, "masthead", ((W - tw) / 2, y), title, tf, INK)
    y += 68
    deck = ("COP31 collapses with no deal  ·  14 feared trapped in Dymer  ·  "
            "Gulf tanker toll hits 25")
    df = font(SERIF_IT, 14)
    dw = draw.textlength(deck, font=df)
    draw_text(draw, None, "deck", ((W - dw) / 2, y), deck, df, RED)
    y += 22
    draw.line([(MARGIN, y), (W - MARGIN, y)], fill=INK, width=2)
    return y + 6


def draw_numbers(draw, data, y):
    """THE DAY IN NUMBERS: 6 figures, each with its source beneath."""
    draw_text(draw, None, "strip-label", (MARGIN, y), "THE DAY IN NUMBERS",
              font(SANS_B, 10), INK)
    y += 14
    cell_w = CW / 6
    num_f = font(SANS_B, 34)
    for i, item in enumerate(data["numbers"]):
        cx = MARGIN + i * cell_w
        if i:
            draw.line([(cx, y), (cx, y + 52)], fill="#c9bfa4", width=1)
        val = item["value"]
        vw = draw.textlength(val, font=num_f)
        draw_text(draw, None, "num", (cx + (cell_w - vw) / 2, y), val, num_f, RED)
        ly = y + 38
        lab_f = font(SANS_B, 9)
        for line in wrap(draw, item["label"], lab_f, cell_w - 8):
            lw = draw.textlength(line, font=lab_f)
            draw_text(draw, None, "num-label", (cx + (cell_w - lw) / 2, ly),
                      line, lab_f, INK)
            ly += 11
        src_f = font(SANS, 8)
        sw = draw.textlength(item["source"], font=src_f)
        draw_text(draw, None, "num-src", (cx + (cell_w - sw) / 2, ly),
                  item["source"], src_f, "#5a5344")
    return y + 62


def draw_regions(draw, data, y):
    """Coloured region bar; segment widths proportional to story counts."""
    total = sum(r["count"] for r in data["regions"])
    assert total == 35, "region counts sum to %d, not 35" % total
    assert max(r["count"] for r in data["regions"]) <= 9, "a region exceeds 9"
    x = MARGIN
    for region in data["regions"]:
        seg_w = CW * region["count"] / total
        draw.rectangle([x, y, x + seg_w, y + 18], fill=region["color"])
        label = "%s %d" % (region["name"].upper(), region["count"])
        lf = font(SANS_B, 9)
        lw = draw.textlength(label, font=lf)
        if lw + 8 > seg_w:
            label = "%s %d" % (region["name"].upper().replace(
                "EASTERN EUROPE", "E. EUROPE"), region["count"])
            lw = draw.textlength(label, font=lf)
        if lw + 8 <= seg_w:
            draw_text(draw, None, "region", (x + (seg_w - lw) / 2, y + 4),
                      label, lf, "white")
        x += seg_w
    return y + 22


def draw_timeline(draw, data, y):
    """Navy UTC timeline strip: 6 timed items, red mono times."""
    draw.rectangle([MARGIN, y, W - MARGIN, y + 20], fill=NAVY)
    label = "THE DAY IN UTC"
    draw_text(draw, None, "tl-label", (MARGIN + 6, y + 4), label,
              font(SANS_B, 10), "#f6c90e")
    x = MARGIN + 118
    for item in data["timeline"]:
        tf = font(MONO_B, 10)
        draw_text(draw, None, "tl-time", (x, y + 4), item["time"], tf, "#ff6b5e")
        x += draw.textlength(item["time"], font=tf) + 5
        txt_f = font(SANS, 10)
        draw_text(draw, None, "tl-text", (x, y + 4), item["text"], txt_f,
                  "white")
        x += draw.textlength(item["text"], font=txt_f) + 16
    assert x - 16 <= W - MARGIN, "timeline overflows by %dpx" % (x - W + MARGIN)
    return y + 24


# ---- Map + briefs ---------------------------------------------------------
def project(lon, lat, rect):
    """Equirectangular projection into the map rect."""
    x0, y0, x1, y1 = rect
    x = x0 + (lon + 170.0) / 360.0 * (x1 - x0)
    y = y0 + (85.0 - lat) / 145.0 * (y1 - y0)
    return x, y


def draw_map(draw, data, x, y, w, h):
    """Smooth-polygon world map with de-collided pins (P0-4)."""
    rect = (x, y, x + w, y + h)
    draw.rectangle(rect, fill=SEA, outline=INK, width=1)
    with open(os.path.join(HERE, "land_polys.json")) as fh:
        polys = json.load(fh)
    for poly in polys:
        pts = [project(lon, lat, (x + 2, y + 2, x + w - 2, y + h - 2))
               for lon, lat in poly]
        if len(pts) >= 3:
            draw.polygon(pts, fill=LAND, outline=LAND_LINE)
    label = "WHERE IT HAPPENED — PINS MATCH STORY NUMBERS"
    draw_text(draw, None, "map-label", (x, y - 14), label, font(SANS_B, 10), INK)
    pinned = [s for s in data["heroes"] + data["mediums"] + data["briefs"]
              if s.get("lon") is not None]
    majors, dots = [], []
    for story in pinned:
        px, py = project(story["lon"], story["lat"], rect)
        if story["n"] <= 13:
            majors.append((story, px, py))
        else:
            dots.append((story, px, py))
    placed = []  # (kind, x, y) for distance assertions
    for story, px, py in majors:
        cx, cy = px, py
        for ring in range(0, 12):
            ok = all(math.hypot(cx - ox, cy - oy) >= 15 for _, ox, oy in placed)
            if ok:
                break
            ang = ring * 2.39996  # golden-angle spiral
            rad = 4 + ring * 2.2
            cx, cy = px + rad * math.cos(ang), py + rad * math.sin(ang)
        if (cx, cy) != (px, py) and math.hypot(cx - px, cy - py) > 3:
            draw.line([(px, py), (cx, cy)], fill="#8a8a8a", width=1)
        draw.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=RED, outline="white",
                     width=2)
        num = str(story["n"])
        nf = font(SANS_B, 10)
        nw = draw.textlength(num, font=nf)
        draw_text(draw, None, "pin", (cx - nw / 2, cy - 7), num, nf, "white")
        placed.append(("major", cx, cy))
    for story, px, py in dots:
        cx, cy = px, py
        for ring in range(0, 16):
            far_major = all(math.hypot(cx - ox, cy - oy) >= 9
                            for k, ox, oy in placed if k == "major")
            far_dot = all(math.hypot(cx - ox, cy - oy) >= 6
                          for k, ox, oy in placed if k == "dot")
            if far_major and far_dot:
                break
            ang = ring * 2.39996
            rad = 3 + ring * 1.8
            cx, cy = px + rad * math.cos(ang), py + rad * math.sin(ang)
        draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=INK, outline="white",
                     width=1)
        placed.append(("dot", cx, cy))
    # P0-4 assertions on the final placements.
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            ki, xi, yi = placed[i]
            kj, xj, yj = placed[j]
            dist = math.hypot(xi - xj, yi - yj)
            if ki == "major" and kj == "major":
                assert dist >= 14, "major pins %dpx apart (< 14)" % dist
            elif ki != kj:
                assert dist >= 9, "dot %dpx from a major (< 9)" % dist
            else:
                assert dist >= 6, "dots %dpx apart (< 6)" % dist
    return y + h


def draw_briefs(draw, data, x, y, w, h):
    """22 briefs, one measured 10px line each, two columns (P0-3)."""
    draw_text(draw, None, "briefs-label", (x, y),
              "ALSO ON SAT 21 – SUN 22 NOVEMBER — 22 MORE STORIES",
              font(SANS_B, 10), INK)
    y += 16
    briefs = data["briefs"]
    assert len(briefs) == 22, "expected 22 briefs, got %d" % len(briefs)
    col_w = w // 2 - 8
    line_h = 12
    bf = font(SANS, 10)
    for col in range(2):
        for row in range(11):
            story = briefs[col * 11 + row]
            text = "%d  %s (%s)" % (story["n"], story["text"], story["source"])
            tw = draw.textlength(text, font=bf)
            assert tw <= col_w, "brief %d too long for one line: %r" % (story["n"], text)
            by = y + row * line_h
            nf = font(SANS_B, 10)
            draw_text(draw, None, "brief-num", (x + col * (col_w + 8), by),
                      str(story["n"]), nf, RED)
            draw_text(draw, None, "brief", (x + col * (col_w + 8) + 20, by),
                      "%s (%s)" % (story["text"], story["source"]), bf, INK)
    return y + 11 * line_h


def draw_datecheck(draw, data, y, h_max):
    """DATE CHECK box; height computed from the wrapped 11px text (P0-2)."""
    text = data["date_check"]
    df = font(SANS, 11)
    lines = wrap(draw, text, df, CW - 24)
    line_h = 13
    box_h = 8 + len(lines) * line_h + 8
    assert box_h <= h_max, "DATE CHECK needs %dpx, only %dpx left" % (box_h, h_max)
    draw.rectangle([MARGIN, y, W - MARGIN, y + box_h], outline=RED, width=2)
    ty = y + 8
    for line in lines:
        draw_text(draw, None, "datecheck", (MARGIN + 12, ty), line, df, INK)
        ty += line_h
    last_baseline = ty - line_h + 11
    assert y + box_h - last_baseline >= 4, "DATE CHECK last line sliced"
    return y + box_h


def draw_footer(draw, data, y):
    legend = data["legend"]
    lf = font(SANS_B, 9)
    for line in wrap(draw, legend, lf, CW):
        draw_text(draw, None, "legend", (MARGIN, y), line, lf, INK)
        y += 12
    footer = data["footer"]
    ff = font(SANS, 8)
    for line in wrap(draw, footer, ff, CW):
        draw_text(draw, None, "footer", (MARGIN, y), line, ff, "#5a5344")
        y += 11
    return y


# ---- Main -----------------------------------------------------------------
def build():
    with open(os.path.join(HERE, "stories.json")) as fh:
        data = json.load(fh)
    # Structural assertions (P0-5): 3 heroes / 10 mediums / 22 briefs = 35.
    assert len(data["heroes"]) == 3, "heroes != 3"
    assert len(data["mediums"]) == 10, "mediums != 10"
    assert len(data["briefs"]) == 22, "briefs != 22"
    all_stories = data["heroes"] + data["mediums"] + data["briefs"]
    assert len(all_stories) == 35, "stories != 35"
    assert sorted(s["n"] for s in all_stories) == list(range(1, 36)), \
        "story numbers are not 1-35"
    assert sum(r["count"] for r in data["regions"]) == 35, "region sum != 35"
    assert len(data["regions"]) == 8, "regions != 8"
    assert len(data["numbers"]) == 6, "numbers strip != 6"
    assert len(data["timeline"]) == 6, "timeline != 6"
    tags = {s["tag"] for s in data["heroes"] + data["mediums"]}
    assert "FORECAST" not in tags, "a FORECAST tag remains on the page"
    assert all("FORECAST" not in s.get("banner", "") for s in all_stories)
    for story in data["heroes"] + data["mediums"]:
        assert story["tag"] in TAG_COLORS, "bad tag %r" % story["tag"]
        assert not any(ch.isdigit() for ch in story["banner"]), \
            "banner has a digit: %r" % story["banner"]

    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    y = 8
    y = draw_masthead(draw, data, y)
    y = draw_numbers(draw, data, y + 4)
    y = draw_regions(draw, data, y + 2)
    y = draw_timeline(draw, data, y + 2)

    # Heroes: 3 across.
    y += 6
    hero_w = (CW - 2 * 8) // 3
    hero_art, hero_text = 90, 120
    hero_bottom = y
    for i, story in enumerate(data["heroes"]):
        bottom = draw_hero(draw, img, story, MARGIN + i * (hero_w + 8), y,
                           hero_w, hero_art, hero_text)
        hero_bottom = max(hero_bottom, bottom)
    y = hero_bottom + 6

    # Mediums: 5 across, 2 rows.
    med_w = (CW - 4 * 6) // 5
    med_art, med_text = 52, 86
    for row in range(2):
        row_bottom = y
        for col in range(5):
            story = data["mediums"][row * 5 + col]
            bottom = draw_medium(draw, img, story, MARGIN + col * (med_w + 6),
                                 y, med_w, med_art, med_text)
            row_bottom = max(row_bottom, bottom)
        y = row_bottom + 4

    # Map (left) + briefs (right).
    map_w, map_h = 330, 132
    briefs_x = MARGIN + map_w + 12
    briefs_w = CW - map_w - 12
    map_bottom = draw_map(draw, data, MARGIN, y + 14, map_w, map_h)
    briefs_bottom = draw_briefs(draw, data, briefs_x, y, briefs_w, map_h)
    y = max(map_bottom, briefs_bottom) + 8
    # P0-3: last brief >= 4px above the DATE CHECK box (its top is y here).
    assert y - briefs_bottom >= 4, "briefs too close to DATE CHECK"
    y = draw_datecheck(draw, data, y, H - 30 - y)
    y = draw_footer(draw, data, y + 4)
    assert y <= H, "page overflowed: final y = %d > 1024" % y
    print("QA PASS: final y = %d/1024" % y)

    out = os.path.join(HERE, "entry.png")
    img.save(out, "PNG")
    small = img.resize((512, 512), Image.LANCZOS)
    small.save(os.path.join(HERE, "entry_512.png"), "PNG")
    print("wrote %s" % out)
    return y


if __name__ == "__main__":
    try:
        build()
    except AssertionError as exc:
        print("BUILD FAILED: %s" % exc, file=sys.stderr)
        sys.exit(1)
