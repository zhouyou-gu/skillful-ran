# Skillful RAN Skill Guide

`skills/` is the tracked source of truth. Everything noisy or experimental belongs under `.local/ocudu/` until it has been reviewed and distilled.

## Required Shape

Create skills as `skills/<skill-id>/` with:

```text
skills/my-skill/
├─ SKILL.md
├─ skill.yaml
├─ tool.json
├─ README.md
└─ evals/
   └─ cases.jsonl
```

Optional when useful:

- `scripts/`
- `references/`
- `examples/`

## Naming and Categories

Use these prefixes consistently:

1. `ocudu-*` for OCUDU workflow skills
2. `srsran-*` for upstream-generic srsRAN skills
3. `skillful-ran-*` for packaging, policy, and meta skills

Allowed categories live in [`config/marketplace.json`](../config/marketplace.json):

- `telco`
- `testing`
- `devtools`
- `automation`

## `SKILL.md` Rules

Every Skillful RAN skill uses:

- YAML frontmatter with `name` and `description` only
- explicit negative routing in the description and Trigger section
- the same five sections:
  - `## Trigger`
  - `## Inputs`
  - `## Workflow`
  - `## Outputs`
  - `## Failure / Escalation`

Keep `SKILL.md` compact. Split detailed material into `references/` instead of turning the skill body into a manual.

## Tool Contract Rules

`tool.json` must include:

- `name`
- `title`
- `description`
- `inputSchema`
- `outputSchema`

Use the shared top-level output envelope:

- `passed`
- `summary`
- `warnings`
- `artifacts`
- `next_steps`

Mutating skills should accept:

- `workspace`
- `dry_run`

Default workspace convention: `.local/ocudu/`.

## Eval Pack Rules

Each skill carries `evals/cases.jsonl` with 8 to 12 compact cases.

Each line should be a JSON object with:

- `name`
- `prompt`
- `should_trigger`

Optional fields:

- `must_include`
- `notes`

Include both positive and negative routing cases.

## Promotion Rule

Do not copy raw logs, captures, or host transcripts into `skills/`.

Promote only:

- stable helper scripts
- concise references
- tiny sanitized examples
- compact skill drafts

Use `skillful-ran-packaging` to review and promote material from `.local/ocudu/`.

## Validation

Run from the repo root:

```bash
python3 scripts/validate_skills.py
python3 scripts/verify_install_targets.py
python3 scripts/build_registry.py
python3 scripts/build_search_index.py
```
