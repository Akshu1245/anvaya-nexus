"""Conversation transcript PDF export (client-supplied redacted turns)."""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


NAVY = colors.HexColor("#0d1b2a")
AMBER = colors.HexColor("#b45309")


def _safe(value: object) -> str:
    text = str(value if value is not None else "")
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, A4[1] - 12 * mm, A4[0], 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(16 * mm, A4[1] - 7 * mm, "ANVAYA · CONVERSATION EXPORT")
    canvas.setFillColor(AMBER)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(A4[0] / 2, A4[1] / 2, "SYNTHETIC DATATHON · NOT OPERATIONAL")
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.setFont("Helvetica", 7)
    canvas.drawString(16 * mm, 6 * mm, "SYNTHETIC PROTOTYPE — HUMAN REVIEW REQUIRED")
    canvas.drawRightString(A4[0] - 16 * mm, 6 * mm, f"Page {doc.page}")
    canvas.restoreState()


def conversation_pdf(turns: list[dict], investigation_title: str, investigation_id: str) -> bytes:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ConvTitle", parent=styles["Title"], fontSize=14, textColor=NAVY, alignment=TA_CENTER, spaceAfter=8))
    styles.add(ParagraphStyle(name="ConvMeta", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#475569"), alignment=TA_CENTER, spaceAfter=10))
    styles.add(ParagraphStyle(name="ConvTurn", parent=styles["Normal"], fontSize=9, leading=12, alignment=TA_LEFT, spaceAfter=6))
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=18 * mm,
        bottomMargin=14 * mm,
        title="ANVAYA Conversation Export",
        author="ANVAYA",
        subject="SYNTHETIC CONVERSATION TRANSCRIPT",
    )
    story = [
        Paragraph("ANVAYA Conversation Export", styles["ConvTitle"]),
        Paragraph(
            f"Investigation {_safe(investigation_id)} · {_safe(investigation_title)} · "
            f"Generated {datetime.now(timezone.utc).isoformat()} · SYNTHETIC ONLY",
            styles["ConvMeta"],
        ),
        Paragraph(
            "Turns are client-supplied and may already be redacted. This export is not a case dossier and cannot file an FIR.",
            styles["ConvMeta"],
        ),
        Spacer(1, 4 * mm),
    ]
    if not turns:
        story.append(Paragraph("No conversation turns were supplied.", styles["ConvTurn"]))
    for index, turn in enumerate(turns[:200], start=1):
        role = _safe(turn.get("role") or "unknown").upper()
        kind = _safe(turn.get("kind") or "text")
        created = _safe(turn.get("created_at") or "")
        text = str(turn.get("text") or "").strip()
        if not text:
            text = str(turn.get("summary") or "").strip()
        text = _safe(text)[:4000]
        story.append(Paragraph(f"<b>{index}. {role}</b> · {kind} · {created}<br/>{text}", styles["ConvTurn"]))
    document.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()
