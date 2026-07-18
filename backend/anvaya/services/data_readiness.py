from __future__ import annotations

import csv
import hashlib
import io
import json
import uuid
from datetime import datetime, timezone

from backend.anvaya.api.errors import ApiError
from backend.anvaya.services.generator import _checksum

REQUIRED_FIELDS = ("external_id","fir_number","crime_number","station_id","district_id","offence","incident_at","registered_at","status")


def _rows(content: bytes, input_format: str) -> list[dict]:
    try:
        text=content.decode("utf-8-sig")
        if input_format=="csv": return list(csv.DictReader(io.StringIO(text)))
        parsed=json.loads(text)
        if not isinstance(parsed,list) or not all(isinstance(row,dict) for row in parsed): raise ValueError("JSON must be an array of objects")
        return parsed
    except (UnicodeDecodeError,json.JSONDecodeError,ValueError,csv.Error) as error:
        raise ApiError("INVALID_IMPORT_FILE",str(error),400,False) from error


def validate_import(repository, content: bytes, input_format: str, source_version: str="synthetic-import-1.0") -> dict:
    if input_format not in {"csv","json"}: raise ApiError("UNSUPPORTED_IMPORT_FORMAT","Use CSV or JSON.",400,False)
    rows=_rows(content,input_format); timestamp=datetime.now(timezone.utc).isoformat(); checksum=hashlib.sha256(content).hexdigest(); job_id=f"SYN-IMPORT-{uuid.uuid4().hex[:12].upper()}"
    mapped=sorted({str(key) for row in rows for key in row.keys()}); missing=sorted(set(REQUIRED_FIELDS)-set(mapped)); accepted=[]; failures=[]; seen=set()
    existing={row[0] for row in repository.connection.execute("SELECT external_id FROM source_records WHERE source_system_id='CCTNS_REPLICA'")}
    for number,row in enumerate(rows,start=2 if input_format=="csv" else 1):
        reasons=[]
        absent=[key for key in REQUIRED_FIELDS if not str(row.get(key,"")).strip()]
        if absent: reasons.append(("missing_required_key",f"Missing: {', '.join(absent)}"))
        for field in ("incident_at","registered_at"):
            if row.get(field):
                try: datetime.fromisoformat(str(row[field]).replace("Z","+00:00"))
                except ValueError: reasons.append(("invalid_date",f"Invalid {field}"))
        external=str(row.get("external_id","")).strip()
        if external and (external in seen or external in existing): reasons.append(("duplicate_identifier","Duplicate external_id"))
        if row.get("document_id") and row.get("document_case_id")!=external: reasons.append(("unlinked_document","Document does not link to its row case"))
        if reasons:
            failures.extend({"row":number,"category":category,"reason":reason} for category,reason in reasons)
        else:
            accepted.append({key:str(row.get(key,"")) for key in mapped}); seen.add(external)
    status="VALIDATED" if not failures else ("PARTIAL" if accepted else "REJECTED")
    conn=repository.connection
    conn.execute("INSERT INTO import_jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(job_id,"CCTNS_REPLICA",input_format,checksum,source_version,status,json.dumps(mapped),json.dumps(accepted,sort_keys=True),len(accepted),len(failures),timestamp,timestamp,None))
    for failure in failures:
        conn.execute("INSERT INTO import_failures VALUES (?,?,?,?,?)",(f"SYN-FAIL-{uuid.uuid4().hex[:12].upper()}",job_id,failure["row"],failure["category"],failure["reason"]))
    conn.commit()
    return get_import_job(repository,job_id,missing)


def get_import_job(repository, job_id: str, missing_required_keys: list[str]|None=None) -> dict:
    row=repository.connection.execute("SELECT * FROM import_jobs WHERE id=?",(job_id,)).fetchone()
    if not row: raise ApiError("IMPORT_JOB_NOT_FOUND","Import job was not found.",404,False)
    failures=[{"row":f["row_number"],"category":f["category"],"reason":f["safe_reason"]} for f in repository.connection.execute("SELECT * FROM import_failures WHERE import_job_id=? ORDER BY row_number",(job_id,))]
    return {"id":row["id"],"input_format":row["input_format"],"mapped_fields":json.loads(row["mapped_fields_json"]),"missing_required_keys":missing_required_keys or [],"accepted_count":row["accepted_count"],"failed_count":row["failed_count"],"failures":failures,"status":row["status"],"import_timestamp":row["started_at"],"checksum":row["checksum"],"source_version":row["source_version"],"committed_at":row["committed_at"]}


def commit_import(repository, job_id: str) -> dict:
    conn=repository.connection; row=conn.execute("SELECT * FROM import_jobs WHERE id=?",(job_id,)).fetchone()
    if not row: raise ApiError("IMPORT_JOB_NOT_FOUND","Import job was not found.",404,False)
    if row["committed_at"]: return get_import_job(repository,job_id)
    imported=datetime.now(timezone.utc).isoformat()
    for item in json.loads(row["accepted_rows_json"]):
        external=item["external_id"]; sr=f"SYN-SR-CCTNS-IMPORT-{job_id}-{external}"; payload={key:item[key] for key in REQUIRED_FIELDS}
        conn.execute("INSERT INTO source_records VALUES (?,?,?,?,?,?,?,?,?,?,?)",(sr,"CCTNS_REPLICA",external,row["source_version"],item["registered_at"],imported,"RESTRICTED","Primary operational record","Fresh",_checksum(payload),json.dumps(payload,sort_keys=True)))
        conn.execute("INSERT INTO transformation_events VALUES (?,?,?,?,?,?,?,?)",(f"SYN-TR-{sr}",sr,"CSV_JSON_CANONICAL_MAP","*","cases","M2-1.0",imported,"ACCEPTED"))
        conn.execute("INSERT INTO cases VALUES (?,?,?,?,?,?,?,?,?,?)",(external,item["fir_number"],item["crime_number"],item["station_id"],item["district_id"],item["offence"],item["incident_at"],item["registered_at"],item["status"],sr))
    conn.execute("UPDATE import_jobs SET status='COMMITTED', committed_at=? WHERE id=?",(imported,job_id)); conn.commit()
    return get_import_job(repository,job_id)
