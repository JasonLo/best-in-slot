# github-actions

**Slot**: CI / CD for everything in this repo.

## Why github-actions

Already where the code lives. `astral-sh/setup-uv@v7` makes Python CI essentially: "install uv, `uv sync --frozen`, run things." Caching is automatic.

## Conventions

- One `ci.yml` per project: lint + type-check + test. Runs on `push` and `pull_request`.
- A separate `publish.yml` triggered on tag `v*` for releases (PyPI, GHCR image).
- Pin actions to a version (`@v7`), not a SHA, unless the repo is security-sensitive.
- Use `astral-sh/setup-uv@v7` with `enable-cache: true`.
- Concurrency cancel-in-progress on PRs so old runs die when you push again.
- Permissions: `contents: read` by default; widen per-job, not workflow-wide.
- For Docker: `docker/build-push-action@v6` + `docker/login-action@v3` against GHCR.

## Alternatives considered

- **gitlab-ci** — fine, different tooling.
- **buildkite** — only if you're already on it.

## Gotchas

- `setup-uv@v7` needs `uv.lock` for `--frozen` to mean anything.
- `actions/checkout@v4` shallow-clones by default — pass `fetch-depth: 0` if you need history (changelogs, version bumps).
- GHCR pushes need `packages: write` permission on the job.
- For matrix builds, mark expensive jobs as `if: github.event_name == 'push'` so PRs don't run them all.
