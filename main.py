import time
import uuid
from collections import defaultdict

from fastapi import FastAPI, Request, Response, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

RATE_LIMIT = 11
WINDOW_SECONDS = 10

client_requests = defaultdict(list)
MY_EMAIL = "24f3003806@ds.study.iitm.ac.in"  # Your logged-in email from the instructions


@app.get("/ping")
def ping(request: Request, response: Response):
    # Request Context: Get existing X-Request-ID or generate a new one
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    # Ensure it's returned in the response headers as well
    response.headers["X-Request-ID"] = request_id

    return {
        "email": MY_EMAIL,
        "request_id": request_id,
    }


@app.middleware("http")
async def rate_limit_and_context_middleware(request: Request, call_next):
    # Skip rate limiting for CORS preflight requests
    if request.method == "OPTIONS":
        return await call_next(request)

    client_id = request.headers.get("X-Client-Id")
    client_id = client_id or "anonymous"

    now = time.time()

    # Clean timestamps older than the 10-second window
    client_requests[client_id] = [
        timestamp for timestamp in client_requests[client_id]
        if now - timestamp < WINDOW_SECONDS
    ]

    if len(client_requests[client_id]) >= RATE_LIMIT:
        oldest_request = client_requests[client_id][0]
        retry_after = max(1, int(WINDOW_SECONDS - (now - oldest_request)) + 1)

        # Build response with proper headers including CORS and Retry-After
        return Response(
            content='{"detail": "Rate limit exceeded"}',
            status_code=429,
            media_type="application/json",
            headers={"Retry-After": str(retry_after)},
        )

    client_requests[client_id].append(now)
    
    response = await call_next(request)
    return response


@app.get("/")
def root():
    return {"status": "Middleware Stack API is running"}


# CORS Middleware added at the very end to act as the outermost wrapper
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-rtbkwg.example.com",
        "https://exam.sanand.workers.dev",
        "http://localhost",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "Retry-After"],
)
