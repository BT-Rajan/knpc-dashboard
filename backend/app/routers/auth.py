from fastapi import APIRouter, HTTPException, status

from app.schemas import LoginRequest, LoginResponse
from app.auth import verify_credentials, issue_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    role = verify_credentials(body.username, body.password)
    if not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token = issue_token(body.username, role)
    return LoginResponse(token=token, role=role, username=body.username)
