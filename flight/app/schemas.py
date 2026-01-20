from pydantic import BaseModel
from datetime import datetime
from typing import List

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