"""Investigation report PDF exporter using ReportLab."""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#003087")
GOLD = colors.HexColor("#c8a84b")
SLATE = colors.HexColor("#475569")
DARK = colors.HexColor("#0f172a")

def _safe(value: object) -> str:
    text = str(value if value is not None else "")
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def generate_report_pdf(report: dict, author_name: str = "Investigating Officer") -> bytes:
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="RepTitle", parent=styles["Title"],
        fontSize=16, leading=20, textColor=NAVY, alignment=TA_CENTER, spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        name="RepSubTitle", parent=styles["Normal"],
        fontSize=9, leading=12, textColor=GOLD, alignment=TA_CENTER, spaceAfter=14
    )
    meta_style = ParagraphStyle(
        name="RepMeta", parent=styles["Normal"],
        fontSize=9, leading=13, textColor=DARK, alignment=TA_LEFT
    )
    section_style = ParagraphStyle(
        name="RepSec", parent=styles["Heading2"],
        fontSize=11, leading=15, textColor=NAVY, spaceBefore=10, spaceAfter=4
    )
    body_style = ParagraphStyle(
        name="RepBody", parent=styles["Normal"],
        fontSize=9, leading=13, textColor=DARK, spaceAfter=6
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=18 * mm,
        bottomMargin=14 * mm,
        title=_safe(report.get("title", "Investigation Report")),
        author="Karnataka State Police",
    )

    story = []

    # Header
    story.append(Paragraph("<b>KARNATAKA STATE POLICE</b>", title_style))
    story.append(Paragraph("ANVAYA INVESTIGATION REPORT · OFFICIAL DOSSIER", subtitle_style))
    story.append(Spacer(1, 4 * mm))

    # Meta Table
    title_text = _safe(report.get("title", "Untitled Investigation Report"))
    status_text = _safe(report.get("status", "DRAFT")).upper()
    created_at = _safe(report.get("created_at", datetime.now(timezone.utc).isoformat()))
    report_id = _safe(report.get("id", "REP-001"))

    meta_data = [
        [Paragraph("<b>Report ID:</b>", meta_style), Paragraph(report_id, meta_style),
         Paragraph("<b>Status:</b>", meta_style), Paragraph(status_text, meta_style)],
        [Paragraph("<b>Title:</b>", meta_style), Paragraph(title_text, meta_style),
         Paragraph("<b>Date:</b>", meta_style), Paragraph(created_at[:10], meta_style)],
        [Paragraph("<b>Author:</b>", meta_style), Paragraph(_safe(author_name), meta_style),
         Paragraph("<b>Classification:</b>", meta_style), Paragraph("CONFIDENTIAL / SYNTHETIC", meta_style)],
    ]
    t = Table(meta_data, colWidths=[25*mm, 60*mm, 25*mm, 60*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 6 * mm))

    # Content Sections
    story.append(Paragraph("1. Executive Summary", section_style))
    summary_text = _safe(report.get("summary") or report.get("content") or "This investigation report contains synthetic case analysis compiled via ANVAYA Nexus Intelligence Platform. All facts cited stem from CCTNS-style synthetic FIR records for the KSP Datathon 2026.")
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("2. Case Findings & Evidence Chain", section_style))
    findings = _safe(report.get("findings") or "Preliminary findings confirm pattern alignment across registered FIR records. Suspect timelines and physical evidence custody tags are verified against synthetic station registries.")
    story.append(Paragraph(findings, body_style))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("3. Recommendations & Next Steps", section_style))
    recs = _safe(report.get("recommendations") or "1. Submit charge sheet draft for Supervisory SHO review.\n2. Cross-reference forensic exhibits with district evidence repository.\n3. Human officer verification required prior to formal court submission.")
    story.append(Paragraph(recs, body_style))
    story.append(Spacer(1, 8 * mm))

    # Signature Block
    sig_data = [
        [Paragraph("<b>Investigating Officer</b>", meta_style), Paragraph("<b>Supervisory Reviewer</b>", meta_style)],
        [Paragraph("<br/><br/>_______________________<br/>Signature & Date", meta_style),
         Paragraph("<br/><br/>_______________________<br/>Signature & Stamp", meta_style)]
    ]
    st = Table(sig_data, colWidths=[85*mm, 85*mm])
    st.setStyle(TableStyle([('PADDING', (0,0), (-1,-1), 4)]))
    story.append(st)

    doc.build(story)
    return buffer.getvalue()
