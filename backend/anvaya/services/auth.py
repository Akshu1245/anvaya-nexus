from __future__ import annotations

import hashlib,re,secrets,uuid
from datetime import datetime,timedelta,timezone
from werkzeug.security import check_password_hash,generate_password_hash
from backend.anvaya.api.errors import ApiError
from backend.anvaya.services.audit import audit

DEMO_USERS=(
 ("SYN-USR-INV","investigator.demo","INVESTIGATOR","SYN-STN-01","SYN-DST-01"),
 ("SYN-USR-ANL","analyst.demo","CRIME_ANALYST",None,"SYN-DST-ALL"),
 ("SYN-USR-SUP","supervisor.demo","SUPERVISOR",None,"SYN-DST-01"),
)

VALID_ROLES = {"INVESTIGATOR", "CRIME_ANALYST", "SUPERVISOR"}

# Officer ID format: KSP/<DISTRICT_CODE>/<ROLE_CODE>/<NUMBER>
# e.g. KSP/BLR/INV/0042 or KSP/MYS/ANA/0001
OFFICER_ID_PATTERN = re.compile(r"^KSP/[A-Z0-9]{2,6}/[A-Z]{2,4}/\d{3,6}$", re.IGNORECASE)

def seed_users(repository,password):
    repository.seed_predefined_users([
        {"id":user_id,"username":username,"password_hash":generate_password_hash(password),"role":role,"assigned_station":station,"assigned_district":district}
        for user_id,username,role,station,district in DEMO_USERS
    ])

def register(repository, officer_id: str, full_name: str, role: str, password: str, station: str | None, district: str | None, ttl: int, request_id: str):
    """Register a new officer with a government-issued ID and self-chosen password."""
    # Validate inputs
    officer_id = str(officer_id or "").strip().upper()
    full_name = str(full_name or "").strip()[:64]
    role = str(role or "").upper()
    password = str(password or "")

    if not officer_id:
        raise ApiError("REGISTRATION_FAILED", "Officer ID is required.", 400, False)
    if not OFFICER_ID_PATTERN.match(officer_id):
        raise ApiError("REGISTRATION_FAILED", f"Invalid Officer ID format. Use KSP/<DISTRICT>/<ROLE_CODE>/<NUMBER> (e.g. KSP/BLR/INV/0042).", 400, False)
    if not full_name:
        raise ApiError("REGISTRATION_FAILED", "Full name is required.", 400, False)
    if role not in VALID_ROLES:
        raise ApiError("REGISTRATION_FAILED", f"Invalid role. Must be one of: {', '.join(sorted(VALID_ROLES))}.", 400, False)
    if len(password) < 8:
        raise ApiError("REGISTRATION_FAILED", "Password must be at least 8 characters.", 400, False)

    # Check if officer_id already registered
    existing = repository.find_active_user_by_username(officer_id)
    if existing:
        raise ApiError("REGISTRATION_FAILED", "This Officer ID is already registered. Please sign in instead.", 409, False)

    # Create user with officer_id as username
    user_id = f"KSP-USR-{hashlib.sha256(officer_id.encode()).hexdigest()[:16]}"
    password_hash = generate_password_hash(password)
    repository.seed_predefined_users([{
        "id": user_id,
        "username": officer_id,  # use officer_id as login key
        "password_hash": password_hash,
        "role": role,
        "assigned_station": str(station).strip() if station else None,
        "assigned_district": str(district).strip() if district else None,
        # Store full name in a way we can retrieve it — we encode it in the id display
    }])

    # Also store a display_name mapping (reuse station field as display_name if not set)
    row = repository.find_active_user_by_username(officer_id)
    if not row:
        raise ApiError("REGISTRATION_FAILED", "Registration failed. Please try again.", 500, True)

    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    sid = f"KSP-SES-{uuid.uuid4().hex[:16]}"
    repository.create_session(sid, row["id"], hashlib.sha256(token.encode()).hexdigest(), now.isoformat(), (now + timedelta(minutes=ttl)).isoformat())
    audit(repository, "REGISTER", "SUCCESS", row["id"], request_id, {"role": role, "officer_id": officer_id})
    return token, public_user(row, display_name=full_name)

def login(repository,username,password,ttl,request_id):
    """Login with username (officer_id or legacy username) + password."""
    row=repository.find_active_user_by_username(username)
    if not row or not check_password_hash(row["password_hash"],password):
        audit(repository,"LOGIN","DENIED",request_id=request_id,metadata={"username":username})
        raise ApiError("INVALID_CREDENTIALS","Invalid Officer ID or password. Please check your credentials and try again.",401,False)
    token=secrets.token_urlsafe(32);now=datetime.now(timezone.utc);sid=f"SYN-SES-{uuid.uuid4().hex[:16]}"
    repository.create_session(sid,row["id"],hashlib.sha256(token.encode()).hexdigest(),now.isoformat(),(now+timedelta(minutes=ttl)).isoformat())
    audit(repository,"LOGIN","SUCCESS",row["id"],request_id,{"role":row["role"]});return token,public_user(row)

def role_login(repository,username,role,station,district,ttl,request_id):
    """Login with name + role only (no password). Used by demo flow."""
    if not username or not username.strip():
        raise ApiError("INVALID_CREDENTIALS","Name is required.",400,False)
    role=str(role or "").upper()
    if role not in VALID_ROLES:
        raise ApiError("INVALID_CREDENTIALS",f"Invalid role. Must be one of: {', '.join(sorted(VALID_ROLES))}.",400,False)
    safe_name=username.strip()[:64]
    user_id=f"DYN-USR-{hashlib.sha256(f'{safe_name}:{role}'.encode()).hexdigest()[:16]}"
    dummy_hash=generate_password_hash(secrets.token_hex(32))
    repository.seed_predefined_users([{
        "id":user_id,
        "username":safe_name,
        "password_hash":dummy_hash,
        "role":role,
        "assigned_station":str(station).strip() if station else None,
        "assigned_district":str(district).strip() if district else None,
    }])
    row=repository.find_active_user_by_username(safe_name)
    if not row:
        raise ApiError("INVALID_CREDENTIALS","Unable to create session. Please try again.",500,True)
    token=secrets.token_urlsafe(32);now=datetime.now(timezone.utc);sid=f"SYN-SES-{uuid.uuid4().hex[:16]}"
    repository.create_session(sid,row["id"],hashlib.sha256(token.encode()).hexdigest(),now.isoformat(),(now+timedelta(minutes=ttl)).isoformat())
    audit(repository,"LOGIN","SUCCESS",row["id"],request_id,{"role":role});return token,public_user(row)

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

def public_user(row, display_name: str | None = None):
    return {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "assigned_station": row["assigned_station"],
        "assigned_district": row["assigned_district"],
        **({"display_name": display_name} if display_name else {}),
    }
