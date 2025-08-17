from fastapi import Depends, HTTPException, Header

from ..deps.auth import (
    get_current_user as _get_current_user,
    User,
)


def is_admin(user: User) -> bool:
    """Return True if the user has admin privileges."""
    return bool(user.is_admin)


def get_current_user(authorization: str = Header(None)) -> User:
    return _get_current_user(authorization)


def require_admin(user: User = Depends(get_current_user)):
    """Ensure the request is from an admin."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return True
