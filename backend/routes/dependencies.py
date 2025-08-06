from backend.deps.auth import get_current_user as _get_current_user


def is_admin(user: dict) -> bool:
    """Return True if the user has admin privileges."""
    return bool(user.get("is_admin"))


def get_current_user(*args, **kwargs):
    return _get_current_user(*args, **kwargs)
