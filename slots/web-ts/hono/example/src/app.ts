import { Hono } from "hono";

const app = new Hono();

app.get("/healthz", (c) => c.json({ status: "ok" }));

app.get("/hello/:name", (c) => {
  const name = c.req.param("name");
  return c.json({ msg: `hello, ${name}` });
});

export default app;
