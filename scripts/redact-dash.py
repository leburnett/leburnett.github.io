#!/usr/bin/env python3
"""Redact strain names and local paths from the optomotor dashboard screenshot.

The dashboard screenshot on the freely-walking-optomotor page is a real view of
unpublished data. At full resolution the summary heatmap is legible, which makes
it a readable results table: the row labels name every silenced line, and the
sidebar exposes a local path and the project codename. This script blurs those
regions so the figure still reads as a working dashboard without disclosing
which cell types did what.

Run it on the *original* capture, not the web-sized copy — the later downscale
to 1600px destroys anything the blur leaves behind. Then optimise the result:

    python3 scripts/redact-dash.py
    python3 scripts/optimise-image.py <redacted output> --figure
    # move the optimised file to assets/projects/freely-walking-optomotor/dash.png

Usage
-----
    # Redact using the committed box list
    python3 scripts/redact-dash.py

    # Different input/output
    python3 scripts/redact-dash.py --src path/to/dash.png --out path/to/out.png

    # Draw labelled outlines instead of blurring, to check the boxes still line
    # up after re-capturing the screenshot
    python3 scripts/redact-dash.py --preview

Re-capturing the dashboard
--------------------------
BOXES is tied to one specific 3130x1204 capture. If the screenshot is retaken,
the coordinates will be wrong and MUST be re-measured — run --preview first and
confirm every box sits over the text it is meant to hide. Getting this wrong
publishes the data, so check the output by eye before committing, at full size
as well as at web size.
"""

import argparse
import sys

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    sys.exit("Pillow is required:  python3 -m pip install Pillow")

SRC = "image-originals/freely-walking-optomotor/dash.png"
OUT = "image-originals/freely-walking-optomotor/dash-redacted.png"

# Expected size of the capture BOXES was measured against. A mismatch means the
# screenshot was retaken and every coordinate below is suspect.
EXPECTED_SIZE = (3130, 1204)

# (left, top, right, bottom) in original pixels. The screenshot is two panels
# side by side, each with its own sidebar, hence the L/R pairs.
BOXES = {
    # Strain names — left panel
    "L strain select": (55, 330, 196, 363),
    "L plot title": (478, 224, 662, 260),
    # Strain names — right panel
    "R strain select": (1598, 331, 1744, 361),
    "R plot title": (2313, 241, 2484, 271),
    "R heatmap row labels": (2098, 388, 2266, 682),
    "R line legend": (2460, 864, 2586, 902),
    "R violin legend": (2788, 823, 3078, 854),
    "R violin axis labels": (2712, 1124, 3020, 1147),
    # Local paths and project codename
    "L data dir input": (52, 148, 376, 175),
    "L data dir wrapped": (48, 194, 376, 238),
    "R data dir input": (1592, 148, 1930, 175),
    "R data dir wrapped": (1588, 194, 1930, 238),
}

# Deliberately left legible: the strain/cohort counts, the acquisition dates,
# the stimulus condition list, the metric axis labels and the colour scale.
# None of those identify a line, and without them the figure stops looking like
# a dashboard at all.


def redact(region):
    """Mosaic then blur. The mosaic discards the glyphs outright — a Gaussian
    blur alone can leave enough structure to guess short strings — and the blur
    then makes the patch read as a deliberate redaction rather than a rendering
    fault."""
    w, h = region.size
    small = region.resize((max(1, w // 14), max(1, h // 8)), Image.BILINEAR)
    return small.resize((w, h), Image.NEAREST).filter(ImageFilter.GaussianBlur(6))


def main():
    ap = argparse.ArgumentParser(
        description="Blur strain names and local paths in the dashboard screenshot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage\n-----\n", 1)[1],
    )
    ap.add_argument("--src", default=SRC, help=f"input image (default {SRC})")
    ap.add_argument("--out", default=OUT, help=f"output image (default {OUT})")
    ap.add_argument("--preview", action="store_true",
                    help="outline and label the boxes instead of blurring them")
    args = ap.parse_args()

    im = Image.open(args.src).convert("RGB")
    if im.size != EXPECTED_SIZE:
        print(f"  [!] {args.src} is {im.size[0]}x{im.size[1]}, expected "
              f"{EXPECTED_SIZE[0]}x{EXPECTED_SIZE[1]}.\n"
              f"      The boxes below were measured against the expected size and are "
              f"almost certainly wrong.\n"
              f"      Re-measure them, checking with --preview, before trusting the output.")

    if args.preview:
        draw = ImageDraw.Draw(im)
        for name, box in BOXES.items():
            draw.rectangle(box, outline=(255, 0, 255), width=3)
            draw.text((box[0], max(0, box[1] - 12)), name, fill=(255, 0, 255))
            print(f"  outlined {name:22} {box}")
    else:
        for name, box in BOXES.items():
            im.paste(redact(im.crop(box)), box)
            print(f"  redacted {name:22} {box}")

    im.save(args.out)
    print(f"\nwrote {args.out}")
    if not args.preview:
        print("Check it by eye at full size before publishing — this hides unpublished data.")


if __name__ == "__main__":
    main()
