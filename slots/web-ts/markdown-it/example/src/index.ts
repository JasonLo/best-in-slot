import { render } from "./md";

const src = `# Hello

\`\`\`ts
console.log("hi");
\`\`\`
`;

console.log(render(src));
