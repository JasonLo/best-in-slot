# argparse

**Slot**: stdlib CLI parser. Use when zero-dep matters or the CLI is small (used in `sound-trim`, `dazzo-monitor`, `server-usage-monitor`).

## Why argparse

It's in the stdlib. No extra resolve, no install size cost. For one-shot scripts that take 1–2 flags, anything more is overkill.

For typed CLIs, subcommands beyond `up`/`down`, or LLM agents with many options → use [typer](../typer/) instead.

## Conventions

- One `cli.py` exposing `def main() -> None`.
- Subcommands via `subparsers.add_parser(...)` + `set_defaults(func=cmd_xxx)`.
- Dispatch: `args.func(args)` at the bottom of `main()`.
- For subcommand modules, lazy-import inside the handler (matches `sound-trim`'s pattern) — keeps `--help` fast.
- Logging via stdlib `logging`, not `print`, so users can `--quiet` / `--verbose`.

## Alternatives considered

- **typer / click** — preferred once the CLI grows.
- **fire** — magic, but discoverability suffers.

## Gotchas

- `add_subparsers(required=True)` is what you want — defaults to `False` and produces confusing "no command" runs.
- Use `metavar` to clean up help text when the choice set is long.
- For repeated args, prefer `nargs="+"` (one-or-more) over `action="append"` (cleaner help).
