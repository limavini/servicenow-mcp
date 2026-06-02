# ServiceNow Claude skills

Claude Code skills for working with this ServiceNow MCP server, version-controlled
alongside the server itself.

| Skill | What it does |
|-------|--------------|
| `servicenow-mcp-tool` | Adds a new CRUD toolset to this MCP server for a ServiceNow table that isn't covered yet. |
| `servicenow-story-builder` | Builds a ServiceNow feature/fix from a story end-to-end (context → scope Q&A → changeset-first plan → execute → QA guide). Manual-invoke only. |

## Install (on any machine)

```bash
git clone https://github.com/limavini/servicenow-mcp.git
cd servicenow-mcp
bash claude-skills/install.sh
```

This symlinks each skill into `~/.claude/skills/`. Because they are symlinks, a
`git pull` updates the skills with no reinstall. Override the destination with
`CLAUDE_SKILLS_DIR=/custom/path bash claude-skills/install.sh`.

Open Claude Code and the skills are available (e.g. `/servicenow-story-builder`).

## Machine-specific values

These skills contain values specific to the author's setup that you must adjust
on a new machine:

- **Instance URL** — `https://dev185907.service-now.com` appears in the skills for
  building record links. Change it to your own ServiceNow instance.
- **Repo path** — `servicenow-mcp-tool` references the local checkout path
  `/Users/vinicius.almeida/repos/servicenow-mcp`. Point it at your own clone.

The MCP server connection itself (instance URL, credentials) is configured in your
Claude Code MCP settings, not here.
