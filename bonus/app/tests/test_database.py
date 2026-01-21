import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app.database import get_privilege_with_history, process_bonus_operation, process_rollback_operation

@patch("app.database.get_db_connection")
def test_get_privilege_with_history_not_found(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = None
    
    result = get_privilege_with_history("unknown")
    
    assert result["balance"] == 0
    assert result["status"] == "BRONZE"
    assert result["history"] == []

@patch("app.database.get_db_connection")
def test_process_bonus_operation_fill(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    
    mock_cur.fetchone.side_effect = [
        {"id": 1, "balance": 100, "status": "BRONZE"},
        {"balance": 110, "status": "BRONZE"}
    ]
    
    result = process_bonus_operation("user", "uid", 100, False)
    
    assert result["paidByBonuses"] == 0
    assert result["balanceDiff"] == 10
    assert result["privilege"]["balance"] == 110
    mock_conn.commit.assert_called_once()

@patch("app.database.get_db_connection")
def test_process_bonus_operation_debit(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    
    mock_cur.fetchone.side_effect = [
        {"id": 1, "balance": 500, "status": "BRONZE"},
        {"balance": 300, "status": "BRONZE"}
    ]
    
    result = process_bonus_operation("user", "uid", 200, True)
    
    assert result["paidByBonuses"] == 200
    assert result["balanceDiff"] == -200
    assert result["privilege"]["balance"] == 300

