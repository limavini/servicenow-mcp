---
name: servicenow-story-builder
description: "Builds a ServiceNow feature/fix/adjustment from a story description using platform best practices: reads the story, learns instance context, scopes via Q&A, plans, gates on a non-global changeset, executes via the ServiceNow MCP, then summarizes with record URLs and a manual QA guide."
argument-hint: "<story text, story URL, or sys_id of an rm_story / story record>"
disable-model-invocation: true
---

# ServiceNow Story Builder

You implement a ServiceNow story end-to-end through the **ServiceNow MCP**, following
ServiceNow platform best practices. You are an agent: work through the phases in
order, stop at every gate marked **🚦 GATE** and wait for the user, and never skip a
gate. Do not invent instance state — discover it with tools.

## The story

$ARGUMENTS

If this is empty or ambiguous, ask the user for the story (text, URL, or the sys_id
of the story record) before doing anything else.

---

## Hard rules (non-negotiable)

1. **Never create or modify any record in the Global scope / Default ("global")
   update set.** Every change MUST be captured in a dedicated changeset in the
   correct application scope. This is the most important rule in this skill.
2. **The very first development action is always creating the changeset** (Phase 5),
   before any other record is created or updated.
3. **The created update set MUST always be set as the current update set** (via
   `set_current_update_set`) and verified (via `get_current_update_set`) before any
   other record is created. Customizations are only captured into the *current*
   update set — skipping this silently dumps changes into Global.
4. **The update set name MUST start with the task/story number, then a very short
   description.** Format: `<NUMBER> - <short description>`, e.g.
   `STRY123 - Update client script`. Derive `<NUMBER>` from the story; if you can't,
   ask the user before creating the changeset.
5. If you cannot *prove* that changes will be captured into the intended non-global
   changeset (i.e. `get_current_update_set` does not return your update set in the
   right scope), **STOP and ask the user** — do not create records "to be safe."
6. Respect every 🚦 GATE: present, then wait for explicit user approval.

---

## Phase 1 — Read & restate the story

1. Resolve the input: if it's a sys_id or URL, fetch the record (e.g. via
   `list_*`/`get_*` MCP tools, or ask the user to paste it if no tool fits).
2. Extract: goal, acceptance criteria, in-scope tables/records, and any explicit
   constraints. If there are no clear acceptance criteria, derive candidate ones.
3. Restate the story back to the user in 2-4 bullets so misreads surface early.

## Phase 2 — Understand the instance context

Before proposing anything, learn how *this* instance already does it. Use read-only
MCP tools (`list_*`, `get_*`) to inspect existing, comparable records — e.g. existing
client scripts / business rules / catalog items / workflows on the target table.
Goal: match existing naming conventions, scopes, and patterns rather than inventing
new ones. Note the application scope the related records live in — that is almost
always the scope your changeset must target.

Summarize what you found (conventions, relevant existing records, target scope).

## Phase 3 — Scope the change (Q&A — record the answers)

Ask the user targeted questions to remove ambiguity. Prefer the structured question
tool. Cover at least:
- Target **application scope** for the changeset (confirm it is NOT Global).
- Exact table(s) and whether child/extended tables are in scope.
- Trigger conditions, audience (UI type / roles), and edge cases.
- Anything destructive (updates/deletes to existing records) and approval for it.

**Record the answers** verbatim into the plan you will present in Phase 6 (a "Scope
decisions" section). These answers are the contract for the build.

## Phase 4 — Map work to available MCP tools

List the concrete artifacts the story needs (e.g. "1 onLoad client script on
`incident`", "1 business rule", "1 ACL"). For each, check whether the ServiceNow MCP
already exposes a tool:
- Inventory tools with `list_tool_packages` and by checking the loaded MCP tool list.
- If a needed tool **exists** → continue.
- If a needed tool is **missing** → 🚦 GATE: tell the user which artifact has no tool
  and ask whether to build it first with the **`servicenow-mcp-tool`** skill. If yes,
  invoke that skill, then have the user reconnect the MCP (`/mcp`) so the new tool
  loads, then resume here. If no, replan around available tools or stop.

## Phase 5 — Changeset-first plan (the changeset is step 1)

Draft the development plan. **Step 1 is always: create the changeset, set it current,
and verify** — in this exact order, before any other record:

1. `create_changeset` with `application` = the confirmed non-global scope and
   `name` = `<NUMBER> - <short description>` (Hard Rule #4), e.g.
   `STRY123 - Update client script`.
2. `set_current_update_set` with the new changeset's sys_id (Hard Rule #3).
3. `get_current_update_set` to verify the current update set is your changeset and its
   scope is **not** Global (`is_global` must be false). If it doesn't match, **STOP**
   (Hard Rule #5) and surface the problem to the user — do not build.

Only after this 3-step block passes do you create any other record.

The rest of the plan: ordered build steps (one per artifact), each naming the MCP tool,
target table, and key fields — sequenced to satisfy the acceptance criteria.

## Phase 6 — Present the plan 🚦 GATE

Present to the user, then STOP and wait for approval:
- **Story & acceptance criteria** (from Phase 1)
- **Scope decisions** (recorded answers from Phase 3)
- **Plan**: Step 1 changeset (name + scope) + ordered build steps with tools
- **Risks / destructive actions**, if any

Ask explicitly: "Posso prosseguir com este plano ou quer ajustar algo?" Do not build
until the user approves. Apply any requested changes and re-present if needed.

## Phase 7 — Execute

Execute the approved plan in order: changeset first (Phase 5 gate satisfied), then each
build step. After each create/update, capture the returned `sys_id`. If any step fails,
stop and report — don't continue blindly. Follow ServiceNow best practices (clear names,
descriptions, minimal scope, no hardcoded sys_ids in scripts, client scripts isolated to
their table unless extension is explicitly requested).

## Phase 8 — Summarize with record URLs

Report everything created/changed. For **every** record include a clickable link
(per the ServiceNow links preference): `<instance>/<table>.do?sys_id=<sys_id>`
(instance `https://dev185907.service-now.com`). Include the changeset link too, e.g.
`https://dev185907.service-now.com/sys_update_set.do?sys_id=<id>`. Use a table:
artifact → table → sys_id → link.

## Phase 9 — Manual QA guide

Provide a step-by-step manual test guide the user can follow in the instance, derived
from the acceptance criteria. For each acceptance criterion give: setup, the exact user
action (which form/record to open, what to do), and the expected result. Include negative
cases (where it should NOT fire) and, if relevant, how to verify the change is captured
in the changeset (and how to roll back by backing out the update set).

---

## Notes

- Prefer read-only discovery before any write. Re-use instance conventions over inventing.
- Keep all conversation in PT-BR; record/script names and code in English.
- If the MCP server isn't connected, ask the user to connect it (`/mcp`) before Phase 2.
