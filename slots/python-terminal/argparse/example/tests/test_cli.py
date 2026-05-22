import pytest

from argparse_example.cli import main


def test_greet(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["greet", "jason"]) == 0
    assert "Hello, jason!" in capsys.readouterr().out


def test_greet_loud(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["greet", "jason", "--loud"]) == 0
    assert "HELLO, JASON!" in capsys.readouterr().out


def test_add(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "2", "3"]) == 0
    assert capsys.readouterr().out.strip() == "5"
