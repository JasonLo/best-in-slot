from typing import Annotated

import typer

app = typer.Typer(help="typer-example CLI", no_args_is_help=True)


@app.command()
def greet(
    name: Annotated[str, typer.Argument(help="who to greet")],
    loud: Annotated[bool, typer.Option(help="UPPERCASE")] = False,
) -> None:
    """Say hello."""
    msg = f"Hello, {name}!"
    typer.echo(msg.upper() if loud else msg)


@app.command()
def add(
    a: int,
    b: int,
) -> None:
    """Add two numbers."""
    typer.echo(a + b)


if __name__ == "__main__":
    app()
