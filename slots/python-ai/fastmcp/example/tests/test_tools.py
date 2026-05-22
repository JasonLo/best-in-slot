"""Tools live as FunctionTool objects on the server — exercise them through the in-memory Client."""

from fastmcp import Client

from fastmcp_example.server import mcp


async def test_echo() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool("echo", {"message": "hello"})
    assert result.data == "hello"


async def test_add() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool("add", {"a": 2, "b": 3})
    assert result.data == 5


async def test_memo() -> None:
    async with Client(mcp) as client:
        result = await client.read_resource("memo://covid")
    assert "covid" in result[0].text
