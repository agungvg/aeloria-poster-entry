#!/usr/bin/env python3
"""Render AELORIA — The Land Above the Clouds (v5, reference rebuild).

A vintage travel poster for a place that does not exist, rebuilt to
Lyso's reference: one great floating island with a rocky, cracked
cliff and a lighthouse town, a long ladder down to a smaller islet,
a big detailed airship arriving at golden hour, a low sun with long
rays, and a cloud sea with little islets and rooftops peeking out.

Everything is drawn from scratch with Pillow: gradient sky, rocky
cliff (strata, cracks, shading, bushes), houses with wavy chimney
smoke, a panelled airship with propeller, and a three-layer cloud
sea. Deterministic: fixed seeds, no clock, no network. Writes
entry.png (1024x1024, < 1 MiB).
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024

# palette
SKY_TOP = (208, 100, 46)
SKY_MID = (233, 148, 76)
SKY_LOW = (249, 206, 128)
CREAM = (252, 244, 224)
CLOUD_WHITE = (253, 248, 236)
CLOUD_SHADE = (214, 196, 164)
CLOUD_DEEP = (188, 168, 138)
TEAL = (46, 110, 106)
GREEN = (106, 148, 84)
GREEN_DARK = (84, 124, 66)
STONE = (201, 170, 128)
STONE_MID = (186, 152, 108)
STONE_DARK = (163, 130, 88)
STONE_DEEP = (140, 110, 72)
ROOF_A = (198, 86, 54)
ROOF_B = (172, 62, 48)
ROOF_C = (214, 128, 60)
INK = (64, 46, 30)
LIT = (255, 214, 130)
WATER = (214, 232, 226)

SERIF_BLACK = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf"


def vgrad(size, stops):
    """Vertical gradient through (pos, rgb) stops."""
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                col = tuple(round(c0[k] + (c1[k] - c0[k]) * f) for k in range(3))
                break
        else:
            col = stops[-1][1]
        for x in range(w):
            px[x, y] = col
    return img


def glow(img, cx, cy, r, colour, peak):
    """Soft radial glow: concentric translucent discs, brightest at centre."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = 22
    for i in range(steps, 0, -1):
        rr = r * i / steps
        a = int(peak * (1 - i / steps) ** 2)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                  fill=colour + (a,))
    layer = layer.filter(ImageFilter.GaussianBlur(6))
    img.paste(layer, (0, 0), layer)


def bird(d, x, y, s):
    """Two-stroke gull."""
    d.arc([x - s, y - s * 0.6, x, y + s * 0.6], 200, 340, fill=INK, width=2)
    d.arc([x, y - s * 0.6, x + s, y + s * 0.6], 200, 340, fill=INK, width=2)


def smoke(d, x, y, height=42):
    """A wavy chimney smoke curl rising from (x, y)."""
    for i in range(6):
        yy = y - i * (height / 6)
        xx = x + 7 * math.sin(i * 0.9)
        r = 5.5 - i * 0.45
        a = 150 - i * 20
        d.ellipse([xx - r, yy - r, xx + r, yy + r],
                  fill=(235, 225, 210, a))


def house(d, x, y, w, h, roof=ROOF_A, lit=True, chimney=False):
    """A whitewashed house: body, roof, door, windows, optional chimney."""
    d.rectangle([x, y, x + w, y + h], fill=(218, 204, 178))
    d.rectangle([x, y, x + w, y + 3], fill=(200, 184, 156))
    d.polygon([(x - 3, y), (x + w / 2, y - h * 0.45), (x + w + 3, y)],
              fill=roof)
    d.rectangle([x + w / 2 - 3, y + h - 11, x + w / 2 + 3, y + h],
                fill=(90, 60, 40))
    for wx in (x + 6, x + w - 12):
        d.rectangle([wx, y + 7, wx + 6, y + 13],
                    fill=LIT if lit else (120, 130, 130))
    if chimney:
        d.rectangle([x + w - 12, y - h * 0.45 - 6, x + w - 7, y - h * 0.45 + 2],
                    fill=(140, 100, 80))
        smoke(d, x + w - 9, y - h * 0.45 - 8)


def cypress(d, x, y, h):
    d.polygon([(x - 5, y), (x, y - h), (x + 5, y)], fill=TEAL)
    d.rectangle([x - 1, y, x + 1, y + 4], fill=(90, 60, 40))


def round_tree(d, x, y, r):
    d.rectangle([x - 2, y, x + 2, y + 8], fill=(90, 60, 40))
    d.ellipse([x - r, y - r * 1.4, x + r, y + r * 0.4], fill=GREEN_DARK)
    d.ellipse([x - r * 0.6, y - r * 1.8, x + r * 0.5, y - r * 0.3],
              fill=GREEN)


def bush(d, x, y, r=9):
    d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=GREEN_DARK)
    d.ellipse([x - r * 0.6, y - r, x + r * 0.4, y + r * 0.2], fill=GREEN)


def cloud(d, x, y, s, shade=True):
    """One billow: a cluster of overlapping puffs with a shadow crescent."""
    puffs = [(-1.15, 0.28, 0.48), (-0.9, 0.15, 0.55), (-0.45, -0.15, 0.7),
             (0.0, -0.3, 0.8), (0.45, -0.12, 0.7), (0.9, 0.15, 0.55),
             (1.15, 0.28, 0.48), (0.0, 0.25, 0.75)]
    if shade:
        for dx, dy, r in puffs:
            d.ellipse([x + dx * s - r * s, y + dy * s + 12 - r * s * 0.60,
                       x + dx * s + r * s, y + dy * s + 12 + r * s * 0.60],
                      fill=CLOUD_SHADE)
    for dx, dy, r in puffs:
        d.ellipse([x + dx * s - r * s, y + dy * s - r * s * 0.60,
                   x + dx * s + r * s, y + dy * s + r * s * 0.60],
                  fill=CLOUD_WHITE)


def draw():
    rng = random.Random(11)
    img = vgrad((W, H), [(0.0, SKY_TOP), (0.45, SKY_MID), (1.0, SKY_LOW)])
    img = img.convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    # --- high wispy clouds (clear of the type) ---
    for x, y, ln in [(60, 350, 120), (850, 440, 130), (60, 530, 120)]:
        d.ellipse([x, y, x + ln, y + 12], fill=(255, 230, 190, 70))
        d.ellipse([x + 20, y + 14, x + ln - 10, y + 24],
                  fill=(255, 230, 190, 50))

    # --- type: stone 3D name with moss, gold tagline ---
    f_name = ImageFont.truetype(SERIF_BLACK, 168)
    f_tag = ImageFont.truetype(SERIF_BOLD, 32)
    # drop shadow
    d.text((518, 104), "AELORIA", font=f_name, fill=(120, 80, 40, 130),
           anchor="ma")
    # stone face with a dark carved edge
    d.text((512, 96), "AELORIA", font=f_name, fill=(228, 216, 190),
           anchor="ma", stroke_width=2, stroke_fill=(150, 135, 110))
    # moss speckles on the letters (seeded, inside the glyph mask)
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.text((512, 96), "AELORIA", font=f_name, fill=255, anchor="ma")
    moss_rng = random.Random(31)
    moss = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mod = ImageDraw.Draw(moss)
    for _ in range(260):
        mx = moss_rng.randint(100, 924)
        my = moss_rng.randint(20, 200)
        if mask.getpixel((mx, my)):
            r = moss_rng.randint(2, 4)
            mod.ellipse([mx - r, my - r, mx + r, my + r],
                        fill=(96, 122, 70, moss_rng.randint(90, 170)))
    img.paste(moss, (0, 0), moss)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((512, 270), "THE LAND ABOVE THE CLOUDS", font=f_tag,
           fill=(232, 190, 110), anchor="ma")
    d.polygon([(152, 288), (164, 278), (176, 288), (164, 298)], fill=CREAM)
    d.polygon([(872, 288), (860, 278), (848, 288), (860, 298)], fill=CREAM)

    # --- birds ---
    for bx, by, bs in [(140, 330, 13), (180, 310, 10), (210, 330, 9),
                       (240, 350, 11), (880, 190, 10), (906, 178, 12),
                       (932, 196, 9)]:
        bird(d, bx, by, bs)

    # --- embers drifting in the sky ---
    emb = random.Random(23)
    for _ in range(46):
        ex = emb.randint(40, 984)
        ey = emb.randint(300, 700)
        er = emb.randint(1, 3)
        d.ellipse([ex - er, ey - er, ex + er, ey + er],
                  fill=(255, 210, 130, emb.randint(110, 200)))

    # --- low sun with long rays fanning up-left ---
    glow(img, 828, 758, 200, (255, 214, 130), 190)
    d = ImageDraw.Draw(img, "RGBA")
    for ang in range(185, 355, 12):
        a = math.radians(ang)
        x0, y0 = 828 + 97 * math.cos(a), 758 + 97 * math.sin(a)
        x1, y1 = 828 + 250 * math.cos(a), 758 + 250 * math.sin(a)
        d.line([x0, y0, x1, y1], fill=(255, 226, 150, 85), width=3)
    d.ellipse([828 - 85, 758 - 85, 828 + 85, 758 + 85], fill=(250, 200, 100))
    d.ellipse([828 - 85, 758 - 85, 828 + 85, 758 + 85],
              outline=(255, 236, 170), width=3)

    # --- the great floating island: rocky cliff ---
    # island outline: top (300,470)-(760,470), tip (530,782)
    def xl(y):
        return 300 + (y - 470) * (230 / 312)

    def xr(y):
        return 760 - (y - 470) * (230 / 312)

    d.polygon([(300, 470), (760, 470), (700, 620), (620, 700), (530, 782),
               (404, 700), (340, 620)], fill=STONE)
    # strata bands
    for y0, y1, col in [(505, 545, STONE_MID), (585, 625, STONE_MID),
                        (655, 695, STONE_DARK), (715, 752, STONE_DEEP)]:
        d.polygon([(xl(y0), y0), (xr(y0), y0), (xr(y1), y1), (xl(y1), y1)],
                  fill=col)
    # right-side shade
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shd = ImageDraw.Draw(shade)
    shd.polygon([(640, 470), (760, 470), (700, 620), (620, 700), (530, 782),
                 (580, 700), (640, 600)], fill=(120, 92, 60, 55))
    shade = shade.filter(ImageFilter.GaussianBlur(10))
    img.paste(shade, (0, 0), shade)
    d = ImageDraw.Draw(img, "RGBA")
    # wavy vertical cracks
    for _ in range(11):
        cx = rng.randint(350, 700)
        cy = rng.randint(480, 560)
        pts = [(cx, cy)]
        for i in range(1, 6):
            pts.append((cx + rng.randint(-14, 14), cy + i * rng.randint(12, 20)))
        d.line(pts, fill=STONE_DEEP, width=3)
    # small rock facets
    for _ in range(14):
        fx = rng.randint(350, 700)
        fy = rng.randint(490, 740)
        d.line([fx, fy, fx + rng.randint(10, 26), fy + rng.randint(4, 12)],
               fill=STONE_DARK, width=2)
    # bushes tucked on ledges
    for bx, by in [(352, 545), (700, 545), (392, 625), (668, 625),
                   (452, 695), (600, 695), (520, 752)]:
        bush(d, bx, by, 10)
    # roots hanging from the island's underside
    root_rng = random.Random(17)
    for _ in range(14):
        rx0 = root_rng.randint(360, 700)
        ry0 = root_rng.randint(690, 760)
        pts = [(rx0, ry0)]
        for i in range(1, 5):
            pts.append((rx0 + root_rng.randint(-12, 12),
                        ry0 + i * root_rng.randint(10, 18)))
        d.line(pts, fill=(96, 70, 48), width=2)
    # vines hanging off the grassy rim
    for vx in (360, 430, 520, 610, 700):
        d.line([vx, 488, vx + 4, 488 + 26], fill=GREEN_DARK, width=2)
        d.ellipse([vx - 2, 510, vx + 8, 518], fill=GREEN_DARK)
    # grassy top with tufts
    d.polygon([(300, 470), (760, 470), (752, 488), (308, 488)], fill=GREEN)
    d.line([300, 470, 760, 470], fill=GREEN_DARK, width=3)
    for tx in range(320, 750, 34):
        d.polygon([(tx, 470), (tx + 4, 458), (tx + 8, 470)], fill=GREEN_DARK)
        d.polygon([(tx + 10, 470), (tx + 14, 460), (tx + 18, 470)],
                  fill=GREEN)

    # --- waterfall spilling off the right edge into the clouds ---
    fall = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fall)
    for fx, fy, fr in [(700, 520, 15), (692, 560, 16), (682, 602, 17),
                       (672, 644, 18), (664, 686, 19), (656, 726, 20),
                       (650, 754, 21)]:
        fd.ellipse([fx - fr, fy - fr, fx + fr, fy + fr],
                   fill=WATER + (200,))
    fd.polygon([(700, 512), (716, 512), (668, 756), (640, 756)],
               fill=WATER + (160,))
    fall = fall.filter(ImageFilter.GaussianBlur(5))
    img.paste(fall, (0, 0), fall)
    d = ImageDraw.Draw(img, "RGBA")
    d.line([696, 524, 660, 732], fill=(255, 255, 255, 160), width=2)
    for fx, fy, fr in [(644, 768, 22), (668, 780, 18), (624, 782, 15)]:
        d.ellipse([fx - fr, fy - fr * 0.6, fx + fr, fy + fr * 0.6],
                  fill=CLOUD_WHITE)

    # --- the town: two rows, chimneys with wavy smoke, trees ---
    cypress(d, 332, 470, 34)
    round_tree(d, 700, 470, 12)
    house(d, 340, 420, 52, 30, ROOF_A, lit=True, chimney=True)
    house(d, 398, 416, 46, 34, ROOF_B, lit=True)
    house(d, 450, 422, 58, 28, ROOF_C, lit=False, chimney=True)
    house(d, 514, 418, 48, 32, ROOF_A, lit=True)
    house(d, 568, 422, 54, 28, ROOF_B, lit=True, chimney=True)
    house(d, 626, 424, 40, 26, ROOF_C, lit=False)
    house(d, 332, 446, 48, 24, ROOF_B, lit=True)
    house(d, 386, 448, 52, 22, ROOF_A, lit=False, chimney=True)
    house(d, 444, 446, 46, 24, ROOF_C, lit=True)
    house(d, 496, 448, 54, 22, ROOF_B, lit=True)
    house(d, 556, 446, 48, 24, ROOF_A, lit=True, chimney=True)
    house(d, 610, 448, 44, 22, ROOF_C, lit=True)
    cypress(d, 640, 470, 26)
    bush(d, 360, 470, 8)
    bush(d, 620, 470, 8)
    # bunting across the front row
    pts = [(332, 444), (410, 454), (490, 456), (570, 450), (640, 442)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d.line([x0, y0, x1, y1], fill=INK, width=1)
        for t in (0.25, 0.5, 0.75):
            fx = x0 + (x1 - x0) * t
            fy = y0 + (y1 - y0) * t + 2
            d.polygon([(fx - 4, fy), (fx + 4, fy), (fx, fy + 8)],
                      fill=(ROOF_A if int(t * 4) % 2 else ROOF_C))

    # --- lighthouse: striped tower, gallery, glowing dome ---
    d.rectangle([652, 336, 704, 470], fill=(250, 244, 230))
    for y0, y1 in [(362, 386), (410, 434)]:
        d.rectangle([652, y0, 704, y1], fill=(198, 74, 54))
    d.rectangle([644, 336, 712, 348], fill=(60, 44, 34))
    d.pieslice([664, 314, 692, 348], 180, 360, fill=(250, 244, 230))
    d.rectangle([672, 330, 684, 348], fill=LIT)
    glow(img, 678, 332, 44, (255, 226, 150), 130)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([672, 330, 684, 342], fill=(255, 240, 190))
    d.rectangle([672, 448, 684, 470], fill=(90, 60, 40))

    # --- long ladder down to the small islet ---
    sx, sy, ex, ey = 330, 492, 238, 692
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    px, py = -uy * 10, ux * 10  # perpendicular, half-width 10
    d.line([sx + px, sy + py, ex + px, ey + py], fill=(120, 90, 60), width=3)
    d.line([sx - px, sy - py, ex - px, ey - py], fill=(120, 90, 60), width=3)
    for i in range(1, 13):
        t = i / 13
        cx, cy = sx + dx * t, sy + dy * t
        d.line([cx + px, cy + py, cx - px, cy - py], fill=(120, 90, 60),
               width=2)
    # side ropes with sag + lanterns
    for sgn in (1, -1):
        pts = []
        for i in range(9):
            t = i / 8
            pts.append((sx + dx * t + sgn * 22,
                        sy + dy * t + 14 * math.sin(t * math.pi)))
        d.line(pts, fill=(90, 66, 44), width=2)
    for t, lx_off in [(0.35, 26), (0.7, 26)]:
        lx, ly = sx + dx * t + lx_off, sy + dy * t + 12
        d.line([lx, ly - 12, lx, ly], fill=INK, width=2)
        d.ellipse([lx - 5, ly - 6, lx + 5, ly + 4], fill=LIT)
        d.rectangle([lx - 5, ly - 8, lx + 5, ly - 6], fill=INK)
    # one climber on the ladder
    cx, cy = sx + dx * 0.55, sy + dy * 0.55
    d.ellipse([cx - 5, cy - 16, cx + 5, cy - 6], fill=(52, 38, 28))
    d.polygon([(cx - 5, cy - 6), (cx + 5, cy - 6), (cx + 3, cy + 8),
               (cx - 3, cy + 8)], fill=(46, 110, 106))

    # --- small islet with two houses ---
    d.polygon([(150, 640), (288, 640), (252, 706), (186, 706)],
              fill=STONE_MID)
    d.polygon([(150, 640), (288, 640), (282, 652), (156, 652)], fill=GREEN)
    house(d, 170, 612, 44, 26, ROOF_A, lit=True, chimney=True)
    house(d, 224, 616, 40, 22, ROOF_C, lit=False)
    cypress(d, 274, 640, 24)
    round_tree(d, 160, 640, 9)

    # --- airship: big panelled envelope, gondola, propeller ---
    cx, cy, rx, ry = 822, 332, 128, 38
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
              outline=(150, 84, 44), width=3, fill=(236, 178, 108))
    # panel seams
    for off in (-84, -44, -4, 36, 76):
        x = cx + off
        half = ry * math.sqrt(max(0.0, 1 - (off / rx) ** 2))
        d.arc([x - 12, cy - half, x + 12, cy + half], 270, 90,
              fill=(200, 130, 70), width=2)
    # cream bands (chords of the ellipse)
    for off in (-64, 0, 64):
        x = cx + off
        half = ry * math.sqrt(max(0.0, 1 - (off / rx) ** 2))
        d.polygon([(x - 9, cy - half), (x + 9, cy - half),
                   (x + 9, cy + half), (x - 9, cy + half)], fill=CREAM)
    # nose cap + tail fins
    d.pieslice([cx - rx - 6, cy - 22, cx - rx + 22, cy + 22], 90, 270,
               fill=(172, 62, 48))
    d.polygon([(cx + rx - 8, cy - ry), (cx + rx + 26, cy - ry - 24),
               (cx + rx + 18, cy - ry + 12)], fill=(198, 86, 54))
    d.polygon([(cx + rx - 8, cy + ry), (cx + rx + 26, cy + ry + 24),
               (cx + rx + 18, cy + ry - 12)], fill=(198, 86, 54))
    # propeller: ring + four blades
    px, py = cx + rx + 30, cy
    for ang in (45, 135, 225, 315):
        a = math.radians(ang)
        d.line([px, py, px + 18 * math.cos(a), py + 18 * math.sin(a)],
               fill=(120, 90, 60), width=3)
    d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(120, 90, 60))
    # gondola with pitched roof + lit windows
    d.polygon([(cx - 48, cy + 40), (cx, cy + 28), (cx + 48, cy + 40)],
              fill=(172, 62, 48))
    d.rectangle([cx - 48, cy + 40, cx + 48, cy + 64], fill=(96, 66, 44))
    for wx in (cx - 36, cx - 8, cx + 20):
        d.rectangle([wx, cy + 46, wx + 12, cy + 58], fill=LIT)
    for rxx in (-40, 0, 40):
        d.line([cx + rxx, cy + 34, cx + rxx, cy + 40], fill=INK, width=2)
    # little flag on top
    d.line([cx - 12, cy - ry, cx - 12, cy - ry - 20], fill=INK, width=2)
    d.polygon([(cx - 12, cy - ry - 20), (cx + 8, cy - ry - 15),
               (cx - 12, cy - ry - 10)], fill=ROOF_A)

    # --- the cloud sea: back layer, island shadow, islets, mid, front ---
    for x, y, s in [(140, 790, 66), (420, 806, 80), (700, 794, 74),
                    (940, 800, 60)]:
        cloud(d, x, y, s)
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shd = ImageDraw.Draw(shade)
    shd.ellipse([300, 806, 720, 866], fill=(170, 150, 120, 46))
    shade = shade.filter(ImageFilter.GaussianBlur(14))
    img.paste(shade, (0, 0), shade)
    d = ImageDraw.Draw(img, "RGBA")
    # little islets peeking out of the clouds
    d.polygon([(96, 820), (196, 820), (168, 860), (124, 860)], fill=STONE_DARK)
    house(d, 118, 796, 30, 20)
    cypress(d, 182, 820, 22)
    cypress(d, 150, 820, 16)
    d.polygon([(856, 832), (948, 832), (922, 868), (882, 868)], fill=STONE_DARK)
    house(d, 878, 808, 28, 19)
    round_tree(d, 930, 832, 10)
    # mid layer
    cloud(d, 90, 890, 62)
    cloud(d, 360, 910, 74)
    cloud(d, 640, 900, 70)
    cloud(d, 910, 898, 64)
    # rooftops peeking out of the cloud sea
    d.polygon([(205, 962), (245, 930), (285, 962)], fill=ROOF_A)
    d.rectangle([268, 930, 274, 948], fill=(140, 100, 80))
    smoke(d, 271, 928, 30)
    d.polygon([(455, 985), (495, 952), (535, 985)], fill=ROOF_B)
    d.polygon([(715, 962), (755, 928), (795, 962)], fill=ROOF_C)
    d.rectangle([748, 928, 754, 946], fill=(140, 100, 80))
    smoke(d, 751, 926, 30)
    bush(d, 560, 985, 12)
    # front layer, big and low
    cloud(d, 200, 982, 76)
    cloud(d, 500, 992, 82)
    cloud(d, 800, 982, 78)
    cloud(d, 980, 960, 54)
    # soft modelling on the front sheet + nearer puffs
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shd = ImageDraw.Draw(shade)
    for cx, cy, rx, ry in [(260, 910, 130, 26), (620, 930, 150, 28),
                           (880, 910, 110, 24), (420, 970, 140, 26)]:
        shd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                    fill=(190, 170, 135, 36))
    shade = shade.filter(ImageFilter.GaussianBlur(18))
    img.paste(shade, (0, 0), shade)
    d = ImageDraw.Draw(img, "RGBA")
    for cx, cy, r in [(180, 870, 42), (520, 860, 48), (860, 866, 40)]:
        d.ellipse([cx - r, cy - r * 0.55, cx + r, cy + r * 0.55],
                  fill=CLOUD_WHITE)
    bird(d, 420, 830, 9)
    bird(d, 760, 840, 8)

    # --- fine grain: kills the flat-vector look, stays deterministic ---
    rng2 = random.Random(7)
    noise = Image.new("L", (128, 128))
    noise.putdata([rng2.randint(0, 255) for _ in range(128 * 128)])
    noise = noise.resize((W, H), Image.BICUBIC)
    grain = Image.merge("RGBA", (noise, noise, noise, noise.point(lambda v: 5)))
    img.paste(grain, (0, 0), grain)

    # --- cream frame ---
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, W - 1, H - 1], outline=CREAM, width=26)
    d.rectangle([26, 26, W - 27, H - 27], outline=(196, 148, 88), width=2)
    return img.convert("RGB")


if __name__ == "__main__":
    out = draw()
    out.save("entry.png", optimize=True)
    import os
    print("wrote entry.png", os.path.getsize("entry.png"), "bytes")
