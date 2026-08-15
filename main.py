from typing import Any, Dict, Optional

from fastapi import Body, FastAPI, Query, Response
from fastapi.responses import JSONResponse

import db

app = FastAPI(
    title="Task API",
    description="A to-do list API backed by SQLite, supporting the four CRUD operations.",
    version="2.0",
)

db.init_db()


def error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


@app.get("/", summary="API description", tags=["meta"])
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Liveness check", tags=["meta"])
def health():
    return {"status": "ok"}


@app.get("/tasks", summary="List tasks, optionally filtered", tags=["tasks"])
def list_tasks(
    done: Optional[bool] = Query(default=None, description="Keep only finished (true) or unfinished (false) tasks"),
    search: Optional[str] = Query(default=None, description="Keep only tasks whose title contains this text"),
):
    return db.list_tasks(done=done, search=search)


@app.get("/tasks/{task_id}", summary="Get one task by id", tags=["tasks"])
def get_task(task_id: int):
    task = db.get_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")
    return task


@app.post("/tasks", status_code=201, summary="Create a new task", tags=["tasks"])
def create_task(payload: Dict[str, Any] = Body(default={})):
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        return error(400, "Field 'title' is required and must be a non-empty string")

    return db.create_task(title.strip())


@app.put("/tasks/{task_id}", summary="Update a task's title and/or done flag", tags=["tasks"])
def update_task(task_id: int, payload: Dict[str, Any] = Body(default={})):
    if "title" not in payload and "done" not in payload:
        return error(400, "Body must contain at least one of 'title' or 'done'")

    changes: Dict[str, Any] = {}

    if "title" in payload:
        title = payload["title"]
        if not isinstance(title, str) or not title.strip():
            return error(400, "Field 'title' must be a non-empty string")
        changes["title"] = title.strip()

    if "done" in payload:
        done = payload["done"]
        if not isinstance(done, bool):
            return error(400, "Field 'done' must be true or false")
        changes["done"] = done

    task = db.update_task(task_id, changes)
    if task is None:
        return error(404, f"Task {task_id} not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task", tags=["tasks"])
def delete_task(task_id: int):
    if not db.delete_task(task_id):
        return error(404, f"Task {task_id} not found")
    return Response(status_code=204)


@app.get("/stats", summary="Count tasks by state", tags=["extras"])
def stats():
    return db.count_tasks()


@app.post("/reset", summary="Restore the 3 example tasks", tags=["extras"])
def reset():
    return db.reset_tasks()
