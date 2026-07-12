import json
import pytest
from fastapi.testclient import TestClient
from src.api.main import create_app


@pytest.fixture
def client(tmp_path):
    db_path = str(tmp_path / "test.db")
    ws_path = str(tmp_path / "workspaces")
    app = create_app(db_path=db_path, base_workspace=ws_path)
    with TestClient(app) as c:
        yield c


def test_create_task(client):
    response = client.post("/api/tasks", json={"description": "fix login bug"})
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"


def test_create_task_missing_description(client):
    response = client.post("/api/tasks", json={})
    assert response.status_code == 422


def test_get_task(client):
    create_resp = client.post("/api/tasks", json={"description": "fix bug"})
    task_id = create_resp.json()["task_id"]
    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["description"] == "fix bug"


def test_get_nonexistent_task(client):
    response = client.get("/api/tasks/nonexistent")
    assert response.status_code == 404


def test_list_tasks(client):
    client.post("/api/tasks", json={"description": "task 1"})
    client.post("/api/tasks", json={"description": "task 2"})
    response = client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_task_steps(client):
    create_resp = client.post("/api/tasks", json={"description": "test"})
    task_id = create_resp.json()["task_id"]
    response = client.get(f"/api/tasks/{task_id}/steps")
    assert response.status_code == 200
    assert response.json() == []


def test_save_and_get_api_key(client):
    response = client.post("/api/config/keys", json={"provider": "openai", "key": "sk-secret-12345"})
    assert response.status_code == 200
    get_resp = client.get("/api/config/keys")
    assert get_resp.status_code == 200
    keys = get_resp.json()
    assert len(keys) == 1
    assert keys[0]["provider"] == "openai"
    assert keys[0]["key_masked"] != "sk-secret-12345"
    assert "****" in keys[0]["key_masked"]
    assert "key_value" not in keys[0]


def test_delete_api_key(client):
    client.post("/api/config/keys", json={"provider": "openai", "key": "sk-secret"})
    response = client.delete("/api/config/keys/openai")
    assert response.status_code == 200
    keys = client.get("/api/config/keys").json()
    assert len(keys) == 0


def test_run_task(client):
    create_resp = client.post("/api/tasks", json={"description": "fix the bug"})
    task_id = create_resp.json()["task_id"]
    client.post("/api/config/keys", json={"provider": "openai", "key": "sk-test-key"})

    from unittest.mock import patch, MagicMock
    mock_llm = MagicMock()
    mock_llm.chat.return_value = json.dumps({"action": "done", "reason": "completed"})

    with patch("src.api.routes.tasks.LiteLLMProvider", return_value=mock_llm), \
         patch("src.llm.litellm_provider.litellm", MagicMock()):
        response = client.post(f"/api/tasks/{task_id}/run", json={"provider": "openai", "model": "gpt-4o"})

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "success"
    assert data["total_steps"] == 1
    assert "final_message" in data