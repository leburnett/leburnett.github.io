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

    # Show what a full sweep would do, without writing anything
    python3 scripts/optimise-image.py --fix --dry-run

    # Sweep the whole of assets/: shrink everything over budget, archive each
    # original to image-originals/, and repoint any reference whose filename
    # changed extension
    python3 scripts/optimise-image.py --fix

Presets
-------
    card    1200px wide, quality 85  — project card images and social previews
    figure  1600px wide, quality 88  — in-page figures (these open in the lightbox)

If no preset is given, files named `card.*` use `card`, everything else `figure`.

--fix
-----
`--fix` is the whole-folder sweep. For every image over the budget it:

  1. copies the original to image-originals/<folder>/ (never deletes it — an
     existing archive is kept and the new one suffixed -v2, -v3, …),
  2. re-encodes it with the preset its filename implies, and
  3. if the extension changed (a .png that compresses better as JPEG becomes
     .jpg), rewrites every reference to it across the site's .qmd, .yml and
     .scss sources.

Step 3 is the reason this exists. Converting by hand leaves `image:` fields and
`![](…)` links pointing at a filename that no longer exists, which shows up as
a silently missing card rather than an error.

Run `--fix --dry-run` first: it prints the plan and touches nothing. Because the
output extension depends on which encoder wins, a dry run can only say a rename
is *possible*, not that it will happen.

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
import re
import shutil
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
    print("\nTo fix:  python3 scripts/optimise-image.py --fix   (add --dry-run first)")
    return 1


# --- --fix ------------------------------------------------------------------
# Files searched for references to a renamed image. Deliberately narrow: the
# site's own sources, not _site/ (a build artefact) or image-originals/.
REFERENCE_GLOBS = ["*.qmd", "projects/*.qmd", "blog/**/*.qmd", "*.yml", "*.scss"]

# Where an original is moved before being replaced. Gitignored, so it keeps
# untracked sources recoverable — `--replace` alone would delete them.
ARCHIVE_ROOT = "image-originals"


def archive_path(path):
    """image-originals/<parent dir name>/<filename>, so archives mirror the
    per-project folders under assets/projects/."""
    parent = os.path.basename(os.path.dirname(path)) or "misc"
    return os.path.join(ARCHIVE_ROOT, parent, os.path.basename(path))


def site_ref(path):
    """The root-relative form the site uses, e.g. /assets/projects/x/card.jpg."""
    rel = os.path.relpath(os.path.abspath(path), os.getcwd())
    return "/" + rel.replace(os.sep, "/")


def find_references(old_ref):
    """Return {file: count} for every source file mentioning `old_ref`.

    Matches both the root-relative form and the bare path without the leading
    slash, since either can appear in markdown.
    """
    hits = {}
    bare = old_ref.lstrip("/")
    # The bare form is a substring of the root-relative one, so counting both
    # naively double-counts every slashed hit. Count slashed occurrences, then
    # only those bare occurrences not preceded by a slash.
    bare_only = re.compile(r"(?<!/)" + re.escape(bare))
    seen = {p for g in REFERENCE_GLOBS for p in glob.glob(g, recursive=True)}
    for f in sorted(seen):
        try:
            text = open(f, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        n = text.count(old_ref) + len(bare_only.findall(text))
        if n:
            hits[f] = n
    return hits


def rewrite_references(old_ref, new_ref, dry_run):
    """Point every reference at the new filename. Returns files touched."""
    touched = []
    for f, n in find_references(old_ref).items():
        if not dry_run:
            text = open(f, encoding="utf-8").read()
            # Longest form first, so replacing the slashless variant cannot
            # corrupt a root-relative path that contains it.
            text = text.replace(old_ref, new_ref)
            text = text.replace(old_ref.lstrip("/"), new_ref.lstrip("/"))
            open(f, "w", encoding="utf-8").write(text)
        print(f"        {'would update' if dry_run else 'updated'} {f} ({n} reference{'s' if n > 1 else ''})")
        touched.append(f)
    if not touched:
        print("        no references found — check nothing points at the old name")
    return touched


def is_spent(path):
    """True for a still JPEG already at or below its preset width.

    Re-encoding one of these is a bad trade: JPEG is lossy, so a second pass
    discards image quality while typically saving under a percent. Such a file
    needs its source resized or recompressed, not another round-trip.
    """
    if os.path.splitext(path)[1].lower() not in (".jpg", ".jpeg"):
        return False
    try:
        with Image.open(path) as im:
            if getattr(im, "n_frames", 1) > 1:
                return False
            width = im.size[0]
    except OSError:
        return False
    preset = "card" if os.path.splitext(os.path.basename(path))[0] == "card" else "figure"
    return width <= PRESETS[preset][0]


def fix(budget_kb=BUDGET_KB, dry_run=False, gif_pinned=(None, None, None)):
    """Shrink every over-budget image, archiving originals and repointing any
    references whose filename extension changes."""
    seen = sorted({p for g in SEARCH_GLOBS for p in glob.glob(g, recursive=True)})
    over = [p for p in seen if os.path.getsize(p) > budget_kb * 1024]

    if not over:
        print(f"Nothing over {budget_kb} KB — no changes needed.")
        return 0

    print(f"{len(over)} image(s) over {budget_kb} KB"
          f"{'  (DRY RUN — nothing will be written)' if dry_run else ''}:\n")

    renamed, failed = [], []
    for path in over:
        print(f"  {path}  ({human(os.path.getsize(path))})")

        if dry_run:
            # Report the plan without touching anything. The exact output
            # filename depends on which encoder wins, which we cannot know
            # without doing the work, so flag that a rename is possible.
            print(f"        would archive original to {archive_path(path)}")
            try:
                animated = getattr(Image.open(path), "n_frames", 1) > 1
            except OSError:
                animated = False
            if animated:
                print("        animated — would search GIF_LADDER for settings that fit; "
                      "stays .gif, so no reference changes")
            else:
                preset = "card" if os.path.splitext(os.path.basename(path))[0] == "card" else "figure"
                print(f"        would re-encode with the {preset} preset")
            refs = find_references(site_ref(path))
            if refs:
                total = sum(refs.values())
                print(f"        {total} reference(s) in {len(refs)} file(s): "
                      f"{', '.join(sorted(refs))}")
                if not animated and path.lower().endswith(".png"):
                    print("        may become .jpg — those references would be repointed")
            continue

        # A JPEG already at or below its preset width has nothing left to give:
        # re-encoding it buys a fraction of a percent and costs a generation of
        # quality. Leave it alone and report it — the source needs resizing or
        # recompressing by hand.
        if is_spent(path):
            with Image.open(path) as probe:
                w = probe.size[0]
            print(f"        already {w}px JPEG — re-encoding would cost quality for "
                  f"~no gain; resize or recompress the source by hand")
            failed.append(path)
            continue

        # Archive first: optimise() with --replace deletes the original.
        arch = archive_path(path)
        os.makedirs(os.path.dirname(arch), exist_ok=True)
        if os.path.exists(arch):
            base, ext = os.path.splitext(arch)
            n = 2
            while os.path.exists(f"{base}-v{n}{ext}"):
                n += 1
            arch = f"{base}-v{n}{ext}"
        shutil.copy2(path, arch)
        print(f"        archived original to {arch}")

        old_ref = site_ref(path)
        out = optimise(path, None, True, False, budget_kb, gif_pinned)
        if out is None:
            failed.append(path)
            continue
        new_ref = site_ref(out)
        if new_ref != old_ref:
            renamed.append((old_ref, new_ref))
            rewrite_references(old_ref, new_ref, dry_run)
        # Being smaller is not the same as being small enough.
        if os.path.getsize(out) > budget_kb * 1024:
            print(f"        [!] still {human(os.path.getsize(out))} — over the "
                  f"{budget_kb} KB budget")
            failed.append(out)

    print()
    if dry_run:
        print("Dry run only. Re-run without --dry-run to apply.")
        return 0
    if renamed:
        print(f"{len(renamed)} file(s) changed extension and had references repointed.")
    if failed:
        print(f"{len(failed)} image(s) still need attention by hand:")
        for p in failed:
            print(f"  {p}")
    print("\nRe-run `--check` to confirm, then rebuild before committing.")
    return 1 if failed else 0


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
    ap.add_argument("--fix", action="store_true",
                    help="sweep assets/: shrink everything over budget, archive originals "
                         "and repoint references whose extension changed")
    ap.add_argument("--dry-run", action="store_true",
                    help="with --fix, print the plan without writing anything")
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
    if args.fix:
        sys.exit(fix(args.budget, args.dry_run,
                     (args.gif_width, args.gif_frame_step, args.gif_colors)))
    if args.dry_run:
        sys.exit("--dry-run only applies to --fix.")
    if not args.paths:
        ap.print_help()
        sys.exit(1)

    gif_pinned = (args.gif_width, args.gif_frame_step, args.gif_colors)
    for p in args.paths:
        optimise(p, args.preset, args.replace, args.force, args.budget, gif_pinned)


if __name__ == "__main__":
    main()
