# leburnett.github.io

Personal portfolio and blog built with [Quarto](https://quarto.org), deployed via GitHub Pages.

## Local Development

```bash
# Preview the site locally (auto-reloads on changes)
quarto preview

# Render the site to _site/
quarto render
```

## Adding Content

### New blog post

Create a new directory and file:

```
blog/posts/my-post-title/index.qmd
```

With frontmatter:

```yaml
---
title: "My Post Title"
date: "2026-03-15"
description: "A short description."
categories: [data-science]
---
```

### New project

Create a new file in `projects/`:

```
projects/my-project.qmd
```

With frontmatter:

```yaml
---
title: "My Project"
description: "One-line description."
categories: [Python, Data Science]
priority: 5
---
```

## Configuration

- **`_quarto.yml`** — Site structure, navigation, theme
- **`_variables.yml`** — Centralized links (GitHub, LinkedIn, Scholar, repo URLs). Update URLs here and they propagate to all pages via `{{< var links.github >}}` shortcodes
- **`custom.scss`** — Visual styling overrides

## Deployment

Automated via GitHub Actions on push to `main`. Configure GitHub Pages source to "GitHub Actions" in repository Settings > Pages.
