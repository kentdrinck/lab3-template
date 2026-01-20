import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app.database import fetch_flights, fetch_flight_by_number

@patch("app.database.get_db_connection")
def test_fetch_flights_logic(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    
    mock_cur.fetchall.return_value = [
        {"flightNumber": "A101", "date": datetime(2026, 1, 1, 12, 0), "price": 100, "fromAirport": "MSK", "toAirport": "SPB"}
    ]
    mock_cur.fetchone.return_value = {"count": 1}
    
    items, total = fetch_flights(1, 10)
    
    assert total == 1
    assert items[0]["flightNumber"] == "A101"
    assert mock_cur.execute.called

@patch("app.database.get_db_connection")
def test_fetch_flight_by_number_not_found(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = None
    
    result = fetch_flight_by_number("NULL000")
    assert result is None