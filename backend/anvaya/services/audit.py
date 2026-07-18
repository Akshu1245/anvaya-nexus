import json, uuid
from datetime import datetime, timezone


def audit(repository,event_type,outcome,user_id=None,request_id=None,metadata=None):
    safe={k:v for k,v in (metadata or {}).items() if k not in {"password","token","query_text","full_value"}}
    repository.connection.execute("INSERT INTO audit_events VALUES (?,?,?,?,?,?,?)",(f"SYN-AUD-{uuid.uuid4().hex[:16]}",user_id,event_type,outcome,request_id,json.dumps(safe,sort_keys=True),datetime.now(timezone.utc).isoformat()))
    repository.connection.commit()
