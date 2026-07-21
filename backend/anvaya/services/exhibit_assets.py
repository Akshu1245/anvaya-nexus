"""Deterministic watermarked synthetic exhibit images for the dossier PDF."""
from __future__ import annotations

import hashlib
from io import BytesIO


def render_synthetic_exhibit_png(
    *,
    exhibit_code: str,
    caption: str,
    case_id: str,
    width: int = 640,
    height: int = 400,
) -> bytes:
    """Return a small PNG with a visible SYNTHETIC watermark. No real scene content."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as error:  # pragma: no cover - dependency declared in requirements
        raise RuntimeError("Pillow is required to generate synthetic exhibits") from error

    image = Image.new("RGB", (width, height), color=(236, 242, 245))
    draw = ImageDraw.Draw(image)
    draw.rectangle((12, 12, width - 13, height - 13), outline=(13, 27, 42), width=3)
    draw.rectangle((24, 24, width - 25, 88), fill=(7, 17, 31))
    font = ImageFont.load_default()
    draw.text((36, 36), "ANVAYA SYNTHETIC EXHIBIT", fill=(112, 197, 197), font=font)
    draw.text((36, 56), f"{exhibit_code} · {case_id}", fill=(233, 240, 242), font=font)
    draw.text((36, 120), caption[:72], fill=(13, 27, 42), font=font)
    draw.text((36, 150), "NOT OPERATIONAL EVIDENCE", fill=(185, 28, 28), font=font)
    draw.text((36, 180), "Generated watermarked placeholder for Datathon demo only.", fill=(71, 85, 105), font=font)
    # Diagonal watermark
    for offset in range(-height, width, 90):
        draw.line([(offset, height), (offset + height, 0)], fill=(201, 162, 39), width=1)
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
