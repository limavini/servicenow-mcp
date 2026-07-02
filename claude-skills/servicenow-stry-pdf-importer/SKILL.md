---
name: servicenow-stry-pdf-importer
description: "Reads a ServiceNow 'Story Details' PDF export (rm_story report) and creates a clean story Markdown file under instances/<inst>/tasks/STRY<number>.md. Use when the user gives only the path to a story PDF and wants it turned into a repo story file."
argument-hint: "<path to the story .pdf>"
---

# Story PDF Importer — PDF export → repo story Markdown

You take a **ServiceNow "Story Details" PDF** (the `rm_story` report export, e.g.
`~/Downloads/rm_story.pdf`) and produce a single clean Markdown story file under
`instances/<instance>/tasks/STRY<number>.md`, matching the exact format of the stories
already in that folder. The user gives you **only the PDF path** — derive everything else
from the PDF and the repo. Preserve 100% of the story's content; only change presentation.

The output is meant to be the source of truth for the `servicenow-story-builder` skill, so
it MUST contain exactly three top sections in this order: **Description**, **Acceptance
Criteria**, **Technical Solution**, under a `# [tag] Title` heading.

## Workflow

### 1. Read the PDF
Read the file with the `Read` tool using the `pages` parameter (PDFs are read by page
range, e.g. `pages: "1-5"`). Read every page. If the path doesn't exist or isn't a PDF,
ask the user for a valid path and stop.

### 2. Extract the fields
From the PDF's `Story` / `Notes` / `Technical solution` blocks, pull:
- **Number** — the `STRY…` value (used for the filename).
- **Short description** — becomes the `# ` title. Keep the `[VCNA]` / bracketed tag.
- **Description** — the narrative ("As a … I want … so that …") plus any context lines.
- **Acceptance criteria** — the `AC1 … AC6 …` block. In the PDF these are often run
  together on one line (`AC1 — title Given … When … Then …`); split them apart.
- **Technical solution** — the numbered items (`1. …`, `2. …`) with their field lists,
  tables, and rules. PDF text frequently concatenates list items with no separator
  (e.g. `Employee SAP#Employee First Name & Last NameEffective Date`) — split these back
  into individual entries using the field names known from the story family.

The PDF metadata (Epic, Release, Sprint, Points, Assignment group, Project, State) is
**not** written into the file — the existing story files omit it. Only the Number is used,
for the filename.

### 3. Resolve the target path
- **Filename:** `STRY<number>.md` from the extracted Number (e.g. `STRY0022590.md`).
- **Instance folder:** write to `instances/<instance>/tasks/`. Resolve `<instance>`:
  1. If only one directory exists under `instances/`, use it.
  2. Otherwise prefer the `default: true` instance from `instances.json`.
  3. If still ambiguous, ask the user which instance.
- If a file with that name already exists, show the user and confirm before overwriting.

### 4. Build the Markdown (reuse `stry-parser` formatting rules)
Format the extracted content following the same conventions the `stry-parser` skill uses,
so the result is indistinguishable from the hand-written stories in the folder:

- **Title:** `# <Short description>` (keep the bracketed tag, e.g. `# [VCNA] …`).
- **`## Description`** — the narrative prose, blank line between paragraphs. Keep any URLs
  or reference links verbatim.
- **`## Acceptance Criteria`** — each AC as a `### AC# — <title>` subheading with
  **Given / When / Then** bullets, keywords bolded:
  ```
  ### AC1 — Short title
  - **Given** <context>
  - **When** <action>
  - **Then** <expected outcome>
  ```
- **`## Technical Solution`** — each numbered item as a `### N. Title` heading. Turn field
  lists / matrices (label + type + mandatory + maps-to, condition→behavior, etc.) into
  real Markdown tables; single-column lists of fields/values become one-column tables or
  bullet lists, whichever reads more naturally — matching how the sibling stories present
  the same kind of block.

### 5. Content-preserving rules (do not invent)
- **Never** change, add, or drop story values: reasons, personas, field names, mandatory
  flags, mappings, limits, table/interface names (`x_visa_vcna_*`, `VCNA HR Workspace`).
- Only fix obvious PDF extraction garbling: split concatenated list items, repair split
  words (`Payout Am ount` → `Payout Amount`, `Desc ription` → `Description`), and add the
  table/heading structure. Keep real characters intact: em-dashes (`–`) in names like
  `Tuition Reimbursement – Pre Enrollment`, `&`, `#`, `?`, `/`.
- When the PDF's structure is ambiguous, mirror the format of the existing files in the
  same `tasks/` folder rather than guessing a new layout. Read a sibling `STRY*.md` first
  if unsure.

### 6. Write and report
Write the full file in a single `Write`. Then briefly report (PT-BR): the file path
created, the story number/title, how many ACs and Technical Solution sections it has, and
confirm the content was preserved (only presentation/structure changed). Mention that the
file is ready to feed into `servicenow-story-builder`.
