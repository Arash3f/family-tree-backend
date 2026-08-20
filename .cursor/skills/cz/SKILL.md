---
name: cz
description: >-
  Draft a Commitizen (cz) commit message from staged git changes using this
  repo's .cz.toml. Use when the user says cz, asks for a commit message,
  commitizen, or conventional commit text for the backend.
---

# cz — Commit message from staged changes

## Hard rules

- **Output a commit message only.** Do **not** run `git commit` unless the user explicitly asked to commit in this turn.
- Work only inside **this** git repo (backend). Do not mix frontend changes.
- Follow **this repo's** `.cz.toml` exactly (prefixes, scopes, template). Do not invent types/scopes that are not in that file.

## Workflow

1. Confirm repo root is this backend project (directory that contains `.cz.toml` and `.git`).
2. Read `.cz.toml` and load:
   - allowed `prefix` values (use the `value` field, e.g. `:sparkles: feat`)
   - allowed `scope` values (or empty for no scope)
   - `message_template`
3. Inspect **staged** changes only:

```powershell
git status
git diff --cached --stat
git diff --cached
```

4. If nothing is staged, say so and stop. Do not invent a message from unstaged files unless the user asks to include them.
5. Pick the best matching `prefix` and optional `scope` from `.cz.toml` based on the staged diff.
6. Write a short imperative `message` (what/why in one line). Add `description` / `issue_number` only when useful or requested.
7. Render the final text with the template from `.cz.toml`:

```text
{{prefix}}{% if scope %}({{scope}}){% endif %}: {{message}}
{% if description %}{{description}}{% endif %}
{% if issue_number %}Closes #{{issue_number}}{% endif %}
```

## Output format

Reply with:

1. One-line summary of what the staged change does
2. The final commit message in a fenced code block (ready to paste)
3. Brief rationale: why that prefix/scope

## Examples (shape only)

```text
:sparkles: feat(domain): add kinship degree calculator
```

```text
:wrench: fix(neo4j): prevent duplicate parent edges on import

Guard against re-linking when the same relationship already exists.
```

```text
:hammer: ref(tests): exclude generated client from mypy
```
