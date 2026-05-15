# leburnett.github.io

Personal portfolio and blog built with [Quarto](https://quarto.org), deployed via GitHub Pages.

## Local Development

```bash
# Preview the site locally (auto-reloads on changes)
quarto preview

# Render the site to _site/
quarto render
```

## Configuration

- **`_quarto.yml`** — Site structure, navigation, theme
- **`_variables.yml`** — Centralized links (GitHub, LinkedIn, Scholar, repo URLs). Update URLs here and they propagate to all pages via `{{< var links.github >}}` shortcodes
- **`custom.scss`** — Visual styling overrides

## Deployment

Automated via GitHub Actions on push to `main`. Configure GitHub Pages source to "GitHub Actions" in repository Settings > Pages.
