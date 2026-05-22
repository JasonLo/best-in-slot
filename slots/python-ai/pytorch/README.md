# pytorch

**Slot**: ML framework — train, fine-tune, run.

Used in `matryoshka-weights` (`torch>=2.10` + `torchvision` + `timm`), `qwen3-tts` (`torch + torchaudio + transformers`).

## Why pytorch

Pythonic, debuggable, the de-facto default for research and production. The newer Compile / Inductor stack delivers competitive speed without leaving Python.

## When to reach for JAX instead

You wrote `JasonLo/poker` and `JasonLo/test_jax` in JAX. JAX wins when:

- The workload is a tight numerical loop and you want functional transforms (`jit`, `vmap`, `grad`).
- You want TPU access trivially.

For everything else (transformers, vision, fine-tuning, deployment): PyTorch.

## Conventions

- Pin a specific minor: `torch>=2.10,<2.11`. Sublibrary versions matter (`torchvision`, `torchaudio`).
- CUDA install via uv source index (see CHEATSHEET); never `pip install torch --index-url ...` manually.
- Use `torch.compile(model)` after the model works eagerly — speed-up is real on 2.x.
- Mixed precision via `torch.autocast("cuda", dtype=torch.bfloat16)` for training; `float16` only when bf16 unavailable.
- Save checkpoints with `torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "step": step}, path)`.
- Reproducibility: `torch.manual_seed`, `numpy.random.default_rng(seed)`, set `cudnn.deterministic=True` only when you really need it (slower).

## Alternatives considered

- **JAX + Flax** — research velocity, functional API. Pick when you're already writing pure-function code.
- **TensorFlow / Keras** — legacy in your work (`connectionist`, `triangle_model`); not the default for new code.
- **lightning** — adds boilerplate-reducing scaffolding for big training jobs; optional.

## Gotchas

- CPU-only wheels are huge (~700 MB); CUDA ones are huger. Use the right uv source index (`pytorch-cu128`, `pytorch-cpu`, etc.).
- `model.eval()` ≠ `with torch.no_grad():` — you usually want both for inference.
- For Apple Silicon, install the default wheels and use `device="mps"` — there's no special index needed.
