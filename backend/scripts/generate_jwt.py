#!/usr/bin/env python3
"""Generate a JWT token for the /api/v1/agent/rescan endpoint."""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

from backend.security import create_jwt

if __name__ == "__main__":
    # Generate token with 30 day expiration
    token = create_jwt({"purpose": "rescan", "source": "cron"}, expires_minutes=30 * 24 * 60)
    
    print("JWT Token for /api/v1/agent/rescan:")
    print(token)
    print("\nUsage:")
    print(f"curl -X POST 'https://your-backend-url/api/v1/agent/rescan?token={token}'")

