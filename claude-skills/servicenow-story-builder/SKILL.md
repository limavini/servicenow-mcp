---
name: servicenow-story-builder
description: "Builds a ServiceNow feature/fix/adjustment from a story description using platform best practices: reads the story, learns instance context, scopes via Q&A, plans, gates on a named (non-Default) update set — Global by default, executes via the ServiceNow MCP, then summarizes with record URLs and a manual QA guide."
argument-hint: "<story text, story URL, or sys_id of an rm_story / story record>"
disable-model-invocation: true
---

# ServiceNow Story Builder

You implement a ServiceNow story end-to-end through the **ServiceNow MCP**, following
ServiceNow platform best practices.

## EXECUTION PROTOCOL — read this first, it overrides your instinct to "just do it"

This skill is a **strict, gated, sequential procedure**, not reference material. The
request will often look simple enough to implement in one shot. **Do not.** Run the
phases in order, one at a time.

1. **Go phase by phase: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9.** Announce each phase by
   name as you enter it ("**Phase 0 — Select the instance**"). Never skip, reorder, or
   merge phases.
2. **A phase marked 🚦 GATE means: ask the question, then STOP and END YOUR TURN.** Do
   not call any further tool and do not start the next phase in the same turn — wait for
   the user's reply. The gates are Phase 0 (instance) and Phase 6 (plan approval).
3. **Create or modify ZERO records until the user approves the plan in Phase 6.** Phases
   0–5 are read-only + planning only. The first write is the update set in Phase 7.
4. **No write ever lands in any Default update set; new work defaults to the Global scope** (see Hard rules).
5. If the story is trivial, you STILL follow every phase — just keep each one short.

If you catch yourself about to create/update a record before Phase 7, stop: you skipped
a gate. Go back.

## The story

$ARGUMENTS

If this is empty or ambiguous, ask the user for the story (text, URL, or the sys_id
of the story record) before doing anything else.

---

## Hard rules (non-negotiable)

0. **Always select the target instance first (Phase 0), before anything else.** Never
   read or write against ServiceNow until the user has explicitly chosen the instance
   for this session via `select_instance`, confirmed with `get_current_instance`.
0b. **Read and follow the best-practices doc before planning or building.** Read
   `~/.claude/skills/servicenow-story-builder/best-practices.md` (e.g. use widget
   Options/system properties instead of hardcoding, never edit baseline widgets, no
   hardcoded sys_ids). The plan and every record you create/update must comply; if the
   story conflicts with a best practice, surface the trade-off to the user.
1. **Never let a change land in any application's Default update set.** Every change
   MUST be captured in a dedicated **named** update set. **Prefer the Global scope** — a
   single Global named update set captures changes across scopes, so one set normally
   covers the whole story. This is the most important rule in this skill.
1b. **Start in the Global application scope and stay there by default.** Create the update
   set in **Global** and keep new artifacts global. Only target another application scope
   when a record you must edit *already lives* in that scope (e.g. a scoped widget or
   table) — then use an update set in that record's application for those edits. Never
   default to a non-Global scope "just in case".
2. **The very first development action is always creating the update set** (Phase 5),
   before any other record is created or updated.
3. **The created update set MUST always be set as the current update set** (via
   `set_current_update_set`) and verified (via `get_current_update_set`) before any
   other record is created. Customizations are only captured into the *current*
   update set — skipping this silently dumps changes into the Default update set.
4. **The update set name MUST start with the task/story number, then a very short
   description.** Format: `<NUMBER> - <short description>`, e.g.
   `STRY123 - Update client script`. Derive `<NUMBER>` from the story; if you can't,
   ask the user before creating the update set.
5. If you cannot *prove* that changes will be captured into the intended **named**
   update set (i.e. `get_current_update_set` does not return your update set, or it
   returns a Default set), **STOP and ask the user** — do not create records "to be safe."
6. **Never modify a default / baseline platform record. Always clone it and modify the
   clone.** A baseline record is anything shipped by ServiceNow / not authored in your
   scope (e.g. OOB widgets, themes, business rules, UI scripts, script includes). Many
   are protected and silently ignore writes anyway; editing them also breaks upgrades.
   When a story requires changing baseline behavior:
   - **🚦 Ask the user for the prefix** to use on the cloned record's name, then name
     the clone `<PREFIX> <original name>` (e.g. prefix `RMT` → `RMT Approval Widget`).
   - Create the clone in your scope/update set, repoint references to it (e.g. a Service
     Portal page's `sp_instance` to the cloned widget), and make all edits there.
   - Never let the plan or execution touch the original baseline record.
7. Respect every 🚦 GATE: present, then wait for explicit user approval.

---

## Phase 0 — Select the instance 🚦 GATE

Before reading the story or touching ServiceNow:

1. Call `list_instances` to get the configured instances.
2. Present them to the user (prefer the structured question tool) and let them choose
   which instance this session targets. If exactly one exists you may still confirm it.
3. Call `select_instance` with the chosen name, then `get_current_instance` to verify
   the active connection is what the user picked.

**🚦 GATE: present the instance options, then STOP and end your turn.** Wait for the
user to choose; only after they reply do you call `select_instance` and continue.
Do not proceed to Phase 1 until an instance is selected and verified. If the user
later wants to switch, re-run this phase.

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
new ones. Note the application scope the related records live in: new artifacts default
to **Global**, but if you must edit a record that already lives in another application,
those edits belong in an update set in *that* application (Hard rule #1b).

Summarize what you found (conventions, relevant existing records, target scope).

Also **read `~/.claude/skills/servicenow-story-builder/best-practices.md` now** and
keep it in mind for the rest of the phases — it governs how the change is designed
and built (Service Portal options vs hardcoding, no baseline edits, no hardcoded
sys_ids, etc.).

## Phase 3 — Scope the change (Q&A — record the answers)

Ask the user targeted questions to remove ambiguity. Prefer the structured question
tool. Cover at least:
- **Update set**: a named set, **Global by default** (never a Default set). Flag any record that already lives in another application — only those edits switch scope (Hard rule #1b).
- Exact table(s) and whether child/extended tables are in scope.
- Trigger conditions, audience (UI type / roles), and edge cases.
- Anything destructive (updates/deletes to existing records) and approval for it.
- **If any baseline / default record must change, the clone prefix** (Hard rule #6):
  identify which baseline records are involved and ask the user what prefix to use for
  the clones (e.g. `RMT`). Record it; you will clone-and-rename, never edit the original.

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

## Phase 5 — Update-set-first plan (the update set is step 1)

Draft the development plan. **Step 1 is always: create the update set, set it current,
and verify** — in this exact order, before any other record:

1. `create_update_set` with `application` = **Global** (default; only another scope if a
   record you must edit already lives there) and `name` = `<NUMBER> - <short description>`
   (Hard Rule #4), e.g. `STRY123 - Update client script`.
2. `set_current_update_set` with the new update set's sys_id (Hard Rule #3).
3. `get_current_update_set` to verify the current update set is your named set and is
   **not** a Default set. If it doesn't match, **STOP** (Hard Rule #5) and surface the
   problem to the user — do not build.

Only after this 3-step block passes do you create any other record.

The rest of the plan: ordered build steps (one per artifact), each naming the MCP tool,
target table, and key fields — sequenced to satisfy the acceptance criteria. Each step
must comply with `best-practices.md` (e.g. expose configurable values as widget options
/ system properties, clone instead of editing baseline). Call out in the plan where a
best practice shaped a decision.

## Phase 6 — Present the plan 🚦 GATE

Present to the user, then STOP and wait for approval:
- **Story & acceptance criteria** (from Phase 1)
- **Scope decisions** (recorded answers from Phase 3)
- **Plan**: Step 1 update set (name + Global scope, or the record's scope if forced) + ordered build steps with tools
- **Risks / destructive actions**, if any

Ask explicitly: "Posso prosseguir com este plano ou quer ajustar algo?" then **STOP and
end your turn** — do not call any tool until the user replies. Do not build until the
user approves. Apply any requested changes and re-present if needed.

## Phase 7 — Execute

Execute the approved plan in order: update set first (Phase 5 gate satisfied), then each
build step. After each create/update, capture the returned `sys_id`. If any step fails,
stop and report — don't continue blindly. Follow `best-practices.md` to the letter
(configurable values as widget options / system properties, clone instead of editing
baseline, no hardcoded sys_ids, scoped CSS, server data via `data`/Script Includes,
client scripts isolated to their table unless extension is explicitly requested).

## Phase 8 — Summarize with record URLs

Report everything created/changed. For **every** record include a clickable link
(per the ServiceNow links preference): `<instance>/<table>.do?sys_id=<sys_id>`, where
`<instance>` is the connected server's `SERVICENOW_INSTANCE_URL` (resolve it from the
Claude MCP config: `grep -A6 '"ServiceNow"' ~/.claude.json`). Include the update set
link too: `<instance>/sys_update_set.do?sys_id=<id>`. Use a table:
artifact → table → sys_id → link.

## Phase 9 — Manual QA guide

Provide a step-by-step manual test guide the user can follow in the instance, derived
from the acceptance criteria. For each acceptance criterion give: setup, the exact user
action (which form/record to open, what to do), and the expected result. Include negative
cases (where it should NOT fire) and, if relevant, how to verify the change is captured
in the update set (and how to roll back by backing out the update set).

---

## Notes

- Prefer read-only discovery before any write. Re-use instance conventions over inventing.
- Keep all conversation in PT-BR; record/script names and code in English.
- If the MCP server isn't connected, ask the user to connect it (`/mcp`) before Phase 2.
