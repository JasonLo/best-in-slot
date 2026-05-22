# bun

**Slot**: JavaScript / TypeScript runtime + package manager + bundler.

## Why bun

One binary that runs `.ts` directly, manages dependencies (`bun install`), bundles, and tests. Matches `md-render`'s setup. Faster cold start than Node + tsx; small Docker images via `oven/bun`.

Use bun when the TS code stands on its own (a small HTTP service, a build script, a CLI). For static sites, Astro lives happily on Node ([astro](../astro/)).

## Conventions

- `package.json` script `dev` uses `bun run --watch <entry>`; `start` uses `bun run <entry>`.
- TypeScript is treated as first-class — no separate `tsc` step for running. Still ship a `typecheck` script (`bun run tsc --noEmit`) for CI.
- Lockfile is `bun.lock` (text-based; commit it).
- For libraries published to npm, build with `bun build --target=node` so consumers on Node still work.
- For HTTP services, pair with [hono](../hono/).

## Alternatives considered

- **Node 22 + tsx** — fine; one more dependency. Pick if your environment already standardised on Node.
- **Deno** — newer permissions model; smaller community than bun.
- **pnpm / npm / yarn** — package managers; bun replaces them.

## Gotchas

- Some Node-only native modules don't work on bun yet. Test before committing.
- `bun install` writes `bun.lock`; if you switch off bun, regenerate the right lockfile (`pnpm-lock.yaml`, `package-lock.json`).
- `bun run` resolves to a script in `package.json` first, then `node_modules/.bin/`, then the file path.
