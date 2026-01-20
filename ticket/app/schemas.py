from pydantic import BaseModel, Field
from uuid import UUID
from typing import List

class TicketInternal(BaseModel):
    ticketUid: UUID
    flightNumber: str
    price: int
    status: str

class CreateTicketRequest(BaseModel):
    flightNumber: str
    price: int
    username: str
    uuid: UUID | None = None

class UpdateTicketStatus(BaseModel):
    status: str # PAID, CANCELED