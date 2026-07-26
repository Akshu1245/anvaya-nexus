"""Professional multi-page synthetic investigation dossier PDF renderer."""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


NAVY = colors.HexColor("#0d1b2a")
TEAL = colors.HexColor("#1f8a8a")
AMBER = colors.HexColor("#b45309")
LIGHT = colors.HexColor("#f4f7f8")
_BODY_FONT = "Helvetica"
_BODY_FONT_BOLD = "Helvetica-Bold"


def _register_unicode_font() -> tuple[str, str]:
    global _BODY_FONT, _BODY_FONT_BOLD
    candidates = [
        Path(r"C:\Windows\Fonts\Nirmala.ttf"),
        Path(r"C:\Windows\Fonts\NotoSans-Regular.ttf"),
        Path(r"C:\Windows\Fonts\seguiemj.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("AnvayaUnicode", str(path)))
            _BODY_FONT = "AnvayaUnicode"
            _BODY_FONT_BOLD = "AnvayaUnicode"
            return _BODY_FONT, _BODY_FONT_BOLD
        except Exception:
            continue
    return _BODY_FONT, _BODY_FONT_BOLD


_register_unicode_font()


def _safe(value: object) -> str:
    text = str(value if value is not None else "Not represented")
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="DossierTitle", parent=styles["Title"], fontName=_BODY_FONT_BOLD, fontSize=18, textColor=NAVY, spaceAfter=8, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="DossierSubtitle", parent=styles["Normal"], fontName=_BODY_FONT, fontSize=10, textColor=TEAL, alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="SectionHead", parent=styles["Heading2"], fontName=_BODY_FONT_BOLD, fontSize=12, textColor=NAVY, spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name="Claim", parent=styles["Normal"], fontName=_BODY_FONT, fontSize=9, leading=12, alignment=TA_JUSTIFY, spaceAfter=2))
    styles.add(ParagraphStyle(name="Meta", parent=styles["Normal"], fontName=_BODY_FONT, fontSize=8, textColor=colors.HexColor("#475569"), spaceAfter=2))
    styles.add(ParagraphStyle(name="Banner", parent=styles["Normal"], fontName=_BODY_FONT_BOLD, fontSize=8, textColor=AMBER, alignment=TA_CENTER, spaceAfter=8))
    styles.add(ParagraphStyle(name="FooterNote", parent=styles["Normal"], fontName=_BODY_FONT, fontSize=7, textColor=colors.HexColor("#64748b"), alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="TOCItem", parent=styles["Normal"], fontName=_BODY_FONT, fontSize=9, leading=12, leftIndent=8))
    return styles


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, A4[1] - 14 * mm, A4[0], 14 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont(_BODY_FONT_BOLD, 8)
    canvas.drawString(18 * mm, A4[1] - 8 * mm, "ANVAYA · SYNTHETIC INVESTIGATION DOSSIER")
    canvas.setFont(_BODY_FONT, 7)
    canvas.drawRightString(A4[0] - 18 * mm, A4[1] - 8 * mm, "DRAFT · HUMAN REVIEW REQUIRED")
    canvas.setFillColor(LIGHT)
    canvas.rect(0, 0, A4[0], 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.setFont(_BODY_FONT, 7)
    canvas.drawString(18 * mm, 5 * mm, "SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE")
    canvas.drawRightString(A4[0] - 18 * mm, 5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def grounded_brief_pdf(brief: dict, investigation_title: str) -> bytes:
    styles = _styles()
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=20 * mm,
        bottomMargin=16 * mm,
        title="ANVAYA Synthetic Investigation Dossier",
        author="ANVAYA",
        subject="DRAFT SYNTHETIC HUMAN REVIEW REQUIRED",
        keywords=",".join(
            filter(
                None,
                ["ANVAYA", "SYNTHETIC", "DRAFT"]
                + [str(exh.get("exhibit_code") or "") for exh in (brief.get("exhibits") or [])[:12]],
            )
        ),
    )
    story = []
    case_id = brief.get("case_id") or "Unknown case"
    snapshot = brief.get("case_snapshot") or {}
    generated = brief.get("generated_at") or datetime.now(timezone.utc).isoformat()

    story.append(Paragraph("ANVAYA", styles["DossierSubtitle"]))
    story.append(Paragraph(_safe(brief.get("dossier_title") or "Synthetic Investigation Dossier (DRAFT)"), styles["DossierTitle"]))
    story.append(Paragraph("DRAFT · HUMAN REVIEW REQUIRED · SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE", styles["Banner"]))
    cover_label = ParagraphStyle(name="CoverLabel", parent=styles["Meta"], fontName=_BODY_FONT_BOLD, fontSize=8, textColor=NAVY, spaceAfter=0)
    cover_value = ParagraphStyle(name="CoverValue", parent=styles["Meta"], fontName=_BODY_FONT, fontSize=8, textColor=NAVY, spaceAfter=0)
    cover_rows = [
        [Paragraph("Investigation", cover_label), Paragraph(_safe(investigation_title), cover_value)],
        [Paragraph("Case ID", cover_label), Paragraph(_safe(case_id), cover_value)],
        [Paragraph("FIR / Crime / Case No.", cover_label), Paragraph(f"{_safe(snapshot.get('fir_number'))} / {_safe(snapshot.get('crime_number'))} / {_safe(snapshot.get('case_number'))}", cover_value)],
        [Paragraph("Status", cover_label), Paragraph(_safe(snapshot.get("status")), cover_value)],
        [Paragraph("Offence", cover_label), Paragraph(_safe(snapshot.get("offence")), cover_value)],
        [Paragraph("Station / district", cover_label), Paragraph(f"{_safe(snapshot.get('station'))} / {_safe(snapshot.get('district'))}", cover_value)],
        [Paragraph("Registering officer", cover_label), Paragraph(_safe(snapshot.get("registering_officer")), cover_value)],
        [Paragraph("Investigating officer (IO)", cover_label), Paragraph(_safe(snapshot.get("investigating_officer")), cover_value)],
        [Paragraph("Registered at", cover_label), Paragraph(_safe(snapshot.get("registered_at")), cover_value)],
        [Paragraph("Generated at (UTC)", cover_label), Paragraph(_safe(generated), cover_value)],
        [Paragraph("Jurisdiction", cover_label), Paragraph(_safe((brief.get("policy") or {}).get("jurisdiction_state")), cover_value)],
        [Paragraph("Masking", cover_label), Paragraph(_safe(((brief.get("policy") or {}).get("masking") or {}).get("level")), cover_value)],
        [Paragraph("Selected sources", cover_label), Paragraph(_safe(", ".join((brief.get("policy") or {}).get("selected_sources") or []) or "None"), cover_value)],
    ]
    cover = Table(cover_rows, colWidths=[45 * mm, 125 * mm])
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("TEXTCOLOR", (0, 0), (-1, -1), NAVY),
        ("FONTNAME", (0, 0), (0, -1), _BODY_FONT_BOLD),
        ("FONTNAME", (1, 0), (1, -1), _BODY_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(cover)
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        "This dossier is assembled only from policy-filtered synthetic FIR records. "
        "It is not a BNSS/CrPC charge-sheet and has no live KSP/CCTNS connection.",
        styles["Claim"],
    ))
    story.append(PageBreak())

    sections = brief.get("sections") or {}
    story.append(Paragraph("Contents", styles["SectionHead"]))
    for index, heading in enumerate(sections.keys(), start=1):
        story.append(Paragraph(f"{index}. {_safe(heading.replace('_', ' ').title())}", styles["TOCItem"]))
    story.append(PageBreak())

    for heading, claims in sections.items():
        block = [Paragraph(_safe(heading.replace("_", " ").title()), styles["SectionHead"])]
        for claim in claims or []:
            text = _safe(claim.get("text"))
            sources = ", ".join(_safe(item) for item in claim.get("source_record_ids") or []) or "No source reference"
            state = _safe(claim.get("verification_state") or "human review required")
            block.append(Paragraph(f"• {text}", styles["Claim"]))
            block.append(Paragraph(f"Evidence: {sources} · {state}", styles["Meta"]))
        story.append(KeepTogether(block))

    exhibits = brief.get("exhibits") or []
    if exhibits:
        story.append(Paragraph("Exhibit Gallery (Synthetic Watermarked Placeholders)", styles["SectionHead"]))
        story.append(Paragraph(
            "These images are generated synthetic placeholders with visible watermarks. "
            "They are not operational crime-scene photographs and must not be treated as exhibits for court use.",
            styles["Meta"],
        ))
        for exh in exhibits:
            custody = "; ".join(
                f"{_safe(event.get('event_type'))}@{_safe(event.get('event_at'))}"
                for event in (exh.get("custody_events") or [])
            ) or "No custody events"
            caption = (
                f"{_safe(exh.get('exhibit_code'))} · {_safe(exh.get('exhibit_kind') or 'untyped')} · {_safe(exh.get('caption'))} · "
                f"SHA-256 {_safe(exh.get('sha256'))} · chain {_safe(exh.get('chain_status'))} · "
                f"custody {custody} · source {_safe(exh.get('source_record_id'))}"
            )
            rows = [[Paragraph(caption, styles["Meta"])]]
            blob = exh.get("content_blob")
            if blob and not exh.get("thumbnail_masked"):
                try:
                    image = Image(BytesIO(blob), width=70 * mm, height=44 * mm, kind="proportional")
                    rows.append([image])
                except Exception:
                    rows.append([Paragraph("Exhibit image could not be rendered.", styles["Meta"])])
            elif exh.get("thumbnail_masked"):
                rows.append([Paragraph("Exhibit thumbnail masked by policy.", styles["Meta"])])
            else:
                rows.append([Paragraph("Exhibit image not available in this render.", styles["Meta"])])
            table = Table(rows, colWidths=[170 * mm])
            table.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, TEAL),
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(table)
            story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("Limitations", styles["SectionHead"]))
    for limitation in brief.get("limitations") or []:
        story.append(Paragraph(f"• {_safe(limitation)}", styles["Claim"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("No source, no factual claim. Decorative offence icons are not exhibits.", styles["FooterNote"]))

    document.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()
