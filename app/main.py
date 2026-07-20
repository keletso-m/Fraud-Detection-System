"""
 FastAPI Entry Point

Starts the API server and wires up all routes.
usage:  python -m uvicorn app.main:app --reload

"""

import logging
import logging.handlers
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.routes import activity, transactions, incidents
from scripts.init_db import init as init_db
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import router as auth_router

#  Paths 
ROOT    = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "sentinel.log"


#  Logging setup 
# Configure once here  all modules use logging.getLogger
# and inherit this config automatically.

def _configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger("sentinel")
    root_logger.setLevel(logging.INFO)

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    # Rotating file handler — never grows unbounded
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,   # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    ))

    root_logger.addHandler(console)
    root_logger.addHandler(file_handler)


#  Lifespan runs on startup and shutdown 

@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    logger = logging.getLogger("sentinel.main")

    logger.info("Sentinel starting up...")
    init_db()                          # safe to run multiple times
    logger.info("Database ready.")
    logger.info("Sentinel is live.")

    yield   # ← server runs here

    logger.info("Sentinel shutting down.")


#  App

app = FastAPI(
    title="Sentinel",
    description=(
        "Security Monitoring & Fraud Detection System. "
        "Dual-module detection: system activity + financial transactions."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes 

app.include_router(activity.router,     prefix="/events",    tags=["Events"])
app.include_router(transactions.router, prefix="/events",    tags=["Events"])
app.include_router(incidents.router,    prefix="/incidents", tags=["Incidents"])


#  Root + health

@app.get("/", tags=["Status"])
def root():
    """Welcome endpoint — confirms the API is running."""
    return {
        "service": "Sentinel",
        "version": "1.0.0",
        "status":  "running",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Status"])
def health():
    """
    Liveness check.
    Always returns 200 OK — intentionally does NOT touch the database.
    Use this for load balancer health checks and uptime monitors.
    """
    return {"status": "ok"}