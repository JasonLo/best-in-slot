export function greet(name: string, loud: boolean = false): string {
  const msg = `Hello, ${name}!`;
  return loud ? msg.toUpperCase() : msg;
}
