import logging
import time
import uuid

from fastapi import Request, Response

logger = logging.getLogger("fastgptrag2api.access")


async def request_id_middleware(request: Request, call_next) -> Response:
    """Attach a unique X-Request-ID to every request and log access details."""
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    request.state.request_id = rid

    start = time.monotonic()
    response = await call_next(request)
    elapsed_ms = round((time.monotonic() - start) * 1000)

    response.headers["X-Request-ID"] = rid

    device = getattr(request.state, "device_name", None) or "-"
    logger.info(
        "%s | %s %s | %s | %sms | device=%s",
        rid,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        device,
    )
    return response
