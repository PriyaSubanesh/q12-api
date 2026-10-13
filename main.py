import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# ---------------------------------------------------------
# Your assigned values
# ---------------------------------------------------------
ALLOWED_ORIGINS = [
    "https://app-rtbkwg.example.com",

    # Add the exam/verification page origin here.
    # Replace this with the exact origin shown by your assignment page.
    "https://app-rtbkwg.example.com",
]

RATE_LIMIT = 11          # B requests
RATE_WINDOW = 10         # per 10 seconds

# Stores request timestamps for each client ID.
# Example:
# {
#   "client-1": deque([1728830001.2, 1728830002.4, ...]),
#   "client-2": deque([...])
# }
client_requests = defaultdict(deque)


# ---------------------------------------------------------
# Middleware 3: Per-client rate limiter
# ---------------------------------------------------------
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id")

    # If no client ID is provided, do not rate-limit it.
    if not client_id:
        return await call_next(request)

    now = time.time()

    # Remove timestamps older than the 10-second window.
    while (
        client_requests[client_id]
        and now - client_requests[client_id][0] >= RATE_WINDOW
    ):
        client_requests[client_id].popleft()

    # If this client already made 11 requests in the current window, block it.
    if len(client_requests[client_id]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

    # Otherwise, record this request and allow it.
    client_requests[client_id].append(now)
    return await call_next(request)


# ---------------------------------------------------------
# Middleware 1: Request context
# ---------------------------------------------------------
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    # Reuse the incoming request ID if present.
    request_id = request.headers.get("X-Request-ID")

    # Otherwise create a fresh unique ID.
    if not request_id:
        request_id = str(uuid.uuid4())

    # Save it so the endpoint can read it.
    request.state.request_id = request_id

    response = await call_next(request)

    # Always send it back in the response header too.
    response.headers["X-Request-ID"] = request_id

    return response


# ---------------------------------------------------------
# Middleware 2: CORS
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["X-Request-ID", "X-Client-Id"],
    expose_headers=["X-Request-ID"],
)


# ---------------------------------------------------------
# Endpoint
# ---------------------------------------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "24f3003806@ds.study.iitm.ac.in",
        "request_id": request.state.request_id,
    }