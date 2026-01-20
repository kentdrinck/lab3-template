from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class PrivilegeShortInfo(BaseModel):
    balance: int
    status: str 

class FlightResponse(BaseModel):
    flightNumber: str
    fromAirport: str
    toAirport: str
    date: str
    price: int

class PaginationResponse(BaseModel):
    page: int
    pageSize: int
    totalElements: int
    items: List[FlightResponse]

class TicketResponse(BaseModel):
    ticketUid: UUID
    flightNumber: str
    fromAirport: str
    toAirport: str
    date: str
    price: int
    status: str

class UserInfoResponse(BaseModel):
    tickets: List[TicketResponse]
    privilege: PrivilegeShortInfo

class TicketPurchaseRequest(BaseModel):
    flightNumber: str
    price: int
    paidFromBalance: bool

class TicketPurchaseResponse(TicketResponse):
    paidByMoney: int
    paidByBonuses: int
    privilege: PrivilegeShortInfo