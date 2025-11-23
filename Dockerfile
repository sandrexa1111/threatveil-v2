FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && pip install -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend source
COPY backend /app/backend

ENV PORT=8000
EXPOSE 8000

# Default startup command; hosts can override PORT env
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
