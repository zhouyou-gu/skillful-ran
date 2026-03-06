# Validated Run

Validated on this PC on March 6, 2026:

- gNB side: `srsRAN_Project release_25_10`
- UE side: `srsUE` from `srsRAN_4G release_23_11`
- core side: vendored Open5GS compose stack
- transport: ZeroMQ, no SDR attached

Required details that came from the passing run:

- use the 20 MHz `gnb_zmq.yaml` profile with `coreset0_index: 12`
- do not force custom `nof_ssb_per_ro` values in this profile
- export `LD_LIBRARY_PATH=/install/lib:$LD_LIBRARY_PATH` in both runtime containers
- start the UE container with `--privileged`, `--cap-add NET_ADMIN`, and `/dev/net/tun`
- create `ue1` inside the UE container before starting `srsUE`

Observed success signals:

- `RRC Connected`
- `PDU Session Establishment successful. IP: 10.45.1.2`
- ping from `ue1` to `10.45.1.1` passed
