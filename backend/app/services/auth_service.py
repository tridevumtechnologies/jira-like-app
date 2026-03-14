"""Auth service — register, login, token rotation, logout."""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    decode_token,
)
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest


async def register_user(payload: RegisterRequest, db: AsyncSession) -> tuple[str, str, str]:
    """
    Create a new user.
    Returns (access_token, refresh_token, jti).
    Raises 409 if email is taken.
    """
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
            headers={"code": "EMAIL_TAKEN"},
        )

    # Hash security answer if provided
    security_answer_hash: str | None = None
    security_question_text: str | None = None
    if payload.security_question:
        security_question_text = payload.security_question.question
        security_answer_hash = hash_password(payload.security_question.answer)

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        address=payload.address,
        security_question=security_question_text,
        security_answer_hash=security_answer_hash,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return await _issue_token_pair(user)


async def login_user(payload: LoginRequest, db: AsyncSession) -> tuple[str, str, str]:
    """
    Authenticate user.
    Returns (access_token, refresh_token, jti).
    Raises 401 on bad credentials.
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalars().first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"code": "INVALID_CREDENTIALS"},
        )

    return await _issue_token_pair(user)


async def refresh_tokens(refresh_token: str) -> tuple[str, str, str]:
    """
    Validate refresh token and rotate it.
    Returns (access_token, new_refresh_token, new_jti).
    Raises 401 on any failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token is invalid or expired.",
        headers={"code": "TOKEN_EXPIRED"},
    )
    try:
        payload = decode_token(refresh_token)
        user_id: str = payload.get("sub", "")
        jti: str = payload.get("jti", "")
        if not user_id or not jti or payload.get("type") != "refresh":
            raise credentials_exception
    except Exception:
        raise credentials_exception

    # Stateless refresh flow: PostgreSQL remains the only required backend service.
    new_access = create_access_token(subject=user_id)
    new_refresh, new_jti = create_refresh_token(user_id=user_id)

    return new_access, new_refresh, new_jti


async def logout_user(user_id: str, refresh_token: str | None) -> None:
    """Stateless logout; the client cookie is cleared by the router."""
    _ = user_id
    _ = refresh_token
    return


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

async def _issue_token_pair(user: User) -> tuple[str, str, str]:
    """Issue a token pair. Returns (access_token, refresh_token, jti)."""
    user_id = str(user.id)
    access_token = create_access_token(subject=user_id)
    refresh_token, jti = create_refresh_token(user_id=user_id)

    return access_token, refresh_token, jti
