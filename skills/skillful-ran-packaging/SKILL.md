---
name: skillful-ran-packaging
description: Review scratch OCUDU or srsRAN artifacts and scaffold compact tracked skills for Skillful RAN. Use when reusable scripts, notes, or examples should move out of `.local/ocudu/` and into `skills/`. Do not use it to build software, run runtime stages, or skip the skill QA gate.
---

# Skillful RAN Packaging

## Trigger

- Use when candidate files under `.local/ocudu/` look reusable and need a keep, rewrite, or drop decision.
- Use when a new skill scaffold or an existing skill update should be generated in a controlled way.
- Do not use this skill for build stages, runtime stages, or skill QA itself.

## Inputs

- `mode`: `review`, `promote`, or `update`
- `candidate_paths`: files or directories to inspect
- `target_skill_id`: tracked skill id; namespace is inferred from the prefix
- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `dry_run`: keep the result in the draft area only
- `qa_report_path`: required for non-dry-run `promote` and `update`
- `title`, `category`, `tags`: required when scaffolding a new skill

## Workflow

1. Read [`tool.json`](tool.json) for the contract.
2. Apply the keep, rewrite, and drop rules from [`references/promotion-rubric.md`](references/promotion-rubric.md).
3. Require a passing `skillful-ran-skill-test` report before non-dry-run promotion or update.
4. Run [`scripts/skillful_ran_packaging.py`](scripts/skillful_ran_packaging.py) so drafts always start in `.local/ocudu/promote/`.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- `decisions`: compact table with `path`, `decision`, `reason`, `target`, `rewrite_notes`
- `draft_path`: generated draft location under `.local/ocudu/promote/`
- `generated_files`: scaffolded tracked files and copied support assets
- `promoted_path`: tracked destination when promotion succeeds
- `backup_path`: pre-update snapshot for `mode=update`

## Failure / Escalation

- If the repo worktree is dirty, block promotion or update and keep the draft outside tracked paths.
- If the QA report is missing or failing, block non-dry-run promotion and report why.
- If a candidate contains secrets, binary clutter, or oversized notes, drop it and report why.
