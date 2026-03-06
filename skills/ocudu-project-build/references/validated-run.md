# Validated Run

Validated on this PC on March 6, 2026:

- `srsRAN_Project release_25_10` built successfully in the repo-owned Docker image
- install tree: `.local/ocudu/install/srsran-project`
- compact verification that passed:
  - `ctest --output-on-failure -R 'radio_zmq_(loopback|validator)_test'`
  - `/install/bin/gnb --version`
  - `/install/bin/srscu --version`
  - `/install/bin/srsdu --version`

Keep this narrow verification set unless a later lane proves a broader test sweep is worth the extra time.
