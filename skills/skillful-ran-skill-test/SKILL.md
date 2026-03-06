---
name: skillful-ran-skill-test
description: Run the compact QA gate for a new or updated Skillful RAN skill. Use when a skill draft should be checked for schema health, eval coverage, and safe helper hooks before packaging promotion. Do not use it to build OCUDU software, start the core, or review scratch lab artifacts for reuse.
---

# Skillful RAN Skill Test

## Trigger

- Use when a tracked skill is new or updated and should pass QA before promotion.
- Use when the user wants a structured report covering validator status, eval shape, and safe helper hooks.
- Do not use this skill to build OCUDU software, start runtime lanes, or classify scratch files.

## Inputs

- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `target_skill_id`: tracked skill to validate
- `dry_run`: still writes the QA report but only runs safe checks

## Workflow

1. Read [`tool.json`](tool.json) for the contract.
2. Run [`scripts/skillful_ran_skill_test.py`](scripts/skillful_ran_skill_test.py).
3. Review the generated QA report before calling `skillful-ran-packaging`.
4. Treat the QA report as a hard gate for promote or update work.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- `qa_report_path`: structured JSON report for packaging to consume
- `checks`: compact check records for validator, evals, and safe helper hooks

## Failure / Escalation

- If repo validation fails, stop and fix that before packaging.
- If helper hooks fail, fix the skill scripts instead of bypassing the check.
- If the skill is too broad, split it before promotion.
