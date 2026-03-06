# Skillful RAN

Skillful RAN is a public OCUDU-first skill marketplace for building, testing, and packaging reusable open RAN workflows on Linux.

This repo is both:

1. a static GitHub Pages marketplace for discovering skills
2. a working lab repo for refining OCUDU and srsRAN workflows
3. a packaging system for turning good experiments into compact reusable skills

## What Ships Here

The first tracked bundle is intentionally narrow:

1. `ocudu-host-audit` checks workstation readiness
2. `ocudu-build-install` plans or executes the baseline build flow
3. `ocudu-smoke-test` validates local post-build sanity without claiming RF coverage
4. `skillful-ran-packaging` reviews and promotes reusable artifacts into tracked skills

The marketplace stays static and GitHub-native:

```text
skills/      source-of-truth skill folders
scripts/     validation and registry builders
registry/    generated machine-readable outputs
marketplace/ static search UI
```

## Working Rule: Use `.local/ocudu/`

All live OCUDU or srsRAN work belongs under `.local/ocudu/` so git never starts tracking scratch artifacts.

Use this layout:

```text
.local/ocudu/
├─ src/        upstream clones
├─ build/      build trees
├─ logs/       run logs
├─ captures/   screenshots and traces
├─ tmp/        throwaway files
└─ promote/
   └─ backups/ pre-update snapshots
```

Only distilled reusable assets belong in `skills/`.

Promote:

- stable scripts
- concise references
- compact templates
- sanitized tiny examples when they teach something

Do not promote:

- raw build logs
- host-specific transcripts
- screenshots with no reusable value
- ad-hoc scratch notes

## Skill Standards

Skillful RAN keeps skills compact on purpose.

Each tracked skill includes:

- `SKILL.md`
- `skill.yaml`
- `tool.json`
- a minimal `README.md`
- `evals/cases.jsonl`

Optional folders:

- `scripts/`
- `references/`
- `examples/`

House rules:

1. `ocudu-*` is for OCUDU task skills
2. `srsran-*` is reserved for upstream-generic srsRAN skills
3. `skillful-ran-*` is for meta, packaging, and policy skills
4. `SKILL.md` stays concise and uses the same five sections
5. tool outputs share the same top-level envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`

The detailed authoring rules live in [skills/README.md](skills/README.md).

## Build and Preview

Validate and generate the public artifacts from the repo root:

```bash
python3 scripts/validate_skills.py
python3 scripts/verify_install_targets.py
python3 scripts/build_registry.py
python3 scripts/build_search_index.py
```

Preview locally:

```bash
python3 -m http.server 8000
```

Open:

- `http://localhost:8000/`
- `http://localhost:8000/marketplace/`

## CI and Publishing

The GitHub Actions workflow validates skill metadata, verifies install targets, rebuilds `registry/index.json`, rebuilds `registry/search.json`, and deploys the static marketplace on pushes to `main`.

`registry/*.json` is generated and intentionally not tracked.

## Source Notes

The OCUDU-facing copy in this repo is based on current official SRS material:

- the March 2, 2026 OCUDU Ecosystem Foundation announcement
- the “Building OCUDU: the Linux of RAN” article
- the latest srsRAN Project documentation for build prerequisites and clone/build flow

- Registry format is ready for CLI consumers.
- Full installer behavior remains a future extension.

## Roadmap

1. v1: registry + UI + CI (current template direction)
2. v1.1: CLI installer integration
3. Future: trust tiers, stronger security policy checks, richer search ranking

## License

MIT License - see [LICENSE](LICENSE).

Copyright (c) 2026 Zhouyou Gu
