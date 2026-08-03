# Task API

A small REST API that manages a to-do list. It supports the four CRUD operations — **C**reate, **R**ead, **U**pdate, **D**elete — over a list of tasks, plus filtering, search and stats.

Built with [FastAPI](https://fastapi.tiangolo.com/) and served by [Uvicorn](https://www.uvicorn.org/). There is no database: the tasks live in a Python list in memory, which has consequences (see [The mortality experiment](#the-mortality-experiment)).

A task looks like this:

```json
{ "id": 1, "title": "Learn FastAPI", "done": true }
```

## Install & run

Requires Python 3.9 or newer. From the project root:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/uvicorn main:app --reload --port 8000
```

The server starts on <http://localhost:8000>. Interactive docs are at <http://localhost:8000/docs>.

## Endpoints

| Method | Path | Description | Success | Errors |
| --- | --- | --- | --- | --- |
| `GET` | `/` | What this API is | `200` | — |
| `GET` | `/health` | Liveness check — returns `{"status":"ok"}` | `200` | — |
| `GET` | `/tasks` | List all tasks | `200` | — |
| `GET` | `/tasks?done=true` | List only finished tasks (`false` for unfinished) | `200` | `422` if not a boolean |
| `GET` | `/tasks?search=milk` | List tasks whose title contains the text (case-insensitive) | `200` | — |
| `GET` | `/tasks/{id}` | Get one task | `200` | `404` unknown id |
| `POST` | `/tasks` | Create a task from `{"title":"..."}` | `201` | `400` missing/empty title |
| `PUT` | `/tasks/{id}` | Update `title` and/or `done` | `200` | `400` empty/invalid body, `404` unknown id |
| `DELETE` | `/tasks/{id}` | Delete a task (empty body) | `204` | `404` unknown id |
| `GET` | `/stats` | Counts: `{"total":3,"done":1,"open":2}` | `200` | — |
| `POST` | `/reset` | Restore the 3 example tasks | `200` | — |

`done` and `search` can be combined: `GET /tasks?done=false&search=milk`.

Errors are always JSON in the shape `{"error": "..."}`.

## Example: create a task, then ask for one that doesn't exist

```console
$ curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Buy milk"}'
HTTP/1.1 201 Created
date: Mon, 03 Aug 2026 23:50:48 GMT
server: uvicorn
content-length: 40
content-type: application/json

{"id":4,"title":"Buy milk","done":false}

$ curl -i http://localhost:8000/tasks/99
HTTP/1.1 404 Not Found
date: Mon, 03 Aug 2026 23:50:48 GMT
server: uvicorn
content-length: 29
content-type: application/json

{"error":"Task 99 not found"}
```

## Interactive docs

FastAPI generates an OpenAPI description of the code and Swagger UI renders it at
<http://localhost:8000/docs> — every endpoint listed, each with a **Try it out** button that
sends real requests from the browser.

![Swagger UI showing all endpoints of the Task API](docs/swagger-ui.png)

## The mortality experiment

Create a couple of tasks, stop the server, start it again, then `GET /tasks`: the tasks you
created are gone and the list is back to the 3 examples — a request for one of them now
returns `404`. That happens because the tasks live in an ordinary Python list held in the
server process's memory, so the list is rebuilt from its seed values every time the process
starts and everything the previous process held is discarded when it exits. Persisting data
past a restart needs somewhere outside the process to put it, such as a file or a database.
