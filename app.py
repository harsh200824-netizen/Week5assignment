
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time

app = FastAPI(title="Simple API Rate Limiter")

# Settings
MAX_REQUESTS = 5
TIME_WINDOW = 60  # seconds

# Store request timestamps for each IP address
requests_data = {}


@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    # Don't limit health checks or documentation
    if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)

    # Identify the client
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()

    # Create a list for this client if necessary
    if client_ip not in requests_data:
        requests_data[client_ip] = []

    # Keep only requests made within the time window
    requests_data[client_ip] = [
        timestamp
        for timestamp in requests_data[client_ip]
        if current_time - timestamp < TIME_WINDOW
    ]

    # Check the request limit
    if len(requests_data[client_ip]) >= MAX_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too many requests",
                "message": f"Maximum {MAX_REQUESTS} requests per {TIME_WINDOW} seconds."
            }
        )

    # Record this request
    requests_data[client_ip].append(current_time)

    return await call_next(request)


@app.get("/")
def home():
    return {
        "message": "Simple API Rate Limiter is running!",
        "limit": MAX_REQUESTS,
        "time_window_seconds": TIME_WINDOW
    }


@app.get("/hello")
def hello():
    return {"message": "Hello! Your request was successful."}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/rate-limit-info")
def rate_limit_info():
    return {
        "max_requests": MAX_REQUESTS,
        "time_window_seconds": TIME_WINDOW,
        "storage": "In-memory"
    }
