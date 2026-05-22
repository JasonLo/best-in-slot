import { greet } from "./greet";

const name = process.argv[2] ?? "world";
console.log(greet(name));
