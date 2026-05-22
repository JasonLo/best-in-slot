# hono cheatsheet

## Minimal app

```ts
// src/app.ts
import { Hono } from "hono";

const app = new Hono();

app.get("/healthz", (c) => c.json({ status: "ok" }));

app.get("/hello/:name", (c) => {
  const name = c.req.param("name");
  return c.json({ msg: `hello, ${name}` });
});

export default app;
```

## Entry (Bun / Workers / Node)

```ts
// src/index.ts
import app from "./app";

export default {
  port: 3000,
  fetch: app.fetch,
};
```

## Zod validation

```ts
import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";

const schema = z.object({ name: z.string().min(1) });

app.post("/hello", zValidator("json", schema), (c) => {
  const { name } = c.req.valid("json");
  return c.json({ msg: `hello, ${name}` });
});
```

## Groups

```ts
const users = new Hono();
users.get("/", (c) => c.json([]));
users.get("/:id", (c) => c.json({ id: c.req.param("id") }));
app.route("/users", users);
```

## Middleware

```ts
import { logger } from "hono/logger";
import { cors } from "hono/cors";
app.use("*", logger(), cors());
```

## Tests (bun:test)

```ts
import { expect, test } from "bun:test";
import app from "./app";

test("hello", async () => {
  const res = await app.request("/hello/jason");
  expect(res.status).toBe(200);
  expect(await res.json()).toEqual({ msg: "hello, jason" });
});
```
