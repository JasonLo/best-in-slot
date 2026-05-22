# mcp cheatsheet

## Server (FastMCP — high-level API)

```python
# mypkg/mcp_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-mcp")


@mcp.tool()
def echo(message: str) -> str:
    """Return the message unchanged."""
    return message


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


@mcp.resource("memo://{topic}")
def get_memo(topic: str) -> str:
    """Look up a saved memo."""
    return f"memo on {topic}"


def main() -> None:
    mcp.run()                          # stdio by default


if __name__ == "__main__":
    main()
```

## `pyproject.toml`

```toml
[project]
dependencies = ["mcp[cli]>=1.0"]

[project.scripts]
my-mcp = "mypkg.mcp_server:main"
```

## Install + add to Claude Code

```sh
uv tool install .
claude mcp add my-mcp --command my-mcp
# or via stdio:
claude mcp add my-mcp --command "$(which my-mcp)"
```

## HTTP transport (hosted)

```python
def main() -> None:
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8765)
```

```sh
claude mcp add my-mcp --transport http --url http://localhost:8765
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

## Inspect with the official tool

```sh
uvx mcp dev mypkg.mcp_server:mcp
```
