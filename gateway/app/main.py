import os
from fastapi import FastAPI, Header, HTTPException, Query, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uuid

import asyncio

from .clients import (
    FlightClient,
    TicketClient,
    BonusClient,
    ServiceUnavailableException,
)

load_dotenv()

app = FastAPI(title="Gateway Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

flight_client = FlightClient(os.getenv("FLIGHT_SERVICE_HOST"), "flight")
ticket_client = TicketClient(os.getenv("TICKET_SERVICE_HOST"), "ticket")
bonus_client = BonusClient(os.getenv("BONUS_SERVICE_HOST"), "bonus")

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    message: str


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(message=exc.detail).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()])
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(message=f"Validation error: {errors}").model_dump(),
    )


@app.get("/manage/health")
async def manage_health():
    return {}


@app.get("/api/v1/flights")
async def get_flights(page: int = 0, size: int = 10):
    resp = await flight_client.get_flights(page, size)
    return resp.json()


@app.get("/api/v1/tickets")
async def get_user_tickets(x_user_name: str = Header(...)):
    t_resp = await ticket_client.get_tickets(x_user_name)
    if t_resp.status_code != 200:
        return []

    tickets = t_resp.json()
    result = []

    for t in tickets:
        f_resp = await flight_client.get_flight(t["flightNumber"])
        f_data = f_resp.json() if f_resp.status_code == 200 else {}
        result.append(
            {
                "ticketUid": t["ticketUid"],
                "flightNumber": t["flightNumber"],
                "fromAirport": f_data.get("fromAirport", "Unknown"),
                "toAirport": f_data.get("toAirport", "Unknown"),
                "date": f_data.get("date", "Unknown"),
                "status": t["status"],
                "price": t["price"],
            }
        )
    return result


@app.get("/api/v1/me")
async def get_user_info(x_user_name: str = Header(...)):
    try:
        tickets = await get_user_tickets(x_user_name)
    except ServiceUnavailableException:
        tickets = []

    try:
        p_resp = await bonus_client.get_privilege(x_user_name)
        privilege = p_resp.json()
    except ServiceUnavailableException:
        privilege = {}

    return {
        "tickets": tickets,
        "privilege": privilege,
    }




async def retry_bonus_rollback(username: str, ticket_uid: str, price: int):
    while True:
        try:
            print("ХУЯРИМ")
            await bonus_client.rollback(username, ticket_uid, price)
            break  # Успешное выполнение, выходим из цикла
        except ServiceUnavailableException:
            # Если сервис все еще недоступен (CB OPEN), ждем 10 секунд
            await asyncio.sleep(10)

class BonusServiceUnavailable(HTTPException):
    def __init__(self, detail="Bonus Service unavailable"):
        super().__init__(status_code=503, detail=detail)


class FlightServiceUnavailable(HTTPException):
    def __init__(self, detail="Flight Service unavailable"):
        super().__init__(status_code=503, detail=detail)


class TicketServiceUnavailable(HTTPException):
    def __init__(self, detail="Flight Service unavailable"):
        super().__init__(status_code=503, detail=detail)


@app.post("/api/v1/tickets")
async def buy_ticket(request: dict, x_user_name: str = Header(...)):
    try:
        f_resp = await flight_client.get_flight(request["flightNumber"])
        if f_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Flight not found")
    except ServiceUnavailableException:
        raise FlightServiceUnavailable

    ticket_uuid = str(uuid.uuid4())
    price = request["price"]
    paid_from_balance = request["paidFromBalance"]
    flight_number = request["flightNumber"]

    try:
        b_data = (
            await bonus_client.calculate(
                x_user_name, ticket_uuid, price, paid_from_balance
            )
        ).json()
    except ServiceUnavailableException:
        raise BonusServiceUnavailable

    f_data = (await flight_client.get_flight(flight_number)).json()

    try:
        t_resp = await ticket_client.create_ticket(
            x_user_name,
            ticket_uuid,
            price,
            flight_number,
        )
        t_data = t_resp.json()
    except ServiceUnavailableException:
        raise TicketServiceUnavailable

    return {
        **f_data,
        **t_data,
        "paidByMoney": request["price"] - b_data["paidByBonuses"],
        "paidByBonuses": b_data["paidByBonuses"],
        "privilege": b_data["privilege"],
    }


@app.delete("/api/v1/tickets/{ticketUid}", status_code=204)
async def refund_ticket(
    ticketUid: str, 
    background_tasks: BackgroundTasks, 
    x_user_name: str = Header(...)
):

    try:
        t_resp = await ticket_client.get_ticket_by_uid(x_user_name, ticketUid)
        if t_resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Ticket not found")
        price = t_resp.json()["price"]
    except ServiceUnavailableException:
        raise TicketServiceUnavailable()

    try:
        t_resp = await ticket_client.delete_ticket(x_user_name, ticketUid)
        if t_resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Ticket not found")
    except ServiceUnavailableException:
        raise TicketServiceUnavailable()

    try:
        await bonus_client.rollback(x_user_name, ticketUid, price)
    except ServiceUnavailableException:
        background_tasks.add_task(retry_bonus_rollback, x_user_name, ticketUid, price)

    return Response(status_code=204)

@app.get("/api/v1/tickets/{ticketUid}")
async def get_ticket_info(ticketUid: str, x_user_name: str = Header(...)):
    t_resp = await ticket_client.get_ticket_by_uid(x_user_name, ticketUid)

    if t_resp.status_code == 404:
        raise HTTPException(
            status_code=404, detail="Билет не найден или не принадлежит пользователю"
        )

    ticket = t_resp.json()

    f_resp = await flight_client.get_flight(ticket["flightNumber"])

    if f_resp.status_code != 200:
        return {
            **ticket,
            "fromAirport": "Unknown",
            "toAirport": "Unknown",
            "date": "Unknown",
        }

    flight_data = f_resp.json()

    return {
        "ticketUid": ticket["ticketUid"],
        "flightNumber": ticket["flightNumber"],
        "fromAirport": flight_data["fromAirport"],
        "toAirport": flight_data["toAirport"],
        "date": flight_data["date"],
        "status": ticket["status"],
        "price": ticket["price"],
    }


@app.get("/api/v1/privilege")
async def get_privilege_with_history(x_user_name: str = Header(...)):
    try:
        resp = await bonus_client.get_privilege(x_user_name)
    except ServiceUnavailableException:
        raise BonusServiceUnavailable

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Бонусный профиль не найден")

    return resp.json()
