# ipykernel

**Slot**: Jupyter kernel for the project's venv (so notebooks see your dependencies).

## Why ipykernel

Whatever editor runs your notebook (VS Code, JupyterLab, Cursor, PyCharm) needs an `ipykernel` installed in the env you want it to talk to. Adding it to the project's dev deps means "this project's notebooks run with this project's deps" — no global kernel ambiguity.

## Conventions

- Always add as `[dependency-groups].dev`, never as a runtime dep.
- Don't register a global kernel; let the editor discover the project's `.venv` (uv puts one there).
- Notebooks live in `notebooks/`; they're for exploration and demos, not production code.
- For repeatable scripts, extract code from notebooks into `<pkg>/` modules; keep the notebook as a thin caller.

## Alternatives considered

- **jupytext** — keep notebooks as `.py`. Worth it for version control, but adds a tool to the chain. Use only when notebooks are heavily reviewed.

## Gotchas

- Don't commit large outputs. Add a pre-commit hook (`nbstripout`) when collaborating.
- Path tricks (`sys.path.insert`) are a red flag — install the package editable instead (`uv sync` handles this).
