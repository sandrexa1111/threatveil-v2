from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings
from .db import Base, engine
from .models import (
    Organization, Scan, ScanAI, Asset, Signal, DecisionImpact,
    ScanSchedule, AuditLog, ShareableReport, SecurityDecision,
    DecisionEvidence, DecisionVerificationRun, Connector, AIAsset,
    Webhook, WebhookDelivery
)  # Ensure all models are imported
from .middleware import SecurityHeadersMiddleware
from .routes import agent, chat, ping, report, scan, org, brief, decisions, horizon, assets, ai_security, verification, ai_governance, connectors, webhooks
from .services.scheduler import start_scheduler, stop_scheduler, get_scheduler_status

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    
    # Start background scheduler for continuous monitoring
    if settings.scheduler_enabled:
        start_scheduler(interval_minutes=settings.scheduler_interval_minutes)
        logger.info("Background scheduler started")
    
    yield
    
    # Shutdown
    stop_scheduler()
    logger.info("Background scheduler stopped")


app = FastAPI(
    title="ThreatVeil API",
    version="0.4.0",
    description="AI-native security decision intelligence for SMBs. Organization-centric continuous monitoring with verification.",
    lifespan=lifespan,
)


allowed_origins = [origin.strip() for origin in settings.allowed_origins.split(",")]

# Security headers middleware (applied first)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Core routes
app.include_router(ping.router)
app.include_router(scan.router)
app.include_router(report.router)
app.include_router(chat.router)
app.include_router(agent.router)

# Organization & asset management (Phase 2)
app.include_router(org.router)
app.include_router(assets.router)

# Security intelligence
app.include_router(brief.router)
app.include_router(decisions.router)
app.include_router(horizon.router)
app.include_router(ai_security.router)

# Phase 2.3: Verification & automation
app.include_router(verification.router)
app.include_router(ai_governance.router)
app.include_router(connectors.router)
app.include_router(webhooks.router)


# =============================================================================
# Scheduler Status Endpoint
# =============================================================================

@app.get("/api/v1/scheduler/status", tags=["system"])
async def scheduler_status():
    """Get current scheduler status and job information."""
    return get_scheduler_status()

