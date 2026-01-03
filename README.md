# ThreatVeil — The AI-Native Security Decision Engine

ThreatVeil is the AI-native security decision engine for organizations without a SOC.
We unify OSINT signals, AI risk, and software vulnerabilities into a unified risk model
and tell you the 3 actions that reduce your breach risk.

## Features

- **Unified Risk Intelligence**: External security, AI exposure, and CVE analysis in one platform
- **AI Exposure Detection**: Identify exposed AI keys, agent configs, and ML tooling
- **Passive OSINT Only**: No intrusive scanning, purely passive intelligence gathering
- **Actionable Insights**: LLM-powered risk explanations and prioritized recommendations
- **Weekly Security Brief**: AI-powered security summaries with email delivery
- **Continuous Monitoring**: Automated scheduled scans for all your assets
- **Asset Management**: Track domains, GitHub orgs, cloud accounts, and SaaS vendors
- **Executive Dashboard**: Organization-wide risk overview for leadership

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python/FastAPI + SQLAlchemy + PostgreSQL + APScheduler |
| Frontend | Next.js 14 (App Router) + TypeScript + TailwindCSS + shadcn/ui |
| AI | Google Gemini 2.0 |

## Deploying

- **Backend (Docker)**: Use the provided `Dockerfile` and run `uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}`. Set env vars from `.env.example`.
- **CORS**: Include your frontend origin(s) in `ALLOWED_ORIGINS` (comma-separated).
- **Frontend**: Set `NEXT_PUBLIC_API_BASE` to the backend URL. Build with `npm run build`.
- **Deploy order**: Backend first → verify `GET /api/v1/ping` → deploy frontend.

## Environment Variables

See `.env.example` for required variables:
- `DATABASE_URL` or `SQLITE_PATH`
- `GEMINI_API_KEY`
- `GITHUB_TOKEN`
- `VULNERS_API_KEY`
- `OTX_API_KEY`
- `RESEND_API_KEY` (for weekly brief emails)
- `JWT_SECRET`
- `SCHEDULER_ENABLED` (default: true)
- `SCHEDULER_INTERVAL_MINUTES` (default: 5)

## API Documentation

### Asset Management
- `GET /api/v1/org/{org_id}/assets`: List all assets with filters
- `POST /api/v1/org/{org_id}/assets`: Create a new asset
- `GET /api/v1/org/{org_id}/assets/{asset_id}`: Get asset with risk info
- `PATCH /api/v1/org/{org_id}/assets/{asset_id}`: Update asset
- `DELETE /api/v1/org/{org_id}/assets/{asset_id}`: Delete asset
- `POST /api/v1/org/{org_id}/assets/{asset_id}/scan`: Trigger manual scan

### Organization Overview
- `GET /api/v1/org/{org_id}/overview`: Executive dashboard data
- `GET /api/v1/org/{org_id}/summary`: Organization summary

### Horizon (Security Briefing)
- `GET /api/v1/org/{org_id}/horizon`: Dashboard metrics (Risk, AI, Decisions)
- `GET /api/v1/org/{org_id}/weekly-brief`: Human-readable weekly summary
- `POST /api/v1/org/{org_id}/weekly-brief/send`: Send brief via email
- `GET /api/v1/org/{org_id}/risk-timeline`: Weekly risk score timeline

### Security Decisions
- `GET /api/v1/scans/{scan_id}/decisions`: Get decisions for a scan
- `POST /api/v1/scans/{scan_id}/decisions`: Generate decisions
- `PATCH /api/v1/decisions/{decision_id}`: Update decision status
- `GET /api/v1/decisions/{decision_id}/impact`: Get measured impact

### System
- `GET /api/v1/scheduler/status`: Get scheduler status and jobs
- `GET /api/v1/ping`: Health check

## Phase 3 — Organization-Centric Security Platform

ThreatVeil now operates as a continuous, organization-centric security platform.

### Asset Types

| Type | Description |
|------|-------------|
| **Domain** | Website domains with full OSINT scanning |
| **GitHub Org** | GitHub organizations for code exposure analysis |
| **Cloud Account** | AWS/Azure/GCP accounts (metadata tracking) |
| **SaaS Vendor** | Third-party services (manual entry) |

### Scan Scheduling

| Frequency | Use Case |
|-----------|----------|
| **Daily** | Critical, internet-facing assets |
| **Weekly** | Default for most assets |
| **Monthly** | Low-risk, internal-only assets |
| **Manual** | On-demand only |

### Decision Engine V2

Each security decision includes:
- 🔧 **Technical Action**: What to do
- 💼 **Business Impact**: Why it matters
- ⏱ **Effort Estimate**: How long it takes
- 📉 **Risk Reduction**: Expected points reduced
- 🧠 **Confidence Score**: How certain we are (0-100%)

### Confidence Scoring (Deterministic)

| Confidence | Condition |
|------------|-----------|
| **1.0 (High)** | After-scan within 7 days AND triggering signal is gone |
| **0.7 (Medium)** | After-scan within 7 days, signal presence unknown |
| **0.4 (Low)** | After-scan exists but older than 7 days |
| **0.2 (Very Low)** | No scan after resolution |

### Key Principles

1. **Gemini never decides, only explains.** All scoring, prioritization, and impact calculations are deterministic.
2. **No intrusive scanning.** All data is gathered passively via OSINT.
3. **No agents required.** Everything runs via API calls.
4. **Explainable at every level.** Every score has evidence, every decision has reasoning.

## Running Tests

```bash
cd backend
pytest -v

# Run specific test suites
pytest tests/test_scheduler.py -v
pytest tests/test_horizon.py -v
pytest tests/test_decisions.py -v
```

## Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```
