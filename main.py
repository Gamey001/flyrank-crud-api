import copy
from typing import Any, Dict, Optional

from fastapi import Body, FastAPI, Query, Response
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Task API",
    description="A small in-memory to-do list API supporting the four CRUD operations.",
    version="1.0",
)

SEED_TASKS = [
    {"id": 1, "title": "Learn FastAPI", "done": True},
    {"id": 2, "title": "Build a CRUD API", "done": False},
    {"id": 3, "title": "Write a README", "done": False},
]

tasks = copy.deepcopy(SEED_TASKS)


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
    results = tasks

    if done is not None:
        results = [task for task in results if task["done"] == done]

    if search is not None:
        needle = search.strip().lower()
        results = [task for task in results if needle in task["title"].lower()]

    return results


@app.get("/tasks/{task_id}", summary="Get one task by id", tags=["tasks"])
def get_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")
    return task


@app.post("/tasks", status_code=201, summary="Create a new task", tags=["tasks"])
def create_task(payload: Dict[str, Any] = Body(default={})):
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        return error(400, "Field 'title' is required and must be a non-empty string")

    task = {"id": next_id(), "title": title.strip(), "done": False}
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}", summary="Update a task's title and/or done flag", tags=["tasks"])
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


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task", tags=["tasks"])
def delete_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")

    tasks.remove(task)
    return Response(status_code=204)


@app.get("/stats", summary="Count tasks by state", tags=["extras"])
def stats():
    done_count = sum(1 for task in tasks if task["done"])
    return {"total": len(tasks), "done": done_count, "open": len(tasks) - done_count}


@app.post("/reset", summary="Restore the 3 example tasks", tags=["extras"])
def reset():
    tasks.clear()
    tasks.extend(copy.deepcopy(SEED_TASKS))
    return tasks
