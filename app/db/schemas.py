from pydantic import BaseModel, Field
from typing import Optional, List, Any
from enum import Enum

class TicketStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class LogEntry(BaseModel):
    timestamp: str
    actor: str
    action: str
    details: Any

class UserCreate(BaseModel):
    username: str = Field(..., example="alice")

class UserRead(BaseModel):
    id: int
    username: str

class TicketCreate(BaseModel):
    issue: str = Field(..., example="VPN not working")
    assigned_to: Optional[int] = Field(None, example=2)

class TicketUpdate(BaseModel):
    issue: Optional[str]
    status: Optional[TicketStatus]
    assigned_to: Optional[int]
    logs: Optional[List[LogEntry]]

class TicketRead(BaseModel):
    id: int
    issue: str
    status: TicketStatus
    assigned_to: Optional[int]
    logs: List[LogEntry]
