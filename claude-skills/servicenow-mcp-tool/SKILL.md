---
name: servicenow-mcp-tool
description: "Adds a new CRUD toolset to the local servicenow-mcp server for a ServiceNow table that isn't covered yet. Use when the user wants to create/list/get/update/delete records of a ServiceNow table (e.g. client scripts, business rules, UI policies, ACLs) but no MCP tool exists for it."
argument-hint: "[table name or feature, e.g. 'business rules (sys_script)']"
---

# ServiceNow MCP — Add Tools for a New Table

You are extending the user's **local** ServiceNow MCP server so it can manage a new
ServiceNow table. It exposes tools backed by the ServiceNow Table API
(`/api/now/table/<table>`). This guide refers to the local checkout of the
servicenow-mcp repo as **`$SN_MCP`** — resolve its real path in "Before you start"
(do not assume a hardcoded path).

## What the user wants

$ARGUMENTS

If the table / feature is unclear, ask which ServiceNow table to target (the
`sys_*` table name, e.g. `sys_script_client` for client scripts) and which
operations they need (default: full CRUD — list, get, create, update, delete).

## Before you start

1. Resolve `$SN_MCP` (the repo path) from the Claude MCP config — it is the parent
   of the `command` path of the ServiceNow server:
   `grep -A6 '"ServiceNow"' ~/.claude.json` (the `command` is `<$SN_MCP>/.venv/bin/python`).
   Likewise resolve `<instance>` from the server's `SERVICENOW_INSTANCE_URL` env in
   the same config. Use these resolved values everywhere below — never a hardcoded path
   or instance.
2. **Read `src/servicenow_mcp/tools/script_include_tools.py` as your template.**
   It is the canonical CRUD module (operates on `sys_script_include`). The
   `client_script_tools.py` module (on `sys_script_client`) is a second worked
   example — read it too if the target has booleans, field aliases, or a shared
   `_build_body` helper. Mirror their structure exactly.
3. Identify the target table's real field names. Don't guess — when unsure, call
   the existing `list_*` MCP tools or fetch one record via the Table API to see
   the columns. Common gotcha: the display label differs from the column name
   (e.g. client script "Field name" is the `field` column; "UI type" is `ui_type`).

## The 4 wiring points (all required)

A tool is only live after it's registered in **all four** places. Missing any one
means the tool silently won't appear or won't dispatch.

### 1. New module: `src/servicenow_mcp/tools/<name>_tools.py`

Follow `script_include_tools.py` precisely:

- Pydantic param models: `List<X>Params`, `Get<X>Params`, `Create<X>Params`,
  `Update<X>Params`, `Delete<X>Params`, plus a `<X>Response` model
  (`success`, `message`, `<x>_id`, `<x>_name`).
- Five functions with the signature `(config: ServerConfig, auth_manager: AuthManager, params) -> ...`.
- Use `requests` against `f"{config.instance_url}/api/now/table/<table>"`.
- Read ops: GET with `sysparm_display_value=true`, `sysparm_exclude_reference_link=true`,
  `sysparm_fields=<explicit field list>`. Create: POST. Update: PATCH to
  `/<table>/{sys_id}`. Delete: DELETE.
- `get_*` should accept either `sys_id:<id>` (direct `/table/{sys_id}`) or a name
  (query `name=<value>`). `update_*` / `delete_*` resolve via `get_*` first.
- **Booleans are sent as lowercase strings** (`str(value).lower()`), and parsed
  back with `item.get("field") == "true"`.
- Build the create/update body including **only provided (non-None) fields** so
  partial updates work. A shared `_build_body(params)` helper (see
  `client_script_tools.py`) keeps create/update consistent.
- If a field name collides with a Python keyword (e.g. `global`), use a Pydantic
  field with `alias="global"` and `class Config: populate_by_name = True`, and map
  it explicitly in the body.

### 2. `src/servicenow_mcp/tools/__init__.py`

- Add a `from servicenow_mcp.tools.<name>_tools import (...)` block importing the
  five functions.
- Add the five tool names to `__all__` under a new comment header.

### 3. `src/servicenow_mcp/utils/tool_utils.py`

- Add imports: the param/response models, plus each function aliased as
  `<fn> as <fn>_tool` (match the existing per-function import style).
- Inside `get_tool_definitions(...)`, add one dict entry per tool. The 5-tuple is:
  `(impl_func, ParamsModel, return_annotation, "description", serialization_hint)`.
  Use the existing script_include entries as the exact pattern:
  - list/get → `Dict[str, Any]`, hint `"raw_dict"`
  - create/update → `<X>Response`, hint `"raw_pydantic"`
  - delete → `str`, hint `"json_dict"`

### 4. `config/tool_packages.yaml`

- Add the five tool names under a comment header in **`full`** (always) and in any
  relevant role package (e.g. `platform_developer` for dev-facing tables,
  `system_administrator` for admin tables). Match where `script_include` tools sit.

## Validate before declaring done

Run with the project venv (`$SN_MCP/.venv/bin/python`):

```bash
cd "$SN_MCP"
.venv/bin/python -c "
from servicenow_mcp.tools.knowledge_base import create_category, list_categories
from servicenow_mcp.utils.tool_utils import get_tool_definitions
defs = get_tool_definitions(create_category, list_categories)
print('registered:', [k for k in defs if '<name>' in k])
"
.venv/bin/python -c "import yaml; d=yaml.safe_load(open('config/tool_packages.yaml')); print('full:', [t for t in d['full'] if '<name>' in t])"
```

Both must list the five new tools. Also smoke-test a param model and `_build_body`
to confirm boolean→string conversion and any aliases behave.

## Tell the user about the reload

The running MCP server loaded the **old** code at session start — new tools won't
appear until it reconnects. Instruct the user to run `/mcp` and reconnect the
ServiceNow server (or restart Claude Code). Only after that can you load the new
tool's schema via ToolSearch (`select:mcp__ServiceNow__<tool>`) and call it.

## Update set: never use any application's Default; prefer a named Global set

Every create/update/delete is captured into the caller's **current update set**.
Before mutating anything, point that at a proper named set — **never leave changes
in any application's `Default` update set** (it is not cleanly transportable and
must not be used).

- **Set the current update set first.** Use the MCP tools `get_current_update_set`
  and `set_current_update_set` (they write the per-user `sys_update_set`
  preference). Point it at a **named** update set before the first
  create/update/delete. If none exists, create one (`sys_update_set`,
  `state=in progress`).
- **Prefer — and prioritize — the Global application scope.** A single Global
  named update set can hold captures from *multiple* scopes: with it current,
  editing even a scoped record (e.g. an `sp_instance` in a scoped app) is captured
  into that Global set. So you normally need just **one** named Global update set
  for the whole change. Via REST the session is always Global, so a set you create
  lands in Global scope — exactly what we want.
- **Capture vs. move.** Routing happens at *capture* time and honors the current
  set. You **cannot move** an already-captured `sys_update_xml` between update sets
  of **different scopes** (HTTP 403). If something landed in the wrong set, make the
  right set current and **re-touch** the record to re-capture it. An orphan
  `sys_update_xml` left in `Default` can simply be DELETEd (that works cross-scope).
  Switching a session's *application scope* is only possible via the UI app-picker,
  not via REST.
- Restore the current update set to its prior value when done, so later operations
  don't leak into this change's set.

## Always send the record link

Whenever you create a record via one of these tools, include a clickable link to
it in your response (not just the sys_id): `<instance>/<table>.do?sys_id=<sys_id>`,
where `<instance>` is the resolved `SERVICENOW_INSTANCE_URL` (see "Before you start").

## Commit & push to the fork (hard rule)

**Any change to the MCP server MUST be committed and pushed to the `main` of the
fork.** The fork (`limavini/servicenow-mcp`, git remote `fork`) is the source of
truth and is shared across machines. After validating new/changed tools:

1. Stage the changed files (new tool module + the 3 wiring files, and any updated
   skill under `claude-skills/`).
2. Commit with a clear conventional message (e.g. `feat: add <table> tools`),
   authored by the repo-local git identity.
3. Push to the fork's `main`: `git push fork main` (fast-forward `main` first if you
   worked on a branch).

Do not leave MCP changes uncommitted/local — the change isn't "done" until it's on
the fork's `main`.

## Notes

- The server is read/write against a real instance — `create`/`update`/`delete`
  mutate live data. For destructive operations on shared/non-dev instances,
  confirm with the user first.
- Keep code style identical to the surrounding modules: same logging, docstrings,
  `timeout=30`, and error-handling shape. Don't introduce new dependencies.
