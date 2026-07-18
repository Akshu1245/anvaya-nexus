from __future__ import annotations

import hashlib
import html
import json
import uuid
from datetime import datetime, timedelta, timezone

from backend.anvaya.api.errors import ApiError


def _checksum(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _source_record(conn, external_id: str, payload: dict, timestamp: str) -> str:
    record_id = f"SYN-SR-OFFICIAL-{external_id}"
    conn.execute(
        """INSERT OR IGNORE INTO source_records
        (id,source_system_id,external_id,version,source_updated_at,imported_at,access_class,
         reliability_role,freshness_state,checksum,payload_json)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            record_id,
            "CCTNS_REPLICA",
            external_id,
            "FIR-ER-1.0",
            timestamp,
            timestamp,
            "RESTRICTED",
            "Official FIR schema synthetic fixture",
            "Fresh",
            _checksum(payload),
            json.dumps(payload, sort_keys=True),
        ),
    )
    return record_id


def seed_official_fir_fixture(repository) -> dict:
    """Seed a curated, synthetic FIR retrieval benchmark.

    Each fixture represents a legitimate record-retrieval or record-assurance workflow.
    Names, stations, locations and facts are fictional; neither the fixture nor its
    legal labels are suitable for operational or legal decisions.
    """
    conn = repository.connection
    now = datetime(2026, 7, 18, 9, 0, tzinfo=timezone.utc)
    ts = now.isoformat()
    units = [
        ("FIR-UNIT-001", "04430006", "Synthetic Central Police Station", "POLICE_STATION", "SYN-DST-01", "KA"),
        ("FIR-UNIT-002", "04430007", "Synthetic North Police Station", "POLICE_STATION", "SYN-DST-01", "KA"),
        ("FIR-UNIT-003", "04430008", "Synthetic East Police Station", "POLICE_STATION", "SYN-DST-02", "KA"),
    ]
    officers = [
        ("FIR-OFF-001", "EMP-1001", "Synthetic Officer One", "INSPECTOR", "SHO", "FIR-UNIT-001"),
        ("FIR-OFF-002", "EMP-1002", "Synthetic Officer Two", "SUB_INSPECTOR", "IO", "FIR-UNIT-002"),
        ("FIR-OFF-003", "EMP-1003", "Synthetic Officer Three", "INSPECTOR", "IO", "FIR-UNIT-003"),
    ]
    courts = [("FIR-COURT-001", "COURT-01", "Synthetic District Court", "SYN-DST-01"),
              ("FIR-COURT-002", "COURT-02", "Synthetic Sessions Court", "SYN-DST-02")]
    acts = [("FIR-ACT-BNS", "BNS", "Synthetic BNS reference - not legal advice", "BNS"),
            ("FIR-ACT-IT", "IT_ACT", "Synthetic information-technology reference - not legal advice", "IT Act"),
            ("FIR-ACT-REPORT", "SPECIAL_REPORT", "Synthetic report category reference", "Special report")]
    sections = [
        ("FIR-SEC-303", "FIR-ACT-BNS", "303", "Synthetic theft-retrieval fixture"),
        ("FIR-SEC-309", "FIR-ACT-BNS", "309", "Synthetic robbery-retrieval fixture"),
        ("FIR-SEC-318", "FIR-ACT-BNS", "318", "Synthetic deception-retrieval fixture"),
        ("FIR-SEC-324", "FIR-ACT-BNS", "324", "Synthetic property-damage retrieval fixture"),
        ("FIR-SEC-356", "FIR-ACT-BNS", "356", "Synthetic intimidation-retrieval fixture"),
        ("FIR-SEC-66C", "FIR-ACT-IT", "66C", "Synthetic digital-identity retrieval fixture"),
        ("FIR-SEC-66D", "FIR-ACT-IT", "66D", "Synthetic digital-deception retrieval fixture"),
        ("FIR-SEC-UDR", "FIR-ACT-REPORT", "SYN-UDR", "Synthetic UDR retrieval fixture"),
        ("FIR-SEC-ZERO", "FIR-ACT-REPORT", "SYN-ZERO", "Synthetic Zero FIR transfer fixture"),
        ("FIR-SEC-PAR", "FIR-ACT-REPORT", "SYN-PAR", "Synthetic petition/report fixture"),
        ("FIR-SEC-MISSING", "FIR-ACT-REPORT", "SYN-MISSING", "Synthetic missing-person retrieval fixture"),
    ]
    act_ids = {row[1]: row[0] for row in acts}
    section_ids = {(act_code, code): section_id for section_id, act_id, code, _ in sections
                   for act_code, mapped_id in act_ids.items() if mapped_id == act_id}
    for row in units:
        sr = _source_record(conn, row[0], {"UnitID": row[0], "UnitCode": row[1], "UnitName": row[2]}, ts)
        conn.execute("INSERT OR IGNORE INTO police_units VALUES (?,?,?,?,?,?,?,?)", (*row, 1, sr))
    for row in officers:
        sr = _source_record(conn, row[0], {"EmployeeID": row[0], "EmployeeCode": row[1]}, ts)
        conn.execute("INSERT OR IGNORE INTO police_employees VALUES (?,?,?,?,?,?,?,?)", (*row, 1, sr))
    for row in courts:
        sr = _source_record(conn, row[0], {"CourtID": row[0], "CourtCode": row[1]}, ts)
        conn.execute("INSERT OR IGNORE INTO courts VALUES (?,?,?,?,?,?)", (*row, 1, sr))
    for row in acts:
        sr = _source_record(conn, row[0], {"ActCode": row[1], "Description": row[2]}, ts)
        conn.execute("INSERT OR IGNORE INTO legal_acts VALUES (?,?,?,?,?,?)", (*row, 1, sr))
    for row in sections:
        act_code = next(code for code, act_id in act_ids.items() if act_id == row[1])
        sr = _source_record(conn, row[0], {"ActCode": act_code, "SectionCode": row[2]}, ts)
        conn.execute("INSERT OR IGNORE INTO legal_sections VALUES (?,?,?,?,?,?)", (*row, 1, sr))

    def case(case_id, crime, offence, status, category, gravity, major, minor, days_ago, station, officer,
             court, act, section, people, facts, *, arrest=None, chargesheet=False):
        incident = now - timedelta(days=days_ago)
        return {"id": case_id, "fir": crime[-9:], "crime": crime, "offence": offence, "status": status,
                "category": category, "gravity": gravity, "major": major, "minor": minor,
                "incident": incident, "registered": incident + timedelta(hours=2), "station": station,
                "officer": officer, "court": court, "act": act, "section": section, "people": people,
                "facts": facts, "lat": 15.10 + (days_ago % 8) / 100, "lon": 75.60 + (days_ago % 8) / 100,
                "arrest": arrest, "chargesheet": chargesheet}

    cases = [
        case("FIR-CASE-0001", "104430006202600001", "THEFT", "UNRESOLVED", "FIR", "NON_HEINOUS", "PROPERTY_OFFENCE", "THEFT", 10, "FIR-UNIT-001", "FIR-OFF-001", "FIR-COURT-001", "BNS", "303", [("COMPLAINANT", "Synthetic Complainant One"), ("VICTIM", "Synthetic Victim One"), ("ACCUSED", "Synthetic Accused Alpha")], "Locked-premises property theft benchmark; status-to-chargesheet assurance review.", chargesheet=True),
        case("FIR-CASE-0002", "104430007202600002", "ROBBERY", "CHARGESHEETED", "FIR", "HEINOUS", "PROPERTY_OFFENCE", "ROBBERY", 6, "FIR-UNIT-002", "FIR-OFF-002", "FIR-COURT-001", "BNS", "309", [("ACCUSED", "Synthetic Accused Alpha"), ("COMPLAINANT", "Synthetic Accused Beta")], "Robbery benchmark with a factual shared-person record and arrest event.", arrest=("ARREST", "Synthetic Accused Alpha"), chargesheet=True),
        case("FIR-CASE-0003", "104430006202600003", "MISSING_PERSON_REPORT", "UNDER_INVESTIGATION", "FIR", "SENSITIVE", "PERSON_SAFETY", "MISSING_PERSON", 18, "FIR-UNIT-001", "FIR-OFF-001", "FIR-COURT-001", "SPECIAL_REPORT", "SYN-MISSING", [("COMPLAINANT", "Synthetic Reporter Mira"), ("VICTIM", "Synthetic Missing Person One")], "Missing-person report benchmark: retrieve by reporter, status, and category."),
        case("FIR-CASE-0004", "804430007202600004", "ZERO_FIR_TRANSFER", "TRANSFERRED", "ZERO_FIR", "NON_HEINOUS", "JURISDICTION", "ZERO_FIR", 20, "FIR-UNIT-002", "FIR-OFF-002", "FIR-COURT-001", "SPECIAL_REPORT", "SYN-ZERO", [("COMPLAINANT", "Synthetic Reporter Mira"), ("VICTIM", "Synthetic Victim Transfer")], "Zero FIR transfer benchmark: show source station and transfer status without altering jurisdiction."),
        case("FIR-CASE-0005", "104430006202600005", "CYBER_FINANCIAL_FRAUD", "UNDER_INVESTIGATION", "FIR", "NON_HEINOUS", "CYBER_CRIME", "DIGITAL_DECEPTION", 15, "FIR-UNIT-001", "FIR-OFF-001", "FIR-COURT-001", "IT_ACT", "66D", [("COMPLAINANT", "Synthetic Reporter Kavya"), ("VICTIM", "Synthetic Account Holder One")], "Digital-deception benchmark: retrieve by Act, section, reporter, and offence family."),
        case("FIR-CASE-0006", "104430007202600006", "DIGITAL_IDENTITY_MISUSE", "UNDER_INVESTIGATION", "FIR", "NON_HEINOUS", "CYBER_CRIME", "IDENTITY_MISUSE", 14, "FIR-UNIT-002", "FIR-OFF-002", "FIR-COURT-001", "IT_ACT", "66C", [("COMPLAINANT", "Synthetic Reporter Kavya"), ("VICTIM", "Synthetic Account Holder Two")], "Digital identity-misuse benchmark sharing an explicitly stored reporter record, requiring human review."),
        case("FIR-CASE-0007", "104430006202600007", "CHAIN_SNATCHING", "UNDER_INVESTIGATION", "FIR", "SERIOUS", "PROPERTY_OFFENCE", "SNATCHING", 25, "FIR-UNIT-001", "FIR-OFF-001", "FIR-COURT-001", "BNS", "309", [("VICTIM", "Synthetic Victim Chain One"), ("ACCUSED", "Synthetic Accused Gamma")], "Street-property offence benchmark with an arrest record.", arrest=("ARREST", "Synthetic Accused Gamma")),
        case("FIR-CASE-0008", "104430007202600008", "HOUSEBREAKING", "CHARGESHEETED", "FIR", "SERIOUS", "PROPERTY_OFFENCE", "HOUSEBREAKING", 32, "FIR-UNIT-002", "FIR-OFF-002", "FIR-COURT-001", "BNS", "303", [("COMPLAINANT", "Synthetic Householder One"), ("ACCUSED", "Synthetic Accused Gamma")], "Housebreaking benchmark: find prior factual appearance of an explicitly shared synthetic person.", chargesheet=True),
        case("FIR-CASE-0009", "304430006202600009", "ROAD_TRAFFIC_UDR", "CLOSED", "UDR", "NON_HEINOUS", "UNNATURAL_DEATH_REPORT", "ROAD_TRAFFIC", 40, "FIR-UNIT-001", "FIR-OFF-001", "FIR-COURT-001", "SPECIAL_REPORT", "SYN-UDR", [("COMPLAINANT", "Synthetic Reporter Road One"), ("VICTIM", "Synthetic Road Victim One")], "UDR benchmark: retrieve non-FIR report category separately from offences."),
        case("FIR-CASE-0010", "304430007202600010", "UNNATURAL_DEATH_REPORT", "UNDER_REVIEW", "UDR", "SENSITIVE", "UNNATURAL_DEATH_REPORT", "UNNATURAL_DEATH", 39, "FIR-UNIT-002", "FIR-OFF-002", "FIR-COURT-001", "SPECIAL_REPORT", "SYN-UDR", [("COMPLAINANT", "Synthetic Reporter Road One"), ("VICTIM", "Synthetic UDR Subject One")], "UDR review benchmark sharing only a factual reporter record; no inference is made."),
        case("FIR-CASE-0011", "104430006202600011", "ASSAULT_COMPLAINT", "UNDER_INVESTIGATION", "FIR", "SERIOUS", "PERSON_OFFENCE", "ASSAULT", 22, "FIR-UNIT-001", "FIR-OFF-001", "FIR-COURT-001", "BNS", "318", [("COMPLAINANT", "Synthetic Reporter Nila"), ("VICTIM", "Synthetic Victim Safety One")], "Person-offence benchmark focused on status and source-cited record verification."),
        case("FIR-CASE-0012", "104430007202600012", "ONLINE_IMPERSONATION", "UNDER_INVESTIGATION", "FIR", "NON_HEINOUS", "CYBER_CRIME", "IMPERSONATION", 17, "FIR-UNIT-002", "FIR-OFF-002", "FIR-COURT-001", "IT_ACT", "66C", [("COMPLAINANT", "Synthetic Reporter Nila"), ("VICTIM", "Synthetic Digital Victim One")], "Online impersonation benchmark: retrieve by person, IT Act section, and investigation status."),
        case("FIR-CASE-0013", "104430006202600013", "EXTORTION_COMPLAINT", "UNDER_INVESTIGATION", "FIR", "SERIOUS", "PROPERTY_OFFENCE", "EXTORTION", 27, "FIR-UNIT-001", "FIR-OFF-001", "FIR-COURT-001", "BNS", "356", [("COMPLAINANT", "Synthetic Business Owner One"), ("ACCUSED", "Synthetic Accused Delta")], "Extortion complaint benchmark: retrieve a person role alongside a legal section."),
        case("FIR-CASE-0014", "104430007202600014", "VEHICLE_THEFT", "PROPERTY_RECOVERED", "FIR", "NON_HEINOUS", "PROPERTY_OFFENCE", "VEHICLE_THEFT", 28, "FIR-UNIT-002", "FIR-OFF-002", "FIR-COURT-001", "BNS", "303", [("COMPLAINANT", "Synthetic Vehicle Owner One"), ("ACCUSED", "Synthetic Accused Delta")], "Vehicle-theft benchmark with a factual shared accused record and property-recovery status.", arrest=("SURRENDER", "Synthetic Accused Delta")),
        case("FIR-CASE-0015", "104430006202600015", "PROPERTY_DAMAGE", "UNDER_INVESTIGATION", "FIR", "NON_HEINOUS", "PROPERTY_OFFENCE", "DAMAGE", 12, "FIR-UNIT-001", "FIR-OFF-001", "FIR-COURT-001", "BNS", "324", [("COMPLAINANT", "Synthetic Property Manager One"), ("VICTIM", "Synthetic Property Owner One")], "Property-damage benchmark: keyword, station, and status retrieval."),
        case("FIR-CASE-0016", "304430007202600016", "UNIDENTIFIED_PROPERTY_UDR", "CLOSED", "UDR", "NON_HEINOUS", "PROPERTY_REPORT", "UNIDENTIFIED_PROPERTY", 45, "FIR-UNIT-002", "FIR-OFF-002", "FIR-COURT-001", "SPECIAL_REPORT", "SYN-UDR", [("COMPLAINANT", "Synthetic Finder One")], "Unidentified-property report benchmark; no identity or ownership conclusion is generated."),
        case("FIR-CASE-0017", "104430006202600017", "CHEATING_COMPLAINT", "UNDER_INVESTIGATION", "FIR", "NON_HEINOUS", "PROPERTY_OFFENCE", "DECEPTION", 30, "FIR-UNIT-001", "FIR-OFF-001", "FIR-COURT-001", "BNS", "318", [("COMPLAINANT", "Synthetic Trader One"), ("ACCUSED", "Synthetic Accused Epsilon")], "Deception complaint benchmark for Act-and-section search."),
        case("FIR-CASE-0018", "104430007202600018", "ROBBERY", "CHARGESHEETED", "FIR", "HEINOUS", "PROPERTY_OFFENCE", "ROBBERY", 55, "FIR-UNIT-002", "FIR-OFF-002", "FIR-COURT-001", "BNS", "309", [("COMPLAINANT", "Synthetic Reporter Robbery Two"), ("ACCUSED", "Synthetic Accused Epsilon")], "Second robbery benchmark enabling evidence-led retrieval of a stored repeat person record.", chargesheet=True),
        case("FIR-CASE-0019", "104430006202600019", "MISSING_PROPERTY", "UNDER_INVESTIGATION", "FIR", "NON_HEINOUS", "PROPERTY_OFFENCE", "MISSING_PROPERTY", 16, "FIR-UNIT-001", "FIR-OFF-001", "FIR-COURT-001", "BNS", "303", [("COMPLAINANT", "Synthetic Student One"), ("VICTIM", "Synthetic Student One")], "Missing-property benchmark with the same recorded person in two roles in one case."),
        case("FIR-CASE-0020", "404430007202600020", "PETITION_ENQUIRY_REPORT", "REFERRED", "PAR", "NON_HEINOUS", "ADMINISTRATIVE_REPORT", "PETITION", 8, "FIR-UNIT-002", "FIR-OFF-002", "FIR-COURT-001", "SPECIAL_REPORT", "SYN-PAR", [("COMPLAINANT", "Synthetic Petitioner One")], "Petition/enquiry report benchmark: category-first filtering without treating it as an FIR."),
        case("FIR-CASE-0021", "104430008202600021", "CYBER_FINANCIAL_FRAUD", "UNDER_INVESTIGATION", "FIR", "NON_HEINOUS", "CYBER_CRIME", "DIGITAL_DECEPTION", 11, "FIR-UNIT-003", "FIR-OFF-003", "FIR-COURT-002", "IT_ACT", "66D", [("COMPLAINANT", "Synthetic Reporter Kavya"), ("VICTIM", "Synthetic Account Holder Three")], "Cross-station cyber-fraud benchmark: retrieve all records for a reporter without asserting a relationship."),
        case("FIR-CASE-0022", "304430008202600022", "UNNATURAL_DEATH_REPORT", "CLOSED", "UDR", "SENSITIVE", "UNNATURAL_DEATH_REPORT", "UNNATURAL_DEATH", 62, "FIR-UNIT-003", "FIR-OFF-003", "FIR-COURT-002", "SPECIAL_REPORT", "SYN-UDR", [("COMPLAINANT", "Synthetic Reporter UDR Two"), ("VICTIM", "Synthetic UDR Subject Two")], "Closed UDR benchmark: status and category retrieval for record review."),
        case("FIR-CASE-0023", "104430008202600023", "PROPERTY_DAMAGE", "UNDER_INVESTIGATION", "FIR", "NON_HEINOUS", "PROPERTY_OFFENCE", "DAMAGE", 7, "FIR-UNIT-003", "FIR-OFF-003", "FIR-COURT-002", "BNS", "324", [("COMPLAINANT", "Synthetic Property Manager One"), ("ACCUSED", "Synthetic Accused Zeta")], "Cross-station property-damage benchmark sharing a factual complainant record."),
        case("FIR-CASE-0024", "104430008202600024", "DIGITAL_IDENTITY_MISUSE", "UNDER_INVESTIGATION", "FIR", "NON_HEINOUS", "CYBER_CRIME", "IDENTITY_MISUSE", 5, "FIR-UNIT-003", "FIR-OFF-003", "FIR-COURT-002", "IT_ACT", "66C", [("COMPLAINANT", "Synthetic Reporter Digital Two"), ("VICTIM", "Synthetic Digital Victim Two")], "Digital identity-misuse benchmark for full-text and section retrieval."),
    ]
    person_ids: dict[str, str] = {}
    role_rows: list[tuple[str, str, str, str, int]] = []
    for item in cases:
        sr = _source_record(conn, item["id"], {"CaseMasterID": item["id"], "CrimeNo": item["crime"], "SyntheticBenchmark": True}, ts)
        conn.execute("INSERT OR IGNORE INTO cases VALUES (?,?,?,?,?,?,?,?,?,?)", (item["id"], item["fir"], item["crime"], item["station"], "SYN-DST-01", item["offence"], item["incident"].isoformat(), item["registered"].isoformat(), item["status"], sr))
        conn.execute("""INSERT OR IGNORE INTO fir_case_details (case_id,case_category_code,gravity_code,crime_major_head,crime_minor_head,court_id,registering_officer_id,incident_from_at,incident_to_at,information_received_at,latitude,longitude,brief_facts,source_record_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (item["id"], item["category"], item["gravity"], item["major"], item["minor"], item["court"], item["officer"], item["incident"].isoformat(), (item["incident"] + timedelta(hours=1)).isoformat(), (item["incident"] + timedelta(hours=2)).isoformat(), item["lat"], item["lon"], item["facts"], sr))
        for order, (role, name) in enumerate(item["people"], start=1):
            if name not in person_ids:
                person_id = f"FIR-PER-{len(person_ids) + 1:03d}"
                person_ids[name] = person_id
                person_sr = _source_record(conn, person_id, {"PersonID": person_id, "Name": name, "SyntheticBenchmark": True}, ts)
                conn.execute("INSERT OR IGNORE INTO persons VALUES (?,?,?,?,?,?)", (person_id, name, 1980 + len(person_ids) % 24, "Synthetic restricted address", "SYNTHETIC_OFFICIAL_FIXTURE", person_sr))
            role_rows.append((f"FIR-ROLE-{len(role_rows) + 1:03d}", item["id"], person_ids[name], role, order))
    for row in role_rows:
        sr = _source_record(conn, row[0], {"CaseMasterID": row[1], "PersonID": row[2], "Role": row[3]}, ts)
        conn.execute("INSERT OR IGNORE INTO case_person_roles VALUES (?,?,?,?,?,?)", (*row, sr))
    for index, item in enumerate(cases, start=1):
        row = (f"FIR-LAW-{index:03d}", item["id"], act_ids[item["act"]], section_ids[(item["act"], item["section"])], 1, 1)
        sr = _source_record(conn, row[0], {"CaseMasterID": row[1], "SectionID": row[3]}, ts)
        conn.execute("INSERT OR IGNORE INTO case_legal_sections VALUES (?,?,?,?,?,?,?)", (*row, sr))
        if item["arrest"]:
            event_type, person_name = item["arrest"]
            event_id = f"FIR-ARR-{index:03d}"; arrest_sr = _source_record(conn, event_id, {"CaseMasterID": item["id"], "AccusedMasterID": person_ids[person_name]}, ts)
            conn.execute("INSERT OR IGNORE INTO arrest_surrender_events VALUES (?,?,?,?,?,?,?,?,?,?,?)", (event_id, item["id"], person_ids[person_name], event_type, (item["registered"] + timedelta(days=1)).isoformat(), "KA", "SYN-DST-01", item["station"], item["officer"], item["court"], arrest_sr))
        if item["chargesheet"]:
            cs_id = f"FIR-CS-{index:03d}"; cs_sr = _source_record(conn, cs_id, {"CaseMasterID": item["id"], "FinalReportType": "CHARGESHEET"}, ts)
            conn.execute("INSERT OR IGNORE INTO chargesheets VALUES (?,?,?,?,?,?)", (cs_id, item["id"], (item["registered"] + timedelta(days=3)).isoformat(), "CHARGESHEET", "FILED", cs_sr))
    conn.commit()
    return official_fir_counts(repository)


def official_fir_counts(repository) -> dict:
    tables = (
        "fir_case_details", "case_person_roles", "legal_acts", "legal_sections", "case_legal_sections",
        "police_units", "police_employees", "courts", "arrest_surrender_events", "chargesheets",
    )
    return {table: int(repository.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in tables}


def search_official_cases(repository, *, crime_no: str | None = None, case_no: str | None = None,
                          person_name: str | None = None, role: str | None = None,
                          act: str | None = None, section: str | None = None,
                          unit_id: str | None = None, court_id: str | None = None,
                          status: str | None = None, category: str | None = None,
                          gravity: str | None = None, major_head: str | None = None,
                          minor_head: str | None = None, q: str | None = None,
                          limit: int = 25, offset: int = 0) -> list[dict]:
    where = ["f.case_id IS NOT NULL"]
    args: list[object] = []
    if crime_no:
        where.append("c.crime_number LIKE ?"); args.append(f"%{crime_no}%")
    if case_no:
        where.append("c.fir_number LIKE ?"); args.append(f"%{case_no}%")
    if unit_id:
        where.append("c.station_id=?"); args.append(unit_id)
    if court_id:
        where.append("f.court_id=?"); args.append(court_id)
    if status:
        where.append("UPPER(c.status) LIKE UPPER(?)"); args.append(f"%{status}%")
    if category:
        where.append("UPPER(f.case_category_code) LIKE UPPER(?)"); args.append(f"%{category}%")
    if gravity:
        where.append("UPPER(COALESCE(f.gravity_code,'')) LIKE UPPER(?)"); args.append(f"%{gravity}%")
    if major_head:
        where.append("UPPER(COALESCE(f.crime_major_head,'')) LIKE UPPER(?)"); args.append(f"%{major_head}%")
    if minor_head:
        where.append("UPPER(COALESCE(f.crime_minor_head,'')) LIKE UPPER(?)"); args.append(f"%{minor_head}%")
    if person_name:
        where.append("EXISTS (SELECT 1 FROM case_person_roles r JOIN persons p ON p.id=r.person_id WHERE r.case_id=c.id AND p.display_name LIKE ?" + (" AND r.role_type=?" if role else "") + ")")
        args.append(f"%{person_name}%")
        if role: args.append(role)
    elif role:
        where.append("EXISTS (SELECT 1 FROM case_person_roles r WHERE r.case_id=c.id AND r.role_type=?)"); args.append(role)
    if act:
        where.append("EXISTS (SELECT 1 FROM case_legal_sections cl JOIN legal_acts a ON a.id=cl.act_id WHERE cl.case_id=c.id AND (a.act_code LIKE ? OR a.short_name LIKE ?))")
        args.extend((f"%{act}%", f"%{act}%"))
    if section:
        where.append("EXISTS (SELECT 1 FROM case_legal_sections cl JOIN legal_sections s ON s.id=cl.section_id WHERE cl.case_id=c.id AND s.section_code LIKE ?)")
        args.append(f"%{section}%")
    if q:
        like = f"%{q}%"
        where.append("""(c.crime_number LIKE ? OR c.fir_number LIKE ? OR c.offence LIKE ? OR c.status LIKE ?
            OR f.case_category_code LIKE ? OR COALESCE(f.gravity_code,'') LIKE ?
            OR COALESCE(f.crime_major_head,'') LIKE ? OR COALESCE(f.crime_minor_head,'') LIKE ?
            OR COALESCE(f.brief_facts,'') LIKE ? OR EXISTS (SELECT 1 FROM police_units u WHERE u.id=c.station_id AND u.name LIKE ?)
            OR EXISTS (SELECT 1 FROM courts ct WHERE ct.id=f.court_id AND ct.name LIKE ?)
            OR EXISTS (SELECT 1 FROM case_person_roles r JOIN persons p ON p.id=r.person_id WHERE r.case_id=c.id AND p.display_name LIKE ?)
            OR EXISTS (SELECT 1 FROM case_legal_sections cl JOIN legal_acts a ON a.id=cl.act_id JOIN legal_sections s ON s.id=cl.section_id WHERE cl.case_id=c.id AND (a.act_code LIKE ? OR a.short_name LIKE ? OR s.section_code LIKE ?)))""")
        args.extend([like] * 15)
    sql = f"""SELECT c.id,c.fir_number,c.crime_number,c.station_id,c.district_id,c.offence,c.status,
                     c.incident_at,c.registered_at,f.case_category_code,f.gravity_code,f.crime_major_head,
                     f.crime_minor_head,f.court_id,f.registering_officer_id,u.name station_name,ct.name court_name,
                     f.brief_facts
              FROM cases c JOIN fir_case_details f ON f.case_id=c.id
              LEFT JOIN police_units u ON u.id=c.station_id LEFT JOIN courts ct ON ct.id=f.court_id
              WHERE {' AND '.join(where)} ORDER BY c.registered_at DESC,c.id LIMIT ? OFFSET ?"""
    args.extend((limit, offset))
    return [dict(row) for row in repository.connection.execute(sql, args)]


def official_case_360(repository, case_id: str) -> dict:
    row = repository.connection.execute(
        """SELECT c.*,f.*,u.name unit_name,e.display_name registering_officer_name,
                  ct.name court_name
           FROM cases c JOIN fir_case_details f ON f.case_id=c.id
           LEFT JOIN police_units u ON u.id=c.station_id
           LEFT JOIN police_employees e ON e.id=f.registering_officer_id
           LEFT JOIN courts ct ON ct.id=f.court_id WHERE c.id=?""", (case_id,)
    ).fetchone()
    if not row:
        raise ApiError("FIR_CASE_NOT_FOUND", "Official FIR case was not found.", 404, False)
    people = [dict(x) for x in repository.connection.execute(
        """SELECT r.id role_id,r.role_type,r.role_order,p.id person_id,p.display_name,p.birth_year,
                  p.identity_status,r.source_record_id
           FROM case_person_roles r JOIN persons p ON p.id=r.person_id
           WHERE r.case_id=? ORDER BY r.role_type,r.role_order""", (case_id,)
    )]
    laws = [dict(x) for x in repository.connection.execute(
        """SELECT a.act_code,a.short_name,a.description act_description,s.section_code,
                  s.description section_description,cl.source_record_id
           FROM case_legal_sections cl JOIN legal_acts a ON a.id=cl.act_id
           JOIN legal_sections s ON s.id=cl.section_id WHERE cl.case_id=?
           ORDER BY cl.act_order,cl.section_order""", (case_id,)
    )]
    arrests = [dict(x) for x in repository.connection.execute(
        """SELECT ar.*,p.display_name accused_name,u.name police_unit_name,e.display_name officer_name,
                  ct.name court_name FROM arrest_surrender_events ar
           JOIN persons p ON p.id=ar.accused_person_id
           LEFT JOIN police_units u ON u.id=ar.police_unit_id
           LEFT JOIN police_employees e ON e.id=ar.investigating_officer_id
           LEFT JOIN courts ct ON ct.id=ar.court_id WHERE ar.case_id=? ORDER BY ar.occurred_at""", (case_id,)
    )]
    chargesheets = [dict(x) for x in repository.connection.execute(
        "SELECT * FROM chargesheets WHERE case_id=? ORDER BY filed_at", (case_id,)
    )]
    related = [dict(x) for x in repository.connection.execute(
        """SELECT DISTINCT c2.id case_id,c2.fir_number,p.id shared_person_id,p.display_name shared_person_name,
                  r1.role_type source_role,r2.role_type related_role
           FROM case_person_roles r1 JOIN case_person_roles r2 ON r2.person_id=r1.person_id AND r2.case_id<>r1.case_id
           JOIN persons p ON p.id=r1.person_id JOIN cases c2 ON c2.id=r2.case_id
           JOIN fir_case_details f2 ON f2.case_id=c2.id WHERE r1.case_id=? ORDER BY c2.id""", (case_id,)
    )]
    data = dict(row)
    return {"case": data, "people": people, "legal_sections": laws, "arrest_surrender_events": arrests,
            "chargesheets": chargesheets, "related_cases": related,
            "provenance": {"source_record_id": data["source_record_id"], "classification": "VERIFIED_SOURCE_FACT"}}


def related_cases_with_evidence(repository, case_id: str) -> list[dict]:
    """Return factual, source-backed relationships - never a suspicion or guilt claim."""
    rows = repository.connection.execute(
        """SELECT DISTINCT c2.id case_id,c2.fir_number,c2.crime_number,c2.offence,c2.status,
                  p.id shared_person_id,p.display_name shared_person_name,r1.role_type source_role,
                  r2.role_type related_role,r1.source_record_id source_role_record,r2.source_record_id related_role_record
           FROM case_person_roles r1
           JOIN case_person_roles r2 ON r2.person_id=r1.person_id AND r2.case_id<>r1.case_id
           JOIN persons p ON p.id=r1.person_id
           JOIN cases c2 ON c2.id=r2.case_id
           WHERE r1.case_id=? ORDER BY c2.registered_at DESC,c2.id""", (case_id,)
    ).fetchall()
    output=[]
    for row in rows:
        item=dict(row)
        counter=[]
        if item["source_role"] != item["related_role"]:
            counter.append("The stored person has a different role in the related case.")
        if item["offence"] is None:
            counter.append("Offence classification is unavailable.")
        output.append({
            **item,
            "relationship_tier":"FACTUAL_SHARED_PERSON",
            "reason":f"The same synthetic person record appears as {item['source_role']} and {item['related_role']}.",
            "supporting_evidence":[item["source_role_record"],item["related_role_record"]],
            "counter_evidence":counter or ["Shared record alone does not establish identity, coordination, guilt, or responsibility."],
            "human_review_required":True,
        })
    return output


def identity_suggestions(repository, case_id: str) -> list[dict]:
    suggestions=[]
    for relation in related_cases_with_evidence(repository, case_id):
        left,right=sorted((case_id,relation["case_id"]))
        row=repository.connection.execute(
            "SELECT * FROM identity_link_suggestions WHERE left_case_id=? AND right_case_id=? AND shared_person_id=?",
            (left,right,relation["shared_person_id"]),
        ).fetchone()
        suggestions.append({
            "id": row["id"] if row else f"LINK-{left}-{right}-{relation['shared_person_id']}",
            "left_case_id":left,"right_case_id":right,"shared_person_id":relation["shared_person_id"],
            "person_display_name":relation["shared_person_name"],"status":row["status"] if row else "PENDING",
            "matches":["Exact shared synthetic person record"],
            "conflicts":relation["counter_evidence"],"source_references":relation["supporting_evidence"],
            "automatic_merge":False,"human_review_required":True,
        })
    return suggestions


def review_identity_suggestion(repository, case_id: str, related_case_id: str, person_id: str, decision: str, user_id: str, note: str) -> dict:
    if decision not in {"CONFIRMED","REJECTED","NEEDS_REVIEW"}:
        raise ApiError("INVALID_IDENTITY_DECISION", "Decision must be CONFIRMED, REJECTED, or NEEDS_REVIEW.", 400, False)
    valid={(x["case_id"],x["shared_person_id"]) for x in related_cases_with_evidence(repository,case_id)}
    if (related_case_id,person_id) not in valid:
        raise ApiError("IDENTITY_SUGGESTION_NOT_FOUND", "The requested identity suggestion is not available for this case.", 404, False)
    left,right=sorted((case_id,related_case_id)); now=datetime.now(timezone.utc).isoformat()
    existing=repository.connection.execute("SELECT id FROM identity_link_suggestions WHERE left_case_id=? AND right_case_id=? AND shared_person_id=?",(left,right,person_id)).fetchone()
    sid=existing["id"] if existing else f"SYN-LINK-{uuid.uuid4().hex[:16].upper()}"
    repository.connection.execute(
        """INSERT INTO identity_link_suggestions(id,left_case_id,right_case_id,shared_person_id,status,reviewed_by_user_id,reviewed_at,review_note,created_at)
           VALUES (?,?,?,?,?,?,?,?,?)
           ON CONFLICT(left_case_id,right_case_id,shared_person_id) DO UPDATE SET status=excluded.status,reviewed_by_user_id=excluded.reviewed_by_user_id,reviewed_at=excluded.reviewed_at,review_note=excluded.review_note""",
        (sid,left,right,person_id,decision,user_id,now,note[:1000],now),
    ); repository.connection.commit()
    return {"id":sid,"status":decision,"reviewed_at":now,"automatic_merge":False,"message":"Human review recorded; no records were merged or changed."}


def record_assurance(repository, case_id: str) -> list[dict]:
    case=repository.connection.execute("SELECT c.*,f.* FROM cases c JOIN fir_case_details f ON f.case_id=c.id WHERE c.id=?",(case_id,)).fetchone()
    if not case: raise ApiError("FIR_CASE_NOT_FOUND", "Official FIR case was not found.", 404, False)
    findings=[]; source=[case["source_record_id"]]
    if case["incident_to_at"] and case["incident_from_at"] > case["incident_to_at"]:
        findings.append({"rule_id":"TIMELINE_ORDER","severity":"HIGH","message":"Incident start is after incident end.","source_references":source})
    if case["information_received_at"] and case["incident_from_at"] > case["information_received_at"]:
        findings.append({"rule_id":"INFORMATION_TIMELINE","severity":"WARNING","message":"Information-received time precedes the recorded incident start.","source_references":source})
    if not (-90 <= (case["latitude"] or 0) <= 90 and -180 <= (case["longitude"] or 0) <= 180):
        findings.append({"rule_id":"COORDINATE_RANGE","severity":"HIGH","message":"Coordinates are outside the permitted geographic range.","source_references":source})
    if repository.connection.execute("SELECT 1 FROM chargesheets WHERE case_id=?",(case_id,)).fetchone() and case["status"] == "UNRESOLVED":
        findings.append({"rule_id":"STATUS_CHARGESHEET_CONTRADICTION","severity":"WARNING","message":"A chargesheet exists while the case status remains UNRESOLVED; review the source status.","source_references":source})
    return findings or [{"rule_id":"NO_DETERMINISTIC_ISSUE","severity":"INFO","message":"No deterministic FIR integrity issue was detected in the available synthetic records.","source_references":source}]


def relationship_graph(repository, case_id: str) -> dict:
    detail=official_case_360(repository,case_id); nodes=[{"id":case_id,"type":"CASE","label":detail["case"]["crime_number"]}]; edges=[]
    for person in detail["people"]:
        nodes.append({"id":person["person_id"],"type":"PERSON","label":person["display_name"]}); edges.append({"from":case_id,"to":person["person_id"],"type":f"HAS_{person['role_type']}","source_record_reference":person["source_record_id"]})
    for law in detail["legal_sections"]:
        lid=f"LAW-{law['act_code']}-{law['section_code']}";nodes.append({"id":lid,"type":"LEGAL_SECTION","label":f"{law['act_code']} {law['section_code']}"});edges.append({"from":case_id,"to":lid,"type":"INVOKES_SECTION","source_record_reference":law["source_record_id"]})
    return {"nodes":nodes[:20],"edges":edges[:20],"limits":{"nodes":20,"hops":3},"derived":False,"warning":"Factual stored links only; this graph does not infer guilt, risk, or identity."}


def investigation_brief(repository, case_id: str, user_id: str) -> dict:
    detail=official_case_360(repository,case_id); case=detail["case"]; citations=[case["source_record_id"]]
    facts=[
        {"statement":f"This synthetic FIR is {case['crime_number']} at {case['unit_name'] or case['station_id']} with status {case['status']}.","source_references":citations},
        {"statement":f"The recorded offence classification is {case['offence']} and the category is {case['case_category_code']}.","source_references":citations},
        {"statement":f"Case 360 contains {len(detail['people'])} linked person role(s), {len(detail['legal_sections'])} legal section(s), {len(detail['arrest_surrender_events'])} arrest/surrender event(s), and {len(detail['chargesheets'])} chargesheet record(s).","source_references":citations},
    ]
    related=related_cases_with_evidence(repository,case_id)
    if related: facts.append({"statement":f"{len(related)} related case relationship(s) are shown through factual shared-person records and require human review.","source_references":related[0]["supporting_evidence"]})
    result={"case_id":case_id,"title":"Evidence-Grounded Investigation Brief","statements":facts,"limitations":["Synthetic demonstration data only.","Statements are deterministic summaries of cited records, not operational advice.","No relationship implies identity, guilt, risk, or responsibility without human verification."],"generated_by":"deterministic_grounded_template"}
    repository.connection.execute("INSERT INTO investigation_briefs VALUES (?,?,?,?,?)",(f"SYN-BRIEF-{uuid.uuid4().hex[:16].upper()}",case_id,user_id,json.dumps(result),datetime.now(timezone.utc).isoformat()));repository.connection.commit()
    return result


def investigation_report_preview(repository, case_id: str, user_id: str) -> dict:
    """Create a print-safe, deterministic, cited draft; existing report review APIs retain lifecycle controls."""
    brief=investigation_brief(repository,case_id,user_id); related=related_cases_with_evidence(repository,case_id); findings=record_assurance(repository,case_id)
    statements="".join(f"<li>{html.escape(item['statement'])}<small>Sources: {html.escape(', '.join(item['source_references']))}</small></li>" for item in brief["statements"])
    relationship_rows="".join(f"<li>{html.escape(item['reason'])}<small>Evidence: {html.escape(', '.join(item['supporting_evidence']))}. Counter-evidence: {html.escape(' '.join(item['counter_evidence']))}</small></li>" for item in related) or "<li>No related case relationship is present in the available fixture.</li>"
    assurance_rows="".join(f"<li><strong>{html.escape(item['severity'])}</strong>: {html.escape(item['message'])}<small>Sources: {html.escape(', '.join(item['source_references']))}</small></li>" for item in findings)
    document=f"""<!doctype html><html><head><meta charset='utf-8'><title>ANVAYA NEXUS report</title><style>body{{font-family:system-ui;margin:2rem;color:#10202c}}header{{border-bottom:3px solid #0f766e;padding-bottom:1rem}}section{{break-inside:avoid;border-bottom:1px solid #d7dee2;padding:1rem 0}}small{{display:block;color:#52616b;margin-top:.3rem}}.watermark{{color:#92400e;font-weight:700}}@media print{{section{{page-break-inside:avoid}}}}</style></head><body><header><h1>ANVAYA NEXUS investigation report draft</h1><p class='watermark'>SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE</p></header><section><h2>Evidence-grounded summary</h2><ul>{statements}</ul></section><section><h2>Related cases, evidence and counter-evidence</h2><ul>{relationship_rows}</ul></section><section><h2>Record assurance</h2><ul>{assurance_rows}</ul></section><section><h2>Limitations</h2><p>{html.escape(' '.join(brief['limitations']))}</p></section></body></html>"""
    return {"case_id":case_id,"html":document,"export":"browser-print-to-PDF","watermark":"SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE","source_cited":True}
