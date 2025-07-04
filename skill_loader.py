"""Dynamic loading of optional skill modules."""

import importlib.util
from pathlib import Path
from typing import Dict, Any

from logger import log

_LOADED: Dict[str, Any] = {}


def load_skills() -> Dict[str, Any]:
    """Discover skills in the ``skills`` directory and load them."""
    skills_dir = Path("skills")
    skills_dir.mkdir(exist_ok=True)
    for file in skills_dir.glob("*.py"):
        name = file.stem
        if name in _LOADED:
            continue
        try:
            spec = importlib.util.spec_from_file_location(name, file)
            if not spec or not spec.loader:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "can_handle") and hasattr(module, "execute"):
                _LOADED[name] = module
                log(f"Loaded skill {name}", "SKILL")
            else:
                log(f"Skipping {name}, missing interface", "WARNING")
        except Exception as exc:
            log(f"Failed to load skill {name}: {exc}", "ERROR")
    return _LOADED


def get_skill(name: str):
    """Return a previously loaded skill by name."""
    return _LOADED.get(name)
