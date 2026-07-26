# Exhibit image brief (user-generated watermarked assets)

Use this brief to create **synthetic placeholder exhibit images** for the ANVAYA Investigation Intelligence Prototype.  
These are **not** real crime-scene photographs and must never look like operational CCTNS evidence.

## Hard rules

- Every image must include a visible watermark: **`SYNTHETIC · DATATHON · NOT EVIDENCE`**
- Prefer abstract diagrams, icons, document mockups, device silhouettes, map sketches — **no real victims, no gore, no identifiable people**.
- Do **not** reuse decorative offence-category SVGs from the UI as exhibits.
- Filenames must match the slots below so regeneration/upload stays deterministic.
- Caption text in the product already discloses “watermarked placeholder”.

## Suggested sizes

| Slot kind | Canvas | Notes |
|---|---|---|
| Photo-style placeholder | 960×640 PNG | Landscape; soft flat illustration |
| Document scan mock | 794×1123 PNG | A4 portrait; stamped DRAFT |
| Device / property | 800×800 PNG | Square object silhouette |

Export as PNG (RGB). Keep file size under ~400 KB where possible.

## Seeded cases / offence context (synthetic)

| Case | Offence (label) | Station vibe | Exhibit slots |
|---|---|---|---|
| SYN-CASE-0001 | Theft / property | Urban PS | EXH-0001-A device photo, EXH-0001-B sketch map |
| SYN-CASE-0002 | Vehicle / property | Highway PS | EXH-0002-A number-plate mock (blurred), EXH-0002-B CCTV still mock |
| SYN-CASE-0003 | Cyber / fraud | City PS | EXH-0003-A phishing-email screenshot mock, EXH-0003-B bank-SMS mock |
| SYN-CASE-0004 | Assault / hurt | Rural PS | EXH-0004-A injury-diagram (medical illustration style), EXH-0004-B scene sketch |
| SYN-CASE-0005 | Missing property | Metro PS | EXH-0005-A jewellery line-drawing, EXH-0005-B receipt mock |

Exact exhibit codes in the DB may differ slightly after regenerate; match on `exhibit_code` / case id when uploading.

## Visual treatment

1. Flat government-portal palette (deep navy `#0B3A5C`, sand `#F4F1EA`, alert amber for DRAFT stamp).
2. Corner ribbon or diagonal band with watermark text.
3. Small footer: `ANVAYA · KSP Datathon 2026 · Synthetic only`.
4. Optional Kannada/Hindi label line is fine if fonts embed cleanly; keep primary caption English for judges.

## Upload / replace path

1. Regenerate or start local backend so `evidence_exhibits` rows exist.
2. Locate exhibit rows for the target case (`exhibit_code`, `mime_type`, `sha256`).
3. Replace `content_blob` / file bytes via your local admin script or a one-off SQL/blob update — **do not** change provenance fields to claim a live source.
4. Recompute SHA-256 of the new PNG and update the `sha256` column to match.
5. Keep `chain_status` as the synthetic custody value already seeded; add custody events only through migrations/generator.
6. Confirm Case 360 → Exhibits shows the image with watermark visible in PDF dossier.

## Acceptance checklist

- [ ] Watermark readable at 100% zoom and in PDF thumbnail.
- [ ] No real faces / real addresses / real phone numbers.
- [ ] MIME remains `image/png` (or documented alternative).
- [ ] Dossier PDF still labels cover **Synthetic Investigation Dossier (DRAFT)**.
- [ ] Decorative offence icons in the chat UI are **unchanged** and unused as exhibit bytes.
