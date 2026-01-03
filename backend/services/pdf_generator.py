"""
PDF Generator Service

Generates PDF briefs from WeeklyBriefResponse using ReportLab.
Simple, lightweight PDF generation for email attachments.
"""
from datetime import datetime
from io import BytesIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..schemas import WeeklyBriefResponse


def generate_brief_pdf(brief: "WeeklyBriefResponse", org_name: str = "Organization") -> bytes:
    """
    Generate a PDF brief from WeeklyBriefResponse.
    
    Args:
        brief: The weekly brief data
        org_name: Organization name for header
        
    Returns:
        PDF file bytes
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    except ImportError:
        # Return simple text-based PDF fallback if ReportLab not installed
        return _generate_simple_pdf(brief, org_name)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=12,
        textColor=colors.HexColor('#7c3aed'),  # Purple
    )
    
    headline_style = ParagraphStyle(
        'Headline',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=6,
        spaceBefore=12,
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
    )
    
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=6,
        spaceBefore=18,
        textColor=colors.HexColor('#64748b'),  # Slate
    )
    
    story = []
    
    # Title
    story.append(Paragraph(f"Weekly Security Brief", title_style))
    story.append(Paragraph(f"{org_name}", body_style))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%B %d, %Y')}", body_style))
    story.append(Spacer(1, 0.25*inch))
    
    # Headline
    story.append(Paragraph("Summary", section_style))
    story.append(Paragraph(brief.headline, headline_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Top Changes
    if brief.top_changes:
        story.append(Paragraph("Completed This Week", section_style))
        for change in brief.top_changes[:5]:
            story.append(Paragraph(f"• {change}", body_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Priority Actions
    if brief.top_3_actions:
        story.append(Paragraph("Priority Actions", section_style))
        
        action_data = [["#", "Action", "Effort", "Risk Reduction"]]
        for i, action in enumerate(brief.top_3_actions, 1):
            action_data.append([
                str(i),
                action.title[:50] + ("..." if len(action.title) > 50 else ""),
                action.effort_estimate,
                f"-{action.estimated_risk_reduction}%"
            ])
        
        action_table = Table(action_data, colWidths=[0.4*inch, 3.5*inch, 1*inch, 1*inch])
        action_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#475569')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(action_table)
        story.append(Spacer(1, 0.1*inch))
    
    # AI Exposure
    story.append(Paragraph("AI Exposure", section_style))
    story.append(Paragraph(brief.ai_exposure_summary, body_style))
    
    # Explanation (if available)
    if brief.explanation:
        story.append(Paragraph("Analysis", section_style))
        story.append(Paragraph(brief.explanation, body_style))
    
    # Confidence footer
    story.append(Spacer(1, 0.25*inch))
    confidence_text = f"Confidence: {brief.confidence_level.upper()}"
    story.append(Paragraph(confidence_text, ParagraphStyle(
        'Confidence',
        parent=body_style,
        textColor=colors.HexColor('#94a3b8'),
        fontSize=9,
    )))
    
    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def _generate_simple_pdf(brief: "WeeklyBriefResponse", org_name: str) -> bytes:
    """
    Fallback: Generate a simple text PDF without ReportLab.
    Uses basic PDF structure.
    """
    # Simple PDF with minimal formatting
    content = f"""Weekly Security Brief
{org_name}
Generated: {datetime.utcnow().strftime('%B %d, %Y')}

SUMMARY
{brief.headline}

"""
    
    if brief.top_changes:
        content += "COMPLETED THIS WEEK\n"
        for change in brief.top_changes[:5]:
            content += f"- {change}\n"
        content += "\n"
    
    if brief.top_3_actions:
        content += "PRIORITY ACTIONS\n"
        for i, action in enumerate(brief.top_3_actions, 1):
            content += f"{i}. {action.title} ({action.effort_estimate}, -{action.estimated_risk_reduction}% risk)\n"
        content += "\n"
    
    content += f"AI EXPOSURE\n{brief.ai_exposure_summary}\n\n"
    
    if brief.explanation:
        content += f"ANALYSIS\n{brief.explanation}\n\n"
    
    content += f"Confidence: {brief.confidence_level.upper()}\n"
    
    # Minimal valid PDF structure
    pdf = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {len(content) + 50} >>
stream
BT
/F1 10 Tf
50 750 Td
12 TL
"""
    
    # Add each line
    for line in content.split('\n'):
        escaped = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        pdf += f"({escaped}) Tj T*\n"
    
    pdf += """ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
0
%%EOF"""
    
    return pdf.encode('latin-1')
