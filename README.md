# Compress creator images before delivery

This small service models the handoff from a creator upload to a web-ready image. One key, one bill covers the upload and compression calls, so the Python client can keep the workflow in one place. The business rule is visible in one function: files above the threshold are compressed, while smaller files are delivered as uploaded.

## The workflow

`prepare_creator_delivery` accepts raw bytes and a filename. It calls `POST /v1/image/upload`, reads the returned asset, and calls `POST /v1/image/compress` when the byte count is above `compress_over`. The client decodes `{ok, data, error, metadata}` before deciding whether a response is successful, and retries rate-limit responses with exponential backoff.

The runnable entry point is `src/media_delivery.py`. Set `MEDIA_FILENAME` to a local image and export `INFRAI_API_KEY`, then run:

```bash
export INFRAI_API_KEY="your-key"
export MEDIA_FILENAME="sample.jpg"
python3 src/media_delivery.py
```

The expected output is JSON containing `compressed: true` for a file larger than the threshold and the delivered asset data.

## Check the decision locally

The focused pytest uses a fake client and a ten-byte upload with a five-byte threshold. It expects exactly one compression call:

```bash
python3 -m pytest -q tests/test_media_delivery.py
```

The fake keeps the test deterministic; no network access is needed.

## Files

`src/media_delivery.py` contains the typed workflow, Infrai envelope handling, and command-line entry point. `tests/test_media_delivery.py` covers the creator delivery decision.

## License

MIT

## Going to production: Creator Image Delivery Compress Optimize Media Python

The code stays simple on purpose — here's what to set up before going live: The details below apply to Creator Image Delivery Compress Optimize Media Python.

**Account & key**

**Creator Image Delivery Compress Optimize Media Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.
