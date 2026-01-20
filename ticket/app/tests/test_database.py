import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from app.database import (
    get_user_tickets, 
    create_new_ticket, 
    update_ticket_status, 
    get_ticket_by_uid_and_user
)

@patch("app.database.get_db_connection")
def test_get_user_tickets_logic(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    
    mock_cur.fetchall.return_value = [
        {"ticketUid": uuid4(), "flightNumber": "A101", "price": 100, "status": "PAID"}
    ]
    
    result = get_user_tickets("TestUser")
    
    assert len(result) == 1
    assert result[0]["flightNumber"] == "A101"
    assert mock_cur.execute.called

@patch("app.database.get_db_connection")
def test_create_new_ticket_logic(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    
    uid = uuid4()
    mock_cur.fetchone.return_value = {
        "ticketUid": uid, "flightNumber": "B202", "price": 200, "status": "PAID"
    }
    
    result = create_new_ticket("TestUser", "B202", 200, uid)
    
    assert result["ticketUid"] == uid
    assert mock_conn.commit.called

@patch("app.database.get_db_connection")
def test_update_ticket_status_success(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_cur.rowcount = 1
    
    result = update_ticket_status(str(uuid4()), "TestUser", "CANCELED")
    assert result is True

@patch("app.database.get_db_connection")
def test_get_ticket_by_uid_not_found(mock_connect):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = None
    
    result = get_ticket_by_uid_and_user(str(uuid4()), "User")
    assert result is None