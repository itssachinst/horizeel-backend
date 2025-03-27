from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.routes.video import router as video_router
from app.routes.user import router as user_router
from app.routes.auth import router as auth_router
import logging
import time
from contextlib import asynccontextmanager
from starlette.datastructures import URL
from starlette.types import ASGIApp, Receive, Scope, Send
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment check for enabling HTTPS middleware
ENABLE_HTTPS_REDIRECT = os.environ.get("ENABLE_HTTPS_REDIRECT", "true").lower() == "true"

# Custom middleware to handle CloudFront/Load balancer HTTPS forwarding
class ProxyHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        
        # Check for X-Forwarded-Proto header from CloudFront/Load Balancer
        forwarded_proto = headers.get(b"x-forwarded-proto", b"").decode("latin1")
        
        # Log the headers for debugging
        logger.debug(f"Request headers: {headers}")
        
        if forwarded_proto == "https":
            # Already HTTPS, no need to redirect
            await self.app(scope, receive, send)
        else:
            # Convert to HTTPS URL for redirect
            url = URL(scope=scope)
            https_url = url.replace(scheme="https")
            
            # Send a 307 redirect response
            headers = [(b"location", https_url.encode())]
            status_code = 307
            
            await send({
                "type": "http.response.start",
                "status": status_code,
                "headers": headers,
            })
            await send({
                "type": "http.response.body",
                "body": b"",
            })

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

# Add CloudFront/Load Balancer proxy headers middleware (before CORS)
if ENABLE_HTTPS_REDIRECT:
    app.add_middleware(ProxyHeadersMiddleware)

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
