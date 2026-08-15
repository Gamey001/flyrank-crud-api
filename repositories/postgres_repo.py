import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg
from psycopg.rows import dict_row

INIT_SQL = Path(__file__).resolve().parent.parent / "db" / "init.sql"


def dsn() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def connect() -> psycopg.Connection:
    return psycopg.connect(dsn(), row_factory=dict_row)


def to_task(row: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


def init_db() -> None:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(INIT_SQL.read_text())


def list_tasks(
    done: Optional[bool] = None, search: Optional[str] = None
) -> List[Dict[str, Any]]:
    query = "SELECT id, title, done FROM tasks"
    conditions = []
    params: List[Any] = []

    if done is not None:
        conditions.append("done = %s")
        params.append(done)

    if search is not None:
        conditions.append("title ILIKE %s")
        params.append(f"%{search.strip()}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id"

    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
    return [to_task(row) for row in rows]


def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s", (task_id,)
            )
            row = cursor.fetchone()
    return to_task(row) if row else None


def create_task(title: str) -> Dict[str, Any]:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, FALSE) "
                "RETURNING id, title, done",
                (title,),
            )
            row = cursor.fetchone()
    return to_task(row)


def update_task(task_id: int, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    assignments = []
    params: List[Any] = []

    if "title" in changes:
        assignments.append("title = %s")
        params.append(changes["title"])

    if "done" in changes:
        assignments.append("done = %s")
        params.append(changes["done"])

    if not assignments:
        return get_task(task_id)

    params.append(task_id)
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE tasks SET {', '.join(assignments)} WHERE id = %s "
                "RETURNING id, title, done",
                params,
            )
            row = cursor.fetchone()
    return to_task(row) if row else None


def delete_task(task_id: int) -> bool:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            return cursor.rowcount > 0


def count_tasks() -> Dict[str, int]:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS total, "
                "COUNT(*) FILTER (WHERE done) AS done FROM tasks"
            )
            row = cursor.fetchone()
    total, done = row["total"], row["done"]
    return {"total": total, "done": done, "open": total - done}


def reset_tasks() -> List[Dict[str, Any]]:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE tasks RESTART IDENTITY")
    init_db()
    return list_tasks()
