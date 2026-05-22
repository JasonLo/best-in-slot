"""Minimal FastMCP server exposing two tools and one resource."""

from fastmcp import FastMCP

mcp = FastMCP("fastmcp-example")


@mcp.tool
def echo(message: str) -> str:
    """Return the message unchanged."""
    return message


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    return a + b


@mcp.resource("memo://{topic}")
def get_memo(topic: str) -> str:
    """Look up a (fake) memo for the given topic."""
    return f"You said: write a memo about {topic}."


def main() -> None:
    mcp.run()  # stdio


if __name__ == "__main__":
    main()
