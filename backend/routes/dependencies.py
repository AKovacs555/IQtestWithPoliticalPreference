import os
from fastapi import Depends, Header, HTTPException

from backend.deps.auth import (
    get_current_user as _get_current_user,
    User,
)


def is_admin(user: User) -> bool:
    """Return True if the user has admin privileges."""
    return bool(user.is_admin)


def get_current_user(*args, **kwargs) -> User:
    return _get_current_user(*args, **kwargs)


def require_admin(
    user: User = Depends(get_current_user),
    admin_key: str = Header(..., alias="X-Admin-Api-Key"),
):
    """Ensure the request is from an admin and the API key matches."""

    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    if admin_key != os.getenv("ADMIN_API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid admin API key")
    return True
