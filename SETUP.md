# Setup — ServiceNow MCP + skills (macOS, from scratch)

Step-by-step to get the ServiceNow MCP server and its Claude skills running on a
fresh Mac (no Homebrew / git / Python yet). Commands are copy-paste friendly.

> Replace `your-instance`, `your-username`, `your-password` with real values.
> This guide clones the repo into `~/servicenow-mcp`.

## 1. Install the base tools (Homebrew, git, Python)

Open **Terminal** (Cmd+Space → "Terminal") and run:

```bash
# Homebrew (will ask for your Mac password; follow the on-screen "Next steps")
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Make brew available in this shell (Apple Silicon path; Intel uses /usr/local)
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

Check the server entry point exists:
```bash
.venv/bin/servicenow-mcp --help
```

## 4. Configure the ServiceNow instances

Create your real credentials file from the template (this file is **gitignored** —
it never gets committed):

```bash
cp instances.example.json instances.json
```

Edit `instances.json` (e.g. `open -e instances.json`) so it has your instance(s):

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

This file is the single source of credentials — the server boots straight from it,
so you do **not** need any ServiceNow values in the environment. With more than one
instance, mark one with `"default": true` (or set the `SERVICENOW_DEFAULT_INSTANCE`
env var) to choose which one the server starts on; switch any time at runtime.

## 5. Install Claude Code (if not already)

If you don't have Claude Code yet, install it and sign in following the official
docs at https://claude.ai/code . Then verify:

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

## 7. Install the Claude skills

```bash
bash claude-skills/install.sh
```

This symlinks the ServiceNow skills into `~/.claude/skills/`. A future `git pull`
updates them automatically.

## 8. Verify

1. Open Claude Code (`claude`) in any folder.
2. Run `/mcp` and confirm **ServiceNow** is connected.
3. Ask: "list the ServiceNow instances" → it should call `list_instances` and show
   what's in your `instances.json`.
4. The skills are available too — e.g. `/servicenow-story-builder`.

## Updating later

```bash
cd ~/servicenow-mcp
git pull
.venv/bin/pip install -e .   # only if dependencies changed
```
Then reconnect the server in Claude with `/mcp`.

## Notes / safety

- `instances.json` and `.env` hold secrets and are **gitignored** — never commit them.
- To switch instances during a session, just ask Claude to select another one
  (`select_instance`), or the `servicenow-story-builder` skill will ask you up front.
