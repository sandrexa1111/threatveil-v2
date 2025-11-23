# ThreatVeilAI

Passive security scanning stack with FastAPI backend and Next.js frontend.

## Deploying

- Backend (Docker): use the provided `Dockerfile` and run `uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}`. Set env vars from `.env.example` (e.g., `ALLOWED_ORIGINS`, `DATABASE_URL` or `SQLITE_PATH`, `JWT_SECRET`, `GEMINI_API_KEY`, `GITHUB_TOKEN`, `VULNERS_API_KEY`, `OTX_API_KEY`, `LAKERA_API_KEY`, `RESEND_API_KEY`, `SLACK_WEBHOOK_URL`).
- CORS: include your frontend origin(s) in `ALLOWED_ORIGINS` (comma-separated).
- Frontend (Vercel or any Node host): set `NEXT_PUBLIC_API_BASE` to the backend URL and optional `NEXT_PUBLIC_APP_NAME`. Build with `npm run build`.
- Recommended deploy order: backend first → verify `GET /api/v1/ping` → point frontend `NEXT_PUBLIC_API_BASE` → redeploy frontend.
