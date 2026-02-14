"""
HTTP execution engine — fires requests against targets and classifies results.

Each call to execute_http_request returns a fully populated Attempt object
that the caller can attach to a Run.
"""

import time
from datetime import datetime, timezone

import httpx

from app.models.run import Attempt, ErrorType


async def execute_http_request(
    url: str,
    method: str,
    headers: dict | None,
    body: dict | None,
    timeout_seconds: int,
) -> Attempt:
    """Fire one HTTP request and return an Attempt with captured metadata."""
    attempt = Attempt(started_at=_utcnow())
    start = time.monotonic()

    try:
        response = await _send_request(url, method, headers, body, timeout_seconds)
        _record_response(attempt, response, start)
    except httpx.TimeoutException as exc:
        _record_error(attempt, ErrorType.TIMEOUT, str(exc), start)
    except httpx.ConnectError as exc:
        _record_error(attempt, _classify_connect_error(exc), str(exc), start)
    except httpx.HTTPError as exc:
        _record_error(attempt, ErrorType.UNKNOWN, str(exc), start)
    except Exception as exc:
        _record_error(attempt, ErrorType.UNKNOWN, str(exc), start)

    return attempt


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

async def _send_request(
    url: str,
    method: str,
    headers: dict | None,
    body: dict | None,
    timeout: int,
) -> httpx.Response:
    """Send the actual HTTP request via httpx."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.request(
            method=method, url=url, headers=headers, json=body
        )


def _record_response(
    attempt: Attempt, response: httpx.Response, start: float
) -> None:
    """Populate attempt fields from a successful HTTP response."""
    attempt.status_code = response.status_code
    attempt.latency_ms = _elapsed_ms(start)
    attempt.response_size_bytes = len(response.content)
    attempt.completed_at = _utcnow()

    if 400 <= response.status_code < 500:
        attempt.error_type = ErrorType.HTTP_4XX.value
        attempt.error_message = f"HTTP {response.status_code}"
    elif response.status_code >= 500:
        attempt.error_type = ErrorType.HTTP_5XX.value
        attempt.error_message = f"HTTP {response.status_code}"


def _record_error(
    attempt: Attempt, error_type: ErrorType, message: str, start: float
) -> None:
    """Populate attempt fields when the request failed at the transport level."""
    attempt.latency_ms = _elapsed_ms(start)
    attempt.error_type = error_type.value
    attempt.error_message = message[:500]
    attempt.completed_at = _utcnow()


def _classify_connect_error(exc: httpx.ConnectError) -> ErrorType:
    """Distinguish DNS failures from generic connection errors."""
    text = str(exc).lower()
    if "name resolution" in text or "dns" in text:
        return ErrorType.DNS
    return ErrorType.CONNECTION


def _elapsed_ms(start: float) -> float:
    """Monotonic elapsed time in milliseconds since *start*."""
    return round((time.monotonic() - start) * 1000, 2)


def _utcnow() -> datetime:
    """Naive UTC now (consistent with model helpers)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
