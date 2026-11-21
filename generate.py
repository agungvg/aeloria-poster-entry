#!/usr/bin/env python3
"""Derive the submitted poster (entry.png) from the in-session generation.

Provenance: the poster image was generated in-session with Muse's image
pipeline (media.generate_image, snapshot
a3056ca8-9fc6-4237-a48d-f141aeb11e52:ce4x86) from the reference artwork
Lyso supplied for this bounty — a 3D stone-letter "AELORIA" render of a
floating island with a lighthouse town, a long ladder, a waterfall, an
airship and a cloud sea at golden hour — with his instruction to make it
look exactly like that reference. The pipeline returned a 1600x1600 PNG,
committed here as entry-gen-1600.png.

This script is the deterministic post-processing step: resize to the
bounty's 1024x1024, a 0.8 px Gaussian blur (the raw 1024 PNG is
1,153,614 bytes, over the 1,048,576-byte cap; the blur brings it to
1,031,266 bytes with no visible change), then save as an optimised PNG.
Two runs write byte-identical output.
"""
import hashlib
import os

from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry-gen-1600.png")
TARGET = os.path.join(HERE, "entry.png")
SIZE = (1024, 1024)
BLUR = 0.8
MAX_BYTES = 1_048_576  # bounty cap: entry.png must be <= 1 MiB


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main():
    im = Image.open(SOURCE)
    assert im.size == (1600, 1600), im.size
    out = im.resize(SIZE, Image.LANCZOS)
    out = out.filter(ImageFilter.GaussianBlur(BLUR))
    # Pillow's PNG writer is deterministic for identical input/settings,
    # so the output hash is stable across runs.
    out.save(TARGET, optimize=True, compress_level=9)
    size = os.path.getsize(TARGET)
    assert size <= MAX_BYTES, size
    print("wrote", TARGET, size, "bytes")
    print("sha256", sha256_file(TARGET))


if __name__ == "__main__":
    main()
