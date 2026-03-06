---
name: ocudu-smoke-test
description: Run local post-build sanity checks for OCUDU and srsRAN artifacts on a Linux workstation. Use when you want a compact smoke result after a build or install step. Do not use it to prove RF interoperability, build software from scratch, or promote files into tracked skills.
---

# OCUDU Smoke Test

## Trigger

- Use when a user needs a local post-build sanity check for a build directory or install prefix.
- Use when you want to confirm that binaries, help output, and optional `ctest` execution behave as expected.
- Do not use this skill to claim RU interoperability, deep performance coverage, or production readiness.

## Inputs

- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `build_dir`: explicit build directory, defaulting to `.local/ocudu/build/srsran-project`
- `mode`: `local-build`, `install-check`, or `zeromq-readiness`
- `install_prefix`: install destination for `install-check`
- `run_ctest`: execute `ctest` when practical
- `dry_run`: print the checks without executing them

## Workflow

1. Read [`tool.json`](tool.json) for the exact contract.
2. Match the requested mode against [`references/smoke-modes.md`](references/smoke-modes.md).
3. Run [`scripts/run_smoke_test.sh`](scripts/run_smoke_test.sh) to keep the local checks consistent.
4. Keep the result narrow: build sanity only, with explicit limits called out in the output.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- `checks`: ordered smoke checks and statuses
- `metrics`: compact counts such as detected binaries or executed test commands
- `logs`: paths or commands worth following up

## Failure / Escalation

- If the build tree is missing, stop and route back to `ocudu-build-install`.
- If `ctest` fails, keep the failure local and avoid overstating what was validated.
- If the request expects RF, RU, or carrier-grade proof, say that this skill does not provide it.
