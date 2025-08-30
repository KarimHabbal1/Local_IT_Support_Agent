from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any, Dict
from enum import Enum
from datetime import datetime

class TicketStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class LogEntry(BaseModel):
    timestamp: str = Field(..., description="ISO timestamp in UTC")
    actor: str = Field(..., description="Who performed the action (system|username)")
    action: str = Field(..., description="Action performed")
    details: Any = Field(..., description="Additional details")

# User schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, json_schema_extra={"example": "alice"})

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str

# Ticket schemas
class TicketCreate(BaseModel):
    issue: str = Field(..., min_length=1, max_length=500, json_schema_extra={"example": "VPN not working"})
    assigned_to: Optional[int] = Field(None, json_schema_extra={"example": 2})

class TicketUpdate(BaseModel):
    issue: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[TicketStatus] = None
    assigned_to: Optional[int] = None

class TicketClose(BaseModel):
    resolution_code: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "VPN-RESET-OK"})

class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    issue: str
    status: TicketStatus
    assigned_to: Optional[int]
    logs: List[LogEntry]
    created_at: datetime
    updated_at: datetime

# Response schemas
class TicketListResponse(BaseModel):
    tickets: List[TicketRead]
    total: int
    page: int
    page_size: int

class UserListResponse(BaseModel):
    users: List[UserRead]
