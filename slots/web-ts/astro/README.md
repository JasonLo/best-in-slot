# astro

**Slot**: Static site framework. Personal site (`jasonlo.dev`), blog, docs landing pages.

## Why astro

Ships zero JS by default; opt in per-island. Markdown + MDX + content collections are first-class. TypeScript out of the box. `@astrojs/sitemap`, `@astrojs/check`, and `sharp` cover the boring stuff.

## Conventions

- Astro `^6.x` (matches `jasonlo.dev`).
- `package.json` scripts: `dev`, `build` (`astro check && astro build`), `preview`.
- Content collections in `src/content/<collection>/` with `src/content/config.ts` schema.
- MDX (`@astrojs/mdx`) for any post that needs components.
- Sitemap via `@astrojs/sitemap` integration.
- Images: place in `src/assets/`; use `<Image />` component (sharp under the hood) for optimised builds.
- Search: client-side via `fuse.js` (matches `jasonlo.dev`); avoid pulling in algolia for small sites.
- TypeScript: `tsconfig.json` extending `astro/tsconfigs/strict`.

## Alternatives considered

- **Next.js / SvelteKit / Nuxt** — heavier; better for app-shaped sites (auth, dashboards).
- **Hugo / Jekyll** — no JS option at all; preferred when you actively reject Node toolchain (`uw-jekyll-theme`, `ospo.wisc.edu`).
- **Quarto** — academic publishing path; use for papers / data reports rather than marketing sites.

## Tiny TS HTTP services (side note)

For a small TS HTTP endpoint (not a static site), don't reach for astro — use [Hono + Bun + markdown-it](../bun/) (matches `md-render`).

## Gotchas

- Astro 6 changed some integration APIs from 5; copy patterns from `jasonlo.dev` directly.
- `astro check` requires `@astrojs/check` + matching TS version (the `jasonlo.dev` lockfile uses `typescript@^6`).
- Image optimisation via `sharp` is slow on huge libraries — consider pre-shrinking originals.
- Deploy targets: Vercel / Cloudflare Pages / GitHub Pages all work out of the box.
