"""
FastAPI application for CasareRPA monitoring dashboard.

Provides REST and WebSocket endpoints for fleet monitoring,
job execution tracking, and analytics.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .routers import metrics, websockets
from .dependencies import get_metrics_collector


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app initialization and cleanup."""
    logger.info("Starting CasareRPA Monitoring API")

    # Initialize metrics collector
    collector = get_metrics_collector()
    logger.info(f"Metrics collector initialized: {collector}")

    yield

    logger.info("Shutting down CasareRPA Monitoring API")


# Create FastAPI application
app = FastAPI(
    title="CasareRPA Monitoring API",
    description="Multi-robot fleet monitoring and analytics API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8000",  # Production (served by FastAPI)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only needed methods for monitoring API
    allow_headers=["Content-Type", "Authorization"],  # Restrict to required headers
)

# Include routers
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
app.include_router(websockets.router, prefix="/ws", tags=["websockets"])


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {"status": "healthy", "service": "casare-rpa-monitoring"}


@app.get("/")
async def root():
    """Root endpoint - redirect to docs."""
    return {
        "message": "CasareRPA Monitoring API",
        "docs": "/docs",
        "health": "/health",
    }
