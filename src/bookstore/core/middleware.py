import base64
import json
import time
from uuid import uuid4

import structlog
from opentelemetry import trace
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = structlog.get_logger()


def _peek_jwt_sub(headers: dict[bytes, bytes]) -> str:
    """Extract sub claim from JWT without validation — for logging only."""
    auth = headers.get(b"authorization", b"").decode()
    if not auth.startswith("Bearer "):
        return "anonymous"
    try:
        payload_b64 = auth[7:].split(".")[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        return payload.get("sub", "anonymous")
    except Exception:
        return "anonymous"

SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "camera=(), microphone=(), geolocation=()",
    "cache-control": "no-store",
}


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode() or str(uuid4())
        method = scope.get("method", "")
        path = scope.get("path", "")

        # Extract client IP from X-Forwarded-For or ASGI client
        forwarded_for = headers.get(b"x-forwarded-for", b"").decode()
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_addr = scope.get("client")
            client_ip = client_addr[0] if client_addr else "unknown"

        # Lightweight JWT sub extraction for logging (no validation)
        user_id = _peek_jwt_sub(headers)

        # Extract OpenTelemetry trace/span IDs if available
        span = trace.get_current_span()
        span_context = span.get_span_context()
        if span_context.is_valid:
            trace_id = format(span_context.trace_id, "032x")
            span_id = format(span_context.span_id, "016x")
        else:
            trace_id = request_id
            span_id = ""

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
            method=method,
            path=path,
            client_ip=client_ip,
            user_id=user_id,
        )

        start_time = time.perf_counter()
        logger.info("request_started")

        status_code = 0

        async def send_with_headers(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
                response_headers = list(message.get("headers", []))
                response_headers.append((b"x-request-id", request_id.encode()))
                for name, value in SECURITY_HEADERS.items():
                    response_headers.append((name.encode(), value.encode()))
                message = {**message, "headers": response_headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "request_completed",
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
        )
