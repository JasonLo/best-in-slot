# mkdocs-material cheatsheet

## Install + run

```sh
uv add --dev mkdocs-material mkdocstrings[python]
uv run mkdocs serve              # http://localhost:8000
uv run mkdocs build              # → site/
uv run mkdocs gh-deploy          # pushes site/ to gh-pages branch
```

## `mkdocs.yml`

```yaml
site_name: my-project
site_url: https://jasonlo.github.io/my-project
repo_url: https://github.com/jasonlo/my-project

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - search.highlight
    - search.share
    - content.code.copy
    - content.code.annotate
    - toc.integrate
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      toggle: { icon: material/weather-night, name: Switch to dark mode }
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      toggle: { icon: material/weather-sunny, name: Switch to light mode }

markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - admonition
  - pymdownx.details
  - tables

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            show_source: true
            show_root_heading: true

nav:
  - Home: index.md
  - API:
    - mypkg: api/mypkg.md
```

## Auto API docs

```md
<!-- docs/api/mypkg.md -->
::: mypkg
    options:
      show_submodules: true
```

## Publish via GitHub Actions

```yaml
- run: uv sync
- run: uv run mkdocs gh-deploy --force
```
