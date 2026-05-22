# astro cheatsheet

## Create / run

```sh
npm create astro@latest
npm run dev                    # http://localhost:4321
npm run build
npm run preview
```

## `astro.config.mjs`

```js
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://jasonlo.dev",
  integrations: [mdx(), sitemap()],
});
```

## Content collection

```ts
// src/content/config.ts
import { defineCollection, z } from "astro:content";

const posts = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    date: z.date(),
    draft: z.boolean().default(false),
    tags: z.array(z.string()).default([]),
  }),
});

export const collections = { posts };
```

```md
---
title: Hello world
date: 2026-05-22
tags: [astro, intro]
---

# Hello

Markdown body...
```

## Page that lists posts

```astro
---
// src/pages/blog/index.astro
import { getCollection } from "astro:content";
const posts = (await getCollection("posts", ({ data }) => !data.draft))
  .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
---

<ul>
  {posts.map((p) => (
    <li>
      <a href={`/blog/${p.slug}/`}>{p.data.title}</a>
    </li>
  ))}
</ul>
```

## Image optimisation

```astro
---
import { Image } from "astro:assets";
import hero from "../assets/hero.jpg";
---

<Image src={hero} alt="hero" width={1200} />
```

## Client-side search with fuse.js

```ts
import Fuse from "fuse.js";
const fuse = new Fuse(posts, { keys: ["title", "tags"] });
const hits = fuse.search("astro");
```

## Deploy (GitHub Pages)

```yaml
# .github/workflows/deploy.yml
- uses: withastro/action@v3
```
