---
name: srsran-4g-ue-build
description: Build the prototype 5G UE path from srsRAN 4G release_23_11. Use when the user wants the `srsUE` side prepared for the ZMQ plus Open5GS proof-of-concept lane. Do not use it for the RAN-side build, the core stack, or tracked skill QA.
---

# srsRAN 4G UE Build

## Trigger

- Use when the user wants `srsUE` built for the PoC E2E lane.
- Use when the next step after the RAN-side local lane is the ZMQ UE preparation stage.
- Do not use this skill for the `srsRAN_Project` build, Open5GS lifecycle control, or packaging.

## Inputs

- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `repo_url`: official srsRAN 4G repository
- `source_ref`: pinned release, default `release_23_11`
- `image`: repo-owned Docker build image for the UE lane
- `clean_build`: remove existing build and install trees first
- `dry_run`: emit commands and stage evidence without executing them

## Workflow

1. Read [`tool.json`](tool.json) for the contract.
2. Keep the prototype UE scope aligned with [`references/release-23-11.md`](references/release-23-11.md).
3. Run [`scripts/run_ue_build.py`](scripts/run_ue_build.py) to clone, apply the workspace-only no-tests patch, build, and install `srsUE`.
4. Keep the validation container-side and export `LD_LIBRARY_PATH=/install/lib:$LD_LIBRARY_PATH` for the post-install checks.
5. Verify the installed `srsUE` binary with `--help` and `--version`, then hand off to `ocudu-zmq-open5gs-e2e`.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- `stage_dir`: evidence path for this build stage
- `source_dir`, `build_dir`, `install_dir`: concrete workspace paths
- `commands`: the exact git, docker, cmake, and test commands used

## Failure / Escalation

- If the Docker image is missing, build it with `ocudu-docker-build-env` first.
- If the UE build or tests fail, keep the logs and stop instead of forcing the E2E lane.
- If the user asks for a production-grade UE claim, route away from this skill.
