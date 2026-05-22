# SKILL.md plugin format

**Slot**: Author Claude Code plugins (skills, commands, agents, hooks).

## Why SKILL.md

Plain markdown with YAML frontmatter; **no build system, no scripts**. Same approach used by `skill-sommelier` and `UW-Madison-DSI/uw-design-system`. The plugin loads when Claude Code sees a valid `plugin.json` + `skills/<name>/SKILL.md`.

## Plugin anatomy

```
my-plugin/
├── plugin.json                       # manifest
├── README.md                         # human docs / install
├── install.sh                        # optional bootstrap (gh + uv etc.)
├── skills/
│   └── my-skill/
│       └── SKILL.md                  # frontmatter + body
├── commands/
│   └── my-command.md                 # slash command
├── agents/
│   └── my-agent.md                   # subagent
└── hooks/
    └── on-stop.json                  # optional hook config
```

Public skills go in `skills/`. Maintainer-only / release-automation skills go in `maintainer-skills/` (matches `skill-sommelier`).

## Conventions

- **SKILL.md frontmatter**: `name`, `description` (one line, third person, action-oriented), `triggers` (optional patterns).
- **One skill = one focused capability.** If a skill is doing two things, split it.
- **Commands** prefix with the plugin name: `/my-plugin:do-thing`.
- **No code unless you need it.** A skill is instructions, not a runtime. Add Python helpers only if shell/curl can't do it.
- **Install via**: `/install /path/to/repo` *inside* Claude Code — that is the only supported install path.

## Alternatives considered

- **Writing a custom CLAUDE.md per project** — fine for single-project tweaks; SKILL.md plugins are for reusable, distributable capabilities.
- **MCP server** — when you need code execution and tool calls, not markdown instructions. Pick MCP when the capability isn't expressible as guidance.

## Gotchas

- The frontmatter `description` is what Claude reads to decide whether to load the skill. Write it like an index entry, not marketing copy.
- Commands are markdown files with frontmatter — they aren't executable scripts.
- Hooks (in `hooks/*.json`) execute shell commands; treat their config as part of the security surface.
