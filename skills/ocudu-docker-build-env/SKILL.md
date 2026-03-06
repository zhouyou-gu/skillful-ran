---
name: ocudu-docker-build-env
description: Build the repo-owned Docker images used by the Skillful RAN OCUDU campaign. Use when the workspace is ready and the next step is to prepare the pinned build and runtime containers. Do not use it to clone source code, run Open5GS, or promote skill drafts.
---

# OCUDU Docker Build Env

## Trigger

- Use when the user wants the pinned Docker images prepared for the campaign stages.
- Use when you need the `srsRAN_Project` and `srsUE` build images built from repo-owned Dockerfiles.
- Do not use this skill to clone source trees, run the core, or review tracked skill quality.

## Inputs

- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `image_set`: `project`, `ue`, or `all`
- `project_image`: tag for the RAN-side build image
- `ue_image`: tag for the `srsUE` build image
- `dry_run`: emit commands and stage evidence without building images

## Workflow

1. Read [`tool.json`](tool.json) for the contract.
2. Keep the image assumptions aligned with [`references/image-policy.md`](references/image-policy.md).
3. Run [`scripts/manage_docker_build_env.py`](scripts/manage_docker_build_env.py).
4. Hand off to `ocudu-project-build` or `srsran-4g-ue-build` after the requested images exist.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- `stage_dir`: evidence path for this image stage
- `images`: the concrete image tags targeted
- `commands`: exact `docker build` commands

## Failure / Escalation

- If Docker is unavailable, stop and return to `ocudu-pc-readiness`.
- If an image build fails, keep the logs and do not continue into source build stages.
- If image tags drift from the pinned defaults, record the override explicitly.
