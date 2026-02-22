from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Self


class SecurityQuestionSchema(BaseModel):
    question: str
    answer: str


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    address: str | None = None
    security_question: SecurityQuestionSchema | None = None

    @field_validator("full_name")
    @classmethod
    def full_name_length(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 100:
            raise ValueError("full_name must be 1–100 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v

    @field_validator("address")
    @classmethod
    def address_length(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 255:
            raise ValueError("address must be at most 255 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
