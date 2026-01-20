import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from uuid import uuid4
from app.main import app

client = TestClient(app)

def test_manage_health():
    response = client.get("/manage/health")
    assert response.status_code == 200
    assert response.json() == {}

@patch("app.main.get_user_tickets")
def test_get_tickets_api(mock_db):
    uid = uuid4()
    mock_db.return_value = [
        {"ticketUid": uid, "flightNumber": "A101", "price": 100, "status": "PAID"}
    ]
    headers = {"x-user-name": "TestUser"}
    response = client.get("/tickets", headers=headers)
    assert response.status_code == 200
    assert response.json()[0]["ticketUid"] == str(uid)

@patch("app.main.create_new_ticket")
def test_create_ticket_api(mock_db):
    uid = uuid4()
    mock_db.return_value = {
        "ticketUid": uid, "flightNumber": "A101", "price": 100, "status": "PAID"
    }
    payload = {
        "flightNumber": "A101",
        "price": 100,
        "username": "TestUser"
    }
    response = client.post("/tickets", json=payload)
    assert response.status_code == 200
    assert response.json()["ticketUid"] == str(uid)

@patch("app.main.update_ticket_status")
def test_patch_ticket_success(mock_db):
    mock_db.return_value = True
    uid = str(uuid4())
    headers = {"x-user-name": "TestUser"}
    response = client.patch(f"/tickets/{uid}", json={"status": "CANCELED"}, headers=headers)
    assert response.status_code == 204

@patch("app.main.update_ticket_status")
def test_patch_ticket_not_found(mock_db):
    mock_db.return_value = False
    uid = str(uuid4())
    headers = {"x-user-name": "TestUser"}
    response = client.patch(f"/tickets/{uid}", json={"status": "CANCELED"}, headers=headers)
    assert response.status_code == 404

@patch("app.main.get_ticket_by_uid_and_user")
def test_get_single_ticket_success(mock_db):
    uid = uuid4()
    mock_db.return_value = {
        "ticketUid": uid, "flightNumber": "A101", "price": 100, "status": "PAID"
    }
    response = client.get(f"/tickets/{uid}?username=TestUser")
    assert response.status_code == 200
    assert response.json()["ticketUid"] == str(uid)