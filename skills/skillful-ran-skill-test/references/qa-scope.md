# QA Scope

This skill is intentionally conservative.

It validates:

- repo schema health via `scripts/validate_skills.py`
- eval pack shape for the target skill
- safe helper hooks only:
  - `python3 -m py_compile`
  - `python3 script.py --help`
  - `bash -n`

It does not run full OCUDU mutation workflows by default.
