---
name: hello
description: Greets the user, optionally personalised by name. Use when the user explicitly asks to test the hello-plugin.
---

# hello

A minimal skill that produces a greeting.

## When to use

- The user types something like "test hello-plugin" or "run the hello skill".

## Steps

1. Identify a name from the user's message; default to "world".
2. Reply with exactly: `Hello, <name>! 👋` (omit the wave if the user disabled emoji).
