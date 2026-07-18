from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timedelta, timezone

from backend.anvaya.services.source_registry import seed_source_registry

DEFAULT_SEED = 20260711

SCALES = {
    "test": {"cases": 24, "persons": 36, "aliases": 18, "organisations": 3, "documents": 6, "vehicles": 14, "phones": 14, "devices": 14, "locations": 12, "evidence": 20, "forensics": 12, "edges": 55},
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
        if i==7: registered=incident-timedelta(days=1)
        payload={"fir":f"SYN-FIR-{i:06d}","crime":crime,"offence":"CHAIN_SNATCHING" if i<=4 else offences[i%len(offences)]}
        sr=_source_record(conn,"CCTNS_REPLICA",eid,payload,timestamp)
        conn.execute("INSERT OR IGNORE INTO cases VALUES (?,?,?,?,?,?,?,?,?,?)",(eid,payload["fir"],crime,f"SYN-STN-{i%12:02d}",f"SYN-DST-{i%4:02d}",payload["offence"],incident.isoformat(),registered.isoformat(),"UNRESOLVED" if i%3 else "RESOLVED",sr))
    for i in range(1, counts["persons"] + 1):
        eid=f"SYN-PER-{i:04d}"; payload={"name":f"Synthetic Person {i:04d}","birth_year":1980+i%25,"address":f"Synthetic Address Block {i%100:03d}"}
        if i==2: payload.update({"name":"Synthetic Person 0001","birth_year":1999,"address":"Synthetic Address Conflict"})
        sr=_source_record(conn,"CCTNS_REPLICA",eid,payload,timestamp)
        conn.execute("INSERT OR IGNORE INTO persons VALUES (?,?,?,?,?,?)",(eid,payload["name"],payload["birth_year"],payload["address"],"CANDIDATE" if i<=2 else "SYNTHETIC",sr))
    for i in range(1, counts["aliases"] + 1):
        eid=f"SYN-ALS-{i:04d}"; person=f"SYN-PER-{(i%counts['persons'])+1:04d}"; sr=_source_record(conn,"CCTNS_REPLICA",eid,{"alias":f"Synthetic Alias {i:04d}"},timestamp)
        conn.execute("INSERT OR IGNORE INTO aliases VALUES (?,?,?,?)",(eid,person,f"Synthetic Alias {i:04d}",sr))
    for i in range(1, counts["organisations"]+1):
        eid=f"SYN-ORG-{i:04d}"; sr=_source_record(conn,"CCTNS_REPLICA",eid,{"name":f"Synthetic Organisation {i:04d}"},timestamp)
        conn.execute("INSERT OR IGNORE INTO organisations VALUES (?,?,?,?)",(eid,f"Synthetic Organisation {i:04d}","SYNTHETIC_ENTITY",sr))
    for i in range(1, counts["documents"]+1):
        eid=f"SYN-DOC-{i:04d}"; case=f"SYN-CASE-{(i%counts['cases'])+1:04d}"; sr=_source_record(conn,"CCTNS_REPLICA",eid,{"case":case,"type":"SYNTHETIC_COMPLAINT"},timestamp)
        conn.execute("INSERT OR IGNORE INTO documents VALUES (?,?,?,?,?)",(eid,case,"SYNTHETIC_COMPLAINT","AVAILABLE",sr))
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
            conn.execute("INSERT OR IGNORE INTO trust_issues VALUES (?,?,?,?,?,?,?)",(f"SYN-ISSUE-{story['id']}",case_id,story["type"],"SEEDED",json.dumps(story,sort_keys=True),"[]","OPEN"))
    conn.execute("INSERT OR IGNORE INTO trust_issues VALUES (?,?,?,?,?,?,?)",("SYN-ISSUE-MISSING-SOURCE","SYN-CASE-0001","missing_source","SEEDED","Synthetic complaint source intentionally absent for later verification tests","[]","OPEN"))
    conn.commit()
    result={name:repository.table_count(name) for name in ("cases","persons","aliases","organisations","documents","vehicles","phones","devices","locations","evidence_records","forensic_events","entity_edges","case_dna_features")}
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
