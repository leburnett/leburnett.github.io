# Project images

One folder per project, named after its `.qmd` file:

    assets/projects/
      connectome/
        card.png          <- the projects-grid card image
        columns.png       <- figures used inside the page
        pipeline.png
      neuview/
        card.png
      ...

Deleting a project means deleting one folder, and nothing else has to be renamed.

## The card image

Set it in the project's frontmatter. Cards are square and the image fills the
top 45%, cropped to fill, so a landscape crop works best:

    image: "/assets/projects/connectome/card.png"
    imagealt: "3D rendering of Drosophila optic lobe neurons."

This doubles as the page's social preview when the link is shared, so it is
worth picking something legible at small sizes.

## Figures inside a page

Standard markdown. The caption is what makes it a numbered figure:

    ![Columns spanning the depth of the optic lobe.](/assets/projects/connectome/columns.png)

Paths start with `/` (site root), so they work from any page without `../`.

Add an ID if you want to refer to it in the text:

    ![Caption here.](/assets/projects/connectome/columns.png){#fig-columns}

    ...as shown in @fig-columns, the columns tile the visual field.

Two side by side:

    ::: {layout-ncol=2}
    ![Left caption.](/assets/projects/connectome/a.png)

    ![Right caption.](/assets/projects/connectome/b.png)
    :::

Control the width of one image:

    ![Caption.](/assets/projects/connectome/wide.png){width=70%}

Every figure is click-to-enlarge (`lightbox: auto` in `_quarto.yml`), which
matters for dense multi-panel figures.

## Preparing the files

- **Max 1600px wide.** Anything larger is wasted — the reading column is ~720px
  and the lightbox scales to the viewport.
- **JPEG (quality ~80) for photos and 3D renders; PNG for plots, diagrams and
  line art.** PNG on a photographic image can be 20x larger for no visible gain.
- **Aim under ~300KB each.** A 2.8MB image is ~15 seconds on a slow connection,
  and the projects page loads every card image at once.
- **Always write `imagealt` / a caption.** Screen readers and search engines
  both rely on it, and a figure with no caption reads as decoration.

To check and resize:

    python3 -c "
    from PIL import Image
    im = Image.open('assets/projects/connectome/card.png')
    im.thumbnail((1600, 10000), Image.LANCZOS)
    im.convert('RGB').save('assets/projects/connectome/card.jpg', quality=82, optimize=True)
    "
