from typing import Any, Dict

from fastapi import Body, FastAPI, Response
from fastapi.responses import JSONResponse

app = FastAPI()

tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": True},
    {"id": 2, "title": "Build a CRUD API", "done": False},
    {"id": 3, "title": "Write a README", "done": False},
]


def find_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def next_id() -> int:
    if not tasks:
        return 1
    return max(task["id"] for task in tasks) + 1


def error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")
    return task


@app.post("/tasks", status_code=201)
def create_task(payload: Dict[str, Any] = Body(default={})):
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        return error(400, "Field 'title' is required and must be a non-empty string")

    task = {"id": next_id(), "title": title.strip(), "done": False}
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: Dict[str, Any] = Body(default={})):
    task = find_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")

    if "title" not in payload and "done" not in payload:
        return error(400, "Body must contain at least one of 'title' or 'done'")

    if "title" in payload:
        title = payload["title"]
        if not isinstance(title, str) or not title.strip():
            return error(400, "Field 'title' must be a non-empty string")
        task["title"] = title.strip()

    if "done" in payload:
        done = payload["done"]
        if not isinstance(done, bool):
            return error(400, "Field 'done' must be true or false")
        task["done"] = done

    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")

    tasks.remove(task)
    return Response(status_code=204)
