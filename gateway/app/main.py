import os
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uuid

from .clients import FlightClient, TicketClient, BonusClient

load_dotenv()

app = FastAPI(title="Gateway Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

flight_client = FlightClient(os.getenv("FLIGHT_SERVICE_HOST"))
ticket_client = TicketClient(os.getenv("TICKET_SERVICE_HOST"))
bonus_client = BonusClient(os.getenv("BONUS_SERVICE_HOST"))


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
    tickets = await get_user_tickets(x_user_name)
    p_resp = await bonus_client.get_privilege(x_user_name)

    return {
        "tickets": tickets,
        "privilege": (
            p_resp.json()
            if p_resp.status_code == 200
            else {"balance": 0, "status": "BRONZE"}
        ),
    }


@app.post("/api/v1/tickets")
async def buy_ticket(request: dict, x_user_name: str = Header(...)):
    f_resp = await flight_client.get_flight(request["flightNumber"])
    if f_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Flight not found")

    ticket_uuid = str(uuid.uuid4())
    price = request["price"]
    paid_from_balance = request["paidFromBalance"]
    flight_number = request["flightNumber"]

    b_data = (
        await bonus_client.calculate(x_user_name, ticket_uuid, price, paid_from_balance)
    ).json()
    f_data = (await flight_client.get_flight(flight_number)).json()

    t_resp = await ticket_client.create_ticket(
        x_user_name,
        ticket_uuid,
        price,
        flight_number,
    )
    t_data = t_resp.json()

    return {
        **f_data,
        **t_data,
        "paidByMoney": request["price"] - b_data["paidByBonuses"],
        "paidByBonuses": b_data["paidByBonuses"],
        "privilege": b_data["privilege"],
    }


@app.delete("/api/v1/tickets/{ticketUid}", status_code=204)
async def refund_ticket(ticketUid: str, x_user_name: str = Header(...)):
    t_resp = await ticket_client.delete_ticket(x_user_name, ticketUid)
    if t_resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Ticket not found")

    await bonus_client.rollback(x_user_name, ticketUid)


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
    resp = await bonus_client.get_privilege(x_user_name)

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Бонусный профиль не найден")

    return resp.json()
