# Core Stack

This skill vendors the Open5GS Docker assets from `srsRAN_Project release_25_10` into `assets/compose/open5gs/`.

Purpose:

- keep the core stack pinned
- avoid depending on an external mutable checkout
- make the E2E lane reproducible from this repo

Validated on this PC on March 6, 2026:

- `docker compose ... up -d --build` completed successfully
- the `5gc` service reported healthy before the ZMQ lane started
- the passing runtime stage was `.local/ocudu/stages/ocudu-open5gs-core/20260306T114819Z`
