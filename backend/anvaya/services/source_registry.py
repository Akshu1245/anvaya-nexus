from __future__ import annotations

from datetime import datetime, timedelta, timezone

SOURCE_DEFINITIONS = (
    ("CCTNS_REPLICA", "Synthetic CCTNS-style Case Replica", "Operational", "RESTRICTED", "Primary operational record", "file_import", "P0"),
    ("FORENSICS_REPLICA", "Synthetic Forensics Replica", "Specialist", "RESTRICTED", "Specialist corroboration", "seed_fixture", "P0"),
    ("VEHICLE_REPLICA", "Synthetic Vehicle Registry Replica", "Administrative", "RESTRICTED", "Authoritative administrative replica", "seed_fixture", "P0"),
    ("CONTEXT_FIXTURE", "Offline Public Context/GIS Fixture", "Context", "PUBLIC_CONTEXT", "Context only; never case proof", "offline_fixture", "P0"),
    ("COURT_REPLICA", "Court Metadata Replica — P1", "Justice", "UNAVAILABLE", "Future synthetic procedural metadata", "unavailable", "P1"),
    ("PROSECUTION_REPLICA", "Prosecution Observations Replica — P1", "Justice", "UNAVAILABLE", "Future synthetic procedural metadata", "unavailable", "P1"),
)


def freshness_state(last_sync: str | None, threshold_hours: int, available: bool = True, now: datetime | None = None) -> str:
    if not available or not last_sync:
        return "Unavailable"
    current = now or datetime.now(timezone.utc)
    synced = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
    return "Fresh" if current - synced <= timedelta(hours=threshold_hours) else "Stale"


def seed_source_registry(repository, config, now: datetime | None = None) -> None:
    current = now or datetime.now(timezone.utc)
    thresholds = {
        "CCTNS_REPLICA": config["CCTNS_FRESHNESS_HOURS"], "FORENSICS_REPLICA": config["FORENSICS_FRESHNESS_HOURS"],
        "VEHICLE_REPLICA": config["VEHICLE_FRESHNESS_HOURS"], "CONTEXT_FIXTURE": config["CONTEXT_FRESHNESS_HOURS"],
        "COURT_REPLICA": 0, "PROSECUTION_REPLICA": 0,
    }
    sources = []
    for source_id, name, tier, access, role, connector, priority in SOURCE_DEFINITIONS:
        available = priority == "P0"
        last_sync = current.isoformat() if available else None
        state = freshness_state(last_sync, thresholds[source_id], available, current)
        sources.append({"id":source_id,"name":name,"source_tier":tier,"access_class":access,"reliability_role":role,"status":state,"last_successful_sync":last_sync,"freshness_threshold_hours":thresholds[source_id],"version":"M2-1.0","connector_type":connector,"description":"Synthetic/offline datathon source; no live integration.","priority":priority})
    repository.upsert_source_systems(sources)


def list_sources(repository, now: datetime | None = None) -> list[dict]:
    rows = repository.list_source_systems()
    result = []
    for row in rows:
        item = dict(row)
        item["status"] = freshness_state(item["last_successful_sync"], item["freshness_threshold_hours"], item["connector_type"] != "unavailable", now)
        result.append(item)
    return result
