import os
import httpx
import logging
from fastapi import HTTPException

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")


class BaseClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def _request(self, method: str, path: str, **kwargs):
        """
        Общий метод для выполнения запросов с явным логированием.
        """
        url = f"{self.base_url}{path}"

        # Логируем детали запроса перед отправкой
        headers = kwargs.get("headers", {})
        body = kwargs.get("json") or kwargs.get("content")
        logger.info(
            f"--> [OUTGOING] {method} {url} | Headers: {headers} | Body: {body}"
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, **kwargs)

                # Логируем детали ответа
                logger.info(
                    f"<-- [INCOMING] {method} {url} | Status: {response.status_code} | Body: {response.text[:200]}"
                )

                return response
            except httpx.RequestError as exc:
                logger.error(f"!!! [ERROR] {method} {url} | Exception: {str(exc)}")
                raise HTTPException(
                    status_code=503, detail=f"Service at {self.base_url} is unavailable"
                )


class FlightClient(BaseClient):
    async def get_flights(self, page: int, size: int):
        return await self._request(
            "GET", "/flights", params={"page": page, "size": size}
        )

    async def get_flight(self, flight_number: str):
        return await self._request("GET", f"/flights/{flight_number}")


class TicketClient(BaseClient):
    async def get_tickets(self, username: str):
        return await self._request("GET", "/tickets", headers={"X-User-Name": username})

    async def create_ticket(self, username: str, ticket_uuid, price, flight_number):
        return await self._request(
            "POST",
            "/tickets",
            json={
                "flightNumber": flight_number,
                "price": price,
                "uuid": ticket_uuid,
                "username": username
            },
        )

    async def delete_ticket(self, username: str, ticket_uid: str):
        return await self._request(
            "DELETE", f"/tickets/{ticket_uid}"
        )

    async def get_ticket_by_uid(self, username: str, ticket_uid: str):
        return await self._request(
            "GET", f"/tickets/{ticket_uid}",
            params={"username": username}
        )


class BonusClient(BaseClient):
    async def get_privilege(self, username: str):
        return await self._request(
            "GET", "/privilege", params={"username": username},
        )

    async def   calculate(
        self, username: str, ticket_uuid: str, price, paid_from_balance
    ):
        return await self._request(
            "POST",
            "/privilege/calculate",
            json={
                "ticketUid": ticket_uuid,
                "price": price,
                "paidFromBalance": paid_from_balance,
                "username": username,
            },
        )

    async def rollback(self, username: str, ticket_uid: str):
        return await self._request(
            "DELETE",
            f"/privilege/rollback/{ticket_uid}",
            headers={"X-User-Name": username},
        )
