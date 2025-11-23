from fastapi import APIRouter, Response

from ..schemas import ReportRequest
from ..services.report_service import build_report

router = APIRouter(prefix="/api/v1/report", tags=["report"])


@router.post("/generate")
async def generate_report(body: ReportRequest):
    pdf_bytes = build_report(body.scan)
    headers = {"Content-Disposition": 'attachment; filename="threatveil-report.pdf"'}
    return Response(content=pdf_bytes, headers=headers, media_type="application/pdf")
