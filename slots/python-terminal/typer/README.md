# typer

**Slot**: Typed CLI parser (used in `raven`, `poker`, `sair-math-cheatsheet-challenge`).

## Why typer

Type-hint-driven CLI building on `click`. Subcommand boilerplate disappears. Rich help out of the box. The right pick when the CLI is even slightly involved (LLM agents, multi-command tools, pydantic-heavy inputs).

For zero-dep one-shot scripts use [argparse](../argparse/).

## Conventions

- One `cli.py` per package, exposing `app = typer.Typer()` and `if __name__ == "__main__": app()`.
- Each subcommand is a function decorated with `@app.command()`.
- Arguments are positional params; options are `Annotated[T, typer.Option(...)]`.
- Settings via [pydantic-settings](../../python-web/pydantic-settings/) — don't read env vars in command functions.
- Wire to `[project.scripts]` so `uv tool install` produces a real binary.

## Alternatives considered

- **argparse** — stdlib, zero dep, fine for ≤2 flags.
- **click** — typer is sugar on click; use click directly only when you need a click-specific extension.

## Gotchas

- `typer.Option`'s default *is* the default — don't `... = "foo"` AND `typer.Option("bar")` ambiguously.
- Rich help requires `rich` (transitive); not a problem in practice.
- For Pydantic models as input use `Annotated[Path, typer.Argument(...)]` + parse inside the command, don't try to make typer parse pydantic.
