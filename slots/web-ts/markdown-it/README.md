# markdown-it

**Slot**: Render Markdown to HTML in TypeScript. Matches `md-render`'s rendering core.

## Why markdown-it

CommonMark + GFM, extensible via plugins, runs anywhere JS runs. Used in `md-render` alongside `markdown-it-anchor` (heading IDs) and `highlight.js` (code blocks).

For Astro / MDX, you don't reach for markdown-it — Astro uses `remark` / `rehype` internally. Use markdown-it when you're rendering markdown *at runtime* in a service (e.g. user-supplied markdown).

## Conventions

- One configured `MarkdownIt` instance, exported from a module — never construct it per request.
- Plugins composed at construction (`.use(plugin, opts)`).
- For headings: `markdown-it-anchor` (with `permalink` for "#" anchors).
- For syntax: `highlight.js` registered in the `highlight` option, not as a plugin.
- For sanitisation when input is untrusted, run output through `DOMPurify` (jsdom-backed) — markdown-it does NOT escape HTML inside the source.

## Alternatives considered

- **remark + rehype** — ecosystem-first; preferred inside Astro / Next.js builds.
- **marked** — simpler API, fewer plugins.
- **micromark** — CommonMark engine underneath remark; low-level.

## Gotchas

- `html: true` lets users embed raw HTML — only enable when input is trusted.
- `linkify: true` auto-detects URLs but matches some non-URLs aggressively; tweak `linkify-it` options if you care.
- Heading IDs are duplicated when titles repeat — `markdown-it-anchor` has `slugify` to disambiguate.
