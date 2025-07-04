"""Loyalty and ethics enforcement for Ghosthand.

This module defines :class:`LoyaltyCore` which ensures that the agent only
executes commands from the authorised owner (William Oakley) and applies a
simple interpretation of modified Asimov laws.  All decisions are logged via
the central logger and significant rejections are stored in the memory
database.
"""

from __future__ import annotations

import re
from typing import Dict

from logger import log
from memory import log_rejection


class LoyaltyCore:
    """Implements basic loyalty rules for Ghosthand."""

    OWNER = "william"

    def can_execute(self, goal: str, user: str) -> bool:
        """Return ``True`` if the goal may be executed."""

        if user.lower() != self.OWNER:
            log("Goal rejected: unauthorised user", "GUARD")
            log_rejection(goal, "unauthorised user", user)
            return False

        harmful = [
            "rm -rf",
            "format",
            "shutdown",
            "delete system32",
            "self-destruct",
        ]
        gl = goal.lower()
        if any(h in gl for h in harmful):
            log("Goal rejected: potential harm detected", "GUARD")
            log_rejection(goal, "potentially harmful", user)
            return False

        return True

    def enforce_rules(self, step: Dict[str, object], user: str) -> Dict[str, object] | None:
        """Validate a planned step before execution."""

        if user.lower() != self.OWNER:
            log("Step skipped for unauthorised user", "GUARD")
            return None

        agent = str(step.get("agent", "")).lower()
        action = str(step.get("action", "")).lower()

        dangerous = re.compile(r"(delete|remove|format|shutdown)")
        if agent in {"os", "subprocess"} or dangerous.search(action):
            log("Step rejected: appears dangerous", "GUARD")
            log_rejection(f"{agent}.{action}", "dangerous step", user)
            return None

        return step


loyalty = LoyaltyCore()

