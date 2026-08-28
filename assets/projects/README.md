Card images for the projects grid.

Add one image per project, named after its `.qmd` file:

    connectome.jpg
    neuview.jpg
    freely-walking-optomotor.jpg
    reiser-documentation.jpg
    nested-rf.jpg
    burnett-2024.jpg
    madm.jpg
    enteric.jpg

Then reference it in that project's frontmatter:

    image: /assets/projects/connectome.jpg
    imagealt: "Short description of the image for screen readers."

Cards are square and the image fills the top 45%, cropped to fill
(`object-fit: cover`), so a landscape crop around 800x450 works well.
A card with no `image:` simply renders without one.
