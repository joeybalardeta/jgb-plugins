# jgb-plugins

Personal plugins and skills for **Claude Code**.

Skills are the portable core — plain `SKILL.md` directories. Plugins wrap them
with slash commands, subagents, hooks and MCP servers, and are distributed
through the marketplace catalog in this repo.

## Layout

```
skills/                       shared skills - source of truth, never duplicated
plugins/<name>/               plugins
  .claude-plugin/plugin.json  plugin manifest
  skills/                     skills scoped to this plugin
  commands/                   slash commands  (/<plugin>:<command>)
  agents/                     subagent definitions
  hooks/hooks.json            lifecycle hooks
  .mcp.json                   MCP servers bundled with the plugin
.claude-plugin/marketplace.json   the catalog Claude Code installs from
tools/agentkit.py             scaffold / install / validate CLI
AGENTS.md                     repo conventions (CLAUDE.md imports it)
```

## Usage

```bash
# scaffold
python tools/agentkit.py new-skill  pr-review --desc "..."
python tools/agentkit.py new-plugin core --desc "..."
python tools/agentkit.py new-skill  release-notes --plugin core

# make the shared skills live in ~/.claude/skills/jgb
python tools/agentkit.py install
python tools/agentkit.py install --copy     # force copy instead of symlink
python tools/agentkit.py uninstall

# inspect and check
python tools/agentkit.py list
python tools/agentkit.py validate
```

`validate` runs in CI and enforces: frontmatter present, `name` matches the
directory, names unique repo-wide, `description` non-trivial, plugins listed in
`marketplace.json` with a manifest that agrees on the name.

## Installing the plugins

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

The `description` is the entire trigger — it is all the model sees before
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
