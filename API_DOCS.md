# API Documentation

Base URL: `http://127.0.0.1:8000`

Interactive Swagger docs: `http://127.0.0.1:8000/docs`

---

## Table of Contents

- [Health](#health)
- [Targets](#targets)
  - [Create Target](#create-target)
  - [List Targets](#list-targets)
  - [Get Target](#get-target)
  - [Update Target](#update-target)
  - [Delete Target](#delete-target)
- [Schedules](#schedules)
  - [Create Schedule](#create-schedule)
  - [List Schedules](#list-schedules)
  - [Get Schedule](#get-schedule)
  - [Pause Schedule](#pause-schedule)
  - [Resume Schedule](#resume-schedule)
  - [Delete Schedule](#delete-schedule)
- [Runs](#runs)
  - [List Runs](#list-runs)
  - [Get Run](#get-run)
- [Metrics](#metrics)
  - [Get Metrics](#get-metrics)
- [Error Responses](#error-responses)
- [Enums & Constants](#enums--constants)

---

## Health

### Health Check

Check if the service is running.

**Endpoint:** `GET /health`

**Response:** `200 OK`

```json
{
  "status": "healthy"
}
```

---

## Targets

A **Target** represents an external HTTP endpoint that scheduled requests will be sent to.

### Create Target

**Endpoint:** `POST /targets`

**Request Body:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | — | Human-readable name for the target |
| `url` | string | Yes | — | Full URL (must start with `http://` or `https://`) |
| `method` | string | No | `"GET"` | HTTP method (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`) |
| `headers` | object | No | `null` | Key-value pairs sent as HTTP headers |
| `body_template` | object | No | `null` | JSON body sent with the request |

**Example Request:**

```bash
curl -X POST http://127.0.0.1:8000/targets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My API",
    "url": "https://httpbin.org/post",
    "method": "POST",
    "headers": {"Authorization": "Bearer token123"},
    "body_template": {"key": "value"}
  }'
```

**Response:** `201 Created`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "My API",
  "url": "https://httpbin.org/post",
  "method": "POST",
  "headers": {"Authorization": "Bearer token123"},
  "body_template": {"key": "value"},
  "created_at": "2026-02-13T18:30:00.000000",
  "updated_at": "2026-02-13T18:30:00.000000"
}
```

---

### List Targets

**Endpoint:** `GET /targets`

**Response:** `200 OK`

Returns an array of all targets, ordered by most recently created.

```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "My API",
    "url": "https://httpbin.org/post",
    "method": "POST",
    "headers": {"Authorization": "Bearer token123"},
    "body_template": {"key": "value"},
    "created_at": "2026-02-13T18:30:00.000000",
    "updated_at": "2026-02-13T18:30:00.000000"
  }
]
```

---

### Get Target

**Endpoint:** `GET /targets/{target_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `target_id` | string (UUID) | The target's unique identifier |

**Response:** `200 OK`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "My API",
  "url": "https://httpbin.org/post",
  "method": "POST",
  "headers": {"Authorization": "Bearer token123"},
  "body_template": {"key": "value"},
  "created_at": "2026-02-13T18:30:00.000000",
  "updated_at": "2026-02-13T18:30:00.000000"
}
```

**Error:** `404 Not Found` if target does not exist.

---

### Update Target

**Endpoint:** `PUT /targets/{target_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `target_id` | string (UUID) | The target's unique identifier |

**Request Body:** (all fields optional — only provided fields are updated)

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Updated name |
| `url` | string | Updated URL (must start with `http://` or `https://`) |
| `method` | string | Updated HTTP method |
| `headers` | object | Updated headers |
| `body_template` | object | Updated body template |

**Example Request:**

```bash
curl -X PUT http://127.0.0.1:8000/targets/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Content-Type: application/json" \
  -d '{"name": "Renamed API", "method": "PUT"}'
```

**Response:** `200 OK` — Returns the full updated target object.

**Error:** `404 Not Found` if target does not exist.

---

### Delete Target

**Endpoint:** `DELETE /targets/{target_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `target_id` | string (UUID) | The target's unique identifier |

**Response:** `204 No Content`

> **Note:** Deleting a target **cascades** — all associated schedules and their runs are also deleted.

**Error:** `404 Not Found` if target does not exist.

---

## Schedules

A **Schedule** defines when and how often HTTP requests are fired against a Target.

Two scheduling modes are supported:

- **Interval** — Repeats every `interval_seconds` indefinitely (until paused or deleted).
- **Window** — Repeats every `interval_seconds` but stops automatically after `duration_seconds`.

### Create Schedule

**Endpoint:** `POST /schedules`

**Request Body:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `target_id` | string (UUID) | Yes | — | ID of the target to send requests to |
| `schedule_type` | string | Yes | — | `"interval"` or `"window"` |
| `interval_seconds` | integer | Yes | — | Seconds between each execution (minimum: 1) |
| `duration_seconds` | integer | Conditional | `null` | **Required for `window` type.** Total seconds the schedule runs before auto-completing |
| `max_retries` | integer | No | `0` | Number of retry attempts on failure (0 = no retries) |
| `request_timeout_seconds` | integer | No | `30` | Timeout for each outbound HTTP request (minimum: 1) |

**Example — Interval Schedule:**

```bash
curl -X POST http://127.0.0.1:8000/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "schedule_type": "interval",
    "interval_seconds": 30
  }'
```

**Example — Window Schedule (runs for 5 minutes, fires every 10 seconds, retries once on failure):**

```bash
curl -X POST http://127.0.0.1:8000/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "schedule_type": "window",
    "interval_seconds": 10,
    "duration_seconds": 300,
    "max_retries": 1
  }'
```

**Response:** `201 Created`

```json
{
  "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "target_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "schedule_type": "window",
  "interval_seconds": 10,
  "duration_seconds": 300,
  "status": "active",
  "started_at": "2026-02-13T18:35:00.000000",
  "expires_at": "2026-02-13T18:40:00.000000",
  "last_run_at": null,
  "max_retries": 1,
  "request_timeout_seconds": 30,
  "created_at": "2026-02-13T18:35:00.000000",
  "updated_at": "2026-02-13T18:35:00.000000"
}
```

**Validation errors:**
- `400` if `schedule_type` is `window` but `duration_seconds` is not provided.
- `404` if the referenced `target_id` does not exist.

---

### List Schedules

**Endpoint:** `GET /schedules`

**Response:** `200 OK`

Returns an array of all schedules, ordered by most recently created.

```json
[
  {
    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "target_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "schedule_type": "interval",
    "interval_seconds": 30,
    "duration_seconds": null,
    "status": "active",
    "started_at": "2026-02-13T18:35:00.000000",
    "expires_at": null,
    "last_run_at": "2026-02-13T18:36:30.000000",
    "max_retries": 0,
    "request_timeout_seconds": 30,
    "created_at": "2026-02-13T18:35:00.000000",
    "updated_at": "2026-02-13T18:36:30.000000"
  }
]
```

---

### Get Schedule

**Endpoint:** `GET /schedules/{schedule_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `schedule_id` | string (UUID) | The schedule's unique identifier |

**Response:** `200 OK` — Returns the full schedule object (same shape as list items above).

**Error:** `404 Not Found` if schedule does not exist.

---

### Pause Schedule

Pause an active schedule. The scheduler will stop firing requests until the schedule is resumed.

**Endpoint:** `POST /schedules/{schedule_id}/pause`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `schedule_id` | string (UUID) | The schedule's unique identifier |

**Response:** `200 OK` — Returns the updated schedule with `"status": "paused"`.

**Errors:**
- `404 Not Found` if schedule does not exist.
- `400 Bad Request` if the schedule is not currently `active`.

---

### Resume Schedule

Resume a paused schedule. Execution resumes from the next interval.

**Endpoint:** `POST /schedules/{schedule_id}/resume`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `schedule_id` | string (UUID) | The schedule's unique identifier |

**Response:** `200 OK` — Returns the updated schedule with `"status": "active"`.

**Errors:**
- `404 Not Found` if schedule does not exist.
- `400 Bad Request` if the schedule is not currently `paused`.

---

### Delete Schedule

**Endpoint:** `DELETE /schedules/{schedule_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `schedule_id` | string (UUID) | The schedule's unique identifier |

**Response:** `204 No Content`

> **Note:** Deleting a schedule **cascades** — all associated runs and attempts are also deleted.

**Error:** `404 Not Found` if schedule does not exist.

---

## Runs

A **Run** represents a single scheduled execution. Each Run contains one or more **Attempts** (the initial request plus any retries).

### List Runs

**Endpoint:** `GET /runs`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `schedule_id` | string (UUID) | No | — | Filter runs by schedule |
| `status` | string | No | — | Filter by status: `pending`, `success`, or `failed` |
| `start_time` | datetime (ISO 8601) | No | — | Only runs started at or after this time |
| `end_time` | datetime (ISO 8601) | No | — | Only runs started at or before this time |
| `limit` | integer | No | `100` | Max results per page (1–1000) |
| `offset` | integer | No | `0` | Number of results to skip |

**Example Request:**

```bash
curl "http://127.0.0.1:8000/runs?schedule_id=b2c3d4e5-f6a7-8901-bcde-f12345678901&status=failed&limit=10"
```

**Response:** `200 OK`

```json
[
  {
    "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "schedule_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "status": "failed",
    "started_at": "2026-02-13T18:36:00.000000",
    "completed_at": "2026-02-13T18:36:03.000000",
    "created_at": "2026-02-13T18:36:00.000000"
  }
]
```

---

### Get Run

Retrieve a single run with its full attempt history.

**Endpoint:** `GET /runs/{run_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | string (UUID) | The run's unique identifier |

**Response:** `200 OK`

```json
{
  "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "schedule_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "status": "failed",
  "started_at": "2026-02-13T18:36:00.000000",
  "completed_at": "2026-02-13T18:36:03.000000",
  "created_at": "2026-02-13T18:36:00.000000",
  "attempts": [
    {
      "id": "d4e5f6a7-b8c9-0123-def1-234567890123",
      "run_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "attempt_number": 1,
      "status_code": 500,
      "latency_ms": 1245.67,
      "response_size_bytes": 0,
      "error_type": "http_5xx",
      "error_message": "HTTP 500",
      "started_at": "2026-02-13T18:36:00.100000",
      "completed_at": "2026-02-13T18:36:01.345000",
      "created_at": "2026-02-13T18:36:01.345000"
    },
    {
      "id": "e5f6a7b8-c9d0-1234-ef12-345678901234",
      "run_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "attempt_number": 2,
      "status_code": 500,
      "latency_ms": 1102.33,
      "response_size_bytes": 0,
      "error_type": "http_5xx",
      "error_message": "HTTP 500",
      "started_at": "2026-02-13T18:36:01.400000",
      "completed_at": "2026-02-13T18:36:02.502000",
      "created_at": "2026-02-13T18:36:02.502000"
    }
  ]
}
```

**Attempt fields explained:**

| Field | Description |
|-------|-------------|
| `attempt_number` | Sequential attempt within the run (1 = initial, 2+ = retries) |
| `status_code` | HTTP status code from the target (`null` if request failed at transport level) |
| `latency_ms` | Round-trip time in milliseconds |
| `response_size_bytes` | Size of the response body in bytes |
| `error_type` | Error classification (see [Enums](#enums--constants)) or `null` on clean 2xx/3xx |
| `error_message` | Human-readable error description |

**Error:** `404 Not Found` if run does not exist.

---

## Metrics

### Get Metrics

Returns aggregated statistics across all schedules and runs.

**Endpoint:** `GET /metrics`

**Response:** `200 OK`

```json
{
  "total_schedules": 3,
  "active_schedules": 2,
  "paused_schedules": 1,
  "total_runs": 150,
  "total_success": 140,
  "total_failures": 10,
  "avg_latency_ms": 245.67,
  "schedules": [
    {
      "schedule_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "total_runs": 100,
      "success_count": 98,
      "failure_count": 2,
      "avg_latency_ms": 210.45,
      "last_run_at": "2026-02-13 18:45:00.000000"
    },
    {
      "schedule_id": "f6a7b8c9-d0e1-2345-6789-abcdef012345",
      "total_runs": 50,
      "success_count": 42,
      "failure_count": 8,
      "avg_latency_ms": 315.89,
      "last_run_at": "2026-02-13 18:44:30.000000"
    }
  ]
}
```

**Fields explained:**

| Field | Description |
|-------|-------------|
| `total_schedules` | Count of all schedules (any status) |
| `active_schedules` | Schedules currently running |
| `paused_schedules` | Schedules that have been paused |
| `total_runs` | Total execution runs across all schedules |
| `total_success` | Runs that completed with a 2xx/3xx response |
| `total_failures` | Runs that ended in failure (after all retries) |
| `avg_latency_ms` | Average latency across all attempts |
| `schedules` | Per-schedule breakdown |

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| `201` | Resource created successfully |
| `204` | Resource deleted successfully (no body) |
| `400` | Validation error or invalid state transition |
| `404` | Resource not found |
| `422` | Request body failed schema validation (Pydantic) |
| `500` | Internal server error |

### Validation Error (422) Example

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "url"],
      "msg": "Value error, URL must start with http:// or https://",
      "input": "ftp://bad-url.com"
    }
  ]
}
```

---

## Enums & Constants

### Schedule Type

| Value | Description |
|-------|-------------|
| `interval` | Repeats every `interval_seconds` indefinitely |
| `window` | Repeats every `interval_seconds` for `duration_seconds`, then auto-completes |

### Schedule Status

| Value | Description |
|-------|-------------|
| `active` | Currently running on schedule |
| `paused` | Temporarily stopped (can be resumed) |
| `completed` | Window schedule finished its duration (terminal state) |

### Run Status

| Value | Description |
|-------|-------------|
| `pending` | Execution in progress |
| `success` | Final attempt returned a 2xx or 3xx status code |
| `failed` | All attempts failed (exhausted retries) |

### Error Type

Captured per-attempt to classify failures:

| Value | Description |
|-------|-------------|
| `timeout` | Request exceeded `request_timeout_seconds` |
| `dns` | DNS name resolution failed |
| `connection` | TCP connection could not be established |
| `http_4xx` | Target responded with a 4xx client error |
| `http_5xx` | Target responded with a 5xx server error |
| `unknown` | Unclassified error |

### Allowed HTTP Methods

`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`
