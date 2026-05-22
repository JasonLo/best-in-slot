# anthropic-sdk example

```sh
uv sync
uv run pytest                              # SDK smoke tests (no network)

cp .env.example .env
# put your real ANTHROPIC_API_KEY in .env
uv run anthropic-example                   # one Claude call (Haiku)
```
