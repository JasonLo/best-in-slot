# pydantic

**Slot**: Data validation at API / config / external-data boundaries.

## Why pydantic

The de-facto standard. FastAPI integrates natively. v2 is fast (Rust-backed). Stop hand-writing `if not isinstance(...)`.

## Conventions

- Use pydantic for **boundaries**: HTTP request/response, config files, LLM tool inputs, external API payloads.
- Don't pydantic-ify internal-only data — `@dataclass` or a plain class is enough.
- Use **strict mode** (`model_config = ConfigDict(strict=True)`) for inbound data to catch silent coercion.
- Keep models thin; computed properties belong elsewhere (services, not models).
- Prefer `Annotated[..., Field(...)]` over class-level defaults for documentation.

## Alternatives considered

- **dataclasses** — fine for internal types; no validation, no JSON schema.
- **attrs** — similar story, slightly more features than dataclasses.
- **msgspec** — faster, smaller scope; consider for very high-throughput services.

## Gotchas

- v1 → v2: most code needs `model_validate`, `model_dump`, `ConfigDict`. Don't mix v1 patterns in new code.
- `BaseModel.model_dump()` is the JSON-safe dict; `dict(model)` is not.
- Custom validators: prefer `@field_validator` (per-field) over `@model_validator` (whole-model) when both work.
