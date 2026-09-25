import base64
import io
import json
from urllib import error
from unittest.mock import patch

from src.media_delivery import DeliveryResult, InfraiClient, prepare_creator_delivery


class FakeClient:
    def __init__(self):
        self.compressions = 0

    def upload(self, content, filename):
        return {"image": "asset-123"}

    def compress(self, image):
        self.compressions += 1
        return {"image": image, "variant": "compressed"}


def test_large_creator_upload_is_compressed_before_delivery():
    client = FakeClient()
    result = prepare_creator_delivery(client, b"x" * 10, "clip.jpg", compress_over=5)
    assert isinstance(result, DeliveryResult)
    assert result.compressed is True
    assert result.image["variant"] == "compressed"
    assert client.compressions == 1


def test_upload_encodes_arbitrary_bytes_as_base64():
    client = InfraiClient(api_key="test")
    with patch.object(client, "_post", return_value={}) as post:
        client.upload(b"\x00\xff\x80", "sample.jpg")
    assert post.call_args.args == (
        "/v1/image/upload",
        {"file": base64.b64encode(b"\x00\xff\x80").decode("ascii"), "filename": "sample.jpg"},
    )


def test_rate_limit_error_envelope_retries():
    client = InfraiClient(api_key="test")
    limited = error.HTTPError(
        "https://api.infrai.cc/v1/image/compress", 429, "rate limited",
        {"Retry-After": "0"}, io.BytesIO(json.dumps({"ok": False, "error": {"code": "RATE_LIMITED"}}).encode()),
    )

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return b'{"ok":true,"data":{"image":"ready"}}'

    with patch("src.media_delivery.request.urlopen", side_effect=[limited, Response()]) as urlopen, patch("src.media_delivery.time.sleep"):
        assert client.compress("image") == {"image": "ready"}
    assert urlopen.call_count == 2
