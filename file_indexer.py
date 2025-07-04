"""Utility module for building and searching a simple file index."""

import os
import sqlite3
from pathlib import Path
from typing import List, Optional

from logger import log

DB_PATH = Path("data/file_index.db")

SUPPORTED_EXT = {".docx", ".xlsx", ".pdf", ".txt", ".png", ".jpg", ".jpeg"}


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def build_file_index(base_dirs: List[str]) -> None:
    """Walk given directories and store file metadata in an index."""
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, name TEXT, size INTEGER, mtime REAL, type TEXT)"
        )
        for base in base_dirs:
            try:
                for root, _, files in os.walk(base):
                    for fname in files:
                        ext = os.path.splitext(fname)[1].lower()
                        if ext not in SUPPORTED_EXT:
                            continue
                        fpath = os.path.join(root, fname)
                        try:
                            stat = os.stat(fpath)
                        except Exception:
                            continue
                        cur.execute(
                            "INSERT OR REPLACE INTO files(path, name, size, mtime, type) VALUES (?, ?, ?, ?, ?)",
                            (fpath, fname, stat.st_size, stat.st_mtime, ext.lstrip(".")),
                        )
            except Exception as exc:
                log(f"Failed to scan {base}: {exc}", "WARNING")
        conn.commit()
        log("File index updated")
    except Exception as exc:
        log(f"Build failed: {exc}", "ERROR")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def search_index(keywords: List[str], type_filter: Optional[str] = None) -> List[str]:
    """Search the file index for files matching keywords and type."""
    matches: List[str] = []
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, name TEXT, size INTEGER, mtime REAL, type TEXT)"
        )
        cur.execute("SELECT path, name, type FROM files")
        rows = cur.fetchall()
        for path, name, ftype in rows:
            if type_filter and ftype != type_filter.lower():
                continue
            lowered = name.lower()
            if all(kw.lower() in lowered for kw in keywords):
                matches.append(path)
    except Exception as exc:
        log(f"Search failed: {exc}", "ERROR")
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return matches
