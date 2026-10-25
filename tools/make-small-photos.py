#!/usr/bin/env python3
"""Make small WebP copies of every show photo on joeydrums.com.

Run from the repo root:  python3 tools/make-small-photos.py

What it does:
1. Finds every photo:'assets/...' in the SHOWS list in index.html.
2. Saves WebP copies at 400, 640 and 960 pixels wide in assets/sized/
   (never bigger than the original).
3. Rewrites the PHOTO_SIZES block in index.html so each show card
   knows its photo size and which small copies exist.

New shows still work if this is never run. Their photo just loads
at full size until the small copies are made.
"""
import json
import os
import re
import sys

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
OUT_DIR = os.path.join(ROOT, "assets", "sized")
WIDTHS = [400, 640, 960]
QUALITY = 78

START = "/* PHOTO-SIZES:START (made by tools/make-small-photos.py) */"
END = "/* PHOTO-SIZES:END */"


def sized_name(photo, width):
    base = os.path.splitext(os.path.basename(photo))[0]
    return "assets/sized/%s-%d.webp" % (base, width)


def main():
    html = open(INDEX, encoding="utf-8").read()
    photos = sorted(set(re.findall(r"photo:'(assets/[^']+)'", html)))
    os.makedirs(OUT_DIR, exist_ok=True)
    table = {}
    for photo in photos:
        src = os.path.join(ROOT, photo)
        if not os.path.exists(src):
            print("missing, skipped:", photo)
            continue
        im = ImageOps.exif_transpose(Image.open(src))
        im.load()
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "A" in im.getbands() or im.mode == "P" else "RGB")
        w, h = im.size
        made = []
        for target in WIDTHS:
            tw = min(target, w)
            if made and tw <= made[-1]:
                break
            th = round(h * tw / w)
            out = os.path.join(ROOT, sized_name(photo, target))
            im.resize((tw, th), Image.LANCZOS).save(out, "WEBP", quality=QUALITY, method=6)
            made.append(tw)
            if tw == w:
                break
        table[photo] = {"w": w, "h": h, "v": [[sized_name(photo, t), m] for t, m in zip(WIDTHS, made)]}
        print("%-50s %dx%d -> %s" % (photo, w, h, made))

    block = START + "\nvar PHOTO_SIZES = " + json.dumps(table, separators=(",", ":")) + ";\n" + END
    if START in html:
        html = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: block, html, flags=re.S)
    else:
        sys.exit("PHOTO-SIZES markers not found in index.html")
    open(INDEX, "w", encoding="utf-8").write(html)
    print("updated PHOTO_SIZES in index.html (%d photos)" % len(table))


if __name__ == "__main__":
    main()
