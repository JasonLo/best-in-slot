# typer cheatsheet

## Minimal

```python
import typer

app = typer.Typer(help="my CLI", no_args_is_help=True)


@app.command()
def greet(name: str, loud: bool = False) -> None:
    """Say hello."""
    msg = f"Hello, {name}!"
    typer.echo(msg.upper() if loud else msg)


if __name__ == "__main__":
    app()
```

## Multiple subcommands

```python
@app.command("up")
def up(detach: bool = False) -> None: ...

@app.command("down")
def down(volumes: bool = False) -> None: ...
```

## Options with metadata

```python
from typing import Annotated
from pathlib import Path
import typer

@app.command()
def run(
    name: Annotated[str, typer.Argument(help="who to greet")],
    config: Annotated[Path, typer.Option("--config", "-c", exists=True)] = Path("config.toml"),
    count: Annotated[int, typer.Option(min=1, max=100)] = 1,
) -> None:
    for _ in range(count):
        typer.echo(f"hello {name} ({config})")
```

## Groups

```python
app = typer.Typer()
users = typer.Typer()
app.add_typer(users, name="users")

@users.command("list")
def users_list(): ...
@users.command("add")
def users_add(name: str): ...
```

## Wire to `pyproject.toml`

```toml
[project.scripts]
mycli = "mypkg.cli:app"
```

## Test (with CliRunner)

```python
from typer.testing import CliRunner
from mypkg.cli import app

def test_greet():
    r = CliRunner().invoke(app, ["greet", "jason"])
    assert r.exit_code == 0
    assert "Hello, jason!" in r.stdout
```
