import { expect, test } from "bun:test";
import { greet } from "./greet";

test("greets by name", () => {
  expect(greet("jason")).toBe("Hello, jason!");
});

test("loud mode uppercases", () => {
  expect(greet("jason", true)).toBe("HELLO, JASON!");
});
