from typing import Any, Dict, List, Optional

try:
    from typing import Protocol
except ImportError:
    Protocol = object

SEED_TASKS = [
    ("Learn FastAPI", True),
    ("Build a CRUD API", False),
    ("Write a README", False),
]


class TaskRepository(Protocol):
    def init_db(self) -> None:
        ...

    def list_tasks(
        self, done: Optional[bool] = None, search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        ...

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        ...

    def create_task(self, title: str) -> Dict[str, Any]:
        ...

    def update_task(
        self, task_id: int, changes: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        ...

    def delete_task(self, task_id: int) -> bool:
        ...

    def count_tasks(self) -> Dict[str, int]:
        ...

    def reset_tasks(self) -> List[Dict[str, Any]]:
        ...
