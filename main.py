from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
from datetime import datetime
from pathlib import Path
import logging
from contextlib import asynccontextmanager

from app.routers import companies, import_export
from app.database import init_db, health_check, close_db
from app.auth import get_current_user
from app.config import (
    DEBUG, API_TITLE, API_DESCRIPTION, API_VERSION, 
    ALLOWED_ORIGINS, LOG_LEVEL
)
from app.exceptions import BeaconError
from app.cache import cache_service

log_file = "logs/beacon.log"
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Starting Beacon Commercial Register API...")
        await init_db()
        logger.info("Database initialized successfully")
        yield
    finally:
        logger.info("Shutting down Beacon Commercial Register API...")
        await close_db()
        logger.info("Database connection closed")


app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    debug=DEBUG,
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "companies",
            "description": "Operations with companies in the commercial register"
        },
        {
            "name": "data",
            "description": "Import and export operations for company data"
        }
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

if not DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]
    )


@app.exception_handler(BeaconError)
async def beacon_exception_handler(request: Request, exc: BeaconError):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.get("/")
async def root():
    return {"message": "Beacon Commercial Register API", "version": API_VERSION}


@app.get("/health")
async def health_check_endpoint():
    try:
        db_healthy = await health_check()
        cache_healthy = await cache_service.health_check()
        
        if db_healthy and cache_healthy:
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "Beacon Commercial Register API",
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy"
            }
        else:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "Beacon Commercial Register API",
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy"
            }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Beacon Commercial Register API",
            "error": str(e)
        }


app.include_router(companies.router, prefix="/api/v1", tags=["companies"])
app.include_router(import_export.router, prefix="/api/v1", tags=["data"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG,
        log_level=LOG_LEVEL.lower()
    )
