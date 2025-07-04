"""Goal scheduling utilities for Ghosthand."""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from memory import DB_PATH
from logger import log


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def add_goal(goal: str, user: str, run_at: datetime, interval: Optional[int] = None) -> None:
    """Add a goal to the queue."""
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS goal_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, goal TEXT, user TEXT, run_at TEXT, interval INTEGER)"
        )
        cur.execute(
            "INSERT INTO goal_queue(goal, user, run_at, interval) VALUES (?, ?, ?, ?)",
            (goal, user, run_at.isoformat(timespec='seconds'), interval),
        )
        conn.commit()
        log(f"Goal queued for {run_at}")
    except Exception as exc:
        log(f"Failed to add goal: {exc}", "ERROR")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def run_due_goals() -> None:
    """Execute any goals whose scheduled time has arrived."""
    now = datetime.now().isoformat(timespec='seconds')
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS goal_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, goal TEXT, user TEXT, run_at TEXT, interval INTEGER)"
        )
        cur.execute("SELECT id, goal, user, run_at, interval FROM goal_queue WHERE run_at <= ?", (now,))
        rows = cur.fetchall()
        for goal_id, goal_text, user, run_at_str, interval in rows:
            log(f"Running queued goal for {user}: {goal_text}")
            from main import run_goal  # local import to avoid circular dependency
            run_goal(goal_text, user=user)
            if interval:
                next_run = datetime.now() + timedelta(minutes=interval)
                cur.execute(
                    "UPDATE goal_queue SET run_at = ? WHERE id = ?",
                    (next_run.isoformat(timespec='seconds'), goal_id),
                )
                log(f"Rescheduled goal {goal_id} for {next_run}")
            else:
                cur.execute("DELETE FROM goal_queue WHERE id = ?", (goal_id,))
                log(f"Removed executed goal {goal_id}")
        conn.commit()
    except Exception as exc:
        log(f"Failed to run due goals: {exc}", "ERROR")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def set_repeat(goal: str, user: str, interval_minutes: int) -> None:
    """Queue a goal to repeat at a given interval."""
    next_run = datetime.now() + timedelta(minutes=interval_minutes)
    add_goal(goal, user, next_run, interval_minutes)
    log(f"Scheduled repeating goal every {interval_minutes} minutes")
