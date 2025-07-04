"""SQLite-backed memory system for Ghosthand.

Stores instructions or other persistent context so that future runs can
access prior interactions.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

from logger import log

DB_PATH = Path("data/memory.db")

class Memory:
    """Simple wrapper around SQLite for storing instructions."""

    def __init__(self, db_path: str = str(DB_PATH)):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS instructions (id INTEGER PRIMARY KEY, text TEXT)"
        )
        self.conn.commit()

    def store_instruction(self, text: str) -> None:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO instructions(text) VALUES (?)", (text,))
        self.conn.commit()

    def last_instruction(self) -> Optional[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT text FROM instructions ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else None


def _connect() -> sqlite3.Connection:
    """Return a connection to the goal log database."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return conn


def learn_preference(user: str, category: str, key: str, value: str) -> None:
    """Store a user preference value."""
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS preferences (user TEXT, category TEXT, key TEXT, value TEXT, PRIMARY KEY(user, category, key))"
        )
        cur.execute(
            "INSERT OR REPLACE INTO preferences(user, category, key, value) VALUES (?, ?, ?, ?)",
            (user, category, key, value),
        )
        conn.commit()
        log(f"Stored preference {user}/{category}/{key}")
    except Exception as exc:
        log(f"Failed to store preference: {exc}", "ERROR")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_preference(user: str, category: str, key: str) -> Optional[str]:
    """Retrieve a stored user preference."""
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS preferences (user TEXT, category TEXT, key TEXT, value TEXT, PRIMARY KEY(user, category, key))"
        )
        cur.execute(
            "SELECT value FROM preferences WHERE user = ? AND category = ? AND key = ?",
            (user, category, key),
        )
        row = cur.fetchone()
        return row[0] if row else None
    except Exception as exc:
        log(f"Failed to get preference: {exc}", "ERROR")
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def log_goal(goal: str, result_summary: str, user: str) -> None:
    """Record a goal, user and result summary with a timestamp."""

    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS goal_log (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user TEXT, goal TEXT, result TEXT)"
        )
        ts = datetime.now().isoformat(timespec="seconds")
        cur.execute(
            "INSERT INTO goal_log(timestamp, user, goal, result) VALUES (?, ?, ?, ?)",
            (ts, user, goal, result_summary),
        )
        conn.commit()
        log(f"Logged goal at {ts}", "INFO")
    except Exception as exc:  # pragma: no cover - best effort logging
        log(f"Failed to log goal: {exc}", "ERROR")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def log_rejection(goal: str, reason: str, user: str) -> None:
    """Record that a goal was rejected with the given reason."""

    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS rejections (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user TEXT, goal TEXT, reason TEXT)"
        )
        ts = datetime.now().isoformat(timespec="seconds")
        cur.execute(
            "INSERT INTO rejections(timestamp, user, goal, reason) VALUES (?, ?, ?, ?)",
            (ts, user, goal, reason),
        )
        conn.commit()
        log(f"Logged rejection for {user}: {reason}", "INFO")
    except Exception as exc:  # pragma: no cover
        log(f"Failed to log rejection: {exc}", "ERROR")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_recent_goals(limit: int = 5, user: Optional[str] = None) -> List[Tuple[str, str, str]]:
    """Return the most recent goals with timestamps."""

    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS goal_log (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user TEXT, goal TEXT, result TEXT)"
        )
        if user:
            cur.execute(
                "SELECT timestamp, goal, result FROM goal_log WHERE user = ? ORDER BY id DESC LIMIT ?",
                (user, limit),
            )
        else:
            cur.execute(
                "SELECT timestamp, goal, result FROM goal_log ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        rows = cur.fetchall()
        return rows
    except Exception as exc:  # pragma: no cover - best effort retrieval
        log(f"Failed to fetch recent goals: {exc}", "ERROR")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def list_users() -> List[str]:
    """Return distinct user identifiers known to the memory system."""
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS goal_log (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user TEXT, goal TEXT, result TEXT)"
        )
        cur.execute("SELECT DISTINCT user FROM goal_log")
        rows = cur.fetchall()
        return [r[0] for r in rows if r[0]]
    except Exception as exc:
        log(f"Failed to list users: {exc}", "ERROR")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def query_memory(goal: str, user: Optional[str] = None) -> List[Tuple[str, str, str]]:
    """Return up to three past goals similar to the provided goal."""
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS goal_log (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user TEXT, goal TEXT, result TEXT)"
        )
        if user:
            cur.execute("SELECT timestamp, goal, result FROM goal_log WHERE user = ?", (user,))
        else:
            cur.execute("SELECT timestamp, goal, result FROM goal_log")
        rows = cur.fetchall()
        goals = [row[1] for row in rows]

        results: List[Tuple[str, str, str]] = []
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            vect = TfidfVectorizer().fit(goals + [goal])
            mat = vect.transform(goals + [goal])
            sims = cosine_similarity(mat[-1], mat[:-1]).flatten()
            top_idx = sims.argsort()[::-1][:3]
            for idx in top_idx:
                if sims[idx] <= 0:
                    continue
                ts, gtxt, res = rows[idx]
                results.append((ts, gtxt, res))
        except Exception:
            import difflib

            matches = difflib.get_close_matches(goal, goals, n=3, cutoff=0.4)
            for m in matches:
                for ts, gtxt, res in rows:
                    if gtxt == m:
                        results.append((ts, gtxt, res))
                        break
        return results
    except Exception as exc:  # pragma: no cover - best effort
        log(f"Failed to query memory: {exc}", "ERROR")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass



def _ensure_event_table(cur):
    cur.execute(
        "CREATE TABLE IF NOT EXISTS events (timestamp TEXT, event TEXT, user TEXT, details TEXT)"
    )


def log_first_run() -> None:
    """Record the first run time."""
    try:
        conn = _connect()
        cur = conn.cursor()
        _ensure_event_table(cur)
        ts = datetime.now().isoformat(timespec="seconds")
        cur.execute(
            "INSERT INTO events(timestamp, event, user, details) VALUES (?, 'first_run', '', '')",
            (ts,),
        )
        conn.commit()
        log("First run logged", "INFO")
    except Exception as exc:  # pragma: no cover
        log(f"Failed to log first run: {exc}", "ERROR")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def log_voice_verification(user: str, success: bool) -> None:
    """Record the result of a voice verification attempt."""
    try:
        conn = _connect()
        cur = conn.cursor()
        _ensure_event_table(cur)
        ts = datetime.now().isoformat(timespec="seconds")
        cur.execute(
            "INSERT INTO events(timestamp, event, user, details) VALUES (?, 'voice', ?, ?)",
            (ts, user, "success" if success else "fail"),
        )
        conn.commit()
    except Exception as exc:
        log(f"Failed to log voice verification: {exc}", "ERROR")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def log_tamper(details: str) -> None:
    """Record a potential tamper event."""
    try:
        conn = _connect()
        cur = conn.cursor()
        _ensure_event_table(cur)
        ts = datetime.now().isoformat(timespec="seconds")
        cur.execute(
            "INSERT INTO events(timestamp, event, user, details) VALUES (?, 'tamper', '', ?)",
            (ts, details),
        )
        conn.commit()
        log("Tamper event logged", "GUARD")
    except Exception as exc:
        log(f"Failed to log tamper: {exc}", "ERROR")
    finally:
        try:
            conn.close()
        except Exception:
            pass
