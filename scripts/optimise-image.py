#!/usr/bin/env python3
"""Prepare images for the website: resize, compress, and pick the best format.

Large source images (screenshots, figure exports, 3D renders) are often 10-40x
bigger than they need to be on the web. This script resizes them to a sensible
width, tries both JPEG and PNG, and keeps whichever is smaller — the same logic
used when the existing project images were converted.

Animated GIFs (UI screencasts) take a different route that keeps the animation:
see "Animated GIFs" below. Still images and animations are both covered by
--check.

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

    # An animated screencast — searches for settings that fit the budget
    python3 scripts/optimise-image.py assets/projects/neuview/demo.gif --replace

    # Force particular GIF settings instead of searching
    python3 scripts/optimise-image.py demo.gif --gif-width 500 --gif-frame-step 4

    # Check the whole site for images that are too heavy (no changes made)
    python3 scripts/optimise-image.py --check

Presets
-------
    card    1200px wide, quality 85  — project card images and social previews
    figure  1600px wide, quality 88  — in-page figures (these open in the lightbox)

If no preset is given, files named `card.*` use `card`, everything else `figure`.

Animated GIFs
-------------
The still-image path would flatten an animation to its first frame, so animated
GIFs are re-encoded instead: frames are resized, every Nth frame is kept (the
dropped frames' durations are added to the survivors, so the clip runs for the
same length of time), and the whole animation shares one palette. Settings are
searched from GIF_LADDER until the result fits the budget; --gif-width,
--gif-frame-step and --gif-colors pin them by hand.

Three details do most of the work, and all three are easy to get wrong:

  * One shared palette. Quantising each frame separately gives every frame its
    own palette, which stops Pillow cropping frames to the region that changed.
    That alone can make the output several times *larger* than the input.
  * MAXCOVERAGE, not MEDIANCUT. Median-cut allocates palette entries by pixel
    population, so in a mostly-dark screencast the small areas of saturated
    colour that carry the meaning get flattened away.
  * A reserved neutral grey ramp (GIF_GREY_SLOTS). Without it, light grey and
    white areas map to the nearest tinted palette entry and the whole thing
    picks up a blue or pink cast. See the comment on GIF_GREY_SLOTS.
"""

import argparse
import glob
import io
import os
import sys

try:
    from PIL import Image, ImageSequence
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

# GIFs are included: an unprocessed screencast is the heaviest thing likely to
# be committed here (a 12-second capture arrived at 4 MB), and leaving them out
# meant --check passed while the deploy shipped it.
SEARCH_GLOBS = [
    "assets/**/*.png",
    "assets/**/*.jpg",
    "assets/**/*.jpeg",
    "assets/**/*.gif",
]

# (width, frame_step, colours), tried in order until one fits the budget. Width
# comes down first because it is the biggest lever; frames are thinned next;
# the palette is only cut once resolution has been given up, since that is what
# costs the most visible quality.
GIF_LADDER = [
    (900, 1, 256),
    (800, 2, 256),
    (720, 2, 256),
    (640, 3, 256),
    (600, 3, 256),
    (560, 3, 256),
    (500, 3, 256),
    (500, 4, 192),
    (440, 4, 128),
]

# Aim a little under the budget so a GIF is not left sitting on the limit.
GIF_TARGET_FRACTION = 0.9

# Palette entries reserved for a true neutral grey ramp. An adaptive palette
# picks colours by where the pixels actually are in colour space, and on a
# screenshot that is mostly dark it will not spend an entry on plain grey — so
# light neutral areas (a white background, a grey table, the white shell of a
# 3D render) get mapped to the nearest tinted entry and pick up a visible blue
# or pink cast. Forcing a ramp of exact greys removes it: measured on the
# neutral pixels of a Neuroglancer capture, mean R/G/B spread went from 5.0
# (peaks of 25 — clearly visible) to 0.0. It costs perhaps 10% in file size,
# because more distinct values in the dominant grey region compress less well.
GIF_GREY_SLOTS = 32


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


def gif_frames(path, width, step):
    """Return (rgb_frames, durations_ms) for a GIF, resized and thinned.

    Every `step`-th frame is kept. The durations of the dropped frames are
    added to the frame that survives them, so the clip still runs for exactly
    as long as it did before — it just plays at a lower frame rate.
    """
    im = Image.open(path)
    frames, durations, carried = [], [], 0
    for i, frame in enumerate(ImageSequence.Iterator(im)):
        ms = frame.info.get("duration", 100)
        if i % step:
            carried += ms
            continue
        rgb = frame.convert("RGB")
        if width and rgb.width > width:
            rgb = rgb.resize((width, round(rgb.height * width / rgb.width)), Image.LANCZOS)
        frames.append(rgb)
        durations.append(ms + carried)
        carried = 0
    if carried and durations:
        durations[-1] += carried
    return frames, durations


def gif_master_palette(frames, colors, grey_slots=GIF_GREY_SLOTS):
    """Build one palette for the whole animation: a neutral grey ramp plus
    adaptive colours sampled from across the clip."""
    # Sampled from frames spread through the animation rather than from the
    # first frame, which on a screencast is often just the starting state and
    # misses colours that only appear later.
    n = len(frames)
    w, h = frames[0].size
    picks = list(range(0, n, max(1, n // 8)))[:8]
    strip = Image.new("RGB", (w, h * len(picks)))
    for slot, idx in enumerate(picks):
        strip.paste(frames[idx], (0, slot * h))

    n_adaptive = max(2, colors - grey_slots)
    adaptive = strip.quantize(colors=n_adaptive, method=Image.MAXCOVERAGE)
    pal = adaptive.getpalette()
    colours = [tuple(pal[i:i + 3]) for i in range(0, 3 * n_adaptive, 3)]
    greys = [(round(255 * i / (grey_slots - 1)),) * 3 for i in range(grey_slots)] if grey_slots > 1 else []

    # Greys first so they survive the 256-entry clamp; dict.fromkeys dedupes
    # while keeping order, since an adaptive entry may already be a pure grey.
    combined = list(dict.fromkeys(greys + colours))[:256]
    flat = [c for triple in combined for c in triple]
    flat += [0] * (768 - len(flat))
    master = Image.new("P", (1, 1))
    master.putpalette(flat)
    return master


def encode_gif(frames, durations, colors):
    """Encode RGB frames as one animated GIF under a single shared palette."""
    master = gif_master_palette(frames, colors)

    # Quantising against `master` gives every frame the same palette, which is
    # what lets Pillow's optimiser store only the changed region of each frame.
    paletted = [f.quantize(palette=master, dither=Image.NONE) for f in frames]
    buf = io.BytesIO()
    paletted[0].save(
        buf, "GIF", save_all=True, append_images=paletted[1:],
        duration=durations, loop=0, optimize=True,
    )
    return buf.getvalue()


def optimise_gif(path, replace, force, budget_kb, pinned):
    """Re-encode an animated GIF to fit the budget, keeping the animation.

    `pinned` is (width, frame_step, colors); any entry that is None is searched
    for using GIF_LADDER.
    """
    orig_bytes = os.path.getsize(path)
    src = Image.open(path)
    orig_size, orig_frames = src.size, getattr(src, "n_frames", 1)
    target = int(budget_kb * 1024 * GIF_TARGET_FRACTION)

    pin_w, pin_step, pin_colors = pinned
    if all(v is not None for v in pinned):
        attempts = [pinned]
    else:
        attempts = []
        for w, step, colors in GIF_LADDER:
            attempt = (pin_w or w, pin_step or step, pin_colors or colors)
            if attempt not in attempts:
                attempts.append(attempt)

    best = None
    for width, step, colors in attempts:
        frames, durations = gif_frames(path, width, step)
        data = encode_gif(frames, durations, colors)
        size = frames[0].size
        print(
            f"        try {size[0]}x{size[1]} step{step} {colors}c"
            f"  ->  {human(len(data))} ({len(frames)} frames)"
        )
        if best is None or len(data) < len(best[0]):
            best = (data, size, step, colors, len(frames), durations)
        if len(data) <= target:
            break

    data, size, step, colors, n_frames, durations = best
    if len(data) >= orig_bytes and not force:
        print(f"  KEEP  {path} — already {human(orig_bytes)}, no gain (use --force to convert anyway)")
        return None

    # A GIF always stays a GIF, so the output path collides with the input
    # unless --replace says overwriting is wanted.
    stem = os.path.splitext(path)[0]
    out = path if replace else f"{stem}-optimised.gif"
    with open(out, "wb") as fh:
        fh.write(data)

    note = ""
    if len(data) > budget_kb * 1024:
        note = f"  [!] still over the {budget_kb} KB budget — pin smaller settings by hand"

    print(
        f"  OK    {path}\n"
        f"        {orig_size[0]}x{orig_size[1]} {orig_frames} frames {human(orig_bytes)}"
        f"  ->  {size[0]}x{size[1]} {n_frames} frames {human(len(data))}"
        f"  ({sum(durations)/1000:.1f}s, {colors}c)"
        f"  -{100*(1-len(data)/orig_bytes):.0f}%{note}"
    )
    print(f"        {'replaced ' + path + ' in place' if replace else 'wrote ' + out}")
    return out


def optimise(path, preset, replace, force, budget_kb=BUDGET_KB, gif_pinned=(None, None, None)):
    if not os.path.isfile(path):
        print(f"  SKIP  {path} (not a file)")
        return None

    # Animations must not go through the still-image path: it would keep only
    # the first frame and silently throw the animation away.
    probe = Image.open(path)
    if getattr(probe, "n_frames", 1) > 1:
        if probe.format == "GIF":
            return optimise_gif(path, replace, force, budget_kb, gif_pinned)
        print(f"  SKIP  {path} — animated {probe.format}, not handled (would lose all but the first frame)")
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
                    help=f"size budget for --check and for GIF search (default {BUDGET_KB})")
    ap.add_argument("--gif-width", type=int, metavar="PX",
                    help="pin animated GIF width instead of searching GIF_LADDER")
    ap.add_argument("--gif-frame-step", type=int, metavar="N",
                    help="pin animated GIF frame thinning (2 = keep every other frame)")
    ap.add_argument("--gif-colors", type=int, metavar="N",
                    help="pin animated GIF palette size (2-256)")
    args = ap.parse_args()

    if args.check:
        sys.exit(check(args.budget))
    if not args.paths:
        ap.print_help()
        sys.exit(1)

    gif_pinned = (args.gif_width, args.gif_frame_step, args.gif_colors)
    for p in args.paths:
        optimise(p, args.preset, args.replace, args.force, args.budget, gif_pinned)


if __name__ == "__main__":
    main()
