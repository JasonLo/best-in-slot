import { expect, test } from "bun:test";
import app from "./app";

test("healthz", async () => {
  const res = await app.request("/healthz");
  expect(res.status).toBe(200);
  expect(await res.json()).toEqual({ status: "ok" });
});

test("hello", async () => {
  const res = await app.request("/hello/jason");
  expect(res.status).toBe(200);
  expect(await res.json()).toEqual({ msg: "hello, jason" });
});
