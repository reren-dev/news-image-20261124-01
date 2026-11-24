#!/usr/bin/env python3
"""Sum up 24 November 2026's world news in one image.

A front-page poster drawn entirely by code (Python 3.13 standard library
only, no network, no fonts, no image files): a 1024x1024 PNG written to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

Design: a newspaper front page.
  - Masthead: TUESDAY 24 NOVEMBER 2026.
  - Hero: the day's biggest breaking story -- a suspected North Korean
    aircraft breaches South Korean airspace near Ulleung Island and the
    islanders are briefly ordered to shelter.
  - Three story cards: Gaza, the World Chess Championship, and the
    Thailand-China-Myanmar river talks.
  - A schematic world map with the five story locations marked.
  - An "also today" strip: Thanksgiving travel week opens in the USA.
  - A DATE CHECK panel naming the big near-miss stories that were left
    out because they happened on another day -- the image only carries
    stories verified against sources dated 24 November 2026.

Every story was verified against a named source at build time:
  AP / Reuters -- Korea airspace breach; Reuters -- Gaza strike;
  FIDE / Chess.com -- World Chess Championship Game 1; Reuters /
  The Diplomat -- Thailand river talks; AAA -- Thanksgiving travel.

Deterministic: the same input always writes the same bytes.
"""

import binascii
import hashlib
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 234)   # warm newsprint
INK = (20, 20, 20)
SOFT_INK = (60, 60, 60)
RED = (193, 39, 45)
NAVY = (14, 30, 51)       # hero night sky, top
NAVY2 = (29, 58, 95)      # hero night sky, bottom
SEA = (8, 20, 36)
GOLD = (232, 163, 23)
TEAL = (14, 124, 123)
SLATE = (52, 68, 88)
WHITE = (255, 255, 255)
CREAM = (255, 250, 235)
LIGHT = (226, 232, 240)   # map land
MAP_BG = (214, 226, 236)
MAP_LAND = (168, 184, 198)
MAP_LINE = (140, 158, 176)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 characters ('#' = ink, '.' = empty).
# Only uppercase is stored; text is upper-cased before drawing.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10011", "10101", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "10100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "00100", "00100", "00100"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    '.': ("00000", "00000", "00000", "00000", "00000", "00000", "01100"),
    ',': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "'": ("00100", "00100", "00100", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "00100", "01000", "10000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '&': ("01110", "10001", "10100", "01000", "10101", "10010", "01101"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    # bullet and em dash
    '\u2022': ("00000", "00000", "01110", "01110", "01110", "00000", "00000"),
    '\u2014': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def glyph_width(scale):
    return 5 * scale


def text_width(text, scale):
    text = text.upper()
    w = 0
    for ch in text:
        w += 5 * scale + scale
    return w - scale if w else 0


def wrap_text(text, max_chars):
    """Greedy word wrap on whole words; returns a list of lines."""
    words = text.split(' ')
    lines = []
    cur = ''
    for word in words:
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= max_chars:
            cur += ' ' + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        r, g, b = bg
        for i in range(0, len(self.buf), 3):
            self.buf[i] = r
            self.buf[i + 1] = g
            self.buf[i + 2] = b

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px(xx, yy, color)

    def rect_outline(self, x, y, w, h, color, t=1):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=False):
        if fill:
            for yy in range(cy - r, cy + r + 1):
                dx = int((r * r - (yy - cy) * (yy - cy)) ** 0.5)
                self.hline(cx - dx, yy, 2 * dx + 1, color)
            return
        x, y, d = r, 0, 1 - r
        while x >= y:
            for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                self.px(cx + sx, cy + sy, color)
            y += 1
            if d <= 0:
                d += 2 * y + 1
            else:
                x -= 1
                d += 2 * (y - x) + 1

    def polyfill(self, pts, color):
        """Scanline fill of a simple polygon given as [(x, y), ...]."""
        if not pts:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                    xs.append(x)
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.hline(int(xs[j]), y, max(1, int(xs[j + 1]) - int(xs[j])), color)

    def vgrad(self, x, y, w, h, top, bottom):
        for yy in range(h):
            t = yy / max(1, h - 1)
            c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            self.hline(x, y + yy, w, c)

    def text(self, x, y, s, scale, color):
        """Draw text left-aligned at (x, y); returns pixel width."""
        s = s.upper()
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[' '])
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits[col] == '1':
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx - x - scale

    def text_center(self, cx, y, s, scale, color):
        w = text_width(s, scale)
        return self.text(cx - w // 2, y, s, scale, color)

    def text_block(self, x, y, lines, scale, color, leading=None):
        """Draw a list of lines; returns y after the last line."""
        if leading is None:
            leading = 9 * scale
        for ln in lines:
            self.text(x, y, ln, scale, color)
            y += leading
        return y


# ---------------------------------------------------------------- helpers
def lcg(seed):
    """Deterministic pseudo-random generator (fixed seed -> fixed stars)."""
    state = seed

    def nxt():
        nonlocal state
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        return state
    return nxt


# ---------------------------------------------------------------- illustrations
def draw_jet(cv, x, y, s, color, stripe):
    """A jet silhouette in profile, nose to the right, scaled by s."""
    body = [
        (x, y + 4 * s), (x + 8 * s, y + 3 * s), (x + 20 * s, y),
        (x + 34 * s, y + 2 * s), (x + 38 * s, y + 3 * s),
        (x + 30 * s, y + 5 * s), (x + 16 * s, y + 6 * s),
        (x + 10 * s, y + 8 * s), (x + 4 * s, y + 7 * s),
    ]
    cv.polyfill(body, color)
    # swept wing
    wing = [(x + 14 * s, y + 5 * s), (x + 22 * s, y + 5 * s),
            (x + 26 * s, y + 12 * s), (x + 18 * s, y + 12 * s)]
    cv.polyfill(wing, color)
    # tail fin
    tail = [(x + 2 * s, y + 4 * s), (x + 6 * s, y + 4 * s),
            (x + 8 * s, y - 3 * s), (x + 4 * s, y - 3 * s)]
    cv.polyfill(tail, color)
    # red tail stripe + cockpit
    cv.rect(x + 3 * s, y + 4 * s, 5 * s, s, stripe)
    cv.polyfill([(x + 26 * s, y + 2 * s), (x + 30 * s, y + 2 * s),
                 (x + 29 * s, y + 4 * s), (x + 26 * s, y + 4 * s)],
                (180, 220, 240))


def draw_island(cv, x, y, w, h, color):
    """A small island silhouette with a lighthouse and a light beam."""
    pts = [(x, y + h), (x + int(w * 0.12), y + int(h * 0.45)),
           (x + int(w * 0.30), y + int(h * 0.30)),
           (x + int(w * 0.45), y + int(h * 0.10)),
           (x + int(w * 0.58), y + int(h * 0.35)),
           (x + int(w * 0.78), y + int(h * 0.42)),
           (x + w, y + h)]
    cv.polyfill(pts, color)
    lx = x + int(w * 0.45)
    ly = y + int(h * 0.10)
    # lighthouse tower
    cv.rect(lx - 3, ly - 26, 6, 26, WHITE)
    cv.rect(lx - 5, ly - 30, 10, 4, RED)
    cv.circle(lx, ly - 28, 3, GOLD, fill=True)
    # beam to the right, fading in three steps
    for i, c in enumerate(((232, 163, 23), (190, 140, 60), (140, 110, 50))):
        cv.polyfill([(lx + 4, ly - 29 + i), (lx + 90, ly - 44 + i * 3),
                     (lx + 90, ly - 16 - i * 2), (lx + 4, ly - 27 + i)], c)


def draw_chess_board(cv, x, y, cell):
    """A 4x4 chess board with a gold king and a white pawn."""
    for r in range(4):
        for c in range(4):
            col = CREAM if (r + c) % 2 == 0 else INK
            cv.rect(x + c * cell, y + r * cell, cell, cell, col)
    cv.rect_outline(x, y, 4 * cell, 4 * cell, GOLD, 2)
    # gold king on d4
    kx = x + 2 * cell + cell // 2
    ky = y + 2 * cell + cell // 2
    cv.circle(kx, ky, cell // 3, GOLD, fill=True)
    cv.rect(kx - 1, ky - cell // 2, 2, cell // 3, GOLD)
    cv.rect(kx - cell // 4, ky - cell // 2, cell // 2, 2, GOLD)
    # white pawn on b2
    px = x + cell + cell // 2
    py = y + cell + cell // 2
    cv.circle(px, py, cell // 4, WHITE, fill=True)
    cv.rect(px - cell // 4, py + cell // 6, cell // 2, cell // 5, WHITE)


def draw_river(cv, x, y, w, h, color):
    """Three wavy river lines."""
    import math
    for k, off in enumerate((0, 14, 28)):
        prev = None
        for xx in range(w):
            yy = y + off + int(6 * math.sin((xx + k * 40) * 0.045))
            if prev is not None:
                cv.line(prev[0], prev[1], x + xx, yy, color)
            prev = (x + xx, yy)
    # a factory / mine silhouette on the bank
    cv.rect(x + w - 52, y + h - 34, 44, 34, SLATE)
    cv.rect(x + w - 46, y + h - 52, 6, 18, SLATE)
    cv.rect(x + w - 34, y + h - 46, 6, 12, SLATE)
    cv.rect(x + w - 52, y + h - 30, 44, 3, RED)


def draw_plane(cv, x, y, s, color):
    """A small passenger-plane silhouette, nose to the right."""
    body = [(x, y + 3 * s), (x + 10 * s, y), (x + 26 * s, y + 2 * s),
            (x + 28 * s, y + 3 * s), (x + 20 * s, y + 5 * s),
            (x + 8 * s, y + 6 * s)]
    cv.polyfill(body, color)
    wing = [(x + 10 * s, y + 4 * s), (x + 16 * s, y + 4 * s),
            (x + 19 * s, y + 9 * s), (x + 13 * s, y + 9 * s)]
    cv.polyfill(wing, color)
    tail = [(x + 1 * s, y + 3 * s), (x + 4 * s, y + 3 * s),
            (x + 6 * s, y - 2 * s), (x + 3 * s, y - 2 * s)]
    cv.polyfill(tail, color)


# Simplified continent outlines (lon, lat) for the schematic map.
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 80),
     (-80, 73), (-75, 62), (-70, 45), (-75, 35), (-80, 26), (-85, 20),
     (-90, 15), (-95, 18), (-105, 22), (-115, 30), (-125, 40), (-125, 50),
     (-140, 60), (-155, 58), (-165, 60)],
    # South America
    [(-80, 10), (-75, 0), (-70, -10), (-60, -20), (-50, -30), (-40, -20),
     (-35, -8), (-45, 0), (-55, 5), (-65, 10), (-75, 12)],
    # Europe
    [(-10, 36), (-5, 44), (0, 50), (5, 55), (10, 58), (20, 60), (25, 65),
     (30, 70), (40, 68), (45, 60), (40, 50), (30, 45), (25, 40), (20, 38),
     (12, 44), (5, 43), (-2, 37)],
    # Africa
    [(-10, 35), (0, 35), (10, 37), (20, 32), (30, 31), (35, 28), (40, 15),
     (45, 10), (50, 5), (45, -5), (40, -15), (35, -25), (30, -35),
     (20, -35), (12, -18), (10, -5), (5, 5), (-5, 5), (-12, 15), (-17, 20)],
    # Asia
    [(40, 70), (60, 72), (80, 73), (100, 76), (120, 73), (140, 72),
     (160, 70), (170, 66), (160, 60), (145, 55), (140, 45), (130, 40),
     (127, 35), (122, 30), (120, 25), (110, 20), (105, 10), (100, 8),
     (95, 15), (90, 22), (85, 20), (80, 10), (75, 8), (70, 20), (65, 25),
     (60, 25), (55, 28), (50, 30), (45, 35), (42, 40), (40, 45), (38, 55),
     (40, 65)],
    # Australia
    [(113, -22), (120, -15), (130, -12), (135, -12), (142, -11), (150, -20),
     (153, -27), (150, -37), (140, -38), (130, -32), (120, -34), (114, -30)],
]

# Story locations: (lon, lat, label, label_dx, label_dy)
MAP_POINTS = [
    (130.9, 37.5, "ULLEUNG", -64, -26),
    (34.3, 31.3, "KHAN YOUNIS", -58, 16),
    (6.1, 46.2, "GENEVA", -58, -24),
    (100.5, 13.8, "BANGKOK", -30, 22),
    (-87.6, 41.9, "CHICAGO", -78, -22),
]


def draw_map(cv, x, y, w, h):
    cv.rect(x, y, w, h, MAP_BG)
    # graticule
    for gx in range(1, 6):
        cv.vline(x + w * gx // 6, y, h, (200, 214, 226))
    for gy in range(1, 3):
        cv.hline(x, y + h * gy // 3, w, (200, 214, 226))
    # continents
    for cont in CONTINENTS:
        pts = [(x + int((lon + 180) / 360 * w),
                y + int((90 - lat) / 150 * h)) for lon, lat in cont]
        cv.polyfill(pts, MAP_LAND)
        for i in range(len(pts)):
            cv.line(pts[i][0], pts[i][1], pts[(i + 1) % len(pts)][0],
                    pts[(i + 1) % len(pts)][1], MAP_LINE)
    # story dots
    for lon, lat, label, dx, dy in MAP_POINTS:
        px = x + int((lon + 180) / 360 * w)
        py = y + int((90 - lat) / 150 * h)
        cv.circle(px, py, 9, RED)
        cv.circle(px, py, 6, WHITE)
        cv.circle(px, py, 3, RED, fill=True)
        cv.text(px + dx, py + dy, label, 2, INK)


# ---------------------------------------------------------------- the page
def build():
    cv = Canvas(W, H, PAPER)

    # ---- masthead ------------------------------------------------------
    cv.text_center(W // 2, 24, "TUESDAY 24 NOVEMBER 2026", 5, INK)
    cv.hline(40, 70, 944, INK, 3)
    cv.text(40, 80, "THE WORLD IN ONE PICTURE", 3, RED)
    cv.text(984 - text_width("ONE DAY \u2022 FIVE STORIES", 3), 80,
            "ONE DAY \u2022 FIVE STORIES", 3, SOFT_INK)

    # ---- hero: Korea airspace breach -----------------------------------
    hx, hy, hw, hh = 40, 110, 944, 312
    cv.vgrad(hx, hy, hw, hh, NAVY, NAVY2)
    # stars (fixed seed -> identical every run)
    rnd = lcg(20261124)
    for _ in range(70):
        sx = hx + 12 + rnd() % (hw - 24)
        sy = hy + 10 + rnd() % 150
        r = rnd() % 3
        cv.rect(sx, sy, 2 if r else 1, 2 if r else 1, (220, 230, 245))
    # moon
    cv.circle(hx + hw - 90, hy + 48, 26, (235, 230, 205), fill=True)
    cv.circle(hx + hw - 98, hy + 40, 6, (210, 204, 178), fill=True)
    cv.circle(hx + hw - 80, hy + 58, 4, (210, 204, 178), fill=True)
    # sea strip at the bottom of the hero
    cv.rect(hx, hy + hh - 64, hw, 64, SEA)
    for i in range(3):
        yy = hy + hh - 54 + i * 12
        for xx in range(hx + 700, hx + hw - 8, 46):
            cv.hline(xx, yy, 26, (40, 70, 105), 2)
    # island with lighthouse, lower left
    draw_island(cv, hx + 36, hy + hh - 118, 240, 56, (6, 14, 26))
    # radar rings around the breach point
    bx, by = hx + 640, hy + 120
    for r, col in ((86, (193, 39, 45)), (60, (220, 90, 90)),
                   (36, (240, 150, 150))):
        cv.circle(bx, by, r, col)
    cv.circle(bx, by, 5, RED, fill=True)
    cv.text(bx - 52, by + 96, "BREACH POINT", 2, (240, 150, 150))
    # jet with contrail
    for i in range(6):
        cv.line(hx + 300 + i * 8, hy + 92 + i, hx + 330 + i * 8,
                hy + 92 + i, (150, 170, 200))
    draw_jet(cv, hx + 520, hy + 70, 2, WHITE, RED)
    # alert banner
    cv.rect(hx, hy, hw, 30, RED)
    cv.text_center(W // 2, hy + 8, "AIRSPACE BREACH \u2022 SHELTER ORDER",
                   2, WHITE)
    # headline over the sky
    cv.text(hx + 28, hy + 44, "JET SCARE", 6, WHITE)
    cv.text(hx + 28, hy + 92, "OVER ULLEUNG", 6, WHITE)
    # sub-lines on the sea strip, clear of the waves (waves are right only)
    cv.text(hx + 28, hy + hh - 56,
            "SUSPECTED NORTH KOREAN PLANE ENTERS SOUTH", 2, CREAM)
    cv.text(hx + 28, hy + hh - 36,
            "KOREA'S AIRSPACE \u2014 ISLANDERS TOLD TO SHELTER", 2, CREAM)

    # ---- three story cards ---------------------------------------------
    cards = [
        ("GAZA", RED, "STRIKE IN KHAN YOUNIS",
         "ISRAELI STRIKE KILLS 3 NEAR A POLICE POST IN KHAN YOUNIS; "
         "5 WOUNDED.",
         "REUTERS"),
        ("CHESS", GOLD, "GAME 1 IN GENEVA",
         "GUKESH DEFENDS CROWN VS SINDAROV IN THE YOUNGEST TITLE MATCH "
         "EVER. BOTH 20.",
         "FIDE / CHESS.COM"),
        ("RIVERS", TEAL, "TALKS OPEN",
         "THAILAND, CHINA AND MYANMAR OPEN TALKS ON TOXIC MINING "
         "POLLUTION IN THAI RIVERS.",
         "REUTERS / THE DIPLOMAT"),
    ]
    cw, gap, cy, ch = 306, 13, 430, 228
    for i, (place, accent, title, body, src) in enumerate(cards):
        x = 40 + i * (cw + gap)
        cv.rect(x, cy, cw, ch, WHITE)
        cv.rect_outline(x, cy, cw, ch, INK, 2)
        cv.rect(x, cy, cw, 8, accent)
        cv.text(x + 14, cy + 18, place, 3, accent)
        cv.text(x + 14, cy + 44, title, 2, INK)
        cv.hline(x + 14, cy + 70, cw - 28, (200, 200, 190), 2)
        if place == "GAZA":
            # blast: concentric rings + starburst
            gx, gy = x + cw - 52, cy + 102
            for r, col in ((24, RED), (16, (230, 110, 90)),
                           (8, GOLD)):
                cv.circle(gx, gy, r, col)
            cv.circle(gx, gy, 3, INK, fill=True)
        elif place == "CHESS":
            draw_chess_board(cv, x + cw - 76, cy + 80, 12)
        else:
            draw_river(cv, x + 14, cy + 82, cw - 28, 44, TEAL)
        lines = wrap_text(body, 22)
        cv.text_block(x + 14, cy + 138, lines, 2, INK, leading=17)
        cv.text(x + 14, cy + ch - 20, "SOURCE: " + src, 1, SOFT_INK)

    # ---- map band -------------------------------------------------------
    my = 668
    cv.text(40, my, "WHERE IT HAPPENED", 3, INK)
    cv.text(984 - text_width("FIVE STORIES \u2022 FIVE REGIONS", 2), my + 4,
            "FIVE STORIES \u2022 FIVE REGIONS", 2, SOFT_INK)
    draw_map(cv, 40, my + 28, 944, 124)

    # ---- also today ------------------------------------------------------
    ay = 828
    cv.rect(40, ay, 944, 54, NAVY)
    draw_plane(cv, 62, ay + 22, 2, WHITE)
    cv.text(120, ay + 10, "ALSO TODAY \u2014 USA", 3, GOLD)
    cv.text(120, ay + 34,
            "THANKSGIVING TRAVEL WEEK OPENS \u2014 81.5M ON THE MOVE, "
            "5.96M FLYING (AAA)", 2, WHITE)

    # ---- date check + sources -------------------------------------------
    dy = 892
    cv.rect(40, dy, 944, 116, INK)
    cv.text(56, dy + 12, "DATE CHECK \u2014 WHAT WE LEFT OUT (WRONG DAY):",
            2, GOLD)
    cv.text(56, dy + 34,
            "INDONESIA FIRE (21 NOV) \u2022 NVIDIA HUANG (23 NOV)", 2, WHITE)
    cv.text(56, dy + 52,
            "EU 22ND SANCTIONS (23 NOV) \u2022 KILLER-ROBOT TALKS (21 NOV)",
            2, WHITE)
    cv.text(56, dy + 70,
            "SPARTA II DOCKS (23 NOV) \u2022 KYIV STRIKES (22-23 NOV)",
            2, WHITE)
    cv.hline(56, dy + 90, 944 - 32, (90, 90, 90), 1)
    cv.text(56, dy + 97,
            "SOURCES: AP \u2022 REUTERS \u2022 FIDE \u2022 CHESS.COM \u2022 "
            "THE DIPLOMAT \u2022 AAA", 1, (180, 180, 180))

    # ---- footer ----------------------------------------------------------
    cv.text_center(W // 2, 1013,
                   "DRAWN BY CODE \u2022 NO PHOTOGRAPHS \u2022 EVERY STORY "
                   "CHECKED AGAINST A SOURCE DATED 24 NOVEMBER 2026",
                   1, SOFT_INK)
    return cv


# ---------------------------------------------------------------- PNG output
def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.buf[y * cv.w * 3:(y + 1) * cv.w * 3]

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    cv = build()
    n = write_png(cv, path)
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print("WROTE %s %d bytes sha256=%s" % (path, n, digest))


if __name__ == "__main__":
    main()
