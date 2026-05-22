# pixi

**Slot**: Environment manager for CUDA / conda-forge / multi-language stacks. Matches `pixi-docker-chtc`.

## Why pixi (instead of uv)

`uv` is your everywhere-default. Reach for `pixi` when:

- The dep set includes CUDA + cuDNN + system libraries that ship only on conda-forge.
- You need a conda-forge package that isn't on PyPI (`magma`, `rapids`, etc.).
- The project ships to UW CHTC GPU nodes via [htcondor](../htcondor/) (`pixi-docker-chtc` precedent).
- You need a multi-language environment (Python + R + system libs).

For pure-Python projects on standard wheels, uv stays the default.

## Conventions

- `pixi.toml` declares the environment.
- `pixi.lock` is committed.
- Use the **pixi Docker base image** when shipping to GPU: `FROM ghcr.io/prefix-dev/pixi:0.49.0-cuda12-bookworm` (or matching CUDA version).
- Tasks via `[tasks]` block (`pixi run train`); equivalent of npm scripts / makefile.
- Always pin a `channel-priority = "strict"` to avoid conda-forge / nvidia channel weirdness.

## Alternatives considered

- **conda / mamba** — slower; pixi is the modern replacement.
- **uv** — preferred when no CUDA / conda-forge dep is in play.
- **micromamba** — fine; pixi has a better task runner and CLI.

## Gotchas

- `pixi install` populates `.pixi/envs/default/` — gitignore it (already in repo's root `.gitignore`).
- Don't mix `pip` and `pixi`-managed packages in the same env unless you pin `pypi` channels explicitly in `pixi.toml`.
- CUDA versions are sticky — bumping requires regenerating the lockfile for all platforms.
