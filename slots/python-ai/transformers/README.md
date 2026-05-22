# huggingface transformers

**Slot**: Load and run pretrained models (text, audio, image, multimodal). Used in `qwen3-tts` (TTS) and `qwen3-tts-api` (serving).

## Why transformers

One library that covers ~every modern open-weights model. Tokenizers, model configs, and inference utilities are unified. Pairs cleanly with `pytorch` (default) and `huggingface datasets`.

## Conventions

- Pin both `transformers` AND the model checkpoint sha (`revision="abc123"`) for reproducibility.
- Cache dir env var: `HF_HOME=/path/to/cache`; outside of `~/.cache` for big servers.
- Use `pipeline(...)` only for quick demos. For production, build `AutoModel` + `AutoTokenizer` directly so you control batching.
- Quantise when shipping: `bitsandbytes` for nf4/int8; `auto-gptq` / `awq` when the model has a pre-quantised checkpoint.
- For audio/vision install the right extras: `transformers[audio]`, `transformers[vision]`.

## Alternatives considered

- **vllm / sglang** — much faster inference servers for LLMs. Use when transformers' speed becomes the bottleneck.
- **llama.cpp** — CPU/Metal inference for GGUF models.
- **timm** — image-only model zoo; use alongside transformers (`matryoshka-weights` uses `timm`).

## Gotchas

- `from_pretrained(...)` downloads on first call — bake into Docker images (multi-stage `RUN python -c "..."`).
- `device_map="auto"` requires `accelerate` and reads available VRAM dynamically; verify the actual placement once.
- For TTS models, sample rate matches the model's training rate — resample explicitly with `torchaudio.functional.resample`.
- Some models require `trust_remote_code=True` — read the model card before flipping it on.
