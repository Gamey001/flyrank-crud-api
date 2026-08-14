import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(os.environ.get("TASKS_DB", Path(__file__).parent / "tasks.db"))

SEED_TASKS = [
    ("Learn FastAPI", 1),
    ("Build a CRUD API", 0),
    ("Write a README", 0),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT    NOT NULL,
    done  INTEGER NOT NULL DEFAULT 0
)
"""


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def to_task(row: sqlite3.Row) -> Dict[str, Any]:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as connection:
        connection.execute(SCHEMA)
        already_seeded = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if already_seeded == 0:
            connection.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)", SEED_TASKS
            )


def list_tasks(
    done: Optional[bool] = None, search: Optional[str] = None
) -> List[Dict[str, Any]]:
    query = "SELECT id, title, done FROM tasks"
    conditions = []
    params: List[Any] = []

    if done is not None:
        conditions.append("done = ?")
        params.append(1 if done else 0)

    if search is not None:
        conditions.append("title LIKE ?")
        params.append(f"%{search.strip()}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id"

    with connect() as connection:
        rows = connection.execute(query, params).fetchall()
    return [to_task(row) for row in rows]


def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    with connect() as connection:
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return to_task(row) if row else None


def create_task(title: str) -> Dict[str, Any]:
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, done) VALUES (?, 0)", (title,)
        )
        task_id = cursor.lastrowid
    return {"id": task_id, "title": title, "done": False}


def update_task(task_id: int, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    assignments = []
    params: List[Any] = []

    if "title" in changes:
        assignments.append("title = ?")
        params.append(changes["title"])

    if "done" in changes:
        assignments.append("done = ?")
        params.append(1 if changes["done"] else 0)

    if not assignments:
        return get_task(task_id)

    params.append(task_id)
    with connect() as connection:
        cursor = connection.execute(
            f"UPDATE tasks SET {', '.join(assignments)} WHERE id = ?", params
        )
        if cursor.rowcount == 0:
            return None
    return get_task(task_id)


def delete_task(task_id: int) -> bool:
    with connect() as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount > 0


def count_tasks() -> Dict[str, int]:
    with connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(done), 0) AS done FROM tasks"
        ).fetchone()
    total, done = row["total"], row["done"]
    return {"total": total, "done": done, "open": total - done}


def reset_tasks() -> List[Dict[str, Any]]:
    with connect() as connection:
        connection.execute("DELETE FROM tasks")
        connection.execute("DELETE FROM sqlite_sequence WHERE name = 'tasks'")
        connection.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)", SEED_TASKS
        )
    return list_tasks()
