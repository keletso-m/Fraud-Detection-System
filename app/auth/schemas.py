from pydantic import BaseModel #validates API request and response data
from typing import Literal


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: Literal["admin", "viewer"] = "viewer"


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str