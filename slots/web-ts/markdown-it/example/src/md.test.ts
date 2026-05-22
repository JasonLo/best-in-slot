import { expect, test } from "bun:test";
import { render } from "./md";

test("renders heading + anchor", () => {
  const html = render("# Hello, world\n");
  expect(html).toContain("<h1");
  expect(html).toContain("Hello, world");
  expect(html).toContain('id="hello');
  expect(html).toContain('class="header-anchor"');
});

test("highlights TypeScript fenced code", () => {
  const html = render("```ts\nconst x = 1;\n```\n");
  expect(html).toContain("language-ts");
  expect(html).toContain("hljs");
});

test("escapes HTML in input (html: false)", () => {
  const html = render("<script>x</script>\n");
  expect(html).not.toContain("<script>x</script>");
});
