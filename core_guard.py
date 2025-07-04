"""Startup integrity checks and voice enrollment management."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
import hmac
import hashlib
from pathlib import Path

from logger import log
from voice_auth import enroll_user, record_voice_sample, verify_user, is_enrolled
from memory import log_first_run, log_tamper


SECRET_KEY = "521f993ae1b34f84b097567e9b9b1081"  # generated once
CONFIG_FILE = Path(".ghosthand_lock.json")
VOICE_DIR = Path("voiceprints")


def _hmac(data: bytes) -> str:
    return hmac.new(SECRET_KEY.encode(), data, hashlib.sha256).hexdigest()


def initialize_core() -> None:
    """Initialise voice enrollment on first run and create lock file."""
    if not CONFIG_FILE.exists():
        log("First run detected. Initialising core", "GUARD")
        VOICE_DIR.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            record_voice_sample(tmp.name, 5)
            enroll_user("william", tmp.name)
        cfg = {
            "first_run": False,
            "enrolled_user": "william",
            "system_id": uuid.getnode(),
        }
        fingerprint = _hmac(json.dumps(cfg, sort_keys=True).encode())
        cfg["fingerprint"] = fingerprint
        CONFIG_FILE.write_text(json.dumps(cfg))
        os.chmod(CONFIG_FILE, 0o400)
        log_first_run()
        log("Core initialised", "GUARD")


def verify_integrity() -> None:
    """Verify startup configuration integrity."""
    if not CONFIG_FILE.exists():
        log_tamper("config missing")
        raise RuntimeError("Missing lock file")
    cfg = json.loads(CONFIG_FILE.read_text())
    fingerprint = cfg.get("fingerprint", "")
    tmp = cfg.copy()
    tmp.pop("fingerprint", None)
    check = _hmac(json.dumps(tmp, sort_keys=True).encode())
    if not hmac.compare_digest(fingerprint, check):
        log_tamper("fingerprint mismatch")
        raise RuntimeError("Integrity check failed")
    if cfg.get("first_run"):
        raise RuntimeError("Core not initialised")
    if cfg.get("system_id") != uuid.getnode():
        log_tamper("system id changed")
        raise RuntimeError("System mismatch")
    log("Integrity verified", "GUARD")
