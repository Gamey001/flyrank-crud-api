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

## AI vs me

> ⚠️ **The prompt below is a placeholder and must be replaced before submitting.** Stage 7
> asks you to write the prompt yourself, from memory — that is the exercise. Swap in your
> own wording; the findings underneath it stay valid either way.

I built Stages 0–6 by hand first, so I knew exactly what "correct" looked like before
letting an AI near it. The AI code is quarantined in [`ai-version/`](ai-version/) and
`main.py` was never touched by the experiment.

### The prompt I gave it

> Build me a small REST API in Python with FastAPI that manages a to-do list.
>
> It should store tasks in memory (no database). Each task has an id, a title, and a
> done flag. I want the four CRUD operations: list all tasks, get one task by its id,
> create a task, update a task, and delete a task. Creating a task should only need a
> title; the server assigns the id and sets done to false. Getting or changing a task
> that doesn't exist should return a 404 error, and creating a task without a title
> should be rejected. Give me Swagger docs at /docs so I can try the endpoints in the
> browser.
>
> Keep it in one file and keep it simple.

Then I fired my own Stage 4 checkpoint calls at what came back. **It failed 4 of 9.**

| Call | want | mine | round 1 |
| --- | --- | --- | --- |
| `POST /tasks {}` | 400 | 400 | **422** |
| `POST /tasks {"title":""}` | 400 | 400 | **201** |
| `PUT /tasks/1 {}` | 400 | 400 | **200** |
| every error body | `{"error":…}` | `{"error":…}` | **`{"detail":…}`** |

### 1. What did the AI do better?

**Pydantic models instead of hand-written type checks.** My `create_task` inspects the
body by hand — `if not isinstance(title, str) or not title.strip()`. The AI declared
`class TaskCreate(BaseModel): title: str` and let the framework enforce it. I can explain
why that is better: the model is *both* the validator and the documentation. Because the
type is declared, FastAPI puts a real request schema into `/openapi.json`, so Swagger UI
shows the expected body shape and pre-fills the example. My version passes
`Dict[str, Any]`, so Swagger shows an empty `{}` and the reader has to guess that `title`
is the field. The AI got validation and documentation from one declaration; I wrote them
separately and only got one of them.

It was also shorter — 78 lines against my 129 — because `HTTPException` and `response_model`
removed the error-formatting and serialising code I had written out longhand.

### 2. What did it get wrong or quietly ignore?

**It ignored the status codes I did say, and invented ones I didn't.** I asked for tasks
without a title to be "rejected"; it rejected them with **422**, because that is Pydantic's
default. A client written against my API would treat that as an unexpected error. Worse,
`{"title": ""}` was *accepted* with **201** — `title: str` is satisfied by an empty string,
so an empty-titled task went straight into the list. The strictness I got by hand was an
accident of writing the check myself.

**It broke my error envelope.** Every error came back as `{"detail": "Task 99 not found"}`.
Mine returns `{"error": …}` everywhere. Neither is more correct, but the AI silently picked
the framework default over the convention my API already used — and the prompt never
mentioned it.

**It shipped an id bug I did not have.** It generated ids with `len(tasks) + 1`. Delete a
task from the middle of the list and the counter goes *backwards*:

```console
$ curl -s -X DELETE http://localhost:8001/tasks/2

$ curl -s http://localhost:8001/tasks
[{"id":1,"title":"Learn FastAPI","done":false},{"id":3,"title":"Write a README","done":false}]

$ curl -s -X POST http://localhost:8001/tasks -H "Content-Type: application/json" -d '{"title":"first new"}'
{"id":3,"title":"first new","done":false}

$ curl -s http://localhost:8001/tasks
[{"id":1,"title":"Learn FastAPI","done":false},{"id":3,"title":"Write a README","done":false},{"id":3,"title":"first new","done":false}]
```

Two tasks now share id 3. `GET /tasks/3` returns whichever comes first and the other is
unreachable — it can never be fetched, updated, or deleted again.

**In fairness, my own version has a milder form of the same bug.** I used
`max(ids) + 1`, which cannot produce duplicates, but it does recycle: delete the
highest-numbered task and the next task created takes its id back. Finding the AI's bug
is what made me go and test my own.

### 3. What did my prompt forget to specify?

Reading it back, my prompt named the error *situations* but almost none of the actual
*codes*. It never said 201, never said 204, never said 400, and never described what an
error body should look like. Every one of the failures above sits precisely in that gap —
the AI did not disobey me, it filled in silence with defaults. It also silently decided
the id strategy, whether an empty string counts as a title, and whether `PUT` with an
empty body is a no-op or an error. Three real product decisions, none of them mine.

### The rematch

I rewrote the prompt as an explicit status-code table with six rules pinning down the
things round 1 had guessed at ([`prompt-v2.md`](ai-version/prompt-v2.md)), and regenerated.

**In one sentence: nothing about the model changed, only the specification — and round 2
went from 5/9 to 9/9 on the checkpoint, added a 27-test suite, and fixed the duplicate-id
bug by replacing `len(tasks) + 1` with a monotonic counter that never reuses an id.**

Round 2 also fixed the one flaw it inherited from *my* code: in my version
`GET /tasks/abc` returns FastAPI's `{"detail":[…]}` instead of my own `{"error":…}` shape,
so my API speaks two different error formats. Round 2 routes every error — including
framework validation errors — through one handler, so a client only ever parses one shape.

**The lesson:** the AI's output was exactly as good as my specification, and I could only
grade it because I had already built the thing myself. When it returned 422 instead of 400
I knew that was wrong; without Stages 0–6 behind me, I would have read that code, seen it
was clean and modern, and shipped it.
