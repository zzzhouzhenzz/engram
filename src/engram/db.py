"""SQLite database layer for engram knowledge store."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_DIR = Path.home() / ".engram"
DB_PATH = DB_DIR / "engram.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    situation TEXT,
    tough_spot TEXT,
    approach TEXT,
    outcome TEXT,
    solution TEXT,
    keywords TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session_turns (
    session_id TEXT PRIMARY KEY,
    turn_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _connect() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(SCHEMA)


def insert_knowledge(
    session_id: str,
    situation: str,
    tough_spot: str,
    approach: str,
    outcome: str,
    solution: str,
    keywords: list[str],
) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            """INSERT INTO knowledge
               (session_id, situation, tough_spot, approach, outcome, solution, keywords)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                situation,
                tough_spot,
                approach,
                outcome,
                solution,
                json.dumps(keywords),
            ),
        )
        return cursor.lastrowid


def search_by_keywords(keywords: list[str]) -> list[dict]:
    with _connect() as conn:
        # Match any entry whose keywords overlap with the query
        conditions = " OR ".join(
            ["keywords LIKE ?" for _ in keywords]
        )
        params = [f"%{kw.strip().lower()}%" for kw in keywords]
        rows = conn.execute(
            f"SELECT * FROM knowledge WHERE {conditions} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def get_recent(n: int = 5) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM knowledge ORDER BY created_at DESC LIMIT ?", (n,)
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def get_all_keywords() -> list[str]:
    with _connect() as conn:
        rows = conn.execute("SELECT keywords FROM knowledge").fetchall()
    all_kws: set[str] = set()
    for row in rows:
        try:
            all_kws.update(json.loads(row["keywords"]))
        except (json.JSONDecodeError, TypeError):
            pass
    return sorted(all_kws)


# --- Session turn tracking ---


def increment_turn(session_id: str) -> int:
    with _connect() as conn:
        conn.execute(
            """INSERT INTO session_turns (session_id, turn_count, last_updated)
               VALUES (?, 1, ?)
               ON CONFLICT(session_id)
               DO UPDATE SET turn_count = turn_count + 1, last_updated = ?""",
            (session_id, _now(), _now()),
        )
        row = conn.execute(
            "SELECT turn_count FROM session_turns WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return row["turn_count"]


def get_turn_count(session_id: str) -> int:
    with _connect() as conn:
        row = conn.execute(
            "SELECT turn_count FROM session_turns WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return row["turn_count"] if row else 0


def reset_turn_count(session_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE session_turns SET turn_count = 0, last_updated = ? WHERE session_id = ?",
            (_now(), session_id),
        )


# --- Helpers ---


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    if "keywords" in d and isinstance(d["keywords"], str):
        try:
            d["keywords"] = json.loads(d["keywords"])
        except json.JSONDecodeError:
            pass
    return d


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
