---
name: ocudu-pc-readiness
description: Audit this Linux PC for the Skillful RAN software-only OCUDU campaign. Use when you need a non-destructive checkpoint before building images, cloning sources, or running the local and ZMQ lanes. Do not use it to build code, start containers, or promote files into tracked skills.
---

# OCUDU PC Readiness

## Trigger

- Use when the user wants to know whether this PC can run the Skillful RAN OCUDU test campaign.
- Use when you need a compact report covering Docker access, host blockers, disk and RAM headroom, and workspace readiness.
- Do not use this skill to clone repos, build software, run the radio stack, or curate tracked skill assets.

## Inputs

- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `profile`: `ubuntu-24.04-gaming-pc` or `portable-linux`
- `check_docker`: include Docker and Compose reachability checks
- `check_storage`: include disk and RAM headroom checks
- `check_usb`: inspect attached USB devices for SDR-like hardware
- `dry_run`: still writes evidence, but never changes the host
- `strict`: fail if any blocker is present

## Workflow

1. Read [`tool.json`](tool.json) for the contract.
2. Run [`scripts/run_pc_readiness.py`](scripts/run_pc_readiness.py) to write `summary.json` under `.local/ocudu/stages/ocudu-pc-readiness/<timestamp>/`.
3. Compare the result against [`references/readiness-baseline.md`](references/readiness-baseline.md) and the current PC notes.
4. Hand off to `ocudu-docker-build-env` only after the blocker list is understood.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- `blockers`: commands, packages, or permissions blocking the campaign
- `checks`: per-check status records
- `stage_dir`: evidence path for this checkpoint
- `hardware`: compact OS, CPU, PCIe, and USB profile

## Failure / Escalation

- If `docker` or `docker compose` is unavailable to the current user, stop and fix that before build work.
- If discovery tools such as `lspci` or `lsusb` are missing, return a partial report and say what could not be inspected.
- If the host is incomplete, do not continue into build or runtime stages blindly.
