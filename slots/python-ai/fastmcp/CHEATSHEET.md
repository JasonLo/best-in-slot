# fastmcp cheatsheet

## Server

```python
# mypkg/mcp_server.py
from fastmcp import FastMCP

mcp = FastMCP("my-mcp")


@mcp.tool
def echo(message: str) -> str:
    """Return the message unchanged."""
    return message


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


@mcp.resource("memo://{topic}")
def get_memo(topic: str) -> str:
    """Look up a saved memo."""
    return f"memo on {topic}"


def main() -> None:
    mcp.run()  # stdio by default


if __name__ == "__main__":
    main()
```

## `pyproject.toml`

```toml
[project]
dependencies = ["fastmcp>=3"]

[project.scripts]
my-mcp = "mypkg.mcp_server:main"
```

## Install + add to Claude Code

```sh
uv tool install .
fastmcp install claude-code mypkg/mcp_server.py:mcp --server-name my-mcp
# or manually, once the entrypoint is on PATH:
claude mcp add my-mcp --command "$(which my-mcp)"
```

## HTTP transport (hosted)

```python
def main() -> None:
    mcp.run(transport="http", host="0.0.0.0", port=8765)
```

```sh
claude mcp add my-mcp --transport http --url http://localhost:8765/mcp
```

## Logging without corrupting stdio

```python
import logging

logging.basicConfig(
    filename="my-mcp.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
```

## In-memory test client (preferred)

```python
import pytest
from fastmcp import Client
from mypkg.mcp_server import mcp


@pytest.mark.asyncio
async def test_add() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool("add", {"a": 2, "b": 3})
        assert result.data == 5
```

## Inspect / run from the CLI

```sh
fastmcp run mypkg/mcp_server.py:mcp                       # stdio
fastmcp run mypkg/mcp_server.py:mcp --transport http      # http on :8000
fastmcp dev mypkg/mcp_server.py:mcp                       # MCP Inspector UI
```
