# jupyter

**Slot**: Notebook execution environment for exploration and demos.

## Why jupyter (over JupyterLab vs Notebook UI)

The `jupyter` meta-package gets you the kernels, server, and CLI in one. The actual UI you use is editor-dependent (VS Code, Cursor, JupyterLab, Colab). Don't choose a UI for the project — let the user pick.

For kernel-in-the-project-venv mechanics see [ipykernel](../../python-tooling/ipykernel/).

## Conventions

- Notebooks live in `notebooks/` at repo root; never in `<pkg>/`.
- Name them `NN_topic.ipynb` (`01_explore.ipynb`, `02_baseline.ipynb`) for clear order.
- Each notebook starts with a markdown cell stating *purpose* and *date*.
- Move stable code into the package (`<pkg>/foo.py`); notebooks import from there.
- Strip outputs before commit (`nbstripout`) — diffs become readable.
- Run headless in CI to detect breakage: `jupyter execute notebooks/01_explore.ipynb`.

## Alternatives considered

- **Quarto** — preferred for *publishing* (reports, books, sites); some DSI repos use it (`open_source_survey_results`). Slot it in alongside, not instead.
- **MyST** — markdown-based notebooks; great for academic publishing.
- **Pure `.py` scripts** — when the notebook stops earning its weight, graduate.

## Gotchas

- Don't use notebooks as the production execution path; build CLIs or services.
- Out-of-order cell execution causes ghost bugs — restart and run-all before committing.
- Heavy `print(df)` cells slow down the editor and bloat the file; use `df.head()` or display(...) sparingly.
