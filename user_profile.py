"""User profile utilities for Ghosthand."""

import os
from typing import Optional


def detect_user(cli_user: Optional[str] = None) -> str:
    """Return the username from CLI or system."""
    if cli_user:
        return cli_user
    try:
        return os.getlogin()
    except Exception:
        return os.environ.get("USER", "default")
