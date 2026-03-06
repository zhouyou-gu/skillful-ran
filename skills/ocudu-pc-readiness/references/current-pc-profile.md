# Current PC Profile

Sanitized notes carried into the campaign:

- Ubuntu 24.04-class Linux workstation
- Docker usable as the current user
- passwordless `sudo` unavailable
- no SDR or O-RU hardware attached over USB
- earlier native blockers:
  - `cmake`
  - `libmbedtls-dev`
  - `libsctp-dev`
  - `libyaml-cpp-dev`
  - `libgtest-dev`

Validated outcome from the Docker-first campaign on March 6, 2026:

- these native blockers did not block the staged test flow
- Docker image builds, `srsRAN_Project`, `srsUE`, local split runtime, vendored Open5GS, and the ZMQ attach plus ping lane all passed
- keep the native blocker list because it still matters if the workflow moves back to host installs
