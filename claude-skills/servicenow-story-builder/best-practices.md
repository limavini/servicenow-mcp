# ServiceNow best practices (read before building)

Authoritative guidance for any change built through the `servicenow-story-builder`
skill. Prefer **configuration over customization** and **never hardcode what should
be configurable**. When a story conflicts with these, surface the trade-off to the
user instead of silently violating them.

---

## Service Portal

### Configuration, not hardcoding
- **Use the widget Option Schema (Options) for any value an admin might change** —
  labels, table names, filters, limits, target pages, colors, feature flags. Read
  them in code via `options.<field>` (server) / `c.options.<field>` (client). Do
  **not** bake these into the HTML/Client/Server script.
- Rationale: options let the same widget be reconfigured per-instance and reused on
  multiple pages **without touching code** (no new update set / no regression risk).
- Global, cross-widget config → **System Properties** (`sys_properties`), read with
  `gs.getProperty('x.y', default)`. Per-instance config → widget options. Never a
  hardcoded literal in script for either.
- **No hardcoded sys_ids, URLs, or instance names.** Look records up by a unique
  field, a property, or an option.

### Don't edit baseline; clone instead
- **Never modify an out-of-box (baseline) widget in place.** Clone it ("Clone Widget")
  and edit the clone, or build a new widget. Editing baseline records gets reverted/
  skipped on upgrade and creates upgrade conflicts (skipped records).
- Same for baseline pages, themes, and OOB Angular providers — extend, don't overwrite.

### Widget structure & data flow
- Keep the **Server script** as the single source of server data: populate the `data`
  object for server→client, read `input` for client→server, and use
  `c.server.update()` / `c.server.get()` from the client controller. Avoid extra
  round-trips; batch what the widget needs into `data`.
- Put reusable server logic in **client-callable Script Includes**, not inline in the
  widget server script, so it can be tested and reused.
- **No DOM manipulation / jQuery.** Use AngularJS data binding and the widget
  controller. Manipulating the DOM directly breaks digest cycles and accessibility.
- Share logic across widgets via **Angular Providers** (services/directives) and the
  widget's Dependencies, not by copy-paste.

### Styling
- Put CSS in the **widget's CSS/SCSS field** and scope it to the widget's root class
  so styles don't leak to the rest of the portal.
- Use **theme CSS variables / SCSS variables** for colors and spacing — don't hardcode
  hex colors. This keeps the widget consistent with the portal theme and themeable.

### Security
- Server scripts run with the portal user's roles — **enforce ACLs**, never trust
  `input`. Validate/whitelist on the server. Use `GlideRecordSecure` when appropriate.
- Don't leak data into `data` that the user isn't allowed to see.

### i18n & accessibility
- Wrap user-facing strings for translation (`${...}` in HTML, `gs.getMessage()` in
  server script) instead of hardcoding text.
- Keep markup semantic and accessible (labels, ARIA, keyboard navigation).

### Performance
- Minimize GlideRecord queries; use `setLimit()`, `GlideAggregate` for counts, and
  query only the fields you need. Avoid queries inside loops.
- Compute on the server into `data`; don't make repeated server calls from the client
  for data you could send once.
- Use `spUtil` helpers (e.g. `spUtil.get`, record watch) rather than reinventing them.

---

## Platform-wide (applies to any change)

- **Scope & update set:** every change is captured in a dedicated, **named** update set
  — **Global by default** (one Global named set captures changes across scopes); never
  any application's **Default** update set. Only switch to another application scope for
  records that already live there (the skill enforces this in Phase 0/5).
- **Configuration over customization:** prefer no-code/low-code (UI Policies, Data
  Policies, Flow Designer) over scripts when they achieve the requirement.
- **Client scripts:** fetch server data via **GlideAjax + client-callable Script
  Includes**, never synchronous `g_form.getReference()` or server calls in a loop.
  Use `g_form` / `g_user` APIs; keep `onChange` scripts guarded against `isLoading`
  and empty `newValue`.
- **Business Rules:** keep them small and idempotent; pick the correct when/order;
  avoid `current.update()` inside a rule on the same record (recursion).
- **Flow Designer over legacy Workflow** for new automation.
- **Naming conventions:** clear, prefixed names tied to the scope/story; descriptions
  filled in; `active` managed intentionally.
- **No hardcoded sys_ids / instance URLs** anywhere; resolve dynamically.
- **Test & document:** provide a manual QA path (the skill's Phase 9) and note any
  rollback (back out the update set).

---

## Quick checklist before creating/updating a record

- [ ] Is any literal in this code something an admin might want to change? → make it a
      widget **option** or a **system property**.
- [ ] Am I editing a **baseline** record? → clone instead.
- [ ] Any hardcoded **sys_id / URL / instance**? → resolve dynamically.
- [ ] Is the change captured in a **named update set** (Global by default, never Default)?
- [ ] Server data via `data`/Script Include (not DOM, not sync client calls)?
- [ ] CSS scoped to the widget and using theme variables?
- [ ] ACLs respected and `input` validated server-side?
