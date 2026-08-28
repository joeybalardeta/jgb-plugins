#!/usr/bin/env python3
"""agentkit - scaffold, install and validate skills/plugins in this repo.

Skills here follow the agentskills.io SKILL.md format, which both Claude Code
and Codex CLI read. Plugins are Claude Code specific.

Usage:
    python tools/agentkit.py new-skill <name> [--plugin <plugin>] [--desc "..."]
    python tools/agentkit.py new-plugin <name> [--desc "..."]
    python tools/agentkit.py install [--claude] [--codex] [--copy] [--dry-run]
    python tools/agentkit.py uninstall
    python tools/agentkit.py list
    python tools/agentkit.py validate

No third-party dependencies. Python 3.9+.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
PLUGINS = REPO / "plugins"
MARKETPLACE = REPO / ".claude-plugin" / "marketplace.json"

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_NAME = "jgb"  # subdirectory name created inside each agent's skills dir

C_OK, C_WARN, C_ERR, C_DIM, C_OFF = "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[0m"
if os.name == "nt" and not os.environ.get("WT_SESSION"):
    C_OK = C_WARN = C_ERR = C_DIM = C_OFF = ""


def say(msg: str, color: str = "") -> None:
    print(f"{color}{msg}{C_OFF}")


def die(msg: str) -> "typing.NoReturn":  # noqa: F821
    say(f"error: {msg}", C_ERR)
    raise SystemExit(1)


def check_slug(name: str, what: str) -> None:
    if not SLUG_RE.match(name):
        die(f"{what} name must be kebab-case (a-z, 0-9, hyphens): got {name!r}")


# --------------------------------------------------------------------------
# frontmatter
# --------------------------------------------------------------------------

def parse_frontmatter(path: Path) -> dict:
    """Minimal YAML frontmatter reader: flat `key: value` pairs only."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    data: dict[str, str] = {}
    key = None
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1] in " \t" and key:  # folded continuation
            data[key] = (data[key] + " " + line.strip()).strip()
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        data[key] = value.strip().strip('"').strip("'")
    return data


SKILL_TEMPLATE = """---
name: {name}
description: {desc}
---

# {title}

## When to use this

{desc}

Do NOT use this when: <the near-miss cases you want the model to skip>.

## Steps

1. <first concrete action>
2. <second>
3. <verify the result>

## Notes

- Keep this file under ~500 lines. Put long reference material in
  `references/` next to this file and link to it.
- Anything executable goes in `scripts/` next to this file.
"""


def write_skill(target: Path, name: str, desc: str) -> None:
    if target.exists():
        die(f"{target.relative_to(REPO)} already exists")
    target.mkdir(parents=True)
    title = name.replace("-", " ").title()
    (target / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(name=name, desc=desc, title=title), encoding="utf-8"
    )
    (target / "references").mkdir()
    (target / "references" / ".gitkeep").touch()


# --------------------------------------------------------------------------
# marketplace
# --------------------------------------------------------------------------

def load_marketplace() -> dict:
    return json.loads(MARKETPLACE.read_text(encoding="utf-8"))


def save_marketplace(data: dict) -> None:
    MARKETPLACE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_new_skill(args: argparse.Namespace) -> int:
    check_slug(args.name, "skill")
    desc = args.desc or (
        f"TODO describe {args.name}. State exactly when this should trigger "
        "and when it should not."
    )
    if args.plugin:
        check_slug(args.plugin, "plugin")
        base = PLUGINS / args.plugin
        if not base.is_dir():
            die(f"no such plugin: {args.plugin} (run new-plugin first)")
        target = base / "skills" / args.name
    else:
        target = SKILLS / args.name

    for existing in all_skill_dirs():
        if existing.name == args.name:
            die(f"skill name {args.name!r} already used at {existing.relative_to(REPO)}")

    write_skill(target, args.name, desc)
    say(f"created {target.relative_to(REPO)}/SKILL.md", C_OK)
    say("  next: write the description first - it is the whole trigger.", C_DIM)
    return 0


PLUGIN_README = """# {name}

{desc}

## Contents

- `skills/` - skills scoped to this plugin
- `commands/` - Claude Code slash commands (`/{name}:<command>`)
- `agents/` - subagent definitions
- `hooks/hooks.json` - lifecycle hooks
- `.mcp.json` - MCP servers bundled with this plugin

Install locally:

    /plugin marketplace add ./
    /plugin install {name}@jgb-plugins
"""


def cmd_new_plugin(args: argparse.Namespace) -> int:
    check_slug(args.name, "plugin")
    base = PLUGINS / args.name
    if base.exists():
        die(f"plugins/{args.name} already exists")
    desc = args.desc or f"TODO describe the {args.name} plugin."

    (base / ".claude-plugin").mkdir(parents=True)
    for sub in ("skills", "commands", "agents", "hooks"):
        (base / sub).mkdir()
        (base / sub / ".gitkeep").touch()

    manifest = {
        "name": args.name,
        "description": desc,
        "version": "0.1.0",
        "author": {"name": "Joey Balardeta"},
    }
    (base / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (base / "hooks" / "hooks.json").write_text(
        json.dumps({"hooks": {}}, indent=2) + "\n", encoding="utf-8"
    )
    (base / "README.md").write_text(
        PLUGIN_README.format(name=args.name, desc=desc), encoding="utf-8"
    )

    data = load_marketplace()
    entry = {
        "name": args.name,
        "source": f"./plugins/{args.name}",
        "description": desc,
        "version": "0.1.0",
    }
    data.setdefault("plugins", [])
    if any(p.get("name") == args.name for p in data["plugins"]):
        die(f"{args.name} already listed in marketplace.json")
    data["plugins"].append(entry)
    data["plugins"].sort(key=lambda p: p.get("name", ""))
    save_marketplace(data)

    say(f"created plugins/{args.name} and registered it in marketplace.json", C_OK)
    return 0


def all_skill_dirs() -> list[Path]:
    found = []
    for root in (SKILLS, PLUGINS):
        if root.is_dir():
            found.extend(sorted(p.parent for p in root.rglob("SKILL.md")))
    return found


def cmd_list(args: argparse.Namespace) -> int:
    data = load_marketplace()
    say("plugins:", C_DIM)
    for p in data.get("plugins", []) or [{"name": "(none)", "description": ""}]:
        print(f"  {p['name']:<24} {p.get('description', '')}")
    say("skills:", C_DIM)
    dirs = all_skill_dirs()
    if not dirs:
        print("  (none)")
    for d in dirs:
        fm = parse_frontmatter(d / "SKILL.md")
        scope = "shared" if SKILLS in d.parents else d.relative_to(PLUGINS).parts[0]
        print(f"  {fm.get('name', d.name):<24} [{scope}] {fm.get('description', '')[:60]}")
    return 0


# --------------------------------------------------------------------------
# install
# --------------------------------------------------------------------------

def targets(args: argparse.Namespace) -> list[tuple[str, Path]]:
    home = Path.home()
    both = not (args.claude or args.codex)
    out = []
    if args.claude or both:
        out.append(("claude", home / ".claude" / "skills" / LINK_NAME))
    if args.codex or both:
        out.append(("codex", home / ".agents" / "skills" / LINK_NAME))
    return out


def link_or_copy(src: Path, dst: Path, force_copy: bool, dry: bool) -> str:
    if dry:
        return f"would link {dst} -> {src}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or dst.exists():
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    if not force_copy:
        try:
            dst.symlink_to(src, target_is_directory=True)
            return f"linked {dst} -> {src}"
        except OSError:
            pass  # Windows without Developer Mode / admin
    shutil.copytree(src, dst)
    return f"copied {src} -> {dst} (re-run install after editing skills)"


def cmd_install(args: argparse.Namespace) -> int:
    if not SKILLS.is_dir():
        die("skills/ not found")
    for label, dst in targets(args):
        msg = link_or_copy(SKILLS, dst, args.copy, args.dry_run)
        say(f"{label}: {msg}", C_OK)
    if not args.dry_run:
        say("\nrestart Claude Code / Codex to pick up new skills.", C_DIM)
        say("plugins are installed separately in Claude Code:", C_DIM)
        say("  /plugin marketplace add joeybalardeta/jgb-plugins", C_DIM)
    return 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    for label, dst in targets(args):
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
            say(f"{label}: removed {dst}", C_OK)
        elif dst.is_dir():
            shutil.rmtree(dst)
            say(f"{label}: removed {dst}", C_OK)
        else:
            say(f"{label}: nothing at {dst}", C_DIM)
    return 0


# --------------------------------------------------------------------------
# validate
# --------------------------------------------------------------------------

def cmd_validate(args: argparse.Namespace) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        data = load_marketplace()
    except Exception as exc:  # noqa: BLE001
        die(f"marketplace.json is not valid JSON: {exc}")

    for field in ("name", "owner", "plugins"):
        if field not in data:
            errors.append(f"marketplace.json missing required field {field!r}")

    listed = set()
    for entry in data.get("plugins", []):
        name = entry.get("name")
        if not name:
            errors.append("marketplace.json has a plugin entry with no name")
            continue
        listed.add(name)
        if not SLUG_RE.match(name):
            errors.append(f"plugin {name!r} is not kebab-case")
        src = entry.get("source")
        if isinstance(src, str) and src.startswith("./"):
            path = REPO / src[2:]
            if not path.is_dir():
                errors.append(f"plugin {name!r} source {src} does not exist")
            elif not (path / ".claude-plugin" / "plugin.json").is_file():
                errors.append(f"plugin {name!r} is missing .claude-plugin/plugin.json")

    if PLUGINS.is_dir():
        for path in sorted(PLUGINS.iterdir()):
            if path.is_dir() and path.name not in listed:
                warnings.append(f"plugins/{path.name} is not listed in marketplace.json")
            if path.is_dir():
                manifest = path / ".claude-plugin" / "plugin.json"
                if manifest.is_file():
                    try:
                        m = json.loads(manifest.read_text(encoding="utf-8"))
                        if m.get("name") != path.name:
                            errors.append(
                                f"plugins/{path.name}: plugin.json name is "
                                f"{m.get('name')!r}, should match directory"
                            )
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"plugins/{path.name}/plugin.json invalid: {exc}")

    seen: dict[str, Path] = {}
    for d in all_skill_dirs():
        rel = d.relative_to(REPO)
        fm = parse_frontmatter(d / "SKILL.md")
        if not fm:
            errors.append(f"{rel}/SKILL.md has no YAML frontmatter")
            continue
        name = fm.get("name")
        desc = fm.get("description", "")
        if not name:
            errors.append(f"{rel}/SKILL.md frontmatter missing 'name'")
        elif name != d.name:
            errors.append(f"{rel}/SKILL.md name {name!r} != directory {d.name!r}")
        elif not SLUG_RE.match(name):
            errors.append(f"{rel}: skill name {name!r} is not kebab-case")
        if name:
            if name in seen:
                errors.append(f"duplicate skill name {name!r}: {rel} and {seen[name]}")
            seen[name] = rel
        if not desc:
            errors.append(f"{rel}/SKILL.md frontmatter missing 'description'")
        elif len(desc) < 30:
            warnings.append(f"{rel}: description is very short - triggering will be poor")
        elif desc.lower().startswith("todo"):
            warnings.append(f"{rel}: description is still a TODO placeholder")
        lines = (d / "SKILL.md").read_text(encoding="utf-8").count("\n")
        if lines > 500:
            warnings.append(f"{rel}/SKILL.md is {lines} lines - move detail to references/")

    for w in warnings:
        say(f"warn: {w}", C_WARN)
    for e in errors:
        say(f"error: {e}", C_ERR)
    if errors:
        say(f"\n{len(errors)} error(s), {len(warnings)} warning(s)", C_ERR)
        return 1
    say(
        f"\nok: {len(seen)} skill(s), {len(listed)} plugin(s), "
        f"{len(warnings)} warning(s)",
        C_OK,
    )
    return 0


# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentkit", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("new-skill", help="scaffold a skill")
    p.add_argument("name")
    p.add_argument("--plugin", help="scope the skill to a plugin instead of skills/")
    p.add_argument("--desc", help="description used for implicit triggering")
    p.set_defaults(func=cmd_new_skill)

    p = sub.add_parser("new-plugin", help="scaffold a Claude Code plugin")
    p.add_argument("name")
    p.add_argument("--desc")
    p.set_defaults(func=cmd_new_plugin)

    p = sub.add_parser("install", help="link skills/ into Claude and Codex skill dirs")
    p.add_argument("--claude", action="store_true", help="only ~/.claude/skills")
    p.add_argument("--codex", action="store_true", help="only ~/.agents/skills")
    p.add_argument("--copy", action="store_true", help="copy instead of symlink")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("uninstall", help="remove the installed links")
    p.add_argument("--claude", action="store_true")
    p.add_argument("--codex", action="store_true")
    p.set_defaults(func=cmd_uninstall)

    p = sub.add_parser("list", help="list plugins and skills")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("validate", help="check structure and frontmatter")
    p.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
