from typer.testing import CliRunner

from typer_example.cli import app


def test_greet_default() -> None:
    r = CliRunner().invoke(app, ["greet", "jason"])
    assert r.exit_code == 0
    assert "Hello, jason!" in r.stdout


def test_greet_loud() -> None:
    r = CliRunner().invoke(app, ["greet", "jason", "--loud"])
    assert r.exit_code == 0
    assert "HELLO, JASON!" in r.stdout


def test_add() -> None:
    r = CliRunner().invoke(app, ["add", "2", "3"])
    assert r.exit_code == 0
    assert r.stdout.strip() == "5"
