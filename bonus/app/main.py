from fastapi import FastAPI, Header, HTTPException
from .database import get_privilege_with_history, process_bonus_operation, process_rollback_operation
from .schemas import PrivilegeInfoResponse, BonusOperationRequest, BonusOperationResponse, RollbackRequest

app = FastAPI(title="Bonus Service")

@app.get("/manage/health")
async def manage_health():
    return {}

@app.get("/privilege", response_model=PrivilegeInfoResponse)
async def get_privilege(username: str):
    data = get_privilege_with_history(username)
    if not data:
        raise HTTPException(status_code=404, detail="Privilege not found")
    return data

@app.post("/privilege/calculate", response_model=BonusOperationResponse)
async def calculate_bonus(request: BonusOperationRequest):
    return process_bonus_operation(
        request.username, str(request.ticketUid), request.price, request.paidFromBalance
    )


@app.post("/privilege/rollback/{ticketUID}")
async def calculate_bonus(request: RollbackRequest, ticketUID: str):
    return process_rollback_operation(
        request.username, ticketUID, request.price,
    )
