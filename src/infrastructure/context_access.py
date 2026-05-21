"""
Process-global AppContext accessor.

Nodes and services that run inside APScheduler jobs can't receive AppContext
through FastAPI's dependency injection because they execute outside a request
cycle. This module provides a simple get/set pair so those callsites can reach
the same context that was built at startup.

set_app_context is called exactly once during lifespan startup. The guard on
double-init catches test setups or accidental re-imports that would silently
replace the live context.
"""

from __future__ import annotations

from infrastructure.app_context import AppContext

_app_context: AppContext | None = None


def set_app_context(ctx: AppContext) -> None:
    global _app_context

    if _app_context is not None:
        raise RuntimeError("AppContext already initialized")

    _app_context = ctx


def get_app_context() -> AppContext:
    if _app_context is None:
        raise RuntimeError("AppContext not initialized")

    return _app_context