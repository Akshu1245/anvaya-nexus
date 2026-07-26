# Research-led synthetic retrieval benchmark

## Why this benchmark exists

ANVAYA NEXUS does not claim that police personnel lack an FIR system. Rather, it demonstrates a safer investigator-facing layer for retrieving, understanding and verifying synthetic FIR records across multiple structured fields with source citations and explicit human review.

This is aligned with the public CCTNS objective of collection, storage, retrieval, analysis, transfer and sharing of police information, and with its stated use in investigation and prosecution tracking. It also complements the Department of Justice's examples of case-status search by FIR number, party name, Act and case type, and judgment search by name, Act, section and full text.

- [MHA: CCTNS/ICJS investigation uses](https://www.mha.gov.in/en/divisionofmha/women-safety-division/cctns)
- [MHA: CCTNS scheme evaluation](https://www.mha.gov.in/sites/default/files/IIPA-Report-CCTNS.pdf)
- [Department of Justice: eCourts and case-information search](https://www.doj.gov.in/static/uploads/2025/09/e79785ce6b1515bbd08c42539febc48c.pdf)
- [Department of Justice: eCourts Phase III and Judgment Search](https://www.doj.gov.in/static/uploads/2025/11/541a9be839604312e9383f375022b6d6.pdf)

## What is implemented

The synthetic benchmark contains 24 deliberately selected cases rather than randomly generated examples. It covers FIR, Zero FIR transfer, UDR and petition/enquiry report records, including property, cyber, person-safety, traffic/UDR and administrative-report workflows.

Search combines any of these grounded record fields:

- free-text across crime number, case number, person, offence, status, category, station, court, Act, section and brief facts;
- dedicated filters for crime number, person and role, Act, section, status, case category, gravity, major head and minor head;
- factual shared-person relationships only, with source references, counter-evidence and mandatory human review.

## Safety boundary

All values are fictional. Similarity, shared names and shared stored synthetic person records never establish identity, coordination, guilt, risk or responsibility. The legal labels are synthetic retrieval fixtures, not legal advice. Protected personal attributes and real police/court data are excluded.
