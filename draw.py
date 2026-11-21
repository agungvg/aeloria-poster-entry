#!/usr/bin/env python3
"""AELORIA — The Land Above the Clouds. (v2 — re-composed after eye test)

A vintage flat travel poster for a place that does not exist, drawn from
scratch with Pillow. No network, no clock, no randomness (fixed seed), so
two runs write byte-identical PNGs.

v1 eye-test failures, fixed here:
  * name/tagline collided with the sun and the airship — the top band is
    now clear sky for type only; sun moved to the horizon, airship to the
    open sky right of the island.
  * island too small and flat — now much larger, with a shaded right face,
    rock facets, and bigger houses in two rows.
  * cloud sea was one flat white blob — now three distinct layers with
    crescent shadows under each puff and gaps of golden light between them.
  * airship read as a target — rebuilt as a simple striped capsule with
    the gondola attached and fins at the rear.
  * the "golden road" polygon looked like a road — replaced by a soft
    glow on the horizon between cloud masses.

Composition (judge criteria, in order):
  1. Invented place name set INTO the picture — huge, legible, across the sky.
  2. One landmark — a single great floating island with a lighthouse town —
     plus golden-hour light and an arriving airship: a clear promise of a stay.
  3. Distinct identity — nothing borrowed from a real destination.
  4. Type with intent — Noto Serif Display, letterspaced, cream on apricot sky.
  5. Palette + layout — apricot/gold/cream with deep-teal cloud shadows;
     the eye goes name -> lighthouse island -> stairway -> sea of clouds.
Only copy: the place name and one tagline. No quotes, no ratings.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

SERIF_BLACK = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf"

CREAM = (251, 240, 211)
CREAM_SOFT = (255, 246, 216)
GOLD = (232, 135, 58)
TERRA = (198, 93, 59)
TERRA_DARK = (166, 74, 45)
STONE = (217, 185, 138)
STONE_DARK = (169, 126, 79)
STONE_DEEP = (124, 90, 56)
WHITE = (255, 252, 240)
CLOUD_WHITE = (255, 250, 235)
CLOUD_SHADOW = (203, 184, 154)
CLOUD_TEAL = (168, 190, 182)
INK = (58, 38, 24)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky(img):
    d = ImageDraw.Draw(img)
    stops = [(0.00, (214, 104, 44)), (0.28, (240, 162, 88)),
             (0.55, (247, 200, 115)), (0.78, (251, 226, 166)),
             (1.00, (250, 220, 168))]
    for y in range(H):
        t = y / (H - 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                d.line([(0, y), (W, y)], fill=lerp(c0, c1, (t - t0) / (t1 - t0)))
                break


def glow(img, cx, cy, radius, colour, peak=140):
    """Soft radial glow composited onto img."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(20, 0, -1):
        r = radius * i / 20
        a = int(peak * (1 - i / 20) ** 1.6)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour + (a,))
    layer = layer.filter(ImageFilter.GaussianBlur(16))
    img.paste(layer, (0, 0), layer)


def cloud(d, x, y, s, tint=CLOUD_WHITE):
    """One billowing cloud: shadow puffs first, white puffs on top, so each
    puff carries a crescent shadow underneath."""
    puffs = [(-1.7, 0.12, 1.00), (-0.95, -0.30, 1.28), (0.0, -0.44, 1.48),
             (0.95, -0.30, 1.28), (1.7, 0.12, 1.00), (-0.45, 0.18, 1.28),
             (0.5, 0.18, 1.28)]
    for dx, dy, r in puffs:
        d.ellipse([x + dx * s - r * s, y + dy * s + 12 - r * s * 0.60,
                   x + dx * s + r * s, y + dy * s + 12 + r * s * 0.60],
                  fill=(205, 188, 160))
    for dx, dy, r in puffs:
        d.ellipse([x + dx * s - r * s, y + dy * s - r * s * 0.60,
                   x + dx * s + r * s, y + dy * s + r * s * 0.60], fill=tint)


def house(d, x, y, w, h, roof=TERRA, body=WHITE):
    """A whitewashed house with a terracotta roof and lit windows."""
    d.polygon([(x, y), (x + w * 0.5, y - h * 0.55), (x + w, y)], fill=roof)
    d.rectangle([x, y, x + w, y + h], fill=body)
    d.rectangle([x, y, x + w, y + 3], fill=TERRA_DARK)
    wy = y + h * 0.30
    for wx in (x + w * 0.18, x + w * 0.62):
        d.rectangle([wx, wy, wx + w * 0.16, wy + h * 0.32], fill=(255, 214, 130))
    d.rectangle([x + w * 0.42, y + h * 0.58, x + w * 0.58, y + h], fill=(94, 62, 32))


def cypress(d, x, y, h):
    d.polygon([(x, y - h), (x - 8, y), (x + 8, y)], fill=(32, 84, 66))
    d.rectangle([x - 2, y, x + 2, y + 6], fill=(94, 62, 32))


def bird(d, x, y, s):
    d.arc([x - s, y - s * 0.5, x, y + s * 0.5], 200, 340, fill=INK, width=3)
    d.arc([x, y - s * 0.5, x + s, y + s * 0.5], 200, 340, fill=INK, width=3)


def draw_tracked(d, cx, y, text, font, fill, tracking):
    widths = [d.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=font, fill=fill)
        x += w + tracking


def build():
    rng = random.Random(7)
    img = Image.new("RGB", (W, H), CREAM)
    sky(img)
    d = ImageDraw.Draw(img, "RGBA")

    # --- type band: clear sky, name + tagline only ---
    big = ImageFont.truetype(SERIF_BLACK, 132)
    draw_tracked(d, 512, 62, "AELORIA", big, (176, 88, 38, 255), 22)
    draw_tracked(d, 512, 66, "AELORIA", big, CREAM_SOFT + (255,), 22)
    small = ImageFont.truetype(SERIF_BOLD, 30)
    draw_tracked(d, 512, 216, "THE LAND ABOVE THE CLOUDS", small,
                 CREAM_SOFT + (255,), 9)
    for dx in (-360, 360):
        d.polygon([(512 + dx, 228), (512 + dx + 6, 234), (512 + dx, 240),
                   (512 + dx - 6, 234)], fill=CREAM_SOFT)

    # --- birds in the open sky, left ---
    bird(d, 150, 300, 13)
    bird(d, 196, 276, 10)
    bird(d, 232, 312, 9)

    # --- airship arriving from the right, clear of the type ---
    glow(img, 800, 330, 90, (255, 220, 150), 70)
    d = ImageDraw.Draw(img, "RGBA")
    # capsule balloon: warm gold with cream vertical stripes (clipped to
    # the balloon by a mask, so the stripes follow its curve)
    d.ellipse([700, 296, 884, 356], fill=(233, 158, 72))
    d.ellipse([700, 296, 884, 356], outline=TERRA_DARK, width=3)
    stripes = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stripes)
    for cx in (748, 792, 836):
        sd.rectangle([cx - 7, 296, cx + 7, 356], fill=CREAM_SOFT + (255,))
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([700, 296, 884, 356], fill=255)
    img.paste(stripes, (0, 0), Image.composite(stripes, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask))
    d = ImageDraw.Draw(img, "RGBA")
    # tail fins
    d.polygon([(700, 322), (672, 300), (672, 344)], fill=TERRA_DARK)
    # gondola attached under the balloon
    d.rectangle([756, 356, 828, 378], fill=(94, 62, 32))
    d.rectangle([766, 360, 780, 372], fill=(255, 214, 130))
    d.rectangle([800, 360, 814, 372], fill=(255, 214, 130))
    d.line([(792, 356), (792, 344)], fill=(94, 62, 32), width=2)

    # --- sun low on the horizon, half-sunk into the cloud sea ---
    glow(img, 830, 726, 150, (255, 214, 130), 160)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([830 - 52, 726 - 52, 830 + 52, 726 + 52], fill=(250, 200, 100))

    # --- small far islet, left, with two houses ---
    d.polygon([(150, 668), (300, 668), (256, 726), (196, 726)], fill=STONE_DARK)
    d.polygon([(150, 668), (300, 668), (284, 640), (168, 640)], fill=(226, 196, 150))
    house(d, 178, 612, 36, 24)
    house(d, 224, 608, 32, 22)
    cypress(d, 282, 640, 28)

    # --- THE landmark: the great floating island of Aeloria ---
    # cliff body, tapering to a point
    cliff = [(300, 470), (724, 470), (700, 548), (660, 618), (606, 682),
             (556, 736), (512, 776), (468, 736), (418, 682), (364, 618),
             (324, 548)]
    d.polygon(cliff, fill=STONE)
    # sunlit left face, shaded right face
    d.polygon([(512, 470), (724, 470), (700, 548), (660, 618), (606, 682),
               (556, 736), (512, 776)], fill=(196, 158, 104))
    # terrace bands across the cliff
    for y0, y1 in [(500, 530), (548, 580), (618, 652), (682, 718)]:
        t0 = (y0 - 470) / 306
        t1 = (y1 - 470) / 306
        d.polygon([(300 + t0 * 212, y0), (724 - t0 * 212, y0),
                   (724 - t1 * 212, y1), (300 + t1 * 212, y1)],
                  fill=(206, 172, 122) if (y0 // 60) % 2 == 0 else (188, 150, 100))
    # rock facets: a few diagonal cracks
    for x0, y0, x1, y1 in [(380, 540, 420, 620), (620, 540, 590, 630),
                           (470, 600, 500, 690), (560, 600, 540, 680)]:
        d.line([(x0, y0), (x1, y1)], fill=STONE_DEEP, width=3)
    # underside point + hanging roots
    d.polygon([(468, 736), (512, 776), (556, 736), (534, 700), (490, 700)],
              fill=STONE_DEEP)
    for rx, ry, rl in [(448, 716, 30), (486, 742, 40), (530, 740, 34),
                       (574, 700, 28), (410, 690, 26)]:
        d.line([(rx, ry), (rx + 4, ry + rl)], fill=(94, 66, 38), width=3)

    # plateau grass rim
    d.polygon([(300, 470), (724, 470), (710, 450), (314, 450)], fill=(96, 138, 84))
    d.polygon([(300, 470), (724, 470), (710, 458), (314, 458)], fill=(120, 160, 96))

    # the town: two rows of bigger houses
    for x, y, w, h in [(322, 420, 52, 32), (382, 414, 46, 30), (436, 420, 56, 34),
                       (500, 414, 48, 30), (556, 420, 54, 33), (618, 416, 46, 30)]:
        house(d, x, y, w, h)
    for x, y, w, h in [(360, 372, 48, 30), (416, 366, 42, 28), (466, 372, 52, 32),
                       (526, 366, 44, 28), (578, 370, 46, 30)]:
        house(d, x, y, w, h)
    cypress(d, 330, 372, 34)
    cypress(d, 668, 372, 38)
    cypress(d, 700, 420, 30)

    # lighthouse tower on the island's crown, beacon lit
    d.rectangle([664, 296, 712, 450], fill=WHITE)
    d.rectangle([664, 326, 712, 342], fill=TERRA)
    d.rectangle([664, 380, 712, 396], fill=TERRA)
    d.rectangle([658, 278, 718, 296], fill=INK)
    d.rectangle([666, 262, 710, 278], fill=(255, 214, 130))
    d.polygon([(658, 262), (688, 236), (718, 262)], fill=TERRA_DARK)
    # beacon glow only — no fan of rays (v2's rays shot up through the name)
    glow(img, 688, 250, 70, (255, 236, 170), 120)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([678, 240, 698, 260], fill=(255, 236, 170))

    # winding stairway down from the island to the small islet
    steps = [(330, 512), (306, 540), (286, 568), (268, 596), (252, 624),
             (238, 650)]
    for i, (sx, sy) in enumerate(steps):
        w = 36 - i * 2
        d.rectangle([sx - w // 2, sy, sx + w // 2, sy + 7], fill=CREAM_SOFT)
        d.rectangle([sx - w // 2, sy + 7, sx + w // 2, sy + 9], fill=CLOUD_SHADOW)
    d.ellipse([296, 552, 304, 564], fill=INK)
    d.rectangle([295, 564, 305, 578], fill=TERRA)
    d.ellipse([258, 606, 266, 618], fill=INK)
    d.rectangle([257, 618, 267, 632], fill=TEAL if False else (46, 110, 106))

    # --- sea of clouds: three layers with gaps of golden light between ---
    glow(img, 512, 880, 260, (255, 210, 130), 90)
    d = ImageDraw.Draw(img, "RGBA")
    # back layer, small and pale, sky still showing between the masses
    cloud(d, 170, 772, 54, tint=(255, 244, 214))
    cloud(d, 450, 788, 62, tint=(255, 244, 214))
    cloud(d, 700, 776, 56, tint=(255, 244, 214))
    # two tiny islets peeking out of the cloud sea, sitting ON the back layer
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
    # soft modelling on the front sheet: faint warm-grey rolls + nearer puffs
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

    # --- frame: cream border + thin gold rule ---
    d.rectangle([0, 0, W - 1, H - 1], outline=CREAM, width=24)
    d.rectangle([28, 28, W - 29, H - 29], outline=(216, 164, 92), width=2)

    # --- print grain: deterministic, very light ---
    grain = Image.new("L", (W, H))
    gp = grain.load()
    for yy in range(0, H, 2):
        for xx in range(0, W, 2):
            gp[xx, yy] = rng.randint(0, 255)
    grain = grain.filter(ImageFilter.GaussianBlur(0.6))
    img = Image.composite(
        Image.blend(img, Image.new("RGB", (W, H), (120, 100, 70)), 0.03),
        img, grain.point(lambda v: 255 if v > 128 else 0))
    img.save(OUT, "PNG", optimize=True)
    print("wrote", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    build()
