import argparse
import logging
from typing import Sequence


def cmd_greet(args: argparse.Namespace) -> int:
    msg = f"Hello, {args.name}!"
    print(msg.upper() if args.loud else msg)
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    print(args.a + args.b)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    p = argparse.ArgumentParser(prog="argparse-example")
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("greet")
    g.add_argument("name")
    g.add_argument("--loud", action="store_true")
    g.set_defaults(func=cmd_greet)

    a = sub.add_parser("add")
    a.add_argument("a", type=int)
    a.add_argument("b", type=int)
    a.set_defaults(func=cmd_add)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
