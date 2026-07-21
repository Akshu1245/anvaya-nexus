from __future__ import annotations

import hashlib,secrets,uuid
from datetime import datetime,timedelta,timezone
from werkzeug.security import check_password_hash,generate_password_hash
from backend.anvaya.api.errors import ApiError
from backend.anvaya.services.audit import audit

DEMO_USERS=(
 ("SYN-USR-INV","investigator.demo","INVESTIGATOR","SYN-STN-01","SYN-DST-01"),
 ("SYN-USR-ANL","analyst.demo","CRIME_ANALYST",None,"SYN-DST-ALL"),
 ("SYN-USR-SUP","supervisor.demo","SUPERVISOR",None,"SYN-DST-01"),
)

def seed_users(repository,password):
    repository.seed_predefined_users([
        {"id":user_id,"username":username,"password_hash":generate_password_hash(password),"role":role,"assigned_station":station,"assigned_district":district}
        for user_id,username,role,station,district in DEMO_USERS
    ])

def login(repository,username,password,ttl,request_id):
    row=repository.find_active_user_by_username(username)
    if not row or not check_password_hash(row["password_hash"],password):
        audit(repository,"LOGIN","DENIED",request_id=request_id,metadata={"username":username});raise ApiError("INVALID_CREDENTIALS","Invalid demo credentials.",401,False)
    token=secrets.token_urlsafe(32);now=datetime.now(timezone.utc);sid=f"SYN-SES-{uuid.uuid4().hex[:16]}"
    repository.create_session(sid,row["id"],hashlib.sha256(token.encode()).hexdigest(),now.isoformat(),(now+timedelta(minutes=ttl)).isoformat())
    audit(repository,"LOGIN","SUCCESS",row["id"],request_id,{"role":row["role"]});return token,public_user(row)

def current_user(repository,token,request_id=None):
    if not token: raise ApiError("AUTHENTICATION_REQUIRED","Authentication is required.",401,False)
    digest=hashlib.sha256(token.encode()).hexdigest();row=repository.find_session_with_user(digest)
    if not row: raise ApiError("INVALID_SESSION","Session is invalid.",401,False)
    if row["revoked_at"]: raise ApiError("SESSION_REVOKED","Session has been revoked.",401,False)
    if datetime.fromisoformat(row["expires_at"])<=datetime.now(timezone.utc):
        audit(repository,"SESSION_EXPIRED","DENIED",row["id"],request_id,{});raise ApiError("SESSION_EXPIRED","Session has expired.",401,False)
    return row

def revoke(repository,token,request_id):
    row=current_user(repository,token,request_id);now=datetime.now(timezone.utc).isoformat();repository.revoke_session(row["session_id"],now);audit(repository,"LOGOUT","SUCCESS",row["id"],request_id,{})

def public_user(row):return {"id":row["id"],"username":row["username"],"role":row["role"],"assigned_station":row["assigned_station"],"assigned_district":row["assigned_district"]}
