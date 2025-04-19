from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from app.routes.video import router as video_router
from app.routes.user import router as user_router
from app.routes.auth import router as auth_router
from app.routes.waiting_list import router as waiting_list_router
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
    openapi_url="/api/openapi.json" ,
    docs_url="/api/docs" ,
    redoc_url="/api/redoc" ,
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

# Manual HTTPS redirect middleware - with improvements for API clients and EC2
@app.middleware("http")
async def redirect_to_https(request: Request, call_next):
    # Check HTTPS redirect setting on each request (allows runtime changes)
    enable_https_redirect = os.environ.get("ENABLE_HTTPS_REDIRECT", "true").lower() == "true"
    
    # Skip HTTPS redirect if it's disabled
    if not enable_https_redirect:
        logger.debug("HTTPS redirect is disabled, proceeding normally")
        return await call_next(request)
        
    # Log the original request for debugging
    path = request.url.path
    host = request.headers.get("host", "")
    user_agent = request.headers.get("user-agent", "")
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    
    # Special handling for EC2 instances
    is_ec2 = "ec2" in host or "amazonaws" in host or "amazon" in host
    if is_ec2:
        logger.info(f"EC2 environment detected, skipping HTTPS redirect for {path}")
        return await call_next(request)
    
    # Log the request details for debugging
    logger.info(f"Request info - Path: {path} | Host: {host} | UA: {user_agent[:20] if user_agent else 'None'}... | Proto: {forwarded_proto}")
    
    # Define paths that should never be redirected
    excluded_paths = [
        "/api/health", 
        "/api/health/",
        "/api/videos",  # Explicitly exclude /api/videos endpoint
    ]
    
    # Check if the path starts with any excluded path
    is_excluded_path = any(path == excluded or path.startswith(excluded + "?") for excluded in excluded_paths)
    is_localhost = "localhost" in host or "127.0.0.1" in host
    is_already_https = forwarded_proto == "https" or request.url.scheme == "https"
    is_browser = user_agent and "Mozilla" in user_agent
    is_api_client = not is_browser
    
    # Never redirect API client requests (non-browser)
    if is_api_client:
        logger.info(f"API client detected, skipping HTTPS redirect for {path}")
        return await call_next(request)
    
    # Never redirect localhost
    if is_localhost:
        logger.info(f"Localhost detected, skipping HTTPS redirect for {path}")
        return await call_next(request)
        
    # Never redirect excluded paths
    if is_excluded_path:
        logger.info(f"Excluded path detected, skipping HTTPS redirect for {path}")
        return await call_next(request)
        
    # Never redirect already HTTPS requests
    if is_already_https:
        logger.info(f"Already HTTPS, skipping redirect for {path}")
        return await call_next(request)
    
    # At this point, we only redirect browser requests to non-excluded paths over HTTP
    if is_browser:
        https_url = str(request.url).replace("http://", "https://")
        logger.info(f"Redirecting browser to HTTPS: {https_url}")
        return RedirectResponse(https_url, status_code=301)
    
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
app.include_router(waiting_list_router, prefix="/api/waiting-list")

@app.get("/api/health")
@app.get("/api/health/")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "version": "1.0.0"}
