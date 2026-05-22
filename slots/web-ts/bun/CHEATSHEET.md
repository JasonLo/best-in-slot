# bun cheatsheet

## Install / run

```sh
curl -fsSL https://bun.sh/install | bash    # install
bun init                                     # new project (interactive)
bun add hono                                 # dep
bun add -d typescript                        # dev dep
bun install                                  # from lockfile
bun run src/index.ts                         # run TS directly
bun --watch run src/index.ts                 # hot reload
```

## Scripts in `package.json`

```json
{
  "scripts": {
    "dev": "bun --watch run src/index.ts",
    "start": "bun run src/index.ts",
    "build": "bun build src/index.ts --outdir dist",
    "typecheck": "tsc --noEmit",
    "test": "bun test"
  }
}
```

## Tests (built-in runner)

```ts
import { expect, test } from "bun:test";

test("two + two", () => {
  expect(2 + 2).toBe(4);
});
```

```sh
bun test
```

## Bundle for Node

```sh
bun build src/index.ts --target=node --outdir dist
```

## Docker

```dockerfile
FROM oven/bun:1.3-alpine
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile --production
COPY . .
EXPOSE 3000
CMD ["bun", "run", "src/index.ts"]
```
