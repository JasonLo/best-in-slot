# SKILL.md cheatsheet

## plugin.json

```json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "What this plugin does in one sentence.",
  "author": "Jason Lo <clo36@wisc.edu>",
  "homepage": "https://github.com/jasonlo/my-plugin"
}
```

## skills/<name>/SKILL.md

```markdown
---
name: my-skill
description: Performs X when the user is doing Y. Use when Z.
---

# my-skill

Step-by-step guidance the agent follows when this skill is loaded.

## When to use

- Bullet for trigger condition 1
- Bullet for trigger condition 2

## Steps

1. First, ...
2. Then, ...
3. Finally, ...
```

## commands/<name>.md

```markdown
---
description: One-line command help (shows in /help)
---

When invoked, do the following:

1. Read CONTEXT.md if present
2. Run `gh pr list --state open` and summarize
```

Invocation: `/my-plugin:<name>`.

## agents/<name>.md

```markdown
---
name: my-agent
description: When to delegate work to this subagent.
tools: Bash, Read, Grep
---

You are an agent specialized in X. Constraints: ...
```

## hooks/<event>.json

```json
{
  "matcher": "Stop",
  "command": "uv run my-plugin-helper --on stop"
}
```

## Install

Inside Claude Code:

```
/install /path/to/this/repo
```

Or globally:

```sh
git clone https://github.com/jasonlo/my-plugin ~/.claude/plugins/my-plugin
```
