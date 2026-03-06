---
name: ocudu-host-audit
description: Audit a Linux workstation for OCUDU and srsRAN build readiness. Use when you need a non-destructive baseline before cloning or building. Do not use it to build software, run smoke tests, or promote files into tracked skills.
---

# OCUDU Host Audit

## Trigger

- Use when a user wants a readiness check for an Ubuntu 24.04-class Linux host before OCUDU or srsRAN work.
- Use when you need a compact report covering OS, toolchain, packages, and basic network visibility.
- Do not use this skill to clone repos, build code, run binaries, or curate tracked skill assets.

## Inputs

- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `profile`: `ubuntu-24.04-gaming-pc` or `portable-linux`
- `check_network`: include interface visibility checks
- `check_packages`: include Ubuntu package checks
- `strict`: fail if any recommended prerequisite is missing

## Workflow

1. Read [`tool.json`](tool.json) for the authoritative input and output contract.
2. Run [`scripts/run_host_audit.py`](scripts/run_host_audit.py) to collect host facts without mutating the system.
3. Compare the report against [`references/official-baseline.md`](references/official-baseline.md) and the local profile notes.
4. Return a concise readiness summary with missing prerequisites and next steps.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- `hardware`: compact OS, CPU, NIC, and GPU profile
- `missing`: commands or packages blocking the baseline flow
- `checks`: per-check status records

## Failure / Escalation

- If hardware discovery tools such as `lspci` or `ip` are missing, return a partial report and say what could not be inspected.
- If package checks fail because `dpkg-query` is unavailable, fall back to command checks and note the gap.
- If the host looks incomplete, hand off to `ocudu-build-install` only after the missing prerequisites are addressed.
