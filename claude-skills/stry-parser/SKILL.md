---
name: stry-parser
description: "Reformats a raw ServiceNow story/task markdown file (typically pasted from a Google Doc / Jira export, with tables flattened to tab- or space-separated text and inconsistent `|` usage) into clean, AI-friendly Markdown: real Markdown tables, Gherkin-formatted Acceptance Criteria, and bullet lists for rule sets. Use when the user wants to tidy up / standardize / make readable a story file under instances/<inst>/tasks/."
argument-hint: "<path to the story .md file, or the STRY number>"
---

# Story Parser — Clean up a pasted ServiceNow story

You take a raw story/task markdown file — usually pasted from a Google Doc, Jira, or an
OCR/export where tables collapsed into tab- or space-separated lines with inconsistent
`|` characters — and reformat it into clean Markdown that is easy for both humans and AI
agents to read. **Preserve 100% of the content**; only change presentation and fix
obvious paste/OCR garbling.

## Goal

The structure of these stories is ambiguous after pasting: column separators may be tabs,
runs of spaces, or stray `|`. Standardize everything so separation is explicit and
unambiguous.

## Rules

### 1. Tables → real Markdown tables
Any 2+ column tabular block (key/value pairs, matrices like "Reason / Personas",
"Variable / Type / Mandatory / Maps to", "Condition / Behavior") becomes a Markdown table:

```
| Header A | Header B |
| --- | --- |
| value | value |
```

- A header line followed by single-value rows (e.g. a bare list of "Reason" options) →
  one-column table, or a bullet list if it reads more naturally as a plain list.
- Watch for rows where a single logical entry spans two table lines (e.g. one Reason with
  two required attachments → two table rows with the same key).

### 2. Acceptance Criteria → Gherkin blocks
Each AC becomes a `### AC# — title` subheading (navigable anchor) with **Given / When /
Then** as bullets, keywords bolded:

```
### AC1 — Short title
- **Given** <context>
- **When** <action>
- **Then** <expected outcome>
```

### 3. Rule lists → bullet lists
A run of imperative rules ("X must be mandatory.", "block the submission;", numbered
behavior steps) that is NOT a 2-column table becomes a `-` bullet list. Don't force prose
rules into a table.

### 4. Numbered sections → `### N. Title`
Top-level numbered Technical Solution items (`1. ...`, `2. ...`) become `### N. Title`
headings for navigation.

### 5. Fix paste/OCR garbling (content-preserving only)
- Repair split words in headers/cells, e.g. `Payout Am ount` → `Payout Amount`.
- Normalize the inconsistent/stray `|` the user added by hand to the same table format
  as the rest.
- Keep real characters intact: em-dashes (`–`) in names like
  `Tuition Reimbursement – Pre Enrollment`, `&`, `#`, `?`, `/`.
- **Never** change values, reasons, personas, mandatory flags, mappings, or limits — only
  layout and obvious typos.

## Workflow

1. Resolve the file path. If given a STRY number, it lives at
   `instances/<instance>/tasks/STRY<number>.md`.
2. Read the whole file.
3. Rewrite it applying the rules above. Prefer a single `Write` of the full reformatted
   file over many small edits.
4. Briefly report what changed: which blocks became tables, AC formatting, and any
   typos/`|` you normalized — and confirm content was preserved.
