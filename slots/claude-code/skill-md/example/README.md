# hello-plugin (example)

A minimal Claude Code plugin: one skill, one command, one agent.

## Install

Inside Claude Code:

```
/install /home/user/best-in-slot/slots/claude-code/skill-md/example
```

Or one-shot for testing:

```sh
claude --plugin-dir /home/user/best-in-slot/slots/claude-code/skill-md/example
```

Then:

- Ask "test hello-plugin" → the `hello` skill fires.
- Run `/hello-plugin:hello` → the command fires.
