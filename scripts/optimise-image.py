#!/usr/bin/env python3
"""Prepare images for the website: resize, compress, and pick the best format.

Large source images (screenshots, figure exports, 3D renders) are often 10-40x
bigger than they need to be on the web. This script resizes them to a sensible
width, tries both JPEG and PNG, and keeps whichever is smaller — the same logic
used when the existing project images were converted.

Usage
-----
    # Convert one image (writes alongside the original)
    python3 scripts/optimise-image.py assets/projects/madm/card.png

    # Convert and delete the original
    python3 scripts/optimise-image.py assets/projects/madm/card.png --replace

    # Convert several at once
    python3 scripts/optimise-image.py assets/projects/*/*.png

    # A figure that will be opened full-size in the lightbox (wider, higher quality)
    python3 scripts/optimise-image.py assets/projects/connectome/fig.png --figure

    # Check the whole site for images that are too heavy (no changes made)
    python3 scripts/optimise-image.py --check

Presets
-------
    card    1200px wide, quality 85  — project card images and social previews
    figure  1600px wide, quality 88  — in-page figures (these open in the lightbox)

If no preset is given, files named `card.*` use `card`, everything else `figure`.
"""

import argparse
import glob
import io
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required:  python3 -m pip install Pillow")

PRESETS = {
    "card": (1200, 85),
    "figure": (1600, 88),
}

# Anything above this is flagged by --check. Set to catch the real failure mode
# — multi-megabyte source images pasted in unprocessed — rather than to police
# every kilobyte. A dense full-width scientific figure can legitimately sit in
# the 400-500 KB range. Override per-run with --budget.
BUDGET_KB = 600

SEARCH_GLOBS = ["assets/**/*.png", "assets/**/*.jpg", "assets/**/*.jpeg"]


def human(n_bytes):
    kb = n_bytes / 1024
    return f"{kb/1024:.2f} MB" if kb >= 1024 else f"{kb:.0f} KB"


def encode(img, quality):
    """Return (jpeg_bytes, png_bytes) for an already-resized RGB image."""
    jb = io.BytesIO()
    img.save(jb, "JPEG", quality=quality, optimize=True, progressive=True)
    pb = io.BytesIO()
    img.quantize(colors=256, method=Image.MEDIANCUT).save(pb, "PNG", optimize=True)
    return jb.getvalue(), pb.getvalue()


def flatten(im):
    """Composite onto white. Returns (rgb_image, pct_transparent)."""
    pct = 0.0
    if im.mode in ("RGBA", "LA"):
        alpha = im.getchannel("A")
        hist = alpha.histogram()
        pct = 100.0 * sum(hist[:255]) / max(sum(hist), 1)
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=alpha)
        return bg, pct
    return im.convert("RGB"), pct


def optimise(path, preset, replace, force):
    if not os.path.isfile(path):
        print(f"  SKIP  {path} (not a file)")
        return None

    chosen = preset or ("card" if os.path.splitext(os.path.basename(path))[0] == "card" else "figure")
    max_w, quality = PRESETS[chosen]

    im = Image.open(path)
    orig_bytes = os.path.getsize(path)
    orig_size = im.size

    rgb, pct_transparent = flatten(im)
    rgb.thumbnail((max_w, 10**6), Image.LANCZOS)

    jpeg, png = encode(rgb, quality)
    use_jpeg = len(jpeg) <= len(png)
    data, ext = (jpeg, ".jpg") if use_jpeg else (png, ".png")

    if len(data) >= orig_bytes and not force:
        print(f"  KEEP  {path} — already {human(orig_bytes)}, no gain (use --force to convert anyway)")
        return None

    # Where to write. If the best format has the same extension as the input,
    # writing to <stem><ext> would silently destroy the original — so only do
    # that when --replace says it is wanted, otherwise write a separate file.
    stem = os.path.splitext(path)[0]
    out = stem + ext
    if os.path.abspath(out) == os.path.abspath(path) and not replace:
        out = f"{stem}-optimised{ext}"

    with open(out, "wb") as fh:
        fh.write(data)

    note = ""
    if pct_transparent > 5:
        note = f"  [!] {pct_transparent:.0f}% transparent, flattened onto white — check it looks right"

    print(
        f"  OK    {path}\n"
        f"        {orig_size[0]}x{orig_size[1]} {human(orig_bytes)}"
        f"  ->  {rgb.size[0]}x{rgb.size[1]} {human(len(data))} ({chosen}, {ext[1:]})"
        f"  -{100*(1-len(data)/orig_bytes):.0f}%{note}"
    )

    if os.path.abspath(out) != os.path.abspath(path):
        print(f"        wrote {out}")
        if replace:
            os.remove(path)
            print(f"        removed original {path}")
        if os.path.splitext(out)[1] != os.path.splitext(path)[1]:
            # Site references are absolute from the project root, e.g.
            # /assets/projects/madm/card.jpg — only build one for paths that
            # actually sit inside the repo.
            rel = os.path.relpath(os.path.abspath(out), os.getcwd())
            hint = "/" + rel if not rel.startswith("..") else out
            print(f"        update references to: {hint}")
    else:
        print(f"        replaced {path} in place")
    return out


def check(budget_kb=BUDGET_KB):
    """Report images above the size budget. Exit 1 if any are found."""
    seen = sorted({p for g in SEARCH_GLOBS for p in glob.glob(g, recursive=True)})
    over = [(p, os.path.getsize(p)) for p in seen if os.path.getsize(p) > budget_kb * 1024]
    total = sum(os.path.getsize(p) for p in seen)

    print(f"{len(seen)} image(s), {human(total)} total")
    if not over:
        print(f"All within the {budget_kb} KB budget.")
        return 0

    print(f"\n{len(over)} image(s) over {budget_kb} KB:")
    for p, n in sorted(over, key=lambda x: -x[1]):
        print(f"  {human(n):>9}  {p}")
    print("\nTo fix:  python3 scripts/optimise-image.py <path> --replace")
    return 1


def main():
    ap = argparse.ArgumentParser(
        description="Resize and compress images for the website.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage\n-----\n", 1)[1],
    )
    ap.add_argument("paths", nargs="*", help="image files to convert")
    ap.add_argument("--card", dest="preset", action="store_const", const="card",
                    help="1200px / q85 — card images and social previews")
    ap.add_argument("--figure", dest="preset", action="store_const", const="figure",
                    help="1600px / q88 — in-page figures opened in the lightbox")
    ap.add_argument("--replace", action="store_true",
                    help="delete the original after converting")
    ap.add_argument("--force", action="store_true",
                    help="write the output even if it is not smaller")
    ap.add_argument("--check", action="store_true",
                    help=f"report images over the budget ({BUDGET_KB} KB) and exit non-zero")
    ap.add_argument("--budget", type=int, default=BUDGET_KB, metavar="KB",
                    help=f"size budget for --check (default {BUDGET_KB})")
    args = ap.parse_args()

    if args.check:
        sys.exit(check(args.budget))
    if not args.paths:
        ap.print_help()
        sys.exit(1)

    for p in args.paths:
        optimise(p, args.preset, args.replace, args.force)


if __name__ == "__main__":
    main()
