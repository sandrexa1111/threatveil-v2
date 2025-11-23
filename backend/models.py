from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text

from .db import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True)
    domain = Column(String, nullable=False, index=True)
    github_org = Column(String, nullable=True)
    risk_score = Column(Integer, nullable=False)
    risk_likelihood_30d = Column(Float, nullable=False)
    risk_likelihood_90d = Column(Float, nullable=False)
    categories_json = Column(JSON, nullable=False)
    signals_json = Column(JSON, nullable=False)
    summary = Column(Text, nullable=False)
    raw_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class CacheEntry(Base):
    __tablename__ = "cache"

    key = Column(String, primary_key=True)
    value = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False)
