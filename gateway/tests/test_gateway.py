import pytest
from httpx import AsyncClient, Response
from unittest.mock import AsyncMock, patch
from app.main import app

# Тестовые данные
MOCK_USERNAME = "TestUser"
MOCK_TICKET_UID = "049161bb-badd-4fa8-9d90-87c9a82b0668"

import pytest
from httpx import AsyncClient, ASGITransport, Response # Добавлен ASGITransport
from app.main import app

@pytest.fixture
async def client():
    # Используем ASGITransport для интеграции с FastAPI app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
@pytest.mark.asyncio
async def test_get_flights(client):
    """Тест получения списка рейсов"""
    with patch("app.main.flight_client.get_flights", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = Response(200, json={"items": [{"flightNumber": "AFL031"}]})
        
        response = await client.get("/api/v1/flights?page=0&size=10")
        
        assert response.status_code == 200
        assert response.json()["items"][0]["flightNumber"] == "AFL031"
        mock_get.assert_called_once_with(0, 10)

@pytest.mark.asyncio
async def test_get_user_tickets_aggregation(client):
    """Тест агрегации данных билета и рейса"""
    with patch("app.main.ticket_client.get_tickets", new_callable=AsyncMock) as mock_tickets, \
         patch("app.main.flight_client.get_flight", new_callable=AsyncMock) as mock_flight:
        
        # Данные из Ticket Service
        mock_tickets.return_value = Response(200, json=[{
            "ticketUid": MOCK_TICKET_UID,
            "flightNumber": "AFL031",
            "price": 1500,
            "status": "PAID"
        }])
        
        # Данные из Flight Service
        mock_flight.return_value = Response(200, json={
            "fromAirport": "Пулково Санкт-Петербург",
            "toAirport": "Шереметьево Москва",
            "date": "2021-10-08 20:00"
        })

        response = await client.get("/api/v1/tickets", headers={"X-User-Name": MOCK_USERNAME})
        
        assert response.status_code == 200
        data = response.json()[0]
        assert data["ticketUid"] == MOCK_TICKET_UID
        assert data["fromAirport"] == "Пулково Санкт-Петербург"
        assert data["price"] == 1500

@pytest.mark.asyncio
async def test_buy_ticket_flow(client):
    """Тест сценария покупки билета с бонусами"""
    with patch("app.main.flight_client.get_flight", new_callable=AsyncMock) as mock_f, \
         patch("app.main.bonus_client.calculate", new_callable=AsyncMock) as mock_b, \
         patch("app.main.ticket_client.create_ticket", new_callable=AsyncMock) as mock_t:
        
        mock_f.return_value = Response(200, json={"price": 1500})
        mock_b.return_value = Response(200, json={
            "paidByBonuses": 500,
            "privilege": {"balance": 0, "status": "BRONZE"}
        })
        mock_t.return_value = Response(200, json={
            "ticketUid": MOCK_TICKET_UID,
            "flightNumber": "AFL031",
            "status": "PAID"
        })

        payload = {
            "flightNumber": "AFL031",
            "price": 1500,
            "paidFromBalance": True
        }
        
        response = await client.post(
            "/api/v1/tickets", 
            json=payload, 
            headers={"X-User-Name": MOCK_USERNAME}
        )

        assert response.status_code == 200
        res_json = response.json()
        assert res_json["paidByMoney"] == 1000
        assert res_json["paidByBonuses"] == 500
        # Проверка, что Ticket Service получил финальную цену
        args, _ = mock_t.call_args
        assert args[1]["price"] == 1000

@pytest.mark.asyncio
async def test_refund_ticket_not_found(client):
    """Тест ошибки при возврате несуществующего билета"""
    with patch("app.main.ticket_client.delete_ticket", new_callable=AsyncMock) as mock_del:
        mock_del.return_value = Response(404)
        
        response = await client.delete(
            f"/api/v1/tickets/{MOCK_TICKET_UID}", 
            headers={"X-User-Name": MOCK_USERNAME}
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Ticket not found"