# Prompt v2 — the rematch, rewritten after running round 1

> Build a REST API in Python with FastAPI that manages a to-do list, stored in a plain
> in-memory list (no database, no files). A task is `{"id": int, "title": str,
> "done": bool}`. Seed it with 3 example tasks.
>
> Endpoints and exact status codes:
>
> | Method | Path | Success | Errors |
> | --- | --- | --- | --- |
> | GET | `/` | 200, returns `{"name","version","endpoints"}` | — |
> | GET | `/health` | 200, returns `{"status":"ok"}` | — |
> | GET | `/tasks` | 200, array | — |
> | GET | `/tasks/{id}` | 200 | 404 unknown id |
> | POST | `/tasks` | 201, body `{"title":"..."}` | 400 missing/empty title |
> | PUT | `/tasks/{id}` | 200 | 400 empty or invalid body, 404 unknown id |
> | DELETE | `/tasks/{id}` | 204 with a genuinely empty body | 404 unknown id |
>
> Rules you must not deviate from:
>
> 1. **Every** error response — including framework-generated validation errors and
>    unparseable path parameters — must have the body `{"error": "<message>"}`. No
>    `detail` key anywhere. A client must never have to parse two error shapes.
> 2. A title that is missing, empty, or only whitespace is a **400**, not a 422.
>    Trim surrounding whitespace before storing.
> 3. `PUT` with a body containing neither `title` nor `done` is a 400. A wrong type
>    (e.g. `"done": "yes"`) is a 400.
> 4. Ids must be **monotonic and never reused**, even after the highest-numbered task
>    is deleted. Two tasks must never share an id.
> 5. Endpoint handlers run in a thread pool, so guard the shared list with a lock.
> 6. Declare the error responses in the OpenAPI schema so Swagger UI shows the 400 and
>    404 shapes instead of labelling them "Undocumented".
>
> Also add `GET /stats` returning `{"total","done","open"}`, `POST /reset` restoring the
> 3 seed tasks, filtering via `?done=`, search via `?search=`, and pagination via
> `?limit=&offset=`. Include a pytest suite that asserts every status code above.

## What changed from v1

Every line above under "Rules you must not deviate from" exists because round 1 got that
exact thing wrong when the prompt left it open.
