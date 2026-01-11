from pydantic import BaseModel


class Token(BaseModel):
    token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str


class TokenPayload(BaseModel):
    user_id: int
    email: str
    role: str
