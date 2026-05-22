# mkdocs-material

**Slot**: Project / API documentation site. Used by `bear`.

## Why mkdocs-material

Sensible defaults, dark mode, search, navigation, full-text indexing — all for free. Markdown + a `mkdocs.yml`. Plays well with `mkdocstrings` for auto-generated Python API docs.

For *content* sites (blog, portfolio, marketing), use [astro](../../web-ts/astro/) instead. Docs sites win with mkdocs-material because the prose-to-config ratio is best.

## Conventions

- `docs/` holds markdown.
- `mkdocs.yml` at repo root.
- Use `mkdocstrings[python]` to auto-document the project's API from docstrings.
- Add Material navigation features: `navigation.tabs`, `navigation.sections`, `navigation.expand`, `toc.integrate`.
- Code blocks: enable `pymdownx.superfences` + `pymdownx.highlight` for the good highlighter.
- Deploy via `mkdocs gh-deploy` (GitHub Pages) or build to `site/` and ship as static.

## Alternatives considered

- **Sphinx** — heavier, RST-default; pick when you must publish to ReadTheDocs's classic theme.
- **Docusaurus** — React-based, larger; better for product docs with a marketing surface.
- **Quarto** — academic publishing; great for papers, less so for API docs.

## Gotchas

- `mkdocs serve` is single-process; iterate with one terminal running it.
- `mkdocs gh-deploy` writes to the `gh-pages` branch; configure your Pages source accordingly.
- Search index is built client-side; very large docs slow the first load — `search.share` and `search.suggest` plugins help.
