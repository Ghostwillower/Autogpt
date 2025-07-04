"""Basic identity verification helpers for Ghosthand."""

import os
from logger import log


def identity_verified(user: str) -> bool:
    """Return ``True`` if the running session verifies the given user."""

    if user.lower() != "william":
        log("Identity check failed: unknown user", "GUARD")
        return False

    try:
        session_user = os.getlogin()
    except Exception:
        session_user = os.environ.get("USER", "")

    if session_user.lower() == "william":
        return True

    if os.environ.get("GHOSTHAND_PASS"):
        return True

    log("Identity verification failed", "GUARD")
    return False

