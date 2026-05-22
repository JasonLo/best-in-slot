# jupyter cheatsheet

## Install

```sh
uv add --dev jupyter ipykernel
```

## Run

```sh
uv run jupyter lab            # JupyterLab UI
uv run jupyter notebook       # classic UI
```

## Execute headless (CI)

```sh
uv run jupyter execute notebooks/01_explore.ipynb
uv run jupyter execute notebooks/*.ipynb --kernel python3
```

## Convert

```sh
uv run jupyter nbconvert --to html notebooks/01_explore.ipynb
uv run jupyter nbconvert --to script notebooks/01_explore.ipynb
uv run jupyter nbconvert --to pdf notebooks/01_explore.ipynb     # needs LaTeX
```

## Strip outputs (pre-commit)

```sh
uv add --dev nbstripout
uv run nbstripout --install --attributes .gitattributes
```

`.gitattributes`:

```
*.ipynb filter=nbstripout
```

## Quarto (publishing path)

```sh
brew install quarto                # or apt-install
quarto render notebooks/01_explore.ipynb --to html
quarto preview                     # live reload
```
