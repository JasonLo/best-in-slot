# huggingface datasets

**Slot**: ML dataset loading, streaming, and format conversion (matches `pelican-data-loader`).

## Why `datasets`

One library, every format: CSV, parquet, JSON, audio, images, web archives. Lazy streaming for datasets that don't fit in RAM. `.with_format("torch" | "jax" | "tensorflow" | "polars" | "pyarrow")` swaps the iterator type without re-encoding.

## Conventions

- Always pin a known split: `datasets.load_dataset(..., split="train[:1%]")` for fast smoke tests.
- For your own files: `load_dataset("csv", data_files="...")` works for csv/json/parquet via the same call.
- Use **streaming** (`streaming=True`) for anything larger than ~1 GB — iterates without downloading the whole thing.
- For data + Croissant metadata: pair with `mlcroissant` (the `pelican-data-loader` pattern).
- For private datasets, set `HF_TOKEN` env var; never hard-code.

## Alternatives considered

- **pandas + glob** — fine for one-shot CSV jobs; lacks the format/streaming machinery.
- **webdataset** — better for very large sharded tar archives; integrates via `datasets` adapter.
- **torch.utils.data.Dataset** directly — when you have a tiny custom loader and want to avoid the dependency.

## Gotchas

- Disk cache at `~/.cache/huggingface/datasets/` grows fast — clean periodically.
- `dataset.with_format("torch")` returns dicts of tensors; `dataset.set_format(...)` mutates in place.
- For audio, install `datasets[audio]`; for images, `datasets[vision]` — features lazily decode on access.
