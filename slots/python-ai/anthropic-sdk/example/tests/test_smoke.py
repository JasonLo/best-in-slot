"""Smoke test: SDK imports and client construction works without making a network call."""

import os

import pytest


def test_sdk_imports() -> None:
    import anthropic  # noqa: F401


def test_client_constructs() -> None:
    from anthropic import Anthropic

    # Constructor with an explicit key should work even when no real network is present.
    c = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "test-key"))
    assert c.api_key


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="needs ANTHROPIC_API_KEY")
def test_live_call() -> None:
    from anthropic_example.main import ask

    out = ask("Reply with exactly one word: 'pong'.")
    assert "pong" in out.lower()
