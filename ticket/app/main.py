from fastapi import FastAPI, Header, HTTPException, Response
from .database import get_user_tickets, create_new_ticket, update_ticket_status, get_ticket_by_uid_and_user
from .schemas import TicketInternal, CreateTicketRequest, UpdateTicketStatus
from typing import List

app = FastAPI(title="Ticket Service")

@app.get("/manage/health")
async def manage_health():
    return {}

@app.get("/tickets", response_model=List[TicketInternal])
async def get_tickets(x_user_name: str = Header(...)):
    return get_user_tickets(x_user_name)

@app.post("/tickets", response_model=TicketInternal)
async def create_ticket(request: CreateTicketRequest):
    return create_new_ticket(request.username, request.flightNumber, request.price, request.uuid)

@app.patch("/tickets/{ticket_uid}")
async def patch_ticket(ticket_uid: str, request: UpdateTicketStatus):
    updated = update_ticket_status(ticket_uid, request.username, request.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return Response(status_code=204)

@app.get("/tickets/{ticket_uid}", response_model=TicketInternal)
async def get_single_ticket(ticket_uid: str, username: str):
    ticket = get_ticket_by_uid_and_user(ticket_uid, username)
    
    if not ticket:
        raise HTTPException(
            status_code=404, 
            detail="Ticket not found or access denied"
        )
        
    return ticket