from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Task API", description="A simple in-memory to-do list API.")


class Task(BaseModel):
    id: int
    title: str
    done: bool


class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


tasks: List[Task] = [
    Task(id=1, title="Learn FastAPI", done=True),
    Task(id=2, title="Build a CRUD API", done=False),
    Task(id=3, title="Write a README", done=False),
]


def get_task_or_404(task_id: int) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.get("/", response_model=dict)
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", response_model=dict)
def health():
    return {"status": "ok"}


@app.get("/tasks", response_model=List[Task])
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    return get_task_or_404(task_id)


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(payload: TaskCreate):
    task = Task(id=len(tasks) + 1, title=payload.title, done=False)
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate):
    task = get_task_or_404(task_id)
    if payload.title is not None:
        task.title = payload.title
    if payload.done is not None:
        task.done = payload.done
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    task = get_task_or_404(task_id)
    tasks.remove(task)
