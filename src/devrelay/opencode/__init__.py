"""DevRelay v0.3-A OpenCode session bridge.

A narrow, provider-contained bridge to one explicitly configured, already
running OpenCode server.  See ``docs/v0.3/V03A_SPEC.md`` for the contract and
``devrelay.opencode.bridge.OpenCodeBridge`` for the capability surface.
"""

from devrelay.opencode.bridge import (
    CAP_INTERRUPT,
    CAP_LIST_SESSIONS,
    CAP_MESSAGES,
    OpenCodeBridge,
)
from devrelay.opencode.models import (
    OpenCodeCallRecord,
    OpenCodeCallState,
    OpenCodeHealth,
    OpenCodeMessage,
    OpenCodeMessagePage,
    OpenCodeMessagePart,
    OpenCodeOperationResult,
    OpenCodeOperationState,
    OpenCodeSession,
    OpenCodeSessionState,
)
from devrelay.opencode.transport import OpenCodePaths, OpenCodeTransport

__all__ = [
    "CAP_INTERRUPT",
    "CAP_LIST_SESSIONS",
    "CAP_MESSAGES",
    "OpenCodeBridge",
    "OpenCodeCallRecord",
    "OpenCodeCallState",
    "OpenCodeHealth",
    "OpenCodeMessage",
    "OpenCodeMessagePage",
    "OpenCodeMessagePart",
    "OpenCodeOperationResult",
    "OpenCodeOperationState",
    "OpenCodePaths",
    "OpenCodeSession",
    "OpenCodeSessionState",
    "OpenCodeTransport",
]
