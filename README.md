# jgb-plugins

Personal agent skills and plugins, shared between **Claude Code** and **Codex CLI**.

Skills are the portable core (the [agentskills.io](https://agentskills.io) `SKILL.md`
format, read by both tools). Plugins are the Claude-only packaging layer that adds
slash commands, subagents, hooks and MCP servers on top.

## Layout

```
skills/                       shared skills - source of truth, never duplicated
plugins/<name>/               Claude Code plugins
  .claude-plugin/plugin.json  plugin manifest
  skills/                     skills scoped to this plugin
  commands/ agents/ hooks/    Claude-only extension points
  .mcp.json                   MCP servers bundled with the plugin
.claude-plugin/marketplace.json   the catalog Claude Code installs from
tools/agentkit.py             scaffold / install / validate CLI
AGENTS.md                     repo conventions (CLAUDE.md imports it)
```

## Where each tool looks for skills

| | Claude Code | Codex CLI |
|---|---|---|
| user-level | `~/.claude/skills/` | `~/.agents/skills/` |
| project-level | `.claude/skills/` | `.agents/skills/` (walks up to repo root) |
| plugins | `/plugin install` | not supported |

`agentkit install` links `skills/` into both user-level directories as `jgb/`,
so one edit here reaches both tools.

## Usage

```bash
# scaffold
python tools/agentkit.py new-skill  pr-review --desc "..."
python tools/agentkit.py new-plugin core --desc "..."
python tools/agentkit.py new-skill  release-notes --plugin core

# make them live (symlink; falls back to copy on Windows without Developer Mode)
python tools/agentkit.py install
python tools/agentkit.py install --claude          # one tool only
python tools/agentkit.py install --copy            # force copy
python tools/agentkit.py uninstall

# inspect and check
python tools/agentkit.py list
python tools/agentkit.py validate
```

`validate` runs in CI and enforces: frontmatter present, `name` matches the
directory, names unique repo-wide, `description` non-trivial, plugins listed in
`marketplace.json` with a manifest that agrees on the name.

### Installing the plugins in Claude Code

```
/plugin marketplace add joeybalardeta/jgb-plugins
/plugin install <plugin>@jgb-plugins
```

Or pin it for a project in its `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "jgb-plugins": { "source": { "source": "github", "repo": "joeybalardeta/jgb-plugins" } }
  },
  "enabledPlugins": { "core@jgb-plugins": true }
}
```

## Writing a good skill

The `description` is the entire trigger - it is all the model sees before
deciding to load the file. Say when it applies *and* when it does not:

```yaml
---
name: release-notes
description: Generate release notes from git history. Use when the user asks for a changelog, release summary, or "what shipped". Not for writing individual commit messages.
---
```

Keep `SKILL.md` under ~500 lines; push detail into `references/` beside it and
link. Put anything executable in `scripts/`.

## Windows note

`install` prefers symlinks so edits are live. Windows only allows those with
Developer Mode enabled (Settings > System > For developers) or an elevated
shell; otherwise it copies, and you re-run `install` after editing a skill.
