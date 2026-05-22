"""Minimal one-shot Claude call. Requires ANTHROPIC_API_KEY."""

import os

from anthropic import Anthropic
from dotenv import load_dotenv

MODEL = "claude-haiku-4-5-20251001"  # cheapest/fastest current Haiku for examples


def ask(prompt: str, model: str = MODEL) -> str:
    client = Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text  # type: ignore[union-attr]


def main() -> None:
    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY in .env or environment.")
    print(ask("Reply with exactly one word: 'pong'."))


if __name__ == "__main__":
    main()
