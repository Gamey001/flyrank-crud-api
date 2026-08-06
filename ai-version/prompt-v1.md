# Prompt v1 — written from memory, before looking at anything

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

## What I was trying to specify

The endpoints, in-memory storage, the shape of a task, who assigns the id, the two
error cases I could remember, and Swagger.

## What I found out afterwards

Reading it back after running the result: this prompt names the error *situations*
("return a 404", "should be rejected") but only pins down one actual status **code**.
It never says 201, never says 204, never says 400, and never says what an error body
should look like. Round 1 filled every one of those gaps by itself — see
[`../README.md#ai-vs-me`](../README.md#ai-vs-me).
