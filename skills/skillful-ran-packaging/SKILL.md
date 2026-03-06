---
name: skillful-ran-packaging
description: Review scratch OCUDU or srsRAN artifacts and scaffold compact tracked skills for Skillful RAN. Use when reusable scripts, notes, or examples should move out of `.local/ocudu/` and into `skills/`. Do not use it to build software, audit hosts, or run smoke validation.
---

# Skillful RAN Packaging

## Trigger

- Use when candidate files under `.local/ocudu/` look reusable and need a keep, rewrite, or drop decision.
- Use when a new skill scaffold or an existing skill update should be generated in a controlled way.
- Do not use this skill for host readiness checks, source builds, or runtime smoke tests.

## Inputs

- `mode`: `review`, `promote`, or `update`
- `candidate_paths`: files or directories to inspect
- `target_skill_id`: tracked skill id; namespace is inferred from the prefix
- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `dry_run`: keep the result in the draft area only
- `title`, `category`, `tags`: required when scaffolding a new skill

## Workflow

1. Read [`tool.json`](tool.json) for the contract.
2. Apply the keep, rewrite, and drop rules from [`references/promotion-rubric.md`](references/promotion-rubric.md).
3. Run [`scripts/skillful_ran_packaging.py`](scripts/skillful_ran_packaging.py) so drafts always start in `.local/ocudu/promote/`.
4. Promote only when the repo is clean, the draft is compact, and the required tracked files are present.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- `decisions`: compact table with `path`, `decision`, `reason`, `target`, `rewrite_notes`
- `draft_path`: generated draft location under `.local/ocudu/promote/`
- `generated_files`: scaffolded tracked files and copied support assets
- `promoted_path`: tracked destination when promotion succeeds
- `backup_path`: pre-update snapshot for `mode=update`

## Failure / Escalation

- If the repo worktree is dirty, block promotion or update and keep the draft outside tracked paths.
- If a candidate contains secrets, binary clutter, or oversized notes, drop it and report why.
- If the target skill already exists, require `mode=update`; do not treat that as a new-skill promotion.
