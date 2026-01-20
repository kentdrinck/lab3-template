import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import datetime
from app.main import app

client = TestClient(app)

def test_manage_health():
    response = client.get("/manage/health")
    assert response.status_code == 200
    assert response.json() == {}

@patch("app.main.fetch_flights")
def test_get_flights_api(mock_fetch):
    mock_fetch.return_value = ([
        {"flightNumber": "A101", "date": datetime(2026, 1, 1, 12, 0), "price": 100, "fromAirport": "MSK", "toAirport": "SPB"}
    ], 1)
    
    response = client.get("/flights?page=1&size=10")
    assert response.status_code == 200
    assert response.json()["totalElements"] == 1
    assert response.json()["items"][0]["date"] == "2026-01-01 12:00"

@patch("app.main.fetch_flight_by_number")
def test_get_flight_not_found_api(mock_fetch):
    mock_fetch.return_value = None
    response = client.get("/flights/NOTFOUND")
    assert response.status_code == 404
    assert response.json()["detail"] == "Flight not found"

@patch("app.main.fetch_flight_by_number")
def test_get_flight_success_api(mock_fetch):
    mock_fetch.return_value = {
        "flightNumber": "A101", 
        "date": datetime(2026, 1, 1, 12, 0), 
        "price": 100, 
        "fromAirport": "MSK", 
        "toAirport": "SPB"
    }
    response = client.get("/flights/A101")
    assert response.status_code == 200
    assert response.json()["flightNumber"] == "A101"