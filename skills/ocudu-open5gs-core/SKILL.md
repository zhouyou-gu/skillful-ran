---
name: ocudu-open5gs-core
description: Control the vendored Open5GS compose stack used by the Skillful RAN proof-of-concept lane. Use when the user wants the core brought up, checked, or torn down through repo-owned assets. Do not use it for the local no-core lane, the srsUE build, or tracked skill QA.
---

# OCUDU Open5GS Core

## Trigger

- Use when the user wants the pinned Open5GS stack brought up, checked, or torn down.
- Use when the ZMQ proof-of-concept lane needs a concrete repo-owned core environment.
- Do not use this skill for the local no-core lane, source builds, or skill promotion.

## Inputs

- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `action`: `up`, `down`, or `status`
- `compose_file`: compose path relative to this skill, defaulting to the vendored core stack
- `dry_run`: emit commands and stage evidence without changing containers

## Workflow

1. Read [`tool.json`](tool.json) for the contract.
2. Keep the compose stack aligned with [`references/core-stack.md`](references/core-stack.md).
3. Run [`scripts/manage_open5gs_core.py`](scripts/manage_open5gs_core.py).
4. Hand off to `ocudu-zmq-open5gs-e2e` after the core is healthy.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- `stage_dir`: evidence path for this core stage
- `services`: core services targeted by the action
- `commands`: exact `docker compose` commands used

## Failure / Escalation

- If Docker or Compose is unavailable, stop and return to `ocudu-pc-readiness`.
- If the core health check fails, keep the compose logs and do not start the ZMQ lane.
- If the user asks for custom core editing, update the vendored assets here instead of scratch copies.
