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

The skills are machine-agnostic: they resolve the instance URL and the repo path at
runtime from your Claude MCP config (`~/.claude.json`) — the ServiceNow server's
`SERVICENOW_INSTANCE_URL` env and the parent of its `command` path. Nothing to edit
by hand.

The only prerequisite is that the **ServiceNow MCP server is configured and connected**
in your Claude Code (instance URL + credentials live there, in a local `.env` /
MCP settings — never committed).
