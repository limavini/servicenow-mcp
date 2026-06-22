# Flow Designer — data model & how flows are stored

This document explains how a **Flow Designer** flow is stored across the
`sys_hub_*` tables, how those records relate, the role of the compiled
**snapshot**, and a clear verdict on building flows through the Table API.

> **TL;DR** — A Flow Designer flow is **not** a self-contained set of editable
> rows. The engine runs a **compiled snapshot**; the `sys_hub_*` rows are the
> *design-time* representation. Inserting those rows via `/api/now/table/...`
> does **not** by itself produce a runnable flow — you must publish/compile so a
> snapshot exists. Building a working flow purely via the Table API is
> **technically possible but impractical and unsupported**. Read and audit flows
> via the Table API; **author** them in Flow Designer and move them via Update
> Sets / scoped apps.

Most table/column facts below were verified by live introspection of
`sys_dictionary` / `sys_db_object` on a current (Flow Engine V2) instance.
Behavioral claims about snapshots/compilation are documented + community-sourced
and flagged **[community]** where they are not a dictionary quote.

> Flow Designer (`sys_hub_*`) is **not** the legacy Workflow engine
> (`wf_workflow`, the Workflow Editor). The MCP's `*_workflow*` tools cover the
> legacy engine; the flow tools below cover Flow Designer.

---

## 0. The one fact that governs everything: Engine V1 vs V2

There are **two parallel storage models**, and which one an instance uses changes
which tables you read/write:

| | Flow Engine V1 (pre‑Washington DC) | Flow Engine V2 (Washington DC+) |
|---|---|---|
| Trigger | `sys_hub_trigger_instance` | `sys_hub_trigger_instance_v2` |
| Action | `sys_hub_action_instance` | `sys_hub_action_instance_v2` |
| Flow logic | `sys_hub_flow_logic` | `sys_hub_flow_logic_instance_v2` |
| Input/output **values** | EAV rows in `sys_variable_value` | inline **compressed** `values` blob on each row |

Importing a V2 flow into a pre‑Washington instance fails with
`Table 'sys_hub_trigger_instance_v2' does not exist`. Any tooling must branch on
engine version. The MCP `get_flow` tool queries the V2 table first and falls back
to V1, and reports the detected `engine_version`.

---

## 1. Table inheritance (verified via `sys_db_object.super_class`)

```
sys_metadata
└── sys_hub_action_type_base            (Action Type Base)
    └── sys_hub_action_type_definition  (Action Type — the reusable action catalog)

sys_hub_flow_block                       (name, label_cache, sys_overrides, sys_domain)
└── sys_hub_flow_base                    (Flow Base — shared flow/subflow/snapshot columns)
    ├── sys_hub_flow                     (Flow — adds snapshot pointers + compiler fields)
    └── sys_hub_flow_snapshot            (Flow Snapshot — adds parent_flow, master)

sys_hub_flow_component                   (flow, order, ui_id, parent_ui_id, display_text, comment)
├── sys_hub_action_instance             (Action Instance — V1)
├── sys_hub_action_instance_v2          (Action Instance — V2)
├── sys_hub_flow_logic                  (Flow Logic Instance — V1)
└── sys_hub_flow_logic_instance_v2      (Flow Logic Instance — V2)

sys_hub_trigger_instance                 (Trigger Instance — V1, no super_class)
sys_hub_trigger_instance_v2              (Trigger Instance — V2, no super_class)

var_dictionary
├── sys_hub_flow_input                  (Flow Inputs — variable definitions)
└── sys_hub_flow_output                 (Flow Outputs — variable definitions)
```

**Key structural insight:** the V1/V2 action & logic tables are **siblings
extending `sys_hub_flow_component`**. The columns you'd expect on every
action/logic row — `flow`, `order`, `ui_id`, `parent_ui_id`, `display_text`,
`comment` — live on the **`sys_hub_flow_component` parent**, not on the leaf
table. You query the leaf table; the inherited columns come through.

---

## 2. Table-by-table

| Table | Purpose | Key columns |
|---|---|---|
| `sys_hub_flow_block` | Topmost shared base for flow records. | `name`, `label_cache`, `sys_overrides`→`sys_hub_flow_block`, `sys_domain` |
| `sys_hub_flow_base` | Shared columns for flows, subflows **and** snapshots. The **Flow Type** (`type`) lives here. | `type` (default `flow`), `status` (default `draft`), `active`, `internal_name`, `description`, `annotation`, `natlang` (Natural Language Title), `category`→`sys_hub_category`, `run_as` (default `user`), `run_with_roles`, `access`, `version`, `outputs`, `attributes`, `copied_from` |
| `sys_hub_flow` | The concrete flow record. Captured by Update Sets. Holds the **snapshot pointers**. | `master_snapshot` ("Main snapshot" — sys_id of the **published** snapshot the engine runs), `latest_snapshot` (most recently compiled), `master_snapshot_digest` (staleness hash), `pre_compiled`, `compiler_build`, `version_record`→`sys_hub_flow_version`, `substatus` |
| `sys_hub_flow_snapshot` | **The compiled snapshot.** One per compile; `master=true` is the published one. **Excluded from Update Sets** (`updateSync=false`) — regenerated on the target. | `parent_flow`→`sys_hub_flow`, `master` (bool). Inherits all of `sys_hub_flow_base`. |
| `sys_hub_flow_component` | Shared base for every component placed in a flow. **Holds the parent-flow link and ordering.** | `flow`→`sys_hub_flow_base` (mandatory), `order` (mandatory), `ui_id`, `parent_ui_id` (nesting/branch membership), `display_text`, `comment`, `sys_class_name` |
| `sys_hub_action_instance` (V1) | An action placed in a flow. | `action_type`→`sys_hub_action_type_base` (mandatory), `action_type_parent`→`sys_hub_action_type_definition`, `action_inputs`, `compiled_snapshot` |
| `sys_hub_action_instance_v2` (V2) | An action placed in a flow; input/output values inline. | `action_type`, `action_type_parent`, **`values`** (compressed JSON of all inputs/outputs, up to 16 MB), `compiled_snapshot` |
| `sys_hub_flow_logic` (V1) | A flow-logic element (If/Else, For Each, Do Until, Try, Parallel…). | inherits `sys_hub_flow_component` |
| `sys_hub_flow_logic_instance_v2` (V2) | Flow-logic element. | `logic_definition`→`sys_hub_flow_logic_definition`, **`values`** (compressed JSON), `connected_to` (branch/edge linkage), `block`→`sys_hub_flow_block`, `decision_table`→`sys_decision` |
| `sys_hub_trigger_instance` (V1) | The flow's trigger. | (no super_class) |
| `sys_hub_trigger_instance_v2` (V2) | The flow's trigger. | `flow`→`sys_hub_flow_base` (mandatory), `trigger_type` (mandatory), `trigger_definition`→`sys_hub_trigger_type_definition`, **`trigger_inputs`** / **`trigger_outputs`** (compressed JSON), `name`, `display_text` |
| `sys_hub_action_type_base` | Base of the **reusable action-type catalog** (not per-flow). Extends `sys_metadata`. | `name`, `internal_name`, `type`, `category`, `outputs`, `action_template`, `action_status` |
| `sys_hub_action_type_definition` | Concrete action type the action instance points at. Extends the base. | (inherits base) |
| `sys_hub_flow_input` / `sys_hub_flow_output` | Flow input/output variable **definitions**. Extend `var_dictionary`. | inherit `var_dictionary` |
| `sys_hub_flow_variable` / `sys_hub_flow_stage` | Flow-scoped variables / stages. [community] | — |
| `sys_hub_flow_logic_definition` | Catalog of logic types (If/For Each/…). Pointed to by logic instances. | — |
| `sys_hub_step_instance` | V1 input/output **configuration** for a step (the *values* went to `sys_variable_value`). [community] | — |
| `sys_hub_flow_version` | Flow Designer versioning (Zurich). Referenced by `sys_hub_flow.version_record`. Known update-set/deploy pain point. | — |
| `sys_variable_value` | **V1 EAV value store.** Holds the actual input/output/trigger values for V1 rows. | `document` (owning table name), `document_key` (owning row sys_id), `variable`→`var_dictionary`, `value`, `order` |

**Subflows** are **not** a separate table — they live in `sys_hub_flow`,
distinguished by the `type` (Flow Type) column. **Actions** (reusable
definitions) live in `sys_hub_action_type_definition`, not in `sys_hub_flow`.

**Runtime tables (outputs of running a flow — never inserted to build one):**
`sys_flow_context` (flow executions, with `source_table`/`source_record`) and
`sys_flow_log` (per-step log).

---

## 3. How the records reference each other

- **Parent flow:** every action/logic row carries `flow` (on
  `sys_hub_flow_component`) → the `sys_hub_flow` sys_id. The trigger carries its
  own `flow` on `sys_hub_trigger_instance_v2`.
- **Ordering / nesting:** `sys_hub_flow_component.order` (mandatory). Nesting
  (steps inside an If / For-Each block) uses `ui_id` / `parent_ui_id`; logic
  edges use `sys_hub_flow_logic_instance_v2.connected_to`.
- **Action → action type:** `action_type` → `sys_hub_action_type_base`, with
  `action_type_parent` → `sys_hub_action_type_definition`.
- **Trigger → trigger type:** `trigger_type` (string code) + `trigger_definition`
  → the trigger-type-definition table.
- **Snapshot ↔ flow:** `sys_hub_flow_snapshot.parent_flow` → `sys_hub_flow`;
  `master=true` marks the published snapshot; `sys_hub_flow.master_snapshot` /
  `latest_snapshot` point back to a snapshot sys_id.
- **Values (V1):** `sys_variable_value` rows where `document` = the component
  table name and `document_key` = the component row sys_id, joined to a
  `var_dictionary` variable. There is **no direct reference** — you join on the
  `document` / `document_key` pair:

  ```javascript
  var actions = new GlideRecord('sys_hub_action_instance');
  actions.addJoinQuery('sys_variable_value', 'sys_id', 'document_key');
  // + filter document='sys_hub_action_instance', value='incident', etc.
  ```

- **Values (V2):** inline in the leaf row's `values` (action / logic) or
  `trigger_inputs` / `trigger_outputs` (trigger) — a **gzip-compressed,
  base64-encoded JSON** blob with a compression header (not encrypted). Community
  decode:

  ```javascript
  var bytes = GlideStringUtil.base64DecodeAsBytes(encoded); // after stripping the header
  var json  = String(GlideCompressionUtil.expandToString(bytes));
  JSON.parse(json); // array of {actionInstanceSysId, id, name, value, displayValue, parameter}
  ```

---

## 4. The snapshot / compiled-plan model [documented + community]

- A **snapshot is a compiled, point-in-time copy of the whole flow** (trigger +
  actions + logic + values). The runtime executes the snapshot, not the raw
  component rows — which is why flows run fast ("precompiled" programs).
- **Publish/activate** compiles the design-time rows into a
  `sys_hub_flow_snapshot` row and sets `master_snapshot` (active) /
  `latest_snapshot` (newest). Editing or clearing `master_snapshot` /
  `latest_snapshot` directly causes "your flow cannot be found" / "could not
  retrieve snapshot" errors. [community]
- Snapshots are **update-set-excluded** (`updateSync=false`) and **recompiled on
  demand**: if a flow is deployed without its snapshot, ServiceNow compiles it
  instantly on first use — provided the design-time rows are internally
  consistent. So the snapshot is a cache, but a valid compiled plan must exist or
  be derivable.
- **Programmatic recompile** (the closest thing to a "make it runnable" API):

  ```javascript
  sn_fd.FlowAPI.getRunner().flow('<scope>.<internal_name>').compile(true);
  ```

---

## 5. Can you build a flow via the Table API? Verdict

**Technically possible, but impractical and unsupported.** Do not build flow
*authoring* on raw Table API inserts. Reasons:

1. **Snapshot requirement.** Component rows are not runnable without a
   publish/compile; there is no Table-API field to set "the compiled plan."
2. **Opaque V2 payloads.** On Washington DC+ the action/trigger/logic values are
   gzip+base64 JSON with an exact internal header — there is no documented spec;
   it is reverse-engineered.
3. **EAV indirection (V1).** Inputs/conditions/the trigger table live in
   `sys_variable_value` joined by `document`/`document_key`, each tied to a
   `variable` definition that must exist and match `element` names.
4. **Graph bookkeeping.** `order`, `ui_id`/`parent_ui_id`, and `connected_to`
   must be internally consistent for blocks/branches; the Designer maintains
   these invariants for you.
5. **Reference integrity.** `action_type` / `action_type_parent` /
   `trigger_definition` must point at real catalog rows with matching I/O
   contracts; `version_record`/scope add capture requirements.
6. **V1 vs V2 divergence.** Writing the wrong table set yields an uncompilable
   flow.

### Supported / realistic alternatives

- **Author in Flow Designer (UI)**, then **transport via Update Set / scoped app**
  — `sys_hub_flow` + component rows are captured; snapshots regenerate on
  install. This is the intended path.
- **Clone-and-recompile** for automation: copy an existing flow's rows, adjust,
  then `sn_fd.FlowAPI.getRunner().flow(name).compile(true)`.
- **`sn_fd.FlowAPI` is runtime-only** — it *executes/compiles* flows
  (`startFlow`, `startSubflow`, `startActionQuick`,
  `getRunner().flow(...).run()`), it does **not** author flow structure. There is
  **no official "create a flow" REST/programmatic API.**

---

## 6. What the MCP provides

- **`list_flows`** — list flows/subflows (`sys_hub_flow`); filter by name,
  `active`, and `flow_type` (`flow`/`subflow`).
- **`get_flow`** — resolve a flow by sys_id or name and assemble its design-time
  structure: trigger + action instances + flow-logic instances **in order**,
  with V2→V1 fallback and the detected `engine_version`. The large compressed
  `values` blobs are omitted; use `query_table` to fetch a raw row if needed.
- **`query_table`** — generic read-only escape hatch for any `sys_hub_*` table
  (e.g. the raw `values` blob, `sys_variable_value` for V1, snapshots).

For end-to-end flow work see the **`servicenow-flow-builder`** Claude skill. It
always uses the **UI + Update Set** method: the user authors in the Flow Designer
UI with detailed, field-by-field coaching, while the MCP handles discovery, the
Update Set, and verification — the most reliable, lowest-rework path.

---

## Sources

- [Community — Flows/Subflows/Actions storage table](https://www.servicenow.com/community/developer-forum/flow-designer-flows-subflows-actions-storage-table/m-p/1454741)
- [Community — Flow Designer related tables](https://www.servicenow.com/community/developer-forum/flow-designer-related-table/m-p/3023189)
- [Community — sys_hub_action_instance vs _v2](https://www.servicenow.com/community/sysadmin-forum/what-is-the-difference-between-quot-sys-hub-action-instance-quot/td-p/3429097)
- [Community — Where are Flow action inputs stored (V1 EAV vs V2 values, decode)](https://www.servicenow.com/community/developer-forum/where-are-flow-action-inputs-stored/m-p/3217296)
- [Community — Viewing the "Values" field of sys_hub_action_instance_v2](https://www.servicenow.com/community/workflow-automation-forum/viewing-the-quot-values-quot-field-of-sys-hub-action-instance-v2/m-p/3149163)
- [Community — sys_hub_trigger_instance_v2 does not exist (engine V2)](https://www.servicenow.com/community/upgrades-and-patching-forum/table-sys-hub-trigger-instance-v2-does-not-exist/m-p/3055641)
- [Community — How useless Flow artifacts bloat your applications (snapshots, updateSync=false)](https://www.servicenow.com/community/now-platform-articles/how-useless-flow-artifacts-bloat-your-applications-amp-how-to/ta-p/2610469)
- [Community — version_record → sys_hub_flow_version (Zurich)](https://www.servicenow.com/community/servicenow-ai-platform-blog/could-not-find-a-record-in-sys-hub-flow-version-for-column/ba-p/3032905)
- [Community — Recompile a flow programmatically (compile(true))](https://www.servicenow.com/community/developer-forum/recompile-a-workflow-from-within-a-fix-script/td-p/3393476)
- [ServiceNow Docs — API access to Flow Designer (client-callable flows)](https://www.servicenow.com/docs/bundle/zurich-build-workflows/page/administer/flow-designer/concept/api-access-flow-designer.html)
- [aaron-costello/ServiceNow-Schema — common tables](https://github.com/aaron-costello/ServiceNow-Schema/blob/main/Filtered_Common_Tables.txt)
- Live instance introspection of `sys_dictionary` / `sys_db_object` — source of the verified column names, types, reference targets and the `super_class` chain.
