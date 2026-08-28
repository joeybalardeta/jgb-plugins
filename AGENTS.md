# jgb-plugins

This repo is a source of truth for agent **skills** (portable across Claude Code,
Codex CLI, and anything else that reads the agentskills.io `SKILL.md` format) and
Claude Code **plugins** (the Claude-only packaging layer: commands, subagents,
hooks, MCP servers).

## Layout

- `skills/` - shared, tool-agnostic skills. Each is a directory with a `SKILL.md`.
- `plugins/<name>/` - Claude Code plugins. Plugin-specific skills live in
  `plugins/<name>/skills/`; shared skills are referenced, not copied.
- `.claude-plugin/marketplace.json` - the catalog Claude Code installs from.
- `tools/agentkit.py` - scaffolding, install, and validation CLI.

## Rules when editing this repo

- Never duplicate a skill body. If two plugins need it, it belongs in `skills/`.
- Every `SKILL.md` needs YAML frontmatter with `name` and `description`. The
  `name` must equal its directory name and be unique across the whole repo.
- Write `description` for implicit matching: say when the skill should fire AND
  when it should not. It is the only thing the model sees before loading.
- Keep `SKILL.md` bodies under ~500 lines; push detail into sibling
  `references/` files and link to them.
- Run `python tools/agentkit.py validate` before committing.
