"""Tools are plain functions decorated by FastMCP — test them directly."""

from mcp_example.server import add, echo, get_memo


def test_echo() -> None:
    assert echo("hello") == "hello"


def test_add() -> None:
    assert add(2, 3) == 5


def test_memo() -> None:
    assert "covid" in get_memo("covid")
