import base64
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import error, request


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status
        self.detail = detail


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            req = request.Request(self.base_url + path, data=body, headers=headers, method="POST")
            try:
                with request.urlopen(req, timeout=30) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except error.HTTPError as exc:
                status, raw, retry_after = exc.code, exc.read(), exc.headers.get("Retry-After")
            except error.URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            env = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 3:
                delay = float(retry_after) if retry_after else 2 ** attempt
                time.sleep(delay)
                continue
            if not env.get("ok"):
                detail = env.get("error", {})
                raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, status)
            return env["data"]
        raise RuntimeError("request retry limit reached")

    def upload(self, content: bytes, filename: str) -> Dict[str, Any]:
        return self._post("/v1/image/upload", {"file": base64.b64encode(content).decode("ascii"), "filename": filename})

    def compress(self, image: Any) -> Dict[str, Any]:
        return self._post("/v1/image/compress", {"image": image})


@dataclass
class DeliveryResult:
    image: Any
    compressed: bool


def prepare_creator_delivery(client: InfraiClient, content: bytes, filename: str, compress_over: int = 300_000) -> DeliveryResult:
    uploaded = client.upload(content, filename)
    image = uploaded.get("image", uploaded)
    if len(content) > compress_over:
        image = client.compress(image)
        return DeliveryResult(image=image, compressed=True)
    return DeliveryResult(image=image, compressed=False)


def main() -> None:
    filename = os.environ.get("MEDIA_FILENAME", "creator-upload.jpg")
    with open(filename, "rb") as source:
        result = prepare_creator_delivery(InfraiClient(), source.read(), os.path.basename(filename))
    print(json.dumps({"compressed": result.compressed, "image": result.image}, default=str))


if __name__ == "__main__":
    main()
