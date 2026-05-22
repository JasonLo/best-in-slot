# argparse cheatsheet

## Subcommand dispatch (matches `sound-trim`)

```python
import argparse
import logging
from typing import Sequence


def cmd_trim(args: argparse.Namespace) -> None:
    from .trim import run_trim
    run_trim(args.input, args.output)


def cmd_wrap(args: argparse.Namespace) -> None:
    from .wrap import run_wrap
    run_wrap(args.input, args.output, args.intro, args.outro)


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    p = argparse.ArgumentParser(prog="mytool")
    p.add_argument("-q", "--quiet", action="store_true")

    sub = p.add_subparsers(dest="command", required=True)

    t = sub.add_parser("trim", help="trim audio")
    t.add_argument("input")
    t.add_argument("output")
    t.set_defaults(func=cmd_trim)

    w = sub.add_parser("wrap", help="add intro/outro")
    w.add_argument("input")
    w.add_argument("output")
    w.add_argument("--intro")
    w.add_argument("--outro")
    w.set_defaults(func=cmd_wrap)

    args = p.parse_args(argv)
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Test

```python
from mytool.cli import main

def test_help(capsys):
    try:
        main(["--help"])
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out
    assert "trim" in out
```
