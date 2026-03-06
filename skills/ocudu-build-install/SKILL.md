---
name: ocudu-build-install
description: Plan or execute the baseline OCUDU and srsRAN clone and build flow inside the local lab workspace. Use when you need reproducible source, build, test, and install steps. Do not use it for host auditing, smoke validation, or promoting files into tracked skills.
---

# OCUDU Build Install

## Trigger

- Use when a user wants a repeatable clone, configure, build, test, or install flow under `.local/ocudu/`.
- Use when a user needs a dry-run plan before mutating the workstation.
- Do not use this skill to diagnose host readiness, validate post-build runtime, or curate tracked skill assets.

## Inputs

- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `source_ref`: branch, tag, or commit to build
- `build_type`: `Release` or `Debug`
- `bootstrap_deps`: install the documented Ubuntu dependency set
- `enable_zeromq`: include ZeroMQ-friendly configuration flags
- `install_prefix`: install destination, defaulting to `/usr/local`
- `dry_run`: print the plan before applying it

## Workflow

1. Read [`tool.json`](tool.json) for the exact contract.
2. Check [`references/build-baseline.md`](references/build-baseline.md) before changing the host.
3. Use [`scripts/plan_build.sh`](scripts/plan_build.sh) to keep the clone and build path deterministic inside `.local/ocudu/`.
4. Prefer dry-run first, then apply only after `ocudu-host-audit` reports an acceptable baseline.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- `commands`: ordered shell commands for the selected plan
- `source`: resolved repo and source reference
- `build_dir`: intended build directory

## Failure / Escalation

- If the host is missing dependencies, stop and route back to `ocudu-host-audit`.
- If the existing source tree is dirty, avoid destructive checkout behavior and require the operator to resolve it.
- If tests fail, hand off to `ocudu-smoke-test` only after the build tree itself is stable.
