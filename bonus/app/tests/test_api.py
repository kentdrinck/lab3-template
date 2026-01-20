import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

def test_manage_health():
    response = client.get("/manage/health")
    assert response.status_code == 200
    assert response.json() == {}

@patch("app.main.get_privilege_with_history")
def test_get_privilege_success(mock_db):
    mock_db.return_value = {
        "balance": 100,
        "status": "BRONZE",
        "history": []
    }
    response = client.get("/privilege?username=TestUser")
    assert response.status_code == 200
    assert response.json()["balance"] == 100

@patch("app.main.get_privilege_with_history")
def test_get_privilege_404(mock_db):
    mock_db.return_value = None
    response = client.get("/privilege?username=NonExistent")
    assert response.status_code == 404

@patch("app.main.process_bonus_operation")
def test_calculate_bonus(mock_db):
    mock_db.return_value = {
        "paidByBonuses": 10,
        "balanceDiff": -10,
        "privilege": {"balance": 90, "status": "BRONZE"}
    }
    payload = {
        "ticketUid": "550e8400-e29b-41d4-a716-446655440000",
        "price": 100,
        "paidFromBalance": True,
        "username": "TestUser"
    }
    response = client.post("/privilege/calculate", json=payload)
    assert response.status_code == 200
    assert response.json()["paidByBonuses"] == 10
