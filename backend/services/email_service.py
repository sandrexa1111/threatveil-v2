"""Email service for sending reports via Resend API."""
import base64
import time
from typing import Optional

import httpx

from ..config import settings
from ..logging_config import log_service_call
from ..schemas import ScanResult
from .utils import with_backoff

RESEND_API_URL = "https://api.resend.com/emails"
TIMEOUT = httpx.Timeout(20.0, connect=5.0, read=15.0)


async def send_report_email(
    to_email: str,
    scan: ScanResult,
    pdf_bytes: bytes,
    from_email: Optional[str] = None,
) -> Optional[str]:
    """
    Send a PDF report via Resend API.
    
    Args:
        to_email: Recipient email address
        scan: Scan result to include in email
        pdf_bytes: PDF file bytes
        from_email: Sender email (defaults to reports@threatveil.com if not set)
    
    Returns:
        Email ID if successful, None if Resend is not configured or fails
    """
    if not settings.resend_api_key:
        log_service_call(
            service="resend",
            latency_ms=0.0,
            cache_hit=False,
            success=False,
            error="RESEND_API_KEY not configured",
        )
        return None

    start_time = time.time()
    from_addr = from_email or "ThreatVeil <reports@threatveil.com>"
    
    # Base64 encode PDF
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    payload = {
        "from": from_addr,
        "to": [to_email],
        "subject": f"ThreatVeil Risk Report: {scan.domain}",
        "html": f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>ThreatVeil Risk Report</h2>
            <p>Your security scan for <strong>{scan.domain}</strong> is complete.</p>
            <p><strong>Risk Score:</strong> {scan.risk_score}/100</p>
            <p><strong>Breach Likelihood:</strong> {scan.breach_likelihood_30d*100:.0f}% (30d), {scan.breach_likelihood_90d*100:.0f}% (90d)</p>
            <p>Please find the detailed PDF report attached.</p>
            <hr>
            <p style="font-size: 0.9em; color: #666;">
                This is an automated report from ThreatVeil.<br>
                For questions, visit https://threatveil.com
            </p>
        </body>
        </html>
        """,
        "attachments": [
            {
                "filename": f"threatveil-report-{scan.domain}-{scan.id[:8]}.pdf",
                "content": pdf_base64,
            }
        ],
    }

    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await with_backoff(
                lambda: client.post(RESEND_API_URL, json=payload, headers=headers),
                retries=3,
                base_delay=0.2,
                max_delay=2.5,
            )
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                email_id = data.get("id")
                log_service_call(
                    service="resend",
                    latency_ms=latency_ms,
                    cache_hit=False,
                    success=True,
                )
                return email_id
            else:
                log_service_call(
                    service="resend",
                    latency_ms=latency_ms,
                    cache_hit=False,
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text[:100]}",
                )
                return None
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        log_service_call(
            service="resend",
            latency_ms=latency_ms,
            cache_hit=False,
            success=False,
            error=str(e),
        )
        return None

