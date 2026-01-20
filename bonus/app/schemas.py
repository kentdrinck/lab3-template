from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class BalanceHistoryDTO(BaseModel):
    date: datetime
    ticketUid: UUID
    balanceDiff: int
    operationType: str

class PrivilegeInfoResponse(BaseModel):
    balance: int
    status: str
    history: List[BalanceHistoryDTO]

class BonusOperationRequest(BaseModel):
    ticketUid: UUID
    price: int
    paidFromBalance: bool
    username: str

class BonusOperationResponse(BaseModel):
    paidByBonuses: int
    balanceDiff: int
    privilege: dict


class RollbackRequest(BaseModel):
    price: int
    username: str

class RollbackResponse(BaseModel):
    ticketUid: UUID
    price: int