"""Resolve natural-language chat actions without inventing FIR facts."""
from __future__ import annotations

import re
from typing import Any

CASE_TOKEN = re.compile(r"\b(SYN-CASE-\d{4}|SYN-FIR-[A-Z0-9-]+|SYN-CRIME-[A-Z0-9-]+)\b", re.I)

BRIEFING_RE = re.compile(
    r"(shift\s*briefing|daily\s*briefing|my\s*briefing|ಬ್ರೀಫಿಂಗ್|ब्रीफिंग)",
    re.I,
)
TRENDS_RE = re.compile(
    r"(crime\s*trends?|aggregate\s*trends?|recorded\s*crime|ಪ್ರವೃತ್ತಿ|प्रवृत्ति)",
    re.I,
)
PDF_RE = re.compile(
    r"(send\s*(me\s*)?(pdf|dossier)|download\s*(pdf|dossier)|export\s*(pdf|dossier)|dossier\s*pdf|"
    r"pdf\s*ಕಳುಹಿಸಿ|पीडीएफ\s*भेजो|पीडीएफ\s*दो)",
    re.I,
)
DETAILS_RE = re.compile(
    r"(complete\s*details?|full\s*(case|details?|fir)|case\s*360|open\s*case|"
    r"fir\s*details?|ಪೂರ್ಣ\s*ವಿವರ|पूर्ण\s*विवरण)",
    re.I,
)
TRANSCRIPT_RE = re.compile(
    r"(conversation\s*pdf|chat\s*(history|transcript)\s*pdf|export\s*(this\s*)?chat|"
    r"save\s*conversation)",
    re.I,
)
CLUSTER_RE = re.compile(r"(network\s*cluster|candidate\s*cluster|connected\s*cases)", re.I)


def resolve_chat_action(text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return {kind, action?, case_ref?, message?} for chat orchestration."""
    raw = (text or "").strip()
    ctx = context or {}
    case_ref = None
    match = CASE_TOKEN.search(raw)
    if match:
        case_ref = match.group(1).upper()
    else:
        case_ref = ctx.get("case_id") or ctx.get("active_case_id")

    if not raw:
        return {"kind": "query", "action": None, "case_ref": case_ref}

    if BRIEFING_RE.search(raw):
        return {"kind": "action", "action": "BRIEFING", "case_ref": case_ref}
    if TRENDS_RE.search(raw):
        return {"kind": "action", "action": "TRENDS", "case_ref": case_ref}
    if TRANSCRIPT_RE.search(raw):
        return {"kind": "action", "action": "CONVERSATION_PDF", "case_ref": case_ref}
    if PDF_RE.search(raw):
        if not case_ref:
            return {
                "kind": "action",
                "action": "NEED_CASE_FOR_PDF",
                "case_ref": None,
                "message": "Open a case first, or include a case id such as SYN-CASE-0001, then ask me to send the PDF.",
            }
        return {"kind": "action", "action": "DOWNLOAD_PDF", "case_ref": case_ref}
    if DETAILS_RE.search(raw):
        if not case_ref:
            return {
                "kind": "action",
                "action": "NEED_CASE_FOR_DETAILS",
                "case_ref": None,
                "message": "Tell me which case to open (for example SYN-CASE-0001), or open a result first.",
            }
        return {"kind": "action", "action": "OPEN_CASE_360", "case_ref": case_ref}
    if CLUSTER_RE.search(raw):
        if not case_ref:
            return {
                "kind": "action",
                "action": "NEED_CASE_FOR_CLUSTER",
                "case_ref": None,
                "message": "Provide a case id to inspect candidate investigative clusters.",
            }
        return {"kind": "action", "action": "NETWORK_CLUSTERS", "case_ref": case_ref}

    return {"kind": "query", "action": None, "case_ref": case_ref}
