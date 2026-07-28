"""
Minimal auth for two hardcoded accounts (admin / viewer). No user table,
no signup — matches the brief. Tokens are a signed, timestamped blob so we
don't need a sessions table either.
"""
import base64
import hashlib
import hmac
import time
from fastapi import Depends, Header, HTTPException, status

from app.config import USERS, SESSION_SECRET, SESSION_TTL_HOURS


def _sign(payload: str) -> str:
    return hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def issue_token(username: str, role: str) -> str:
    expiry = int(time.time()) + SESSION_TTL_HOURS * 3600
    payload = f"{username}:{role}:{expiry}"
    sig = _sign(payload)
    raw = f"{payload}:{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def verify_credentials(username: str, password: str):
    user = USERS.get(username)
    if not user or user["password"] != password:
        return None
    return user["role"]


def _decode_token(token: str):
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        username, role, expiry, sig = raw.split(":")
    except Exception:
        return None
    payload = f"{username}:{role}:{expiry}"
    if not hmac.compare_digest(_sign(payload), sig):
        return None
    if int(expiry) < time.time():
        return None
    return {"username": username, "role": role}


def get_current_user(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    session = _decode_token(token)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")
    return session


def get_current_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
