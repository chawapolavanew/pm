import secrets
from typing import Annotated, Optional
from fastapi import Header, HTTPException

_tokens: dict[str, str] = {}  # token -> username


def create_token(username: str) -> str:
    token = secrets.token_urlsafe(32)
    _tokens[token] = username
    return token


def revoke_token(token: str) -> None:
    _tokens.pop(token, None)


def _extract_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return authorization.removeprefix("Bearer ")


def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
) -> str:
    token = _extract_token(authorization)
    username = _tokens.get(token)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return username


def check_credentials(username: str, password: str) -> bool:
    """Validate credentials against the database."""
    from database import get_db, verify_password
    with get_db() as db:
        row = db.execute(
            "SELECT password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
    if not row:
        return False
    return verify_password(password, row["password_hash"])
