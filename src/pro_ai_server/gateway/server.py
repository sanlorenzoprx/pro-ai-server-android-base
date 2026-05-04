from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from pro_ai_server.gateway.app import handle_gateway_request
from pro_ai_server.gateway.settings import GatewaySettings


class GatewayStatusError(RuntimeError):
    pass


def serve_gateway(settings: GatewaySettings | None = None) -> None:
    gateway_settings = settings or GatewaySettings()
    handler_class = make_gateway_request_handler(gateway_settings)
    with ThreadingHTTPServer((gateway_settings.host, gateway_settings.port), handler_class) as server:
        server.serve_forever()


def make_gateway_request_handler(settings: GatewaySettings) -> type[BaseHTTPRequestHandler]:
    class GatewayRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib handler method name.
            self._send_gateway_response("GET")

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler method name.
            self._send_gateway_response("POST")

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_gateway_response(self, method: str) -> None:
            body = self.rfile.read(_content_length(self.headers.get("Content-Length"))).decode("utf-8")
            response = handle_gateway_request(method, self.path, body=body, settings=settings)
            encoded_body = response.body.encode("utf-8")
            self.send_response(response.status_code)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(encoded_body)))
            self.end_headers()
            self.wfile.write(encoded_body)

    return GatewayRequestHandler


def fetch_gateway_health(settings: GatewaySettings | None = None) -> dict[str, object]:
    gateway_settings = settings or GatewaySettings()
    url = f"{gateway_settings.bind_url}/health"
    try:
        with urlopen(url, timeout=gateway_settings.timeout_seconds) as response:
            payload = response.read().decode("utf-8")
    except HTTPError as exc:
        raise GatewayStatusError(f"Gateway health check returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise GatewayStatusError(f"Gateway is not reachable at {url}: {exc.reason}") from exc
    except OSError as exc:
        raise GatewayStatusError(f"Gateway is not reachable at {url}: {exc}") from exc

    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise GatewayStatusError("Gateway health response was not valid JSON.") from exc
    if not isinstance(decoded, dict):
        raise GatewayStatusError("Gateway health response must be a JSON object.")
    return decoded


def _content_length(value: str | None) -> int:
    if value is None:
        return 0
    try:
        return max(0, int(value))
    except ValueError:
        return 0

