import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent.parent / "agent_memory.db"


def get_connection():
    return sqlite3.connect(DB_PATH, timeout=10)


def initialize_memory():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                tasks TEXT,
                results TEXT,
                status TEXT,
                created_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                command TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def save_execution(command, tasks, results, status):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO task_history
            (command, tasks, results, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            command,
            json.dumps(tasks),
            json.dumps(results),
            status,
            datetime.now(timezone.utc).isoformat()
        ))


def get_history(limit=10):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT * FROM task_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [
            {
                "id": row["id"],
                "command": row["command"],
                "tasks": json.loads(row["tasks"] or "[]"),
                "results": json.loads(row["results"] or "[]"),
                "status": row["status"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]


def create_job(job_id, command):
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO jobs
            (job_id, command, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (job_id, command, "queued", now, now))


def update_job(job_id, status, result=None, error=None):
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        conn.execute("""
            UPDATE jobs
            SET status = ?, result = ?, error = ?, updated_at = ?
            WHERE job_id = ?
        """, (
            status,
            json.dumps(result) if result is not None else None,
            error,
            now,
            job_id
        ))


def get_job(job_id):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute(
            "SELECT * FROM jobs WHERE job_id = ?",
            (job_id,)
        ).fetchone()

        if row is None:
            return None

        return {
            "job_id": row["job_id"],
            "command": row["command"],
            "status": row["status"],
            "result": json.loads(row["result"]) if row["result"] else None,
            "error": row["error"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }


def list_jobs(limit=20):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT * FROM jobs
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [
            {
                "job_id": row["job_id"],
                "command": row["command"],
                "status": row["status"],
                "result": json.loads(row["result"]) if row["result"] else None,
                "error": row["error"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            for row in rows
        ]


initialize_memory()
