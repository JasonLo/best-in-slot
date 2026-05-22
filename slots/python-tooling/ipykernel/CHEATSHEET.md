# ipykernel cheatsheet

## Install

```sh
uv add --dev ipykernel
```

## Use

In VS Code / Cursor: open a `.ipynb`, click "Select Kernel", pick the project's `.venv` (uv created it under `.venv/`).

In a terminal:

```sh
uv run jupyter notebook
uv run jupyter lab
```

## Strip outputs in git

```sh
uv add --dev nbstripout
uv run nbstripout --install --attributes .gitattributes
```

## Run a notebook headless (CI / smoke test)

```sh
uv run jupyter execute notebooks/explore.ipynb
```
