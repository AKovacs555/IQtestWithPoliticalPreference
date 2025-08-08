
"""Compatibility wrapper for the backend FastAPI application.

This module proxies all attribute access and assignment to
``backend.main``. The tests patch objects such as ``AD_REWARD_POINTS``
or ``get_surveys`` on the top level :mod:`main` module. Previously this
file imported everything from ``backend.main`` using ``*`` which copied
objects by value. Patching ``main`` therefore did not affect the
original definitions used by the application, leading to tests failing
when they attempted to monkeypatch configuration or helper functions.

By delegating attribute access and assignment to ``backend.main`` we keep
both modules in sync: updates made via ``main`` are reflected in
``backend.main`` and vice versa.
"""

from __future__ import annotations

import sys
import types

from backend import main as _backend_main

# Re-export the FastAPI application instance
app = _backend_main.app


class _MainProxy(types.ModuleType):
    """Module proxy forwarding attribute access to ``backend.main``."""

    def __getattr__(self, name: str):  # pragma: no cover - trivial forwarding
        return getattr(_backend_main, name)

    def __setattr__(self, name: str, value):  # pragma: no cover - trivial forwarding
        setattr(_backend_main, name, value)


# Replace this module's type so attribute access/assignment uses the proxy
sys.modules[__name__].__class__ = _MainProxy
