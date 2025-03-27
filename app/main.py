from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from app.routes.video import router as video_router
from app.routes.user import router as user_router
from app.routes.auth import router as auth_router
import logging
import time
from contextlib import asynccontextmanager
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment check for enabling HTTPS middleware
ENABLE_HTTPS_REDIRECT = os.environ.get("ENABLE_HTTPS_REDIRECT", "true").lower() == "true"

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: run before the app starts
    logger.info("Starting up Horizeel API")
    yield
    # Shutdown: run when the app is shutting down
    logger.info("Shutting down Horizeel API")

# Create FastAPI application with performance-optimized config
app = FastAPI(
    title="Horizeel API",
    description="Video streaming platform API",
    version="1.0.0",
    # Disable OpenAPI docs in production for better performance
    # Set to True only in development
    openapi_url="/api/openapi.json" if __debug__ else None,
    docs_url="/api/docs" if __debug__ else None,
    redoc_url="/api/redoc" if __debug__ else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Add GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Manual HTTPS redirect middleware - even simpler approach, only redirect specific endpoints
@app.middleware("http")
async def redirect_to_https(request: Request, call_next):
    # Skip HTTPS redirect if it's disabled
    if not ENABLE_HTTPS_REDIRECT:
        return await call_next(request)
        
    # Check for X-Forwarded-Proto header (from CloudFront/load balancer)
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    host = request.headers.get("host", "")
    
    # Only redirect if:
    # 1. It's not already HTTPS
    # 2. It's not a local request (localhost)
    # 3. It's not a direct server health check
    if (forwarded_proto != "https" and request.url.scheme != "https" and
        "localhost" not in host and "127.0.0.1" not in host and
        not request.url.path.endswith("/health")):
        
        # Only redirect API endpoints for browser requests
        if "/api/" in request.url.path and "Mozilla" in request.headers.get("user-agent", ""):
            # Build HTTPS URL for redirect
            https_url = str(request.url).replace("http://", "https://")
            logger.info(f"Redirecting browser to HTTPS: {https_url}")
            return RedirectResponse(https_url, status_code=301)  # 301 is more cache-friendly than 307
    
    # For all other cases, just proceed normally
    return await call_next(request)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        logger.info(f"Request processed in {process_time:.4f} seconds: {request.method} {request.url.path}")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed in {process_time:.4f} seconds: {request.method} {request.url.path} - {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "message": str(e)},
        )

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = []
    for error in exc.errors():
        error_details.append({
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": error_details
        }
    )

# Include routers with their prefixes
app.include_router(video_router, prefix="/api")
app.include_router(user_router, prefix="/api/users")
app.include_router(auth_router, prefix="/api/auth")

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "version": "1.0.0"}
