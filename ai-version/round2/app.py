import itertools
import threading
from typing import Any, Dict, List, Optional

from fastapi import Body, FastAPI, Path, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

SEED_TASKS = [
    {"id": 1, "title": "Learn FastAPI", "done": True},
    {"id": 2, "title": "Build a CRUD API", "done": False},
    {"id": 3, "title": "Write a README", "done": False},
]


class Task(BaseModel):
    id: int = Field(examples=[1])
    title: str = Field(examples=["Learn FastAPI"])
    done: bool = Field(examples=[False])


class ApiInfo(BaseModel):
    name: str
    version: str
    endpoints: List[str]


class Health(BaseModel):
    status: str


class Stats(BaseModel):
    total: int
    done: int
    open: int


class ApiError(BaseModel):
    error: str = Field(examples=["Task 99 not found"])


class TaskStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> List[Dict[str, Any]]:
        with self._lock:
            self._tasks = [dict(task) for task in SEED_TASKS]
            highest = max((task["id"] for task in self._tasks), default=0)
            self._ids = itertools.count(highest + 1)
            return [dict(task) for task in self._tasks]

    def all(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(task) for task in self._tasks]

    def get(self, task_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            for task in self._tasks:
                if task["id"] == task_id:
                    return dict(task)
        return None

    def add(self, title: str) -> Dict[str, Any]:
        with self._lock:
            task = {"id": next(self._ids), "title": title, "done": False}
            self._tasks.append(task)
            return dict(task)

    def update(self, task_id: int, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            for task in self._tasks:
                if task["id"] == task_id:
                    task.update(changes)
                    return dict(task)
        return None

    def remove(self, task_id: int) -> bool:
        with self._lock:
            for index, task in enumerate(self._tasks):
                if task["id"] == task_id:
                    del self._tasks[index]
                    return True
        return False


store = TaskStore()

NOT_FOUND = {"model": ApiError, "description": "No task has that id"}
BAD_REQUEST = {"model": ApiError, "description": "The request body is invalid"}

app = FastAPI(
    title="Task API",
    description="An in-memory to-do list API. Every error uses the shape {\"error\": \"...\"}.",
    version="2.0",
)


def fail(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    location = ".".join(str(part) for part in first["loc"][1:]) or "body"
    in_path = first["loc"] and first["loc"][0] == "path"
    code = status.HTTP_404_NOT_FOUND if in_path else status.HTTP_400_BAD_REQUEST
    if in_path:
        return fail(code, f"Task {request.path_params.get('task_id')} not found")
    return fail(code, f"Invalid value for '{location}': {first['msg']}")


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == status.HTTP_204_NO_CONTENT:
        return Response(status_code=exc.status_code)
    return fail(exc.status_code, str(exc.detail))


@app.get("/", response_model=ApiInfo, summary="API description", tags=["meta"])
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", response_model=Health, summary="Liveness check", tags=["meta"])
def health():
    return {"status": "ok"}


@app.get(
    "/tasks",
    response_model=List[Task],
    summary="List tasks, optionally filtered and paginated",
    tags=["tasks"],
)
def list_tasks(
    done: Optional[bool] = Query(default=None, description="Keep only finished or unfinished tasks"),
    search: Optional[str] = Query(default=None, description="Keep tasks whose title contains this text"),
    limit: Optional[int] = Query(default=None, ge=1, le=100, description="Maximum tasks to return"),
    offset: int = Query(default=0, ge=0, description="How many tasks to skip"),
):
    results = store.all()

    if done is not None:
        results = [task for task in results if task["done"] == done]

    if search is not None:
        needle = search.strip().lower()
        results = [task for task in results if needle in task["title"].lower()]

    results = results[offset:]
    if limit is not None:
        results = results[:limit]
    return results


@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Get one task by id",
    responses={404: NOT_FOUND},
    tags=["tasks"],
)
def get_task(task_id: int = Path(description="Id of the task")):
    task = store.get(task_id)
    if task is None:
        return fail(404, f"Task {task_id} not found")
    return task


@app.post(
    "/tasks",
    response_model=Task,
    status_code=201,
    summary="Create a new task",
    responses={400: BAD_REQUEST},
    tags=["tasks"],
)
def create_task(payload: Dict[str, Any] = Body(default={}, examples=[{"title": "Buy milk"}])):
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        return fail(400, "Field 'title' is required and must be a non-empty string")
    return store.add(title.strip())


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Update a task's title and/or done flag",
    responses={400: BAD_REQUEST, 404: NOT_FOUND},
    tags=["tasks"],
)
def update_task(
    task_id: int = Path(description="Id of the task"),
    payload: Dict[str, Any] = Body(default={}, examples=[{"title": "Buy oat milk", "done": True}]),
):
    if "title" not in payload and "done" not in payload:
        return fail(400, "Body must contain at least one of 'title' or 'done'")

    changes: Dict[str, Any] = {}

    if "title" in payload:
        title = payload["title"]
        if not isinstance(title, str) or not title.strip():
            return fail(400, "Field 'title' must be a non-empty string")
        changes["title"] = title.strip()

    if "done" in payload:
        done = payload["done"]
        if not isinstance(done, bool):
            return fail(400, "Field 'done' must be true or false")
        changes["done"] = done

    task = store.update(task_id, changes)
    if task is None:
        return fail(404, f"Task {task_id} not found")
    return task


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
    responses={404: NOT_FOUND},
    tags=["tasks"],
)
def delete_task(task_id: int = Path(description="Id of the task")):
    if not store.remove(task_id):
        return fail(404, f"Task {task_id} not found")
    return Response(status_code=204)


@app.get("/stats", response_model=Stats, summary="Count tasks by state", tags=["extras"])
def stats():
    tasks = store.all()
    done_count = sum(1 for task in tasks if task["done"])
    return {"total": len(tasks), "done": done_count, "open": len(tasks) - done_count}


@app.post(
    "/reset",
    response_model=List[Task],
    summary="Restore the 3 example tasks",
    tags=["extras"],
)
def reset():
    return store.reset()
