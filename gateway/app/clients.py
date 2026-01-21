import os
import httpx
import logging
from fastapi import HTTPException
from circuitbreaker import circuit, CircuitBreaker  #

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")


class ServiceUnavailableException(HTTPException):
    def __init__(
        self, detail="Service is temporarily unavailable (Circuit Breaker OPEN)"
    ):
        super().__init__(status_code=503, detail=detail)


class BaseClient:
    def __init__(self, base_url: str, service_name: str):
        self.base_url = base_url.rstrip("/")
        self.breaker = CircuitBreaker(
            name=f"{service_name}_breaker",
            failure_threshold=3,
            recovery_timeout=10,
            expected_exception=httpx.HTTPError,
        )

    async def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        headers = kwargs.get("headers", {})
        body = kwargs.get("json") or kwargs.get("content")

        logger.info(
            f"--> [OUTGOING] {method} {url} | Breaker State: {self.breaker.state}"
        )

        try:
            return await self.breaker.call(
                self._execute_http_call, method, url, **kwargs
            )
        except Exception as exc:
            logger.error(f"!!! [CB BLOCK] {method} {url} | Reason: {str(exc)}")
            raise ServiceUnavailableException()

    async def _execute_http_call(self, method: str, url: str, **kwargs):
        """Метод, который реально выполняет запрос к сети"""
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, timeout=2.0, **kwargs)
            if response.status_code >= 500:
                raise httpx.HTTPStatusError(
                    f"Server error {response.status_code}",
                    request=response.request,
                    response=response,
                )
            return response


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
                "username": username,
            },
        )

    async def delete_ticket(self, username: str, ticket_uid: str):
        return await self._request("DELETE", f"/tickets/{ticket_uid}")

    async def get_ticket_by_uid(self, username: str, ticket_uid: str):
        return await self._request(
            "GET", f"/tickets/{ticket_uid}", params={"username": username}
        )


class BonusClient(BaseClient):
    async def get_privilege(self, username: str):
        return await self._request(
            "GET",
            "/privilege",
            params={"username": username},
        )

    async def calculate(
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
