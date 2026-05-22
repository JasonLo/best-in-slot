# markdown-it cheatsheet

## Setup (with anchors + highlight)

```ts
import MarkdownIt from "markdown-it";
import anchor from "markdown-it-anchor";
import hljs from "highlight.js";

export const md = new MarkdownIt({
  html: false,              // disallow raw HTML in input
  linkify: true,
  typographer: true,
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre><code class="hljs language-${lang}">${
          hljs.highlight(code, { language: lang, ignoreIllegals: true }).value
        }</code></pre>`;
      } catch {
        /* fall through */
      }
    }
    return `<pre><code class="hljs">${md.utils.escapeHtml(code)}</code></pre>`;
  },
}).use(anchor, {
  permalink: anchor.permalink.headerLink({ safariReaderFix: true }),
});

export const render = (src: string) => md.render(src);
```

## Render

```ts
const html = render(`# Hello

\`\`\`ts
console.log("hi");
\`\`\``);
```

## Inside hono

```ts
import { Hono } from "hono";
import { render } from "./md";

const app = new Hono();
app.post("/render", async (c) => {
  const { source } = await c.req.json<{ source: string }>();
  return c.html(render(source));
});
```

## Sanitise untrusted input

```ts
import { JSDOM } from "jsdom";
import DOMPurify from "dompurify";

const window = new JSDOM("").window as unknown as Window;
const purify = DOMPurify(window);
const safe = purify.sanitize(render(userSrc));
```
