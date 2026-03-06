---
name: ocudu-local-runtime-test
description: Run the software-only local OCUDU lane on one host using split CU DU binaries, no-core, and test-mode overlays. Use when the user wants a 60 second local runtime checkpoint after the RAN build is complete. Do not use it for Open5GS, srsUE, or skill promotion work.
---

# OCUDU Local Runtime Test

## Trigger

- Use when the built `srsRAN_Project` install tree is ready and the next step is the local split-lane runtime check.
- Use when the user wants the one-host CU/DU startup plus `test_mode` checkpoint, not the full E2E path.
- Do not use this skill for the Open5GS core, `srsUE`, or tracked skill QA.

## Inputs

- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `install_dir`: installed `srsRAN_Project` tree
- `image`: repo-owned Docker runtime image
- `duration_seconds`: target stable runtime window
- `dry_run`: emit the runtime command and evidence path without executing it

## Workflow

1. Read [`tool.json`](tool.json) for the contract.
2. Use the pinned overlay configs under [`assets/config`](assets/config).
3. Check [`references/validated-run.md`](references/validated-run.md) before changing the stable 60 second checkpoint.
4. Run [`scripts/run_local_runtime_test.py`](scripts/run_local_runtime_test.py) to start `srscucp`, `srscuup`, and `srsdu` inside one container.
5. Hand off to `ocudu-open5gs-core` or `ocudu-zmq-open5gs-e2e` only after this stage is stable.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- `stage_dir`: evidence path for this runtime stage
- `config_paths`: config overlays used by the stage
- `commands`: exact container command used to run the local lane

## Failure / Escalation

- If the install tree is missing the split binaries, go back to `ocudu-project-build`.
- If the processes exit early, keep the logs and stop instead of forcing the E2E lane.
- If config drift is required, update the overlays in this skill rather than editing scratch copies.
