# ServiceNow MCP — install from scratch (macOS)

A Model Context Protocol (MCP) server that lets Claude work with ServiceNow instances.
This is a fork of [echelon-ai-labs/servicenow-mcp](https://github.com/echelon-ai-labs/servicenow-mcp)
with extra tools (client scripts, current update set, multi-instance selection) and a
set of Claude skills bundled under `claude-skills/`.

This README is a **step-by-step setup for a fresh Mac** (no Homebrew / git / Python /
Claude Code yet). Commands are copy-paste friendly.

> Replace `your-instance`, `your-username`, `your-password` with real values.
> This guide clones the repo into `~/servicenow-mcp`.

---

## 1. Install the base tools (Homebrew, git, Python)

Open **Terminal** (Cmd+Space → type "Terminal") and run:

```bash
# Homebrew (asks for your Mac password; then follow its "Next steps" output)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Make brew available in this shell (Apple Silicon path; Intel Macs use /usr/local)
eval "$(/opt/homebrew/bin/brew shellenv)"

# git + Python 3.11+
brew install git python
```

Check:
```bash
git --version && python3 --version   # Python must be >= 3.11
```

## 2. Get the code

```bash
cd ~
git clone https://github.com/limavini/servicenow-mcp.git
cd servicenow-mcp
```

## 3. Create the Python environment and install

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .
```

Check the server entry point works:
```bash
.venv/bin/servicenow-mcp --help
```

## 4. Configure your ServiceNow instance(s)

Create your real credentials file from the template (it is **gitignored** — it never
gets committed):

```bash
cp instances.example.json instances.json
open -e instances.json
```

Fill it in with your instance(s). The server boots straight from this file, so you do
**not** need any credentials in the environment:

```json
{
  "your-instance": {
    "default": true,
    "instance_url": "https://your-instance.service-now.com",
    "auth_type": "basic",
    "username": "your-username",
    "password": "your-password"
  }
}
```

- With more than one instance, mark one with `"default": true` (or set the
  `SERVICENOW_DEFAULT_INSTANCE` env var) to choose which one the server starts on.
- You can switch instances at runtime later (the skills ask you up front).
- OAuth: `"auth_type": "oauth"` with `client_id`/`client_secret`/`username`/`password`
  (and optional `token_url`). API key: `"auth_type": "api_key"` with `api_key`.

## 5. Install Claude Code

If you don't have it yet, install Claude Code and sign in following the official docs at
https://claude.ai/code . Then verify:

```bash
claude --version
```

## 6. Register the MCP server in Claude Code

No credentials needed here — the server reads them from `instances.json` (step 4):

```bash
claude mcp add ServiceNow \
  --scope user \
  -- "$HOME/servicenow-mcp/.venv/bin/servicenow-mcp"
```

## 7. Install the bundled Claude skills

```bash
bash claude-skills/install.sh
```

This symlinks the ServiceNow skills into `~/.claude/skills/`. A future `git pull`
updates them automatically. See `claude-skills/README.md` for what each skill does.

## 8. Verify

1. Open Claude Code (`claude`) in any folder.
2. Run `/mcp` and confirm **ServiceNow** is connected.
3. Ask: "list the ServiceNow instances" → it calls `list_instances` and shows your
   `instances.json` entries.
4. The skills are available too — e.g. `/servicenow-story-builder`.

---

## Updating later

```bash
cd ~/servicenow-mcp
git pull
.venv/bin/pip install -e .   # only if dependencies changed
```
Then reconnect the server in Claude with `/mcp`.

## Safety

- `instances.json` and `.env` hold secrets and are **gitignored** — never commit them.
- To switch instances during a session, ask Claude to select another one
  (`select_instance`), or let the `servicenow-story-builder` skill ask you up front.

## Credits & license

Fork of [echelon-ai-labs/servicenow-mcp](https://github.com/echelon-ai-labs/servicenow-mcp).
Licensed under the MIT License — see the [LICENSE](LICENSE) file.
