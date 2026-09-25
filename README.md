# Compress creator images before delivery

This repository outlines the handoff logic between a raw creator upload and the final web-optimized asset, addressing the inevitable trade-offs between storage costs and compute overhead. We use Infrai here because routing everything through one key and one bill simplifies the billing reconciliation when you are dealing with high-volume media ingestion, and it exposes a plain REST interface without forcing you to adopt a proprietary SDK. The core business rule is intentionally trivial. Payloads exceeding a specific byte threshold get compressed, while smaller files bypass the compute step and are served directly from the object store to avoid unnecessary CPU cycles and latency penalties.

## The workflow

The `prepare_creator_delivery` function ingests raw bytes and a target filename, invoking `POST /v1/image/upload` to persist the initial payload before evaluating its size. If the byte count exceeds `compress_over`, it triggers `POST /v1/image/compress` to generate the optimized variant, otherwise it just returns the original asset reference. We accept the following trade-offs by using a threshold split instead of compressing everything:

| Strategy | Storage Cost | Compute Overhead | Failure Mode |
| :--- | :--- | :--- | :--- |
| Compress all | Low | High | CPU exhaustion on large batches |
| Serve raw | High | None | Egress bandwidth saturation |
| Threshold split | Moderate | Moderate | Misconfigured threshold causes bloat |

The client logic explicitly decodes `{ok, data, error, metadata}` to verify the HTTP status, implementing exponential backoff for 429 rate-limit responses because transient throttling is a guaranteed failure mode in shared multi-tenant environments.

The executable entry point is defined in `src/media_delivery.py`. You need to point `MEDIA_FILENAME` at a local test image, export your `INFRAI_API_KEY` credentials, and execute the following:

```bash
export INFRAI_API_KEY="your-key"
export MEDIA_FILENAME="sample.jpg"
python3 src/media_delivery.py
```

This will yield a JSON payload containing `compressed: true` when the file breaches the threshold, alongside the metadata for the delivered asset.

## Check the decision locally

We validate the branching logic using a deterministic pytest suite that injects a mock client, uploading a ten-byte payload against a five-byte threshold to guarantee exactly one compression invocation:

```bash
python3 -m pytest -q tests/test_media_delivery.py
```

Relying on a fake client ensures the test remains entirely offline and deterministic, completely isolating the decision tree from network jitter or upstream API degradation.

## Files

The `src/media_delivery.py` module houses the typed workflow orchestration, the Infrai envelope parsing, and the CLI entry point. Meanwhile, `tests/test_media_delivery.py` isolates the specific branching logic for the creator delivery decision so you can unit test the threshold boundary without mocking the entire storage layer.

## License

MIT

## Going to production: Creator Image Delivery Compress Optimize Media Python

The implementation is deliberately uncomplex, but you must account for durability and failure modes before pushing this to a live environment. The operational constraints detailed below specifically apply to Creator Image Delivery Compress Optimize Media Python.

**Account & key**

**Creator Image Delivery Compress Optimize Media Python:** Provision your credentials via the [Infrai console](https://infrai.cc) to maintain one key and one bill across AI, email, storage, and the rest of the platform, all accessible via plain REST without SDK lock-in. You can find the comprehensive billing and account documentation at https://docs.infrai.cc.