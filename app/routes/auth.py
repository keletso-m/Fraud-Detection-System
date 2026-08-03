from fastapi import APIRouter, HTTPException, status
from app.auth.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.auth.models import create_user, get_user, verify_password
from app.auth.jwt import create_access_token
# add slowapi imports for rate limiting
from fastapi import APIRouter, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest):
    ok = create_user(body.username, body.password, body.role)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    return {"message": f"User '{body.username}' created with role '{body.role}'"}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    user = get_user(body.username)
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return TokenResponse(access_token=token, role=user["role"])