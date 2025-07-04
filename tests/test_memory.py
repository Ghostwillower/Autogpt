import os
import sqlite3
import tempfile
from memory import learn_preference, get_preference, log_goal, get_recent_goals, query_memory


def test_preferences(tmp_path, monkeypatch):
    db_path = tmp_path / "memory.db"
    monkeypatch.setattr("memory.DB_PATH", db_path)
    learn_preference("u1", "comms", "default_recipient", "a@example.com")
    val = get_preference("u1", "comms", "default_recipient")
    assert val == "a@example.com"


def test_goal_logging(tmp_path, monkeypatch):
    db_path = tmp_path / "memory.db"
    monkeypatch.setattr("memory.DB_PATH", db_path)
    log_goal("do stuff", "ok", "u1")
    recent = get_recent_goals(1, "u1")
    assert recent and recent[0][1] == "do stuff"
    # query_memory should return similar goal
    res = query_memory("do stuff", "u1")
    assert res
