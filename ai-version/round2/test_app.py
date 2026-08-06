import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_state():
    client.post("/reset")
    yield


def test_root_describes_the_api():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


def test_health_is_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_returns_seed_tasks():
    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_get_single_task():
    response = client.get("/tasks/1")
    assert response.status_code == 200
    assert response.json()["title"] == "Learn FastAPI"


def test_get_unknown_task_is_404_with_error_envelope():
    response = client.get("/tasks/99")
    assert response.status_code == 404
    assert response.json() == {"error": "Task 99 not found"}


def test_non_numeric_id_is_404_not_422():
    response = client.get("/tasks/abc")
    assert response.status_code == 404
    assert "error" in response.json()
    assert "detail" not in response.json()


def test_create_returns_201():
    response = client.post("/tasks", json={"title": "Buy milk"})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Buy milk"
    assert body["done"] is False
    assert client.get(f"/tasks/{body['id']}").status_code == 200


@pytest.mark.parametrize("payload", [{}, {"title": ""}, {"title": "   "}, {"title": 5}])
def test_invalid_create_is_400(payload):
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    assert "error" in response.json()


def test_create_trims_whitespace():
    response = client.post("/tasks", json={"title": "  padded  "})
    assert response.json()["title"] == "padded"


def test_ids_are_never_reused():
    first = client.post("/tasks", json={"title": "alpha"}).json()["id"]
    client.delete(f"/tasks/{first}")
    second = client.post("/tasks", json={"title": "beta"}).json()["id"]
    assert second != first


def test_ids_are_unique_after_middle_delete():
    client.delete("/tasks/2")
    client.post("/tasks", json={"title": "one"})
    client.post("/tasks", json={"title": "two"})
    ids = [task["id"] for task in client.get("/tasks").json()]
    assert len(ids) == len(set(ids))


def test_update_returns_200():
    response = client.put("/tasks/1", json={"title": "Renamed", "done": False})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "Renamed", "done": False}


@pytest.mark.parametrize("payload", [{}, {"title": ""}, {"done": "yes"}])
def test_invalid_update_is_400(payload):
    response = client.put("/tasks/1", json=payload)
    assert response.status_code == 400
    assert "error" in response.json()


def test_update_unknown_task_is_404():
    response = client.put("/tasks/99", json={"done": True})
    assert response.status_code == 404


def test_delete_returns_204_with_empty_body():
    response = client.delete("/tasks/1")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/tasks/1").status_code == 404


def test_delete_unknown_task_is_404():
    response = client.delete("/tasks/99")
    assert response.status_code == 404
    assert response.json() == {"error": "Task 99 not found"}


def test_filter_by_done():
    assert all(task["done"] for task in client.get("/tasks?done=true").json())
    assert not any(task["done"] for task in client.get("/tasks?done=false").json())


def test_search_is_case_insensitive():
    client.post("/tasks", json={"title": "Buy MILK"})
    results = client.get("/tasks?search=milk").json()
    assert len(results) == 1


def test_pagination():
    assert len(client.get("/tasks?limit=2").json()) == 2
    assert client.get("/tasks?offset=2").json()[0]["id"] == 3


def test_stats_counts_match_the_list():
    stats = client.get("/stats").json()
    assert stats == {"total": 3, "done": 1, "open": 2}
    assert stats["done"] + stats["open"] == stats["total"]


def test_every_error_uses_the_same_envelope():
    responses = [
        client.get("/tasks/99"),
        client.get("/tasks/abc"),
        client.post("/tasks", json={}),
        client.put("/tasks/1", json={}),
        client.delete("/tasks/99"),
        client.get("/tasks?limit=0"),
    ]
    for response in responses:
        assert response.status_code >= 400
        assert set(response.json()) == {"error"}, response.json()


def test_openapi_documents_error_responses():
    schema = client.get("/openapi.json").json()
    assert "404" in schema["paths"]["/tasks/{task_id}"]["get"]["responses"]
    assert "400" in schema["paths"]["/tasks"]["post"]["responses"]
