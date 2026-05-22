# numpy

**Slot**: N-dimensional arrays and vectorised math.

## Why numpy

The foundation. pytorch / pandas / altair / scipy / scikit-learn / pyarrow all interop via numpy. Use it directly for any numeric work that doesn't deserve a full DataFrame.

## Conventions

- Pin a major version (`numpy>=2.0`) — v1→v2 introduced API breaks.
- Use `np.random.default_rng(seed=...)` (the modern Generator API), not the legacy `np.random.*` calls.
- Prefer dtypes you own (`np.float32`, `np.int64`) over Python int/float when allocating arrays.
- Vectorise; if you find yourself writing `for i in range(len(arr))`, you're missing something.
- For mixed-typed records use a pandas DataFrame instead of a structured array.

## Alternatives considered

- **jax.numpy** — same API, GPU/TPU, autodiff. Pick when you're already in JAX-land.
- **pytorch tensors** — same shape, GPU-native. Pick when training a model.
- **cupy** — drop-in GPU replacement; rarely worth it over jax/torch.

## Gotchas

- `np.float_` is gone in v2 — use `np.float64`.
- Default integer dtype on Windows used to be 32-bit; v2 unified it to 64. Old code paths may break.
- Beware silent broadcasting bugs — assert shapes explicitly at function boundaries.
