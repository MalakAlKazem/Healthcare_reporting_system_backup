"""
Healthcare Mortality Analysis - Python Service
FastAPI application for data processing
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys
import os

# Import API routes
from app.api.routes import router
from app.api.medication_routes import router as medication_router

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

# Create logs directory
os.makedirs("logs", exist_ok=True)
logger.add(
    "logs/python-service.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG"
)

# Create FastAPI app
app = FastAPI(
    title="Mortality Analysis API",
    description="Data processing and statistics service",
    version="1.0.0",
    docs_url="/docs"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")
app.include_router(medication_router, prefix="/api/medication")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "python-data-processor",
        "version": "1.0.0",
        "ai_enabled": False  # Phase 1
    }


@app.on_event("startup")
async def startup_event():
    """Initialize service"""
    logger.info("="*60)
    logger.info("🏥 Healthcare Mortality Analysis - Python Service")
    logger.info("="*60)
    logger.info("📊 Phase 1: AI Disabled (Placeholder Text)")
    logger.info("🔧 Environment: development")
    
    # Create directories
    os.makedirs("../storage/uploads", exist_ok=True)
    os.makedirs("../storage/charts", exist_ok=True)
    os.makedirs("../storage/temp", exist_ok=True)
    
    logger.success("✅ Python service ready on port 8000")
    logger.info("📖 API Docs: http://localhost:8000/docs")
    logger.info("="*60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup"""
    logger.info("👋 Shutting down Python service")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )