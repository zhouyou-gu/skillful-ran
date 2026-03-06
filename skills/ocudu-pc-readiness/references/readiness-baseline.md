# Readiness Baseline

The software-only Skillful RAN campaign assumes:

- Docker and `docker compose` are usable by the current user.
- `.local/ocudu/` exists and has room for cloned trees, build outputs, images, logs, and stage evidence.
- Native commands are still worth checking even though build and runtime use containers:
  - `git`
  - `cmake`
  - `make`
  - `gcc`
  - `g++`
  - `pkg-config`
  - `python3`
- Known native blockers should still be surfaced:
  - `libmbedtls-dev`
  - `libsctp-dev`
  - `libyaml-cpp-dev`
  - `libgtest-dev`
- No SDR or O-RU is required for the first milestone.
