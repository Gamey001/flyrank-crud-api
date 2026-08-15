import os

from dotenv import load_dotenv

load_dotenv()

if os.environ.get("DATABASE_URL"):
    from repositories import postgres_repo as _repo
else:
    from repositories import sqlite_repo as _repo

BACKEND = _repo.__name__.rsplit(".", 1)[-1]

init_db = _repo.init_db
list_tasks = _repo.list_tasks
get_task = _repo.get_task
create_task = _repo.create_task
update_task = _repo.update_task
delete_task = _repo.delete_task
count_tasks = _repo.count_tasks
reset_tasks = _repo.reset_tasks
