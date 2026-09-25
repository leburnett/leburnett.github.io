# Project pages — working notes

Reference for editing the project pages in `projects/`. Covers the conventions in
use, the mechanics behind the projects grid, gotchas that have already cost time,
and what's outstanding.

---

## 1. How a project page becomes a card

`projects/index.qmd` runs a Quarto listing over `projects/*.qmd` and renders each
one through `_project-card.ejs`. **There is no hand-written HTML for the grid** —
adding a `.qmd` adds a card.

Frontmatter fields the card template reads:

| Field | Purpose |
|---|---|
| `title` | Card heading. **Plain text only** — see gotcha 1. |
| `subtitle` | The one line under the title. Falls back to `description` if absent. |
| `image` / `imagealt` | Card image, root-relative (`/assets/projects/<slug>/card.jpg` *or* `.png` — the optimiser keeps whichever format is smaller, so check which one actually exists). Also becomes the page's social-preview image, and is shown at the top of the page itself. |
| `kinds` | Coloured pills: `Experiments`, `Data Analysis`, `Web Resource`, `Pipeline`. Adding a new value needs a colour in `custom.scss`. |
| `priority` | Sort order, ascending. Controls position in the grid. |
| `categories` | Chips shown on the project page itself (not the card). |
| `description` | SEO + social text. Aim 140–160 chars. Not shown on the page (hidden via CSS). |

Current order (`priority`): connectome 1, neuview 2, freely-walking 3,
nested-rf 4, burnett-2024 5, madm 7, enteric 8. (`reiser-documentation` was
deleted; 6 is now unused, which is harmless — the sort only needs to be
ascending, not contiguous.)

---

## 2. Conventions

### Boxes

Two styles, both fenced divs. Defined in `custom.scss` (shared layout, separate
surfaces) with dark-mode overrides in `custom-dark.scss`.

```markdown
::: {.problem-box}      <!-- filled grey — framing question / result -->
## Problem
...
:::

::: {.note-box}         <!-- thin outline — asides, and the Highlights box -->
## Highlights
- ...
:::
```

Keep to ~3–4 boxes per page. They work by contrast; past that they become the
page's default texture and stop signalling anything. `burnett-2024` currently has
five and is at the limit; everything else sits at 1–3.

### The card image as page hero

Every project page opens with its own card image, uncaptioned, as the first
thing in the body — before the Highlights box:

```markdown
![](/assets/projects/<slug>/card.png){fig-alt="…"}
```

Normally uncaptioned. **It still needs `fig-alt`** — Quarto derives `alt` from
the caption, so an uncaptioned image with no `fig-alt` reaches screen readers as
nothing at all. Copy the frontmatter `imagealt` into it.

Caption the hero when the image needs an attribution — `connectome`'s carries
an HHMI copyright line. **Give it a caption but no `#fig-` label**: Quarto only
numbers a figure that has one, so an unnumbered caption sits happily above
`Figure 1` and keeps the attribution visible without consuming a number.

Because that one file is now the grid card, the social preview *and* the page
hero, `imagealt` has to describe the image accurately — if the card is ever
swapped, `imagealt` is easy to forget and goes stale silently.

### The Highlights box

Goes at the top of every project page, in a `.note-box`, immediately after the
hero image. Content is **what you gained from the project**, not what the
project was about.

House style for the bullets, agreed this session:

- **Open every bullet with a past-tense verb.** Not "Participated in", "Became
  experienced with", "Improved my" — those describe exposure. "Wrote", "Built",
  "Performed", "Led" describe work.
- **Evidence over adjectives.** Cut "large scale", "numerous", "successful",
  "custom". Replace with a number where one exists (14 contributors, 150,000+
  neurons, 11 students).
- **Bold the searchable terms, not the soft nouns.** Neo4j, Cypher, Snakemake,
  pandas, PLOS Biology — not "collaborative coding" or "technical writing".
- **Name credentials explicitly.** "Published as first author in PLOS Biology"
  beats "resulted in a published, peer-reviewed article".
- **Keep grammatical structure parallel** across the five bullets.

Worked example (connectome), after rewriting:

```markdown
::: {.note-box}
## Highlights
- Contributed to a shared codebase with 14 contributors, **authoring and reviewing pull requests** as part of the team's review process.
- Helped release the analysis as an **"executable paper"**: **Snakemake** pipelines that build the 3D neuron renders, plus **Jupyter notebooks** that reproduce each figure from the source data.
- Wrote **Cypher** queries against a **Neo4j** graph database to analyse connectivity across **150,000+ neurons**.
- Applied **object-oriented design** and the core Python data stack (**pandas**, **Plotly**) across the analysis code.
- Documented code for reuse by others: **docstrings**, **READMEs** and inline comments.
:::
```

### Page skeleton

The standard structure, now on connectome / neuview / freely-walking /
nested-rf / madm, is:

```
card hero  →  Highlights (note-box)  →  Background  →  Problem (problem-box)
→  Methods  →  Outcome (problem-box)  →  Links  →  References  →  Acknowledgements
```

`References` and `Acknowledgements` are optional; use them where there is
something to cite or someone to credit.

`burnett-2024` runs a deliberately bespoke shape (paired `Hypothesis I` /
`Hypothesis II` sections, plus a `Colloquial context`) and is left alone.
`enteric` is the last page still on the old `Overview → Links` shape. `madm` is
converged apart from a stray `Overview` section that should be folded in.

### Images

**Always run new images through the script before referencing them:**

```bash
python3 scripts/optimise-image.py <path> --card --replace     # 1200px, q85
python3 scripts/optimise-image.py <path> --figure --replace   # 1600px, q88
python3 scripts/optimise-image.py --check                     # audit, exits 1 if over budget
```

It resizes, tries JPEG and PNG, and keeps whichever is smaller. Full guidance in
`assets/projects/README.md`.

- One folder per project: `assets/projects/<slug>/`, with `card.*` plus figures.
- Reference root-relative: `![Caption.](/assets/projects/<slug>/fig.jpg)`
- **Figure numbers are generated, never typed.** Give a figure a `#fig-` label
  and write the caption with no number:
  `![The behavioural rig. …](/assets/…/setup.jpg){#fig-setup}` renders as
  "Figure 2: The behavioural rig. …". Insert or reorder figures freely — the
  numbers follow. A label also lets you write `@fig-setup` in the prose to get
  a live cross-reference.
- A caption with **no** `#fig-` label renders unnumbered. That is what the page
  heroes use.
- `crossref: title-delim: ":"` in `_quarto.yml` sets the separator. **Do not
  set it to `"."`** — Quarto emits that twice ("Figure 1.."), though every other
  value renders once. Hence the colon.
- `{width=50%}` halves the rendered size (aspect ratio is preserved, so width
  and height scale together). Useful for tall full-page screenshots, which
  otherwise run several screens deep — the reading column is 720px.
- Every figure is click-to-enlarge (`lightbox: auto`), so a caption should be
  self-contained: figures get read enlarged and out of order.
- **Omit `--replace` if the original isn't committed** — otherwise there's no way
  back. Untracked originals are moved to `image-originals/<slug>/` (gitignored)
  rather than deleted.
- **Format changes rename the file.** A `.png` that compresses better as JPEG
  comes out as `.jpg`, so every reference to it — including frontmatter
  `image:` — has to be updated. The script prints the new path when this
  happens.
- A CI step in `.github/workflows/publish.yml` fails the deploy if any image in
  `assets/` exceeds 600 KB. GIFs are included in that check.

**Animated GIFs** take a separate path in the same script, which preserves the
animation (the still-image path would keep only the first frame). It searches
resolution / frame-thinning / palette settings until the result fits the budget;
`--gif-width`, `--gif-frame-step` and `--gif-colors` pin them by hand. A
12-second screen capture went 3.96 MB → 519 KB this way, at the same duration.
Three things in there are worth knowing before touching that code, and all are
documented at the top of the script: the animation needs **one shared palette**
(per-frame palettes defeat Pillow's frame-diffing and can make the output
*larger* than the input), `MAXCOVERAGE` beats `MEDIANCUT` for a mostly-dark
capture, and a **reserved neutral grey ramp** is needed or light greys pick up a
visible blue/pink cast.

### Redacting a screenshot

`scripts/redact-dash.py` blurs the strain names and local paths in the optomotor
dashboard screenshot, which is a real view of unpublished data. Run it on the
original capture and *then* optimise, so the downscale destroys anything the
blur leaves. `--preview` outlines and labels the boxes instead of blurring, for
re-checking after a re-capture — the coordinates are tied to one exact 3130×1204
capture and the script warns if the input is a different size. Check the output
by eye at full size before publishing.

---

## 3. Gotchas that have already cost time

**1. Quarto HTML-escapes listing field values.** Markup in a `title` renders as
literal text on the card (`<i>` shows as `&lt;i&gt;`). No workaround found —
tested several. Use Unicode instead: `nNOS⁻/⁻`, not `nNOS<sup>−/−</sup>`. This is
why gene and species names aren't italicised in card titles.

**2. Only one Quarto process may touch the project at a time.** Not just
"don't render while previewing" — *two previews race just as badly*, and so does
a render against someone else's preview. Symptoms: edits silently vanish, the
SASS cache corrupts (`BadResource: Bad resource ID`), or the build dies with

```
ERROR: NotFound: No such file or directory (os error 2):
rename '…/projects/<page>.html' -> '…/_site/projects/<page>.html'
    at safeMoveSync … at renderProject …
```

That error is **always** a concurrency collision, never a broken page. Quarto
renders each `.qmd` to an HTML file *beside its source* and then moves it into
`output-dir` (`quarto.js`, in `renderProject`):

```js
safeMoveSync(join4(projDir, renderedFile.file), outputFile5);
```

`safeMoveSync` only recovers from `EXDEV` (cross-filesystem moves) and rethrows
everything else, so when a second process has already moved the file the
`renameSync` fails with `NotFound`. The page named in the error is just whichever
one lost the race — which is why the name changes run to run. This also explains
why `ls projects/*.html` finds nothing: those files exist for milliseconds.

Before rendering, check what's already running:

```bash
ps -eo pid,etime,command | grep "[q]uarto preview"
lsof -nP -iTCP -sTCP:LISTEN | grep deno     # which port a preview holds
```

`quarto preview` picks a **random** port unless given `--port`, so don't assume
4200 means "mine". To recover: leave one process alive, then stop preview,
`rm -rf .quarto _site`, `quarto render`, restart preview. Deleting `.quarto/` is
always safe — it's a cache — but doing it *underneath* a running preview leaves
that preview stale, so restart it afterwards.

**3. `quarto render <one-file.qmd>` does not re-copy site assets.** Replacing an
image and rendering a single page leaves the old image in `_site/`. Use a full
`quarto render`, then hard-reload (Cmd+Shift+R) since the URL is unchanged.

The same trap catches a *running preview*: if only an asset changed and no
`.qmd` did, the preview has nothing to rebuild, so it keeps serving the old
file. Symptom is a stale image with a correct-looking page. Either touch the
`.qmd`, or copy the file straight into `_site/assets/…` — and hard-reload
either way.

**4. Quarto merges a fenced div with the section it contains.** `::: {.hero}`
wrapping a `#` heading produces `<section class="level1 hero">`, not a nested
div. Wrapping a level-1 heading in an *inner* div makes Quarto promote it to the
page title and hoist it out of the container entirely.

**5. Don't name two sections `## Highlights` on one page.** All pages are now
down to one, at the top. Keep it that way: when adding to a page, fold new
material into the existing box rather than starting a second one.

**6. Whitespace between inline-block elements counts** in narrow containers.
Cost two separate wrapping bugs in the sidebar. Flex with `gap` avoids it.

**7. `listings.json` 404s on every project page.** Cosmetic, deliberately left.
Quarto only emits the `quarto:offset` meta when site search is enabled; without
it the category-activation fetch resolves to the wrong path. Fixing it makes the
category chips into links to `#category=X`, which **doesn't filter** — the custom
EJS template emits no `.listing-category` elements. A dead link is worse than a
silent 404, so it stays.

---

## 4. Current state

Words are of rendered body text; figures are captioned figures, excluding the
card hero. In grid order.

| Pri | Page | Words | Figures | Skeleton | Highlights |
|---:|---|---:|---:|---|---|
| 1 | connectome | 762 | 3 | standard | ✅ top |
| 2 | neuview | 1152 | 5 | standard | ✅ top |
| 3 | freely-walking | 1923 | 7 | standard | ✅ top |
| 4 | burnett-2024 | 1886 | 5 | bespoke (Hypothesis I/II) | ✅ top |
| 5 | nested-rf | 297 | 0 | standard | ⚠️ still at bottom |
| 7 | madm | 237 | 0 | standard + stray `Overview` | ✅ top |
| 8 | enteric | 261 | 0 | `Overview → Links` only | ✅ top |

All seven now open with their card image as an uncaptioned hero, and all seven
have exactly one `## Highlights`.

---

## 5. Outstanding

**On the project pages**

1. **Expand the three thin pages** — `nested-rf` (297 words), `madm` (237) and
   `enteric` (261). They have no figures at all, against 762–1923 words and 3–7
   figures on the four that have been worked through. `nested-rf` matters most:
   it is card #5 and one of the more data-science-relevant projects.
2. **Add at least one figure to each of those three.** Now that every page opens
   with a card hero, a page with no other image looks conspicuously bare.
3. **Move `## Highlights` to the top on `nested-rf`** and rewrite the bullets to
   the house style above. It is the last page with it at the bottom.
4. **Finish converging `enteric` and `madm`.** `enteric` is still
   `Overview → Links`; `madm` has a stray `Overview` section to fold into
   Background or Methods.
5. **Refer to figures from the prose.** Every figure now has a `#fig-` label,
   so `@fig-setup` produces a numbered cross-reference that also links to it.
   No page currently points at a figure from its body text.
6. **`freely-walking`'s `card.png` is 437 KB** — inside the budget but 2–8×
   heavier than the other cards, and it is now loaded on both the grid and the
   page. Running it through `--card` would roughly halve it.

**Elsewhere**

7. **Cloudflare Web Analytics won't collect until pushed.** GA was removed —
   it was running in cookieless consent mode (`gcs=G100`), which meant Google
   accepted the requests and discarded them.
8. **GitHub Pages was silently switched to legacy branch mode**, which took the
   whole site down (every URL 404). Fixed by setting `build_type: workflow`.
   Worth re-checking Settings → Pages if the site ever 404s again.
9. **Consider a custom domain** (e.g. `lauraburnett.dev`). Reads better than
   `github.io` on a CV, survives a move off GitHub Pages, and would make
   ad-blocker-resistant analytics (Fathom) worthwhile.
10. **Check `card.png` heroes in dark mode.** `freely-walking`'s is a white
    BioRender illustration on a transparent background, which renders as a
    bright slab at the top of the page in the dark theme.
11. **`.DS_Store` files sit inside `assets/projects/*/`.** Harmless but they
    turn up in diffs; a `.gitignore` entry plus `git rm --cached` clears them.

---

## 6. Quick reference

```bash
ps -eo pid,etime,command | grep "[q]uarto preview"   # ALWAYS check first — see gotcha 2
lsof -nP -iTCP -sTCP:LISTEN | grep deno              # which port a preview holds
quarto preview                      # build + serve + watch (nothing else may render)
quarto render                       # full build
rm -rf .quarto _site                # clear caches if the build misbehaves
python3 scripts/optimise-image.py --check            # image budget audit
python3 scripts/redact-dash.py --preview             # check redaction boxes
gh run list --limit 3               # deploy status
```

Site: <https://leburnett.github.io> · Local preview: whichever port
`quarto preview` prints — it picks a random one unless given `--port`.
