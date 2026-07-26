from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timedelta, timezone

from backend.anvaya.services.source_registry import seed_source_registry

DEFAULT_SEED = 20260711

SCALES = {
    "test": {"cases": 30, "persons": 90, "aliases": 18, "organisations": 3, "documents": 6, "vehicles": 14, "phones": 14, "devices": 14, "locations": 12, "evidence": 20, "forensics": 12, "edges": 55},
    "full": {"cases": 900, "persons": 1250, "aliases": 300, "organisations": 30, "documents": 225, "vehicles": 450, "phones": 400, "devices": 400, "locations": 350, "evidence": 600, "forensics": 300, "edges": 2200},
}

STORIES = [
    {"id": "STORY-HARD-ID", "type": "true_hard_identifier", "cases": ["SYN-CASE-0001", "SYN-CASE-0002"], "shared_imei": "SYN-IMEI-000000000001"},
    {"id": "STORY-MO-ONLY", "type": "behavioural_similarity_unconfirmed", "cases": ["SYN-CASE-0003", "SYN-CASE-0004"]},
    {"id": "STORY-VEHICLE-CONFLICT", "type": "vehicle_colour_conflict", "cases": ["SYN-CASE-0001", "SYN-CASE-0002"], "values": ["BLACK", "BLUE"]},
    {"id": "STORY-DUPLICATE", "type": "duplicate_identifier", "cases": ["SYN-CASE-0005", "SYN-CASE-0006"], "crime_number": "SYN-CRIME-DUP-001"},
    {"id": "STORY-CHRONOLOGY", "type": "invalid_chronology", "cases": ["SYN-CASE-0007"]},
    {"id": "STORY-CANDIDATE", "type": "candidate_identity_conflict", "persons": ["SYN-PER-0001", "SYN-PER-0002"], "conflicts": ["birth_year", "address"]},
]


def _checksum(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _source_record(conn, source: str, external_id: str, payload: dict, timestamp: str) -> str:
    record_id = f"SYN-SR-{source}-{external_id}"
    conn.execute(
        "INSERT OR IGNORE INTO source_records VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (record_id, source, external_id, "1.0", timestamp, timestamp, "RESTRICTED" if source != "CONTEXT_FIXTURE" else "PUBLIC_CONTEXT",
         "Primary operational record" if source == "CCTNS_REPLICA" else "Synthetic corroboration/context", "Fresh", _checksum(payload), json.dumps(payload, sort_keys=True)),
    )
    conn.execute("INSERT OR IGNORE INTO transformation_events VALUES (?,?,?,?,?,?,?,?)",
                 (f"SYN-TR-{record_id}", record_id, "CANONICAL_MAP", "*", "canonical", "M2-1.0", timestamp, "ACCEPTED"))
    return record_id


def generate(repository, config, scale: str = "full", seed: int = DEFAULT_SEED) -> dict:
    if scale not in SCALES:
        raise ValueError("scale must be test or full")
    rng = random.Random(seed)
    counts = SCALES[scale]
    conn = repository.connection
    now = datetime(2026, 7, 11, 8, 0, tzinfo=timezone.utc)
    timestamp = now.isoformat()
    seed_source_registry(repository, config, now)

    # D-4 minimal FIR organisation catalog: entirely synthetic operational
    # references, never HR, address, or real police/court data.
    state_rows = [("SYN-STATE-01", "SYN-KA", "Synthetic State One", 1), ("SYN-STATE-02", "SYN-TS", "Synthetic State Two", 0)]
    for row_id, code, name, active in state_rows:
        sr = _source_record(conn, "CCTNS_REPLICA", row_id, {"source_table":"State","code":code,"active":bool(active)}, timestamp)
        conn.execute("INSERT OR IGNORE INTO states VALUES (?,?,?,?,?)", (row_id, code, name, active, sr))
    district_rows = [(f"SYN-DIST-{i:02d}", "SYN-STATE-01", f"D{i:02d}", f"Synthetic District {i}", 0 if i == 4 else 1) for i in range(1,5)]
    for row_id, state_id, code, name, active in district_rows:
        sr = _source_record(conn, "CCTNS_REPLICA", row_id, {"source_table":"District","code":code,"state":state_id,"active":bool(active)}, timestamp)
        conn.execute("INSERT OR IGNORE INTO districts VALUES (?,?,?,?,?,?)", (row_id,state_id,code,name,active,sr))
    unit_types = [("SYN-UT-POLICE","POLICE_STATION","Synthetic Police Station",1),("SYN-UT-SPECIAL","SPECIAL_UNIT","Synthetic Special Unit",1),("SYN-UT-INACTIVE","INACTIVE","Synthetic inactive type",0)]
    for row_id, code, name, active in unit_types:
        sr=_source_record(conn,"CCTNS_REPLICA",row_id,{"source_table":"UnitType","code":code,"active":bool(active)},timestamp); conn.execute("INSERT OR IGNORE INTO police_unit_types VALUES (?,?,?,?,?)",(row_id,code,name,active,sr))
    unit_rows=[]
    for i in range(1,9):
        district_id=f"SYN-DIST-{(i-1)//2+1:02d}"; row_id=f"SYN-UNIT-{i:02d}"; active=0 if i==8 else 1
        unit_rows.append((row_id,district_id,"SYN-UT-POLICE" if i%2 else "SYN-UT-SPECIAL",f"U{i:02d}",f"Synthetic Unit {i}",active))
    for row_id,district_id,type_id,code,name,active in unit_rows:
        sr=_source_record(conn,"CCTNS_REPLICA",row_id,{"source_table":"Unit","code":code,"district":district_id,"active":bool(active)},timestamp);conn.execute("INSERT OR IGNORE INTO police_units VALUES (?,?,?,?,?,?,?)",(row_id,district_id,type_id,code,name,active,sr))
    ranks=[("SYN-RANK-INS","INSPECTOR","Synthetic Inspector",1),("SYN-RANK-SI","SUB_INSPECTOR","Synthetic Sub-Inspector",1),("SYN-RANK-CON","CONSTABLE","Synthetic Constable",1),("SYN-RANK-INACTIVE","INACTIVE","Synthetic inactive rank",0)]
    designations=[("SYN-DESG-IO","INVESTIGATING_OFFICER","Synthetic Investigating Officer",1),("SYN-DESG-SHO","STATION_OFFICER","Synthetic Station Officer",1),("SYN-DESG-STAFF","CASE_STAFF","Synthetic Case Staff",1),("SYN-DESG-INACTIVE","INACTIVE","Synthetic inactive designation",0)]
    for table,rows,source_table in (("police_ranks",ranks,"Rank"),("police_designations",designations,"Designation")):
        for row_id,code,name,active in rows:
            sr=_source_record(conn,"CCTNS_REPLICA",row_id,{"source_table":source_table,"code":code,"active":bool(active)},timestamp);conn.execute(f"INSERT OR IGNORE INTO {table} VALUES (?,?,?,?,?)",(row_id,code,name,active,sr))
    for i in range(1,13):
        row_id=f"SYN-OFF-{i:02d}"; unit_id=f"SYN-UNIT-{(i-1)%7+1:02d}"; active=0 if i==12 else 1
        sr=_source_record(conn,"CCTNS_REPLICA",row_id,{"source_table":"Employee","employee_code":f"SYN-EMP-{i:03d}","unit":unit_id,"active":bool(active)},timestamp)
        conn.execute("INSERT OR IGNORE INTO police_employees VALUES (?,?,?,?,?,?,?,?)",(row_id,f"SYN-EMP-{i:03d}",f"Synthetic Officer {i:02d}",ranks[(i-1)%3][0],designations[(i-1)%3][0],unit_id,active,sr))
    for i in range(1,6):
        district_id=f"SYN-DIST-{(i-1)%3+1:02d}"; row_id=f"SYN-COURT-{i:02d}"; active=0 if i==5 else 1
        sr=_source_record(conn,"CCTNS_REPLICA",row_id,{"source_table":"Court","code":f"C{i:02d}","district":district_id,"active":bool(active)},timestamp);conn.execute("INSERT OR IGNORE INTO courts VALUES (?,?,?,?,?,?)",(row_id,district_id,f"C{i:02d}",f"Synthetic Court {i}",active,sr))

    colours = ["BLACK", "BLUE", "WHITE", "SILVER", "RED"]
    offences = ["CHAIN_SNATCHING", "HOUSEBREAKING", "VEHICLE_THEFT", "ROBBERY"]
    for i in range(1, counts["locations"] + 1):
        eid=f"SYN-LOC-{i:04d}"; payload={"locality":f"Synthetic Sector {i:04d}"}; sr=_source_record(conn,"CONTEXT_FIXTURE",eid,payload,timestamp)
        conn.execute("INSERT OR IGNORE INTO locations VALUES (?,?,?,?,?,?,?)",(eid,payload["locality"],f"SYN-STN-{i%12:02d}",f"SYN-DST-{i%4:02d}",12.8+rng.random()/10,77.5+rng.random()/10,sr))
        conn.execute("INSERT OR IGNORE INTO public_context VALUES (?,?,?,?,?,?)",(f"SYN-CTX-{i:04d}",eid,"SYNTHETIC_ZONE",f"zone-{i%8}","offline-2026.1",sr))
    for i in range(1, counts["cases"] + 1):
        eid=f"SYN-CASE-{i:04d}"; crime=f"SYN-CRIME-{i:05d}"
        if i in (5,6): crime="SYN-CRIME-DUP-001"
        incident=now-timedelta(days=i%120); registered=incident+timedelta(hours=2)
        payload={"fir":f"SYN-FIR-{i:06d}","crime":crime,"offence":"CHAIN_SNATCHING" if i<=4 else offences[i%len(offences)]}
        sr=_source_record(conn,"CCTNS_REPLICA",eid,payload,timestamp)
        conn.execute("INSERT OR IGNORE INTO cases (id,fir_number,crime_number,station_id,district_id,offence,incident_at,registered_at,status,source_record_id) VALUES (?,?,?,?,?,?,?,?,?,?)",(eid,payload["fir"],crime,f"SYN-STN-{i%12:02d}",f"SYN-DST-{i%4:02d}",payload["offence"],incident.isoformat(),registered.isoformat(),"UNRESOLVED" if i%3 else "RESOLVED",sr))
        district_number=(i-1)%3+1; unit_number=((district_number-1)*2)+((i-1)%2)+1; officer_number=((unit_number-1)%7)+1; court_number=(district_number-1)%3+1
        conn.execute("UPDATE cases SET state_id=?,canonical_district_id=?,police_unit_id=?,registering_officer_id=?,court_id=? WHERE id=?",("SYN-STATE-01",f"SYN-DIST-{district_number:02d}",f"SYN-UNIT-{unit_number:02d}",f"SYN-OFF-{officer_number:02d}",f"SYN-COURT-{court_number:02d}",eid))
        incident_from=incident.isoformat(); incident_to=(incident+timedelta(minutes=45)).isoformat(); received=(incident+timedelta(hours=1)).isoformat()
        conn.execute("UPDATE cases SET case_number=?,incident_from_at=?,incident_to_at=?,information_received_at=?,latitude=?,longitude=?,brief_facts=? WHERE id=?",(f"SYN-CASE-NO-{i:05d}",incident_from,incident_to,received,12.01+(i%5)/100 if i%4 else None,77.01+(i%5)/100 if i%4 else None,f"Synthetic FIR brief facts for case {i}; neutral factual fixture only.",eid))
        if i <= min(counts["cases"], 100):
            for suffix, target_type, target_id, relationship in (("UNIT","POLICE_UNIT",f"SYN-UNIT-{unit_number:02d}","CASE_REGISTERED_AT_UNIT"),("OFF","OFFICER",f"SYN-OFF-{officer_number:02d}","CASE_REGISTERED_BY_OFFICER"),("COURT","COURT",f"SYN-COURT-{court_number:02d}","CASE_HEARD_AT_COURT")):
                edge_source=_source_record(conn,"CCTNS_REPLICA",f"SYN-ORG-EDGE-{i:04d}-{suffix}",{"case":eid,"relationship":relationship},timestamp)
                conn.execute("INSERT OR IGNORE INTO entity_edges VALUES (?,?,?,?,?,?,?,?)",(f"SYN-EDGE-ORG-{i:04d}-{suffix}","CASE",eid,target_type,target_id,relationship,"RECORDED_ASSOCIATION",edge_source))
    for unit_id,district_id,_,_,_,_ in unit_rows:
        source=_source_record(conn,"CCTNS_REPLICA",f"SYN-ORG-EDGE-{unit_id}",{"unit":unit_id,"district":district_id},timestamp)
        conn.execute("INSERT OR IGNORE INTO entity_edges VALUES (?,?,?,?,?,?,?,?)",(f"SYN-EDGE-UNIT-DIST-{unit_id}","POLICE_UNIT",unit_id,"DISTRICT",district_id,"UNIT_BELONGS_TO_DISTRICT","RECORDED_ASSOCIATION",source))
    for district_id,state_id,_,_,_ in district_rows:
        source=_source_record(conn,"CCTNS_REPLICA",f"SYN-ORG-EDGE-{district_id}",{"district":district_id,"state":state_id},timestamp)
        conn.execute("INSERT OR IGNORE INTO entity_edges VALUES (?,?,?,?,?,?,?,?)",(f"SYN-EDGE-DIST-STATE-{district_id}","DISTRICT",district_id,"STATE",state_id,"DISTRICT_BELONGS_TO_STATE","RECORDED_ASSOCIATION",source))
    for officer_number in range(1,13):
        officer_id=f"SYN-OFF-{officer_number:02d}"; unit_id=f"SYN-UNIT-{(officer_number-1)%7+1:02d}"; source=_source_record(conn,"CCTNS_REPLICA",f"SYN-ORG-EDGE-{officer_id}",{"officer":officer_id,"unit":unit_id},timestamp)
        conn.execute("INSERT OR IGNORE INTO entity_edges VALUES (?,?,?,?,?,?,?,?)",(f"SYN-EDGE-OFF-UNIT-{officer_id}","OFFICER",officer_id,"POLICE_UNIT",unit_id,"OFFICER_ASSIGNED_TO_UNIT","RECORDED_ASSOCIATION",source))
    for i in range(1, counts["persons"] + 1):
        eid=f"SYN-PER-{i:04d}"; payload={"name":f"Synthetic Person {i:04d}","birth_year":1980+i%25,"address":f"Synthetic Address Block {i%100:03d}"}
        if i==2: payload.update({"name":"Synthetic Person 0001","birth_year":1999,"address":"Synthetic Address Conflict"})
        sr=_source_record(conn,"CCTNS_REPLICA",eid,payload,timestamp)
        conn.execute(
            "INSERT OR IGNORE INTO persons (id,display_name,birth_year,address_text,identity_status,source_record_id,age_years,gender_code,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (eid,payload["name"],payload["birth_year"],payload["address"],"CANDIDATE" if i<=2 else "SYNTHETIC",sr,2026-payload["birth_year"],("X","F","M")[i%3],timestamp,timestamp),
        )
    role_targets = {
        "COMPLAINANT": lambda case_number: "SYN-PER-0002" if case_number in {1, 4} else f"SYN-PER-{(case_number % counts['persons']) + 1:04d}",
        "VICTIM": lambda case_number: f"SYN-PER-{((case_number + 7) % counts['persons']) + 1:04d}",
        "ACCUSED": lambda case_number: "SYN-PER-0001" if case_number in {1, 2, 3} else f"SYN-PER-{((case_number + 13) % counts['persons']) + 1:04d}",
    }
    # FIR role scenarios are a compact deterministic demo fixture in this
    # milestone.  The full legacy generator remains within its established
    # generic-edge scale until D-5 replaces it with the complete FIR dataset.
    for case_number in range(1, min(counts["cases"], 30) + 1):
        case_id = f"SYN-CASE-{case_number:04d}"
        role_rows = [("COMPLAINANT", role_targets["COMPLAINANT"](case_number), None)]
        if case_number % 3:
            role_rows.append(("VICTIM", role_targets["VICTIM"](case_number), None))
        if case_number <= 4 or case_number % 2 == 0:
            role_rows.append(("ACCUSED", role_targets["ACCUSED"](case_number), 1))
        if case_number in {1, 8}:
            role_rows.append(("ACCUSED", f"SYN-PER-{((case_number + 19) % counts['persons']) + 1:04d}", 2))
        if case_number <= 5:
            role_rows.append(("WITNESS", f"SYN-PER-{((case_number + 23) % counts['persons']) + 1:04d}", 1))
        for role, person_id, sequence in role_rows:
            role_id = f"SYN-CPR-{case_number:04d}-{role[:3]}-{sequence or 0:02d}"
            role_source = _source_record(conn, "CCTNS_REPLICA", role_id, {"case": case_id, "person": person_id, "role": role, "sequence": sequence}, timestamp)
            conn.execute(
                "INSERT OR IGNORE INTO case_person_roles (id,case_id,person_id,role,role_sequence,source_record_id,created_at) VALUES (?,?,?,?,?,?,?)",
                (role_id, case_id, person_id, role, sequence, role_source, timestamp),
            )
            conn.execute(
                "INSERT OR IGNORE INTO entity_edges VALUES (?,?,?,?,?,?,?,?)",
                (f"SYN-EDGE-ROLE-{case_number:04d}-{role[:3]}-{sequence or 0:02d}", "CASE", case_id, "PERSON", person_id, f"CASE_HAS_{role}", "RECORDED_ASSOCIATION", role_source),
            )
    # Synthetic complaint / witness statement summaries (not invented operational narratives beyond fixtures).
    statement_samples = {
        1: ("COMPLAINT", "Synthetic complaint summary: chain snatching near SYN-STN-01 market road. सिंथेटिक / ಸಿಂಥೆಟಿಕ್ multilingual fixture line."),
        2: ("WITNESS", "Synthetic witness summary (KN fixture): vehicle seen near crossing."),
        3: ("WITNESS", "Synthetic witness summary (HI fixture): fraud call reported after SMS."),
        4: ("COMPLAINT", "Synthetic complaint summary: injury reported after a public altercation."),
        5: ("WITNESS", "Synthetic witness summary: observed property removal from a locked stall."),
    }
    for case_number, (statement_type, body) in statement_samples.items():
        case_id = f"SYN-CASE-{case_number:04d}"
        role_name = "WITNESS" if statement_type == "WITNESS" else "COMPLAINANT"
        role_row = conn.execute(
            "SELECT id,person_id FROM case_person_roles WHERE case_id=? AND role=? ORDER BY role_sequence,id LIMIT 1",
            (case_id, role_name),
        ).fetchone()
        if not role_row:
            continue
        statement_id = f"SYN-STMT-{case_number:04d}-01"
        sr = _source_record(conn, "CCTNS_REPLICA", statement_id, {"case": case_id, "type": statement_type}, timestamp)
        try:
            conn.execute(
                "INSERT OR IGNORE INTO case_person_statements (id,case_id,case_person_role_id,statement_type,recorded_at,body_text,source_record_id,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (statement_id, case_id, role_row["id"], statement_type, (now - timedelta(days=case_number)).isoformat(), body, sr, timestamp),
            )
        except Exception:
            pass
    # Prefer a distinct investigating officer where the employee catalogue allows it.
    for case_number in range(1, min(counts["cases"], 30) + 1):
        case_id = f"SYN-CASE-{case_number:04d}"
        reg = conn.execute("SELECT registering_officer_id FROM cases WHERE id=?", (case_id,)).fetchone()
        registering = reg["registering_officer_id"] if reg else None
        io_id = f"SYN-OFF-{(case_number % 7) + 1:02d}"
        if registering and io_id == registering:
            io_id = f"SYN-OFF-{((case_number + 2) % 7) + 1:02d}"
        try:
            conn.execute("UPDATE cases SET investigating_officer_id=? WHERE id=?", (io_id, case_id))
        except Exception:
            pass
    acts = [
        ("SYN-ACT-01", "SYN-ACT-01", "Synthetic property offence act", "Property", 1),
        ("SYN-ACT-02", "SYN-ACT-02", "Synthetic public order act", "PublicOrder", 1),
        ("SYN-ACT-03", "SYN-ACT-03", "Synthetic personal safety act", "Safety", 1),
        ("SYN-ACT-04", "SYN-ACT-04", "Synthetic transport offence act", "Transport", 1),
        ("SYN-ACT-05", "SYN-ACT-05", "Synthetic evidence procedure act", "Evidence", 1),
        ("SYN-ACT-06", "SYN-ACT-06", "Synthetic inactive reference act", "Inactive", 0),
    ]
    for act_id, act_code, description, short_name, active in acts:
        source_id = _source_record(conn, "CCTNS_REPLICA", act_id, {"source_table": "Act", "code": act_code, "active": bool(active)}, timestamp)
        conn.execute("INSERT OR IGNORE INTO legal_acts VALUES (?,?,?,?,?,?,?,?)", (act_id, act_code, description, short_name, active, source_id, timestamp, timestamp))
    sections = []
    for act_number, (act_id, _, _, _, act_active) in enumerate(acts, start=1):
        for section_number in range(1, 5):
            section_id = f"SYN-SEC-{act_number:02d}-{section_number:02d}"
            section_code = f"S-{act_number:02d}-{section_number:02d}"
            active = 0 if (act_number, section_number) == (1, 4) else act_active
            source_id = _source_record(conn, "CCTNS_REPLICA", section_id, {"source_table": "Section", "act_id": act_id, "code": section_code, "active": bool(active)}, timestamp)
            conn.execute("INSERT OR IGNORE INTO legal_sections VALUES (?,?,?,?,?,?,?,?)", (section_id, act_id, section_code, f"Synthetic section {act_number}-{section_number}", active, source_id, timestamp, timestamp))
            sections.append((section_id, act_id, section_code, active))
    categories = [("SYN-CAT-PROPERTY", "PROPERTY", "Synthetic property category", 1), ("SYN-CAT-PERSON", "PERSON", "Synthetic person category", 1), ("SYN-CAT-PUBLIC", "PUBLIC_ORDER", "Synthetic public order category", 1), ("SYN-CAT-INACTIVE", "INACTIVE", "Synthetic inactive category", 0)]
    for row_id, code, name, active in categories:
        source_id = _source_record(conn, "CCTNS_REPLICA", row_id, {"source_table": "CaseCategory", "code": code, "active": bool(active)}, timestamp)
        conn.execute("INSERT OR IGNORE INTO case_categories VALUES (?,?,?,?,?)", (row_id, code, name, active, source_id))
    gravities = [("SYN-GRV-LOW", "LOW", "Synthetic low gravity", 1), ("SYN-GRV-HIGH", "HIGH", "Synthetic high gravity", 1), ("SYN-GRV-INACTIVE", "INACTIVE", "Synthetic inactive gravity", 0)]
    for row_id, code, name, active in gravities:
        source_id = _source_record(conn, "CCTNS_REPLICA", row_id, {"source_table": "GravityOffence", "code": code, "active": bool(active)}, timestamp)
        conn.execute("INSERT OR IGNORE INTO gravity_offences VALUES (?,?,?,?,?)", (row_id, code, name, active, source_id))
    heads = [("SYN-HEAD-PROPERTY", "Synthetic property head", 1), ("SYN-HEAD-PERSON", "Synthetic person head", 1), ("SYN-HEAD-PUBLIC", "Synthetic public order head", 1), ("SYN-HEAD-TRANSPORT", "Synthetic transport head", 1), ("SYN-HEAD-INACTIVE", "Synthetic inactive head", 0)]
    for row_id, name, active in heads:
        source_id = _source_record(conn, "CCTNS_REPLICA", row_id, {"source_table": "CrimeHead", "name": name, "active": bool(active)}, timestamp)
        conn.execute("INSERT OR IGNORE INTO crime_heads VALUES (?,?,?,?)", (row_id, name, active, source_id))
    subheads = []
    for head_number, (head_id, _, head_active) in enumerate(heads, start=1):
        for sequence in (1, 2):
            row_id = f"SYN-SUB-{head_number:02d}-{sequence:02d}"
            source_id = _source_record(conn, "CCTNS_REPLICA", row_id, {"source_table": "CrimeSubHead", "crime_head_id": head_id, "sequence": sequence, "active": bool(head_active)}, timestamp)
            conn.execute("INSERT OR IGNORE INTO crime_subheads VALUES (?,?,?,?,?,?)", (row_id, head_id, f"Synthetic sub-head {head_number}-{sequence}", sequence, head_active, source_id))
            subheads.append((row_id, head_id))
    statuses = [("SYN-STATUS-UNRESOLVED", "UNRESOLVED", "Synthetic unresolved status", 1), ("SYN-STATUS-RESOLVED", "RESOLVED", "Synthetic resolved status", 1), ("SYN-STATUS-INACTIVE", "INACTIVE", "Synthetic inactive status", 0)]
    for row_id, code, name, active in statuses:
        source_id = _source_record(conn, "CCTNS_REPLICA", row_id, {"source_table": "CaseStatusMaster", "code": code, "active": bool(active)}, timestamp)
        conn.execute("INSERT OR IGNORE INTO case_statuses VALUES (?,?,?,?,?)", (row_id, code, name, active, source_id))
    active_categories = [row[0] for row in categories[:3]]
    active_gravities = [row[0] for row in gravities[:2]]
    active_heads = [row[0] for row in heads[:4]]
    for case_number in range(1, min(counts["cases"], 30) + 1):
        case_id = f"SYN-CASE-{case_number:04d}"
        head_id = active_heads[(case_number - 1) % len(active_heads)]
        subhead_id = next(row_id for row_id, parent_id in subheads if parent_id == head_id)
        category_id = active_categories[(case_number - 1) % len(active_categories)]
        gravity_id = active_gravities[(case_number - 1) % len(active_gravities)]
        status_id = "SYN-STATUS-RESOLVED" if case_number % 3 == 0 else "SYN-STATUS-UNRESOLVED"
        if case_number == 9:
            category_id = "SYN-CAT-INACTIVE"
        conn.execute("UPDATE cases SET case_category_id=?,gravity_offence_id=?,crime_major_head_id=?,crime_minor_head_id=?,case_status_id=? WHERE id=?", (category_id, gravity_id, head_id, subhead_id, status_id, case_id))
        act_id = acts[(case_number - 1) % 5][0]
        section_id = next(section_id for section_id, section_act_id, _, active in sections if section_act_id == act_id and active)
        if case_number == 7:
            section_id = "SYN-SEC-01-04"
            act_id = "SYN-ACT-01"
        if case_number == 8:
            act_id = "SYN-ACT-06"
            section_id = "SYN-SEC-06-01"
        legal_rows = [(act_id, section_id, 1, 1)]
        if case_number in {1, 2, 10}:
            legal_rows.append(("SYN-ACT-02", "SYN-SEC-02-01", 2, 1))
        for link_act_id, link_section_id, act_order, section_order in legal_rows:
            link_id = f"SYN-CLS-{case_number:04d}-{link_act_id[-2:]}-{link_section_id[-2:]}"
            source_id = _source_record(conn, "CCTNS_REPLICA", link_id, {"source_table": "ActSectionAssociation", "case": case_id, "act": link_act_id, "section": link_section_id}, timestamp)
            conn.execute("INSERT OR IGNORE INTO case_legal_sections VALUES (?,?,?,?,?,?,?,?)", (link_id, case_id, link_act_id, link_section_id, act_order, section_order, source_id, timestamp))
            conn.execute("INSERT OR IGNORE INTO entity_edges VALUES (?,?,?,?,?,?,?,?)", (f"SYN-EDGE-ACT-{case_number:04d}-{link_act_id[-2:]}", "CASE", case_id, "ACT", link_act_id, "CASE_INVOKES_ACT", "RECORDED_ASSOCIATION", source_id))
            conn.execute("INSERT OR IGNORE INTO entity_edges VALUES (?,?,?,?,?,?,?,?)", (f"SYN-EDGE-SEC-{case_number:04d}-{link_section_id[-2:]}", "CASE", case_id, "SECTION", link_section_id, "CASE_INVOKES_SECTION", "RECORDED_ASSOCIATION", source_id))
    # D-3 uses a compact operational-event fixture. Every stored row is
    # source-backed; rejected/orphan source rows stay outside canonical tables.
    event_count = min(counts["cases"], 20)
    for event_number in range(1, event_count + 1):
        case_id = f"SYN-CASE-{event_number:04d}"
        event_id = f"SYN-ASE-{event_number:04d}"
        event_type = "SURRENDER" if event_number % 3 == 0 else "ARREST"
        event_at = (now - timedelta(days=event_number * 2)).isoformat()
        event_source = _source_record(conn, "CCTNS_REPLICA", event_id, {
            "source_table": "ArrestSurrender", "case": case_id, "event_type": event_type,
        }, timestamp)
        conn.execute(
            "INSERT OR IGNORE INTO arrest_surrender_events (id,case_id,event_type,event_at,state_code,district_code,police_unit_code,investigating_officer_ref,court_ref,remarks,source_record_id,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (event_id, case_id, event_type, event_at, "SYN-STATE-KA", f"SYN-DIST-{event_number % 4 + 1:02d}",
             f"SYN-UNIT-{event_number % 8 + 1:02d}", None, None, "Synthetic operational event.", event_source, timestamp, timestamp),
        )
        district_number=(event_number-1)%3+1; unit_number=((district_number-1)*2)+((event_number-1)%2)+1; officer_number=((unit_number-1)%7)+1; court_number=(district_number-1)%3+1
        conn.execute("UPDATE arrest_surrender_events SET state_id=?,district_id=?,police_unit_id=?,investigating_officer_id=?,court_id=? WHERE id=?",("SYN-STATE-01",f"SYN-DIST-{district_number:02d}",f"SYN-UNIT-{unit_number:02d}",f"SYN-OFF-{officer_number:02d}",f"SYN-COURT-{court_number:02d}",event_id))
        conn.execute("INSERT OR IGNORE INTO entity_edges VALUES (?,?,?,?,?,?,?,?)", (
            f"SYN-EDGE-ARREST-{event_number:04d}", "CASE", case_id, "ARREST_EVENT", event_id,
            "CASE_HAS_ARREST_EVENT", "RECORDED_ASSOCIATION", event_source,
        ))
        accused_rows = conn.execute(
            "SELECT id,person_id FROM case_person_roles WHERE case_id=? AND role='ACCUSED' ORDER BY role_sequence,person_id,id",
            (case_id,),
        ).fetchall()
        for link_number, accused in enumerate(accused_rows, start=1):
            link_id = f"SYN-AAL-{event_number:04d}-{link_number:02d}"
            link_source = _source_record(conn, "CCTNS_REPLICA", link_id, {
                "source_table": "ArrestSurrenderAccused", "event": event_id, "person": accused[1],
            }, timestamp)
            conn.execute("INSERT OR IGNORE INTO arrest_accused_links VALUES (?,?,?,?,?,?,?)", (
                link_id, event_id, accused[1], accused[0], link_number, link_source, timestamp,
            ))
            conn.execute("INSERT OR IGNORE INTO entity_edges VALUES (?,?,?,?,?,?,?,?)", (
                f"SYN-EDGE-ARREST-ACCUSED-{event_number:04d}-{link_number:02d}", "ARREST_EVENT", event_id,
                "PERSON", accused[1], "ARREST_INVOLVES_ACCUSED", "RECORDED_ASSOCIATION", link_source,
            ))
    for chargesheet_number in range(1, min(counts["cases"], 16) + 1):
        case_id = f"SYN-CASE-{chargesheet_number:04d}"
        chargesheet_id = f"SYN-CHG-{chargesheet_number:04d}"
        report_type = ("A_CHARGESHEET", "B_FALSE", "C_UNDETECTED")[(chargesheet_number - 1) % 3]
        filed_at = (now - timedelta(days=chargesheet_number)).isoformat()
        chargesheet_source = _source_record(conn, "CCTNS_REPLICA", chargesheet_id, {
            "source_table": "ChargesheetDetails", "case": case_id, "report_type": report_type,
        }, timestamp)
        conn.execute("INSERT OR IGNORE INTO chargesheets (id,case_id,filed_at,report_type,filing_officer_ref,summary,source_record_id,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)", (
            chargesheet_id, case_id, filed_at, report_type, None, "Synthetic final-report summary.", chargesheet_source, timestamp, timestamp,
        ))
        case_unit = conn.execute("SELECT registering_officer_id FROM cases WHERE id=?", (case_id,)).fetchone()[0]
        conn.execute("UPDATE chargesheets SET filing_officer_id=? WHERE id=?", (case_unit, chargesheet_id))
        conn.execute("INSERT OR IGNORE INTO entity_edges VALUES (?,?,?,?,?,?,?,?)", (
            f"SYN-EDGE-CHARGESHEET-{chargesheet_number:04d}", "CASE", case_id, "CHARGESHEET", chargesheet_id,
            "CASE_HAS_CHARGESHEET", "RECORDED_ASSOCIATION", chargesheet_source,
        ))
    for i in range(1, counts["aliases"] + 1):
        eid=f"SYN-ALS-{i:04d}"; person=f"SYN-PER-{(i%counts['persons'])+1:04d}"; sr=_source_record(conn,"CCTNS_REPLICA",eid,{"alias":f"Synthetic Alias {i:04d}"},timestamp)
        conn.execute("INSERT OR IGNORE INTO aliases VALUES (?,?,?,?)",(eid,person,f"Synthetic Alias {i:04d}",sr))
    for i in range(1, counts["organisations"]+1):
        eid=f"SYN-ORG-{i:04d}"; sr=_source_record(conn,"CCTNS_REPLICA",eid,{"name":f"Synthetic Organisation {i:04d}"},timestamp)
        conn.execute("INSERT OR IGNORE INTO organisations VALUES (?,?,?,?)",(eid,f"Synthetic Organisation {i:04d}","SYNTHETIC_ENTITY",sr))
    for i in range(1, counts["documents"]+1):
        eid=f"SYN-DOC-{i:04d}"; case=f"SYN-CASE-{(i%counts['cases'])+1:04d}"
        doc_type=("SYNTHETIC_COMPLAINT","SYNTHETIC_SEIZURE_MEMO","SYNTHETIC_FORENSIC_DISPATCH")[(i-1)%3]
        sr=_source_record(conn,"CCTNS_REPLICA",eid,{"case":case,"type":doc_type},timestamp)
        conn.execute("INSERT OR IGNORE INTO documents (id,case_id,document_type,status,source_record_id) VALUES (?,?,?,?,?)",(eid,case,doc_type,"AVAILABLE",sr))
    for kind in ("phones","devices","vehicles"):
        for i in range(1, counts[kind]+1):
            prefix={"phones":"PH","devices":"DEV","vehicles":"VEH"}[kind]; eid=f"SYN-{prefix}-{i:04d}"
            source="VEHICLE_REPLICA" if kind=="vehicles" else "CCTNS_REPLICA"; payload={"id":eid}; sr=_source_record(conn,source,eid,payload,timestamp)
            digest=hashlib.sha256(eid.encode()).hexdigest()
            if kind=="phones": conn.execute("INSERT OR IGNORE INTO phones VALUES (?,?,?,?)",(eid,f"SYN-PHONE-{i:06d}",digest,sr))
            elif kind=="devices": conn.execute("INSERT OR IGNORE INTO devices VALUES (?,?,?,?,?)",(eid,"SYN-IMEI-000000000001" if i==1 else f"SYN-IMEI-{i:012d}",digest,"SYNTHETIC_HANDSET",sr))
            else: conn.execute("INSERT OR IGNORE INTO vehicles VALUES (?,?,?,?,?,?)",(eid,f"SYN-REG-{i:06d}",digest,"SYNTHETIC_TWO_WHEELER",colours[i%len(colours)],sr))
    for i in range(1, counts["evidence"]+1):
        eid=f"SYN-EVD-{i:04d}"; case=f"SYN-CASE-{(i%counts['cases'])+1:04d}"; sr=_source_record(conn,"CCTNS_REPLICA",eid,{"case":case},timestamp)
        conn.execute("INSERT OR IGNORE INTO evidence_records VALUES (?,?,?,?,?,?,?)",(eid,case,"SYNTHETIC_ITEM",f"Synthetic evidence {i}","AVAILABLE","RESTRICTED",sr))
    # Watermarked synthetic exhibits for dossier PDF (1-2 per early cases).
    from backend.anvaya.services.exhibit_assets import render_synthetic_exhibit_png, sha256_bytes
    exhibit_kinds=(
        ("SCENE_SKETCH","Synthetic scene sketch placeholder"),
        ("SEIZURE_MEMO_SCAN","Synthetic seizure-memo scan placeholder"),
        ("DEVICE_PHOTO","Synthetic device photograph placeholder"),
    )
    for case_number in range(1, min(counts["cases"], 30) + 1):
        case_id=f"SYN-CASE-{case_number:04d}"
        evidence_row=conn.execute("SELECT id FROM evidence_records WHERE case_id=? ORDER BY id LIMIT 1",(case_id,)).fetchone()
        evidence_id=evidence_row["id"] if evidence_row else None
        for kind_index, (kind, caption) in enumerate(exhibit_kinds[:2 if case_number % 2 else 3], start=1):
            exhibit_id=f"SYN-EXH-{case_number:04d}-{kind_index:02d}"
            exhibit_code=f"EXH-{case_number:04d}-{kind_index:02d}"
            filename=f"{exhibit_code.lower()}.png"
            blob=render_synthetic_exhibit_png(exhibit_code=exhibit_code, caption=caption, case_id=case_id)
            digest=sha256_bytes(blob)
            sr=_source_record(conn,"CCTNS_REPLICA",exhibit_id,{"case":case_id,"exhibit":exhibit_code,"kind":kind,"sha256":digest},timestamp)
            conn.execute(
                "INSERT OR IGNORE INTO evidence_exhibits (id,case_id,evidence_id,exhibit_code,filename,mime_type,sha256,byte_size,collected_at,collected_by_ref,chain_status,caption,sensitivity,content_blob,source_record_id,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (exhibit_id,case_id,evidence_id,exhibit_code,filename,"image/png",digest,len(blob),
                 (now-timedelta(days=case_number)).isoformat(),f"SYN-OFF-{(case_number-1)%7+1:02d}","CHAIN_RECORDED",
                 caption,"RESTRICTED",blob,sr,timestamp),
            )
            try:
                conn.execute("UPDATE evidence_exhibits SET exhibit_kind=? WHERE id=?", (kind, exhibit_id))
            except Exception:
                pass
            custody_plan = (
                ("SEIZED", f"SYN-OFF-{(case_number-1)%7+1:02d}", "SEAL-A"),
                ("STORED", f"SYN-OFF-{(case_number)%7+1:02d}", "SEAL-B"),
                ("VERIFIED", f"SYN-OFF-{(case_number+1)%7+1:02d}", "SEAL-C"),
            )
            for sequence, (event_type, custodian, seal) in enumerate(custody_plan[:2 + (kind_index % 2)], start=1):
                custody_id = f"{exhibit_id}-CUST-{sequence:02d}"
                custody_sr = _source_record(conn, "CCTNS_REPLICA", custody_id, {"exhibit": exhibit_id, "event": event_type}, timestamp)
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO evidence_custody_events (id,exhibit_id,sequence,event_type,event_at,custodian_ref,seal_ref,source_record_id,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                        (custody_id, exhibit_id, sequence, event_type, (now - timedelta(days=case_number, hours=sequence)).isoformat(), custodian, seal, custody_sr, timestamp),
                    )
                except Exception:
                    pass
    document_titles={"SYNTHETIC_COMPLAINT":"Synthetic complaint copy","SYNTHETIC_SEIZURE_MEMO":"Synthetic seizure memo","SYNTHETIC_FORENSIC_DISPATCH":"Synthetic forensic dispatch note"}
    for i in range(1, counts["documents"]+1):
        doc_id=f"SYN-DOC-{i:04d}"
        doc_row=conn.execute("SELECT case_id,document_type FROM documents WHERE id=?",(doc_id,)).fetchone()
        if not doc_row:
            continue
        linked_exhibit=None
        if doc_row["document_type"]=="SYNTHETIC_SEIZURE_MEMO":
            exhibit_row=conn.execute("SELECT id FROM evidence_exhibits WHERE case_id=? ORDER BY exhibit_code,id LIMIT 1",(doc_row["case_id"],)).fetchone()
            linked_exhibit=exhibit_row["id"] if exhibit_row else None
        try:
            conn.execute(
                "UPDATE documents SET title=?, issued_at=?, linked_exhibit_id=? WHERE id=?",
                (f"{document_titles.get(doc_row['document_type'],'Synthetic document')} {i:04d}", (now-timedelta(days=i%40)).isoformat(), linked_exhibit, doc_id),
            )
        except Exception:
            pass
    for i in range(1, counts["forensics"]+1):
        eid=f"SYN-FOR-{i:04d}"; case=f"SYN-CASE-{(i%counts['cases'])+1:04d}"; occurred=(now-timedelta(days=i%90)).isoformat(); sr=_source_record(conn,"FORENSICS_REPLICA",eid,{"case":case},timestamp)
        conn.execute("INSERT OR IGNORE INTO forensic_events VALUES (?,?,?,?,?,?)",(eid,case,"DEVICE_METADATA",occurred,"SYNTHETIC_RESULT",sr))
    for i in range(1, counts["edges"]+1):
        eid=f"SYN-EDGE-{i:05d}"; case=f"SYN-CASE-{(i%counts['cases'])+1:04d}"; target=f"SYN-DEV-{(i%counts['devices'])+1:04d}"; sr=_source_record(conn,"CCTNS_REPLICA",eid,{"case":case,"target":target},timestamp)
        conn.execute("INSERT OR IGNORE INTO entity_edges VALUES (?,?,?,?,?,?,?,?)",(eid,"CASE",case,"DEVICE",target,"RECORDED_DEVICE","RECORDED_ASSOCIATION",sr))
    for i in range(1,counts["cases"]+1):
        case=f"SYN-CASE-{i:04d}"; sr=conn.execute("SELECT source_record_id FROM cases WHERE id=?",(case,)).fetchone()[0]
        conn.execute("INSERT OR IGNORE INTO case_dna_features VALUES (?,?,?,?,?,?)",(f"SYN-DNA-{i:04d}",case,"MODUS_OPERANDI","SYNTHETIC_PATTERN_A" if i<=4 else f"SYNTHETIC_PATTERN_{i%8}",0.0,sr))
    # Golden story: two cases share one synthetic IMEI; conflicting colour remains in separate source records.
    for index,case in enumerate(("SYN-CASE-0001","SYN-CASE-0002"),start=1):
        eid=f"SYN-EDGE-GOLDEN-{index}"; sr=_source_record(conn,"CCTNS_REPLICA",eid,{"case":case,"imei":"SYN-IMEI-000000000001"},timestamp)
        conn.execute("INSERT OR IGNORE INTO entity_edges VALUES (?,?,?,?,?,?,?,?)",(eid,"CASE",case,"DEVICE","SYN-DEV-0001","SHARED_IMEI","DIRECT_EVIDENCE",sr))
        for target_type,target_id,relationship in (("PHONE","SYN-PH-0001","RECORDED_PHONE"),("VEHICLE","SYN-VEH-0001","RECORDED_VEHICLE")):
            edge=f"SYN-EDGE-GOLDEN-{target_type}-{index}";edge_sr=_source_record(conn,"CCTNS_REPLICA",edge,{"case":case,"target":target_id},timestamp)
            conn.execute("INSERT OR IGNORE INTO entity_edges VALUES (?,?,?,?,?,?,?,?)",(edge,"CASE",case,target_type,target_id,relationship,"RECORDED_ASSOCIATION",edge_sr))
    _source_record(conn,"CCTNS_REPLICA","SYN-VEH-CONFLICT-CCTNS",{"vehicle":"SYN-VEH-0001","colour":"BLACK"},timestamp)
    _source_record(conn,"VEHICLE_REPLICA","SYN-VEH-CONFLICT-REGISTRY",{"vehicle":"SYN-VEH-0001","colour":"BLUE"},timestamp)
    # Seed later-engine inputs only; no engine executes in M2.
    for story in STORIES:
        if story["type"] in {"vehicle_colour_conflict","duplicate_identifier","invalid_chronology","candidate_identity_conflict"}:
            case_id=(story.get("cases") or [None])[0]
            conn.execute("INSERT OR IGNORE INTO trust_issues (id,case_id,issue_type,severity,description,source_record_ids_json,status) VALUES (?,?,?,?,?,?,?)",(f"SYN-ISSUE-{story['id']}",case_id,story["type"],"SEEDED",json.dumps(story,sort_keys=True),"[]","OPEN"))
    conn.execute("INSERT OR IGNORE INTO trust_issues (id,case_id,issue_type,severity,description,source_record_ids_json,status) VALUES (?,?,?,?,?,?,?)",("SYN-ISSUE-MISSING-SOURCE","SYN-CASE-0001","missing_source","SEEDED","Synthetic complaint source intentionally absent for later verification tests","[]","OPEN"))
    conn.commit()
    result={name:repository.table_count(name) for name in ("cases","persons","case_person_roles","case_person_statements","legal_acts","legal_sections","case_legal_sections","case_categories","gravity_offences","crime_heads","crime_subheads","case_statuses","states","districts","police_unit_types","police_units","police_ranks","police_designations","police_employees","courts","arrest_surrender_events","arrest_accused_links","chargesheets","aliases","organisations","documents","vehicles","phones","devices","locations","evidence_records","evidence_exhibits","evidence_custody_events","forensic_events","entity_edges","case_dna_features")}
    result.update({"seed":seed,"scale":scale,"stories":len(STORIES)})
    return result


def ground_truth_manifest() -> dict:
    return {
        "manifest_version":"M2-1.0", "synthetic_only":True, "stories":STORIES,
        "true_relationships":[{"cases":["SYN-CASE-0001","SYN-CASE-0002"],"identifier":"SYN-IMEI-000000000001"}],
        "false_similarities":[{"cases":["SYN-CASE-0003","SYN-CASE-0004"],"reason":"behaviour_only"}],
        "seeded_defects":["duplicate_identifier","invalid_chronology","missing_source","candidate_identity_conflict"],
        "conflicts":[{"field":"vehicle_colour","values":["BLACK","BLUE"]}],
        "expected_source_states":{"CCTNS_REPLICA":"Fresh","FORENSICS_REPLICA":"Fresh","VEHICLE_REPLICA":"Fresh","CONTEXT_FIXTURE":"Fresh","COURT_REPLICA":"Unavailable","PROSECUTION_REPLICA":"Unavailable"},
        "expected_import_failures":["missing_required_key","invalid_date","duplicate_identifier","unlinked_document"],
        "expected_permission_denials_placeholder":["M3_EXTERNAL_JURISDICTION","M3_UNPERMITTED_SOURCE"],
        "later_action_expectation":{"story":"STORY-HARD-ID","highest_priority":"REVIEW_CCTV","implemented_in":"M5"},
    }
