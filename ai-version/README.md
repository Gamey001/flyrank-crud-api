# ai-version — AI-generated code, kept separate

Nothing in this folder is part of the Stage 0–6 submission. The hand-built API is
`../main.py` and it was not modified by this experiment.

```
ai-version/
├── prompt-v1.md        the loose prompt, written from memory
├── prompt-v2.md        the rematch prompt, rewritten after running round 1
├── round1/app.py       what prompt v1 produced
└── round2/
    ├── app.py          what prompt v2 produced
    └── test_app.py     27 tests over both
```

## Run them

Both use the virtualenv from the parent project. Each runs on its own port so all three
implementations can be compared side by side.

```bash
# round 1 on :8001
.venv/bin/uvicorn app:app --port 8001 --app-dir ai-version/round1

# round 2 on :8002
.venv/bin/uvicorn app:app --port 8002 --app-dir ai-version/round2
```

Run round 2's test suite:

```bash
.venv/bin/pip install -r ai-version/requirements-dev.txt
cd ai-version/round2 && ../../.venv/bin/python -m pytest -q
```

```
27 passed in 0.81s
```

## Checkpoint results

The Stage 4 checkpoint calls, fired at all three implementations:

| Call | want | mine | round 1 | round 2 |
| --- | --- | --- | --- | --- |
| `GET /tasks/1` | 200 | 200 | 200 | 200 |
| `GET /tasks/99` | 404 | 404 | 404 | 404 |
| `POST /tasks {"title":"Buy milk"}` | 201 | 201 | 201 | 201 |
| `POST /tasks {}` | 400 | 400 | **422** | 400 |
| `POST /tasks {"title":""}` | 400 | 400 | **201** | 400 |
| `PUT /tasks/1 {"done":true}` | 200 | 200 | 200 | 200 |
| `PUT /tasks/1 {}` | 400 | 400 | **200** | 400 |
| `PUT /tasks/99` | 404 | 404 | 404 | 404 |
| `DELETE /tasks/99` | 404 | 404 | 404 | 404 |
| **passed** | | **9/9** | **5/9** | **9/9** |

The full write-up is in [`../README.md#ai-vs-me`](../README.md#ai-vs-me).
