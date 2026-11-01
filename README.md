# Distributed API Rate Limiter

A small FastAPI + Redis project demonstrating an **atomic sliding-window log** rate limiter. Redis is the shared state store, so multiple API instances use the same counter state instead of keeping independent process-local counters.

## Features

- Sliding-window log algorithm: counts requests within the previous time window.
- Redis Lua script makes cleanup, count, decision, and write atomic.
- HTTP `429 Too Many Requests` with `Retry-After` when the limit is exceeded.
- Configurable request limit and window via environment variables.
- Docker Compose Redis service and Dockerfile for the API.
- Fail-closed behavior: returns `503` if Redis cannot be reached.

## Run locally (Windows PowerShell)

1. Install Python 3.11+ and Docker Desktop, or run Redis separately.
2. Start Redis:

   ```powershell
   docker compose up -d redis
   ```

3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` directly.

4. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Start the API:

   ```powershell
   python -m uvicorn app:app --reload
   ```

6. Open `http://127.0.0.1:8000/docs` to try the endpoints.

## Test the limit

Default limit is 10 requests per 60 seconds. Repeat the request:

```powershell
1..12 | ForEach-Object {
  Invoke-WebRequest http://127.0.0.1:8000/ -Headers @{"X-API-Key"="demo-user"} -SkipHttpErrorCheck |
    Select-Object StatusCode, Headers
}
```

The first 10 requests should be allowed for that key during the window; subsequent requests should receive `429`. Use a new `X-API-Key` value to test a separate identity.

## Configure

PowerShell example:

```powershell
$env:RATE_LIMIT_REQUESTS = "5"
$env:RATE_LIMIT_WINDOW_SECONDS = "30"
$env:REDIS_URL = "redis://localhost:6379/0"
python -m uvicorn app:app --reload
```

## Design notes

- **Gateway vs service:** In production, a gateway is a good place for broad IP/API-key/tenant protection before traffic reaches services. Add service-level checks for expensive or business-specific operations.
- **Redis key:** `rate-limit:sliding:<identity>` stores a sorted set of request timestamps. Expired entries are removed on each request; the key has a TTL.
- **Atomicity:** A Redis Lua script runs as one atomic operation, preventing concurrent API instances from both observing stale counts and exceeding the limit.
- **Multi-instance behavior:** All API replicas must use the same Redis deployment and identical policy/key conventions. Do not use process-local counters for a global limit.
- **Consistency caveat:** Redis atomic scripts serialize updates on the active Redis primary, but asynchronous replication/failover can lose recent writes. If strict global limits are a hard correctness requirement, evaluate Redis topology/failover guarantees or a stronger centralized coordinator.
- **Identity caveat:** This demo accepts `X-API-Key` as a simple example and falls back to the client IP. In production, authenticate the API key first, derive identity from trusted auth context, and only trust forwarded IP headers from known proxies.
- **Algorithm trade-offs:** Token bucket allows bursts up to bucket capacity; leaky bucket smooths throughput and may queue or reject; sliding-window log is accurate but stores per-request timestamps. A sliding-window counter is cheaper but approximate.
- **Security:** Do not expose Redis publicly. Add authentication, TLS, network restrictions, metrics, and route-specific policies before production use.

## Project structure

```text
api-rate-limiter/
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

This is a runnable learning/demo project, not a drop-in production gateway.
