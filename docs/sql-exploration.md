# Stage 4 — exploring the database directly

Every query below was run against `tasks.db` outside the API, using the `sqlite3` shell.
The output is pasted verbatim.

```bash
sqlite3 -header -column tasks.db
```

## List every task

```sql
SELECT * FROM tasks;
```

```
id  title             done
--  ----------------  ----
1   Learn FastAPI     1
2   Build a CRUD API  0
3   Write a README    0
4   Buy milk          0
```

Note that `done` is stored as `1`/`0`. SQLite has no boolean type, so the API converts
the integer back into `true`/`false` before returning JSON.

## Show only completed tasks

```sql
SELECT * FROM tasks WHERE done = 1;
```

```
id  title          done
--  -------------  ----
1   Learn FastAPI  1
```

## Count all tasks

```sql
SELECT COUNT(*) FROM tasks;
```

```
COUNT(*)
--------
4
```

## Mark every task as completed

```sql
UPDATE tasks SET done = 1;
```

The API reflects this immediately, with no restart and no code change:

```console
$ curl -s http://localhost:8000/stats
{"total":4,"done":4,"open":0}

$ curl -s "http://localhost:8000/tasks?done=false"
[]
```

## Delete all completed tasks

```sql
DELETE FROM tasks WHERE done = 1;
```

Since the previous query marked everything done, this empties the table:

```console
$ sqlite3 tasks.db "SELECT COUNT(*) FROM tasks;"
0

$ curl -s http://localhost:8000/tasks
[]

$ curl -s http://localhost:8000/stats
{"total":0,"done":0,"open":0}
```

`POST /reset` puts the three example tasks back.

## What this demonstrates

The API holds no copy of the data. Every request reads the table at the moment it is
asked, so a change made in the SQL shell is visible through the API on the very next
request. In Assignment 1 this was impossible — the list lived inside the server process,
and nothing outside that process could see or change it.
