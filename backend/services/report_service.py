from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from ..schemas import ScanResult


def build_report(scan: ScanResult) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    margin = 40

    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, height - margin, "ThreatVeilAI Risk Report")
    c.setFont("Helvetica", 12)
    c.drawString(margin, height - margin - 24, f"Domain: {scan.domain}")
    c.drawString(margin, height - margin - 40, f"Generated: {datetime.utcnow():%Y-%m-%d %H:%M UTC}")
    c.drawString(margin, height - margin - 56, f"Risk Score: {scan.risk_score}/100")
    c.drawString(
        margin,
        height - margin - 72,
        f"Breach likelihood 30d/90d: {scan.breach_likelihood_30d * 100:.0f}% / {scan.breach_likelihood_90d * 100:.0f}%",
    )

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, height - margin - 110, "Category Scores")
    y = height - margin - 130
    for category, data in scan.categories.items():
        c.setFont("Helvetica", 12)
        c.drawString(margin, y, f"{category.title()}: {data.score}/100 ({data.severity})")
        y -= 16

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y - 16, "Top Signals")
    y -= 32
    for signal in scan.signals[:5]:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, f"{signal.severity.upper()} - {signal.detail}")
        y -= 14
        c.setFont("Helvetica", 11)
        c.drawString(margin, y, f"Type: {signal.type} | Category: {signal.category}")
        y -= 14
        if y < margin + 60:
            c.showPage()
            y = height - margin

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y - 20, "Summary")
    y -= 36
    summary_lines = _wrap_text(scan.summary, 90)
    c.setFont("Helvetica", 11)
    for line in summary_lines:
        c.drawString(margin, y, line)
        y -= 14
        if y < margin:
            c.showPage()
            y = height - margin

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


def _wrap_text(text: str, width: int):
    words = text.split()
    line = []
    current = 0
    for word in words:
        if current + len(word) + 1 > width:
            yield " ".join(line)
            line = [word]
            current = len(word)
        else:
            line.append(word)
            current += len(word) + 1
    if line:
        yield " ".join(line)
