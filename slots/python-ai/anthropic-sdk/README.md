# anthropic SDK

**Slot**: Python client for the Claude API. Default LLM SDK.

## Why anthropic

You're a Claude user (skill-sommelier, claude-code, claude-quota-esp32). The official SDK supports prompt caching, extended thinking, tool use, batch API, files, citations, and memory — features you actually use.

OpenAI is the alternative when interop matters (used in `bear`, `raven`, `faculty-search` for compatibility with existing infra).

## Conventions

- **Default model** for new builds: `claude-sonnet-4-6` (good cost/quality). Use `claude-opus-4-7` when you need maximum quality; `claude-haiku-4-5-20251001` when latency / cost matter.
- **Always set `max_tokens`** explicitly — the API requires it.
- **Use prompt caching** for system prompts and large reference docs (`cache_control={"type": "ephemeral"}`).
- **Streaming** for any UI-bound call (`with client.messages.stream(...) as stream`).
- **System prompt** as a top-level `system=` param, not as a `role: system` message.
- Keys from env: `ANTHROPIC_API_KEY`.
- Retries / backoff: the SDK retries 5xx/429 automatically (3 attempts). Don't wrap with tenacity unless you've hit the SDK's ceiling.

## Alternatives considered

- **openai SDK** — same shape; use when integrating with OpenAI-compatible servers (vLLM, llama.cpp, Ollama, OpenRouter).
- **LiteLLM** — one API across providers; only worth it when you actually need provider-switching.
- **anthropic-bedrock** — if you're on AWS Bedrock specifically.

## Gotchas

- `max_tokens` caps the *output* only.
- Cache breakpoints accumulate cost — set them at the boundary between "stable" and "varies-per-call" content.
- Tool use returns `tool_use` content blocks; you must POST back a `tool_result` block with the same `tool_use_id` to continue.
- Don't paste API keys into commits — use `.env` + [pydantic-settings](../../python-web/pydantic-settings/).
