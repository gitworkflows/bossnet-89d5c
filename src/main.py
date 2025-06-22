"""
Main FastAPI application for Bangladesh Student Data API
"""
import logging
from fastapi import FastAPI, Request, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from infrastructure.container import container
from interfaces.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Bangladesh Education Data Warehouse API",
    description="""
    Bangladesh Education Data Warehouse API provides access to comprehensive education data
    for Bangladesh, including student demographics, enrollment statistics, and academic performance
    metrics across different regions and institutions.
    """,
    version=settings.VERSION,
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default ReDoc
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Add middleware"
app.add_middleware(
    SecurityHeadersMiddleware,
    **settings.SECURITY_HEADERS
)
app.add_middleware(RequestValidationMiddleware)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors and return a clean error response."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        },
    )

# Custom docs endpoint
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.PROJECT_NAME} - Swagger UI",
        oauth2_redirect_url=None,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

# Custom OpenAPI schema
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_endpoint():
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "Bangladesh Student Data API",
        "documentation": "/docs",
        "openapi_schema": "/openapi.json"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    # Initialize database connection
    # await database.connect()
    logger.info("Application startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    # Close database connection
    # await database.disconnect()
    logger.info("Application shutdown complete")
