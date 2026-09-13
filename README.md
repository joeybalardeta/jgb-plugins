# jgb-plugins

Personal plugins and skills for **Claude Code**.

## Layout

```
skills/                             shared skills, each a directory with a SKILL.md
plugins/<name>/                     plugins
  .claude-plugin/plugin.json        plugin manifest
  skills/                           skills scoped to this plugin
  commands/                         slash commands  (/<plugin>:<command>)
  agents/                           subagent definitions
  hooks/hooks.json                  lifecycle hooks
  .mcp.json                         MCP servers bundled with the plugin
.claude-plugin/marketplace.json     the catalog Claude Code installs from
```

## Installing the plugins

```
/plugin marketplace add joeybalardeta/jgb-plugins
/plugin install <plugin>@jgb-plugins
```

## Writing a good skill

The `description` frontmatter is the entire trigger — it is all the model sees
before deciding to load the file. Say when it applies *and* when it does not:

```yaml
---
name: release-notes
description: Generate release notes from git history. Use when the user asks for a changelog, release summary, or "what shipped". Not for writing individual commit messages.
---
```

Keep `SKILL.md` under ~500 lines; push detail into `references/` beside it and
link. Put anything executable in `scripts/`.
