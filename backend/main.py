from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .middleware import SecurityHeadersMiddleware
from .routes import agent, chat, ping, report, scan

app = FastAPI(
    title="ThreatVeilAI API",
    version="0.1.0",
    description="Passive risk intelligence service for SMBs.",
)


@app.on_event("startup")
def on_startup():
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


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

app.include_router(ping.router)
app.include_router(scan.router)
app.include_router(report.router)
app.include_router(chat.router)
app.include_router(agent.router)
