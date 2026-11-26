"""DeepTutor execution context helpers for the MCP bridge."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from deeptutor.multi_user.paths import local_admin_user, user_context


@asynccontextmanager
async def deep_context() -> AsyncIterator[None]:
    """Run the wrapped call inside the local-admin DeepTutor user context.

    The MCP bridge is a trusted local sidecar, so all calls execute as the
    local administrator. Tools that read user/workspace data need this
    context to resolve their data roots.
    """
    with user_context(local_admin_user()):
        yield
