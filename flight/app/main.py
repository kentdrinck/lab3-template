from fastapi import FastAPI, HTTPException, Query
from .database import fetch_flights, fetch_flight_by_number
from .schemas import PaginationResponse, FlightResponse

app = FastAPI(title="Flight Service")

@app.get("/manage/health")
async def manage_health():
    return {}

@app.get("/flights", response_model=PaginationResponse)
async def get_flights(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100)):
    items, total = fetch_flights(page, size)
    # Приведение даты к формату из примера
    for item in items:
        item['date'] = item['date'].strftime("%Y-%m-%d %H:%M")
        
    return {
        "page": page,
        "pageSize": size,
        "totalElements": total,
        "items": items
    }

@app.get("/flights/{flight_number}", response_model=FlightResponse)
async def get_flight(flight_number: str):
    flight = fetch_flight_by_number(flight_number)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    flight['date'] = flight['date'].strftime("%Y-%m-%d %H:%M")
    return flight