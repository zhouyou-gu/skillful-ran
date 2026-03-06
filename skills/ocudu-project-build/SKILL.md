---
name: ocudu-project-build
description: Build the pinned OCUDU-aligned RAN side from srsRAN Project release_25_10 in the local workspace. Use when the user wants the concrete project source cloned and compiled inside the repo-owned Docker build environment. Do not use it for host readiness checks, Open5GS core control, or srsUE builds.
---

# OCUDU Project Build

## Trigger

- Use when the user wants `srsRAN_Project release_25_10` cloned and built in `.local/ocudu/`.
- Use when the user needs reproducible build commands, logs, and install artifacts for the RAN side.
- Do not use this skill for host gating, Open5GS lifecycle work, or the `srsUE` build lane.

## Inputs

- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `repo_url`: source repo, defaulting to the official SRS repository
- `source_ref`: pinned release, default `release_25_10`
- `image`: repo-owned Docker build image
- `clean_build`: remove the existing build and install trees first
- `dry_run`: emit commands and stage evidence without executing them

## Workflow

1. Read [`tool.json`](tool.json) for the contract.
2. Use [`references/release-25-10.md`](references/release-25-10.md) for the pinned source and build assumptions.
3. Check [`references/validated-run.md`](references/validated-run.md) before widening the verification scope.
4. Run [`scripts/run_project_build.py`](scripts/run_project_build.py) to clone, build, run the compact verification set, and install inside `.local/ocudu/`.
5. Hand off to `ocudu-local-runtime-test` after the build stage is stable.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- `stage_dir`: evidence path for this build stage
- `source_dir`, `build_dir`, `install_dir`: concrete workspace paths
- `commands`: the exact git, docker, cmake, and test commands used

## Failure / Escalation

- If the Docker build image is missing, run `ocudu-docker-build-env` first.
- If clone or fetch fails, stop and capture the git error in the stage logs.
- If configure or test steps fail, do not continue into runtime stages.
