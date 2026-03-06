---
name: ocudu-zmq-open5gs-e2e
description: Run the proof-of-concept OCUDU lane with `srsRAN_Project` gNB, vendored Open5GS, `srsUE`, and ZeroMQ. Use when the user wants the software-only attach plus ping path on this PC. Do not use it for the local no-core lane, source builds, or skill promotion.
---

# OCUDU ZMQ Open5GS E2E

## Trigger

- Use when the RAN build, UE build, and vendored Open5GS core are ready.
- Use when the user wants the software-only attach plus ping proof-of-concept lane.
- Do not use this skill for the local no-core lane, source builds, or tracked skill QA.

## Inputs

- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `project_install_dir`: installed `srsRAN_Project` tree
- `ue_install_dir`: installed `srsUE` tree
- `project_image`, `ue_image`: repo-owned container images
- `duration_seconds`: target runtime window
- `dry_run`: emit commands and stage evidence without executing them

## Workflow

1. Read [`tool.json`](tool.json) for the contract.
2. Use the pinned tutorial configs under [`assets/config`](assets/config).
3. Read [`references/validated-run.md`](references/validated-run.md) before changing container privileges or the ZMQ config pair.
4. Run [`scripts/run_zmq_e2e.py`](scripts/run_zmq_e2e.py) only after `ocudu-open5gs-core` reports healthy status.
5. Keep the result scoped to PoC attach plus ping, not production claims.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- `stage_dir`: evidence path for this E2E stage
- `config_paths`: gNB and UE configs used for the lane
- `commands`: exact container and ping commands used

## Failure / Escalation

- If the core is not healthy, stop and fix that before starting the gNB and UE containers.
- If attach or ping fails, keep the logs and do not present the lane as passed.
- If the user wants real RF or RU claims, route away from this skill.
