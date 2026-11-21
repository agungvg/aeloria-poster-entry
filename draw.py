#!/usr/bin/env python3
"""Render AELORIA — The Land Above the Clouds (v4, detailed rebuild).

A vintage travel poster for a place that does not exist: one great
floating island with a lighthouse town, a waterfall spilling off its
edge into the cloud sea, a winding stairway down to a smaller islet,
and an airship arriving at golden hour.

Everything is drawn from scratch with Pillow: gradient sky, wispy
high clouds, a varied town (lit windows, chimneys, bunting, a domed
house, trees), a detailed airship, and a three-layer cloud sea with
shadows, highlights and wisps. Deterministic: fixed seed, no clock,
no network. Writes entry.png (1024x1024, < 1 MiB).
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024

# palette
SKY_TOP = (206, 96, 44)       # burnt orange
SKY_MID = (232, 146, 74)      # warm amber
SKY_LOW = (248, 205, 126)     # pale gold
CREAM = (252, 244, 224)       # type / clouds
CREAM_SOFT = (250, 238, 210)
CLOUD_WHITE = (253, 248, 236)
CLOUD_SHADE = (214, 196, 164)
CLOUD_DEEP = (188, 168, 138)
TEAL = (46, 110, 106)         # cypress / deep green
GREEN = (106, 148, 84)        # grass
GREEN_DARK = (84, 124, 66)
STONE = (201, 170, 128)       # cliff light
STONE_MID = (186, 152, 108)
STONE_DARK = (163, 130, 88)
STONE_DEEP = (140, 110, 72)
ROOF_A = (198, 86, 54)        # terracotta
ROOF_B = (172, 62, 48)        # deep red
ROOF_C = (214, 128, 60)       # ochre
INK = (64, 46, 30)            # outlines / dark
LIT = (255, 214, 130)         # lit windows
WATER = (214, 232, 226)       # waterfall
WATER_DEEP = (168, 200, 196)

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


def house(d, x, y, w, h, roof=ROOF_A, lit=True, chimney=False):
    """A whitewashed house: body, roof, door, windows, optional chimney."""
    d.rectangle([x, y, x + w, y + h], fill=(250, 244, 230))
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
        d.ellipse([x + w - 13, y - h * 0.45 - 16, x + w - 5, y - h * 0.45 - 8],
                  fill=(230, 220, 205, 160))
        d.ellipse([x + w - 16, y - h * 0.45 - 26, x + w - 6, y - h * 0.45 - 16],
                  fill=(230, 220, 205, 110))


def cypress(d, x, y, h):
    d.polygon([(x - 5, y), (x, y - h), (x + 5, y)], fill=TEAL)
    d.rectangle([x - 1, y, x + 1, y + 4], fill=(90, 60, 40))


def round_tree(d, x, y, r):
    d.rectangle([x - 2, y, x + 2, y + 8], fill=(90, 60, 40))
    d.ellipse([x - r, y - r * 1.4, x + r, y + r * 0.4], fill=GREEN_DARK)
    d.ellipse([x - r * 0.6, y - r * 1.8, x + r * 0.5, y - r * 0.3],
              fill=GREEN)


def cloud(d, x, y, s, shade=True):
    """One billow: a cluster of overlapping puffs with a shadow crescent."""
    puffs = [(-0.9, 0.15, 0.55), (-0.45, -0.15, 0.7), (0.0, -0.3, 0.8),
             (0.45, -0.12, 0.7), (0.9, 0.15, 0.55), (0.0, 0.25, 0.75)]
    if shade:
        for dx, dy, r in puffs:
            d.ellipse([x + dx * s - r * s, y + dy * s + 12 - r * s * 0.60,
                       x + dx * s + r * s, y + dy * s + 12 + r * s * 0.60],
                      fill=CLOUD_SHADE)
    for dx, dy, r in puffs:
        d.ellipse([x + dx * s - r * s, y + dy * s - r * s * 0.60,
                   x + dx * s + r * s, y + dy * s + r * s * 0.60],
                  fill=CLOUD_WHITE)


def wisp(d, x, y, length, alpha=90):
    """A thin curl of cloud rising off the sea."""
    d.arc([x, y, x + length, y + length * 0.35], 180, 330,
          fill=CLOUD_WHITE, width=5)


def draw():
    img = vgrad((W, H), [(0.0, SKY_TOP), (0.45, SKY_MID), (1.0, SKY_LOW)])
    img = img.convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    # --- high wispy clouds (kept clear of the name and tagline) ---
    for x, y, ln in [(60, 340, 120), (820, 430, 130),
                     (880, 420, 130), (60, 520, 120)]:
        d.ellipse([x, y, x + ln, y + 12], fill=(255, 230, 190, 70))
        d.ellipse([x + 20, y + 14, x + ln - 10, y + 24],
                  fill=(255, 230, 190, 50))

    # --- type: name + tagline ---
    f_name = ImageFont.truetype(SERIF_BLACK, 168)
    f_tag = ImageFont.truetype(SERIF_BOLD, 32)
    name = "AELORIA"
    d.text((512, 96), name, font=f_name, fill=CREAM, anchor="ma")
    tag = "THE LAND ABOVE THE CLOUDS"
    d.text((512, 270), tag, font=f_tag, fill=CREAM, anchor="ma")
    d.polygon([(512 - 360, 288), (512 - 348, 278), (512 - 336, 288),
               (512 - 348, 298)], fill=CREAM)
    d.polygon([(512 + 360, 288), (512 + 348, 278), (512 + 336, 288),
               (512 + 348, 298)], fill=CREAM)

    # --- birds: two flocks, clear of the name ---
    for bx, by, bs in [(140, 330, 13), (180, 310, 10), (210, 330, 9),
                       (240, 350, 11), (880, 190, 10), (906, 178, 12),
                       (932, 196, 9)]:
        bird(d, bx, by, bs)

    # --- sun low on the horizon, half-sunk into the cloud sea ---
    glow(img, 830, 726, 170, (255, 214, 130), 170)
    d = ImageDraw.Draw(img, "RGBA")
    for ang in range(0, 360, 24):
        a = math.radians(ang)
        if 200 < ang < 340:  # keep rays out of the cloud sea below
            continue
        x0, y0 = 830 + 62 * math.cos(a), 726 + 62 * math.sin(a)
        x1, y1 = 830 + 96 * math.cos(a), 726 + 96 * math.sin(a)
        d.line([x0, y0, x1, y1], fill=(255, 226, 150, 120), width=4)
    d.ellipse([830 - 52, 726 - 52, 830 + 52, 726 + 52], fill=(250, 200, 100))
    d.ellipse([830 - 52, 726 - 52, 830 + 52, 726 + 52],
              outline=(255, 236, 170), width=3)

    # --- the great floating island ---
    d.polygon([(322, 470), (738, 470), (700, 620), (620, 700), (512, 762),
               (404, 700), (340, 620)], fill=STONE)
    # cliff strata, with little ledges and bushes
    d.polygon([(330, 500), (730, 500), (706, 540), (352, 540)], fill=STONE_MID)
    d.polygon([(360, 580), (700, 580), (668, 622), (392, 622)], fill=STONE_MID)
    d.polygon([(410, 650), (640, 650), (600, 692), (452, 692)], fill=STONE_DARK)
    d.polygon([(470, 712), (580, 712), (548, 748), (500, 748)], fill=STONE_DEEP)
    for cx, cy in [(352, 540), (700, 540), (392, 622), (668, 622),
                   (452, 692), (600, 692)]:
        d.ellipse([cx - 8, cy - 5, cx + 8, cy + 3], fill=GREEN_DARK)
    # cracks
    for x0, y0, x1, y1 in [(420, 540, 452, 640), (610, 540, 580, 660),
                           (500, 620, 520, 720)]:
        d.line([x0, y0, x1, y1], fill=STONE_DEEP, width=3)
    # grassy top with a stone rim
    d.polygon([(322, 470), (738, 470), (730, 486), (330, 486)], fill=GREEN)
    d.line([322, 470, 738, 470], fill=GREEN_DARK, width=3)

    # --- waterfall spilling off the left edge into the clouds ---
    fall = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fall)
    for i, (fx, fy, fr) in enumerate([(352, 496, 15), (344, 532, 16),
                                      (330, 570, 17), (322, 610, 18),
                                      (312, 652, 19), (302, 694, 20),
                                      (296, 722, 21)]):
        fd.ellipse([fx - fr, fy - fr, fx + fr, fy + fr],
                   fill=WATER + (200,))
    fd.polygon([(352, 488), (368, 488), (314, 724), (286, 724)],
               fill=WATER + (160,))
    fall = fall.filter(ImageFilter.GaussianBlur(5))
    img.paste(fall, (0, 0), fall)
    d = ImageDraw.Draw(img, "RGBA")
    d.line([348, 500, 306, 700], fill=(255, 255, 255, 160), width=2)
    # foam where the fall meets the clouds
    for fx, fy, fr in [(292, 736, 22), (316, 748, 18), (272, 750, 15)]:
        d.ellipse([fx - fr, fy - fr * 0.6, fx + fr, fy + fr * 0.6],
                  fill=CLOUD_WHITE)

    # --- the town: varied houses, lit windows, chimneys, trees ---
    cypress(d, 338, 470, 34)
    round_tree(d, 700, 470, 12)
    house(d, 356, 424, 52, 30, ROOF_A, lit=True, chimney=True)
    house(d, 414, 420, 46, 34, ROOF_B, lit=True)
    house(d, 466, 426, 58, 28, ROOF_C, lit=False, chimney=True)
    house(d, 530, 422, 48, 32, ROOF_A, lit=True)
    house(d, 584, 426, 54, 28, ROOF_B, lit=True, chimney=True)
    # front row
    house(d, 344, 448, 48, 24, ROOF_B, lit=True)
    house(d, 398, 450, 52, 22, ROOF_A, lit=False, chimney=True)
    house(d, 456, 448, 46, 24, ROOF_C, lit=True)
    house(d, 508, 450, 54, 22, ROOF_B, lit=True)
    house(d, 568, 448, 48, 24, ROOF_A, lit=True, chimney=True)
    cypress(d, 626, 470, 26)
    # bunting across the front row
    pts = [(344, 446), (420, 456), (500, 458), (580, 452), (640, 444)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d.line([x0, y0, x1, y1], fill=INK, width=1)
        for t in (0.25, 0.5, 0.75):
            fx = x0 + (x1 - x0) * t
            fy = y0 + (y1 - y0) * t + 2
            d.polygon([(fx - 4, fy), (fx + 4, fy), (fx, fy + 8)],
                      fill=(ROOF_A if int(t * 4) % 2 else ROOF_C))

    # --- lighthouse: striped tower, gallery, lamp, soft glow ---
    d.rectangle([648, 330, 700, 470], fill=(250, 244, 230))
    for y0, y1 in [(356, 380), (404, 428)]:
        d.rectangle([648, y0, 700, y1], fill=(198, 74, 54))
    d.rectangle([640, 336, 708, 348], fill=(60, 44, 34))
    # low glowing dome on the gallery: keeps the lamp below the tagline
    d.pieslice([660, 314, 688, 348], 180, 360, fill=(250, 244, 230))
    d.rectangle([668, 330, 680, 348], fill=LIT)
    glow(img, 674, 332, 40, (255, 226, 150), 110)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([668, 330, 680, 342], fill=(255, 240, 190))

    # --- winding stairway down to the small islet ---
    steps = [(330, 486), (312, 508), (296, 530), (280, 552), (264, 574),
             (248, 596), (232, 618), (216, 640)]
    for sx, sy in steps:
        d.rectangle([sx - 16, sy, sx + 16, sy + 6], fill=(240, 232, 214))
        d.line([sx - 16, sy + 6, sx + 16, sy + 6], fill=STONE_DARK, width=2)
    # lantern posts along the stair
    for lx, ly in [(322, 500), (272, 566), (224, 632)]:
        d.line([lx, ly, lx, ly - 14], fill=INK, width=2)
        d.ellipse([lx - 4, ly - 20, lx + 4, ly - 12], fill=LIT)
    # two travellers on the stair
    for tx, ty, tc in [(300, 540, (198, 86, 54)), (252, 606, (46, 110, 106))]:
        d.ellipse([tx - 5, ty - 16, tx + 5, ty - 6], fill=(52, 38, 28))
        d.polygon([(tx - 5, ty - 6), (tx + 5, ty - 6), (tx + 3, ty + 8),
                   (tx - 3, ty + 8)], fill=tc)

    # --- small islet with two houses ---
    d.polygon([(150, 640), (280, 640), (246, 700), (184, 700)],
              fill=STONE_MID)
    d.polygon([(150, 640), (280, 640), (274, 652), (156, 652)], fill=GREEN)
    house(d, 168, 612, 44, 26, ROOF_A, lit=True, chimney=True)
    house(d, 218, 616, 40, 22, ROOF_C, lit=False)
    cypress(d, 268, 640, 24)
    round_tree(d, 158, 640, 9)

    # --- airship: panelled envelope, gondola, propeller, flag ---
    cx, cy = 800, 336
    d.ellipse([cx - 112, cy - 34, cx + 112, cy + 34],
              outline=(150, 84, 44), width=3, fill=(236, 178, 108))
    d.ellipse([cx - 112, cy - 34, cx + 112, cy + 34],
              outline=(150, 84, 44), width=1)
    # panel seams + cream bands
    for px in (-70, -30, 10, 50):
        d.arc([cx + px - 14, cy - 32, cx + px + 14, cy + 32], 270, 90,
              fill=(200, 130, 70), width=2)
    for bx in (-58, 6, 62):
        d.polygon([(cx + bx - 8, cy - 32), (cx + bx + 8, cy - 32),
                   (cx + bx + 8, cy + 32), (cx + bx - 8, cy + 32)],
                  fill=CREAM)
    # nose cap + tail fins
    d.pieslice([cx - 118, cy - 20, cx - 92, cy + 20], 90, 270,
               fill=(172, 62, 48))
    d.polygon([(cx + 104, cy - 30), (cx + 128, cy - 52), (cx + 122, cy - 8)],
              fill=(198, 86, 54))
    d.polygon([(cx + 104, cy + 30), (cx + 128, cy + 52), (cx + 122, cy + 8)],
              fill=(198, 86, 54))
    # propeller at the rear
    d.ellipse([cx + 118, cy - 16, cx + 150, cy + 16],
              outline=(120, 90, 60), width=2)
    d.line([cx + 134, cy - 14, cx + 134, cy + 14], fill=(120, 90, 60),
           width=3)
    # gondola with lit windows + suspension ropes
    d.rectangle([cx - 46, cy + 36, cx + 46, cy + 58], fill=(96, 66, 44))
    for wx in (cx - 34, cx - 8, cx + 18):
        d.rectangle([wx, cy + 42, wx + 12, cy + 52], fill=LIT)
    for rx in (-40, 0, 40):
        d.line([cx + rx, cy + 30, cx + rx, cy + 36], fill=INK, width=2)
    # little flag on top
    d.line([cx - 10, cy - 34, cx - 10, cy - 54], fill=INK, width=2)
    d.polygon([(cx - 10, cy - 54), (cx + 10, cy - 49), (cx - 10, cy - 44)],
              fill=ROOF_A)

    # --- the cloud sea: back layer, island shadow, mid, front ---
    for x, y, s in [(140, 772, 66), (420, 788, 80), (700, 776, 74),
                    (940, 782, 60)]:
        cloud(d, x, y, s)
    # island's soft shadow on the clouds
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shd = ImageDraw.Draw(shade)
    shd.ellipse([300, 790, 720, 850], fill=(170, 150, 120, 46))
    shade = shade.filter(ImageFilter.GaussianBlur(14))
    img.paste(shade, (0, 0), shade)
    d = ImageDraw.Draw(img, "RGBA")
    # two tiny islets peeking out of the cloud sea
    d.polygon([(96, 800), (196, 800), (168, 840), (124, 840)], fill=STONE_DARK)
    house(d, 118, 776, 30, 20)
    cypress(d, 182, 800, 22)
    d.polygon([(856, 812), (948, 812), (922, 848), (882, 848)], fill=STONE_DARK)
    house(d, 878, 788, 28, 19)
    # mid layer
    cloud(d, 90, 876, 62)
    cloud(d, 360, 896, 74)
    cloud(d, 640, 886, 70)
    cloud(d, 910, 884, 64)
    # front layer, big and low
    cloud(d, 200, 978, 76)
    cloud(d, 500, 988, 82)
    cloud(d, 800, 978, 78)
    cloud(d, 980, 956, 54)
    # soft modelling on the front sheet + nearer puffs + wisps
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shd = ImageDraw.Draw(shade)
    for cx, cy, rx, ry in [(260, 900, 130, 26), (620, 920, 150, 28),
                           (880, 900, 110, 24), (420, 960, 140, 26)]:
        shd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                    fill=(190, 170, 135, 36))
    shade = shade.filter(ImageFilter.GaussianBlur(18))
    img.paste(shade, (0, 0), shade)
    d = ImageDraw.Draw(img, "RGBA")
    for cx, cy, r in [(180, 860, 42), (520, 850, 48), (860, 856, 40)]:
        d.ellipse([cx - r, cy - r * 0.55, cx + r, cy + r * 0.55],
                  fill=CLOUD_WHITE)
    bird(d, 420, 820, 9)
    bird(d, 760, 830, 8)

    # --- fine grain: kills the flat-vector look, stays deterministic ---
    rng = random.Random(7)
    noise = Image.new("L", (128, 128))
    noise.putdata([rng.randint(0, 255) for _ in range(128 * 128)])
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
