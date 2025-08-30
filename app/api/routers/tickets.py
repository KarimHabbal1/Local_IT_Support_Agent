from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.db.schemas import (
    TicketCreate, TicketRead, TicketUpdate, TicketClose, 
    TicketListResponse, TicketStatus, LogEntry
)
from app.services.tickets import TicketService

router = APIRouter()

@router.post("", response_model=TicketRead, status_code=201)
def create_ticket(
    ticket_data: TicketCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new ticket.
    
    Example request:
    ```json
    {
        "issue": "VPN not working",
        "assigned_to": 2
    }
    ```
    
    Response includes the ticket with initial log entry.
    """
    ticket = TicketService.create_ticket(db, ticket_data, actor="system")
    
    # Convert to response model
    return TicketRead(
        id=ticket.id,
        issue=ticket.issue,
        status=ticket.status,
        assigned_to=ticket.assigned_to,
        logs=TicketService.parse_logs(ticket.logs),
        created_at=ticket.created_at,
        updated_at=ticket.updated_at
    )

@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Get a ticket by ID.
    """
    ticket = TicketService.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return TicketRead(
        id=ticket.id,
        issue=ticket.issue,
        status=ticket.status,
        assigned_to=ticket.assigned_to,
        logs=TicketService.parse_logs(ticket.logs),
        created_at=ticket.created_at,
        updated_at=ticket.updated_at
    )

@router.get("", response_model=TicketListResponse)
def list_tickets(
    status: Optional[TicketStatus] = Query(None, description="Filter by status"),
    assigned_to: Optional[int] = Query(None, description="Filter by assigned user ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    List tickets with optional filtering and pagination.
    
    Query parameters:
    - status: Filter by ticket status (NEW, IN_PROGRESS, RESOLVED, CLOSED)
    - assigned_to: Filter by assigned user ID
    - page: Page number (starts from 1)
    - page_size: Number of items per page (max 100)
    """
    tickets, total = TicketService.list_tickets(db, status, assigned_to, page, page_size)
    
    ticket_reads = [
        TicketRead(
            id=ticket.id,
            issue=ticket.issue,
            status=ticket.status,
            assigned_to=ticket.assigned_to,
            logs=TicketService.parse_logs(ticket.logs),
            created_at=ticket.created_at,
            updated_at=ticket.updated_at
        )
        for ticket in tickets
    ]
    
    return TicketListResponse(
        tickets=ticket_reads,
        total=total,
        page=page,
        page_size=page_size
    )

@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(
    ticket_id: int,
    update_data: TicketUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a ticket.
    
    Can update: issue, status (with valid transitions), assigned_to.
    
    Valid status transitions:
    - NEW -> IN_PROGRESS
    - IN_PROGRESS -> RESOLVED  
    - RESOLVED -> CLOSED or IN_PROGRESS (re-open)
    - CLOSED -> (no transitions allowed)
    
    Example request:
    ```json
    {
        "status": "IN_PROGRESS"
    }
    ```
    """
    ticket = TicketService.update_ticket(db, ticket_id, update_data, actor="system")
    
    return TicketRead(
        id=ticket.id,
        issue=ticket.issue,
        status=ticket.status,
        assigned_to=ticket.assigned_to,
        logs=TicketService.parse_logs(ticket.logs),
        created_at=ticket.created_at,
        updated_at=ticket.updated_at
    )

@router.post("/{ticket_id}/close", response_model=TicketRead)
def close_ticket(
    ticket_id: int,
    close_data: TicketClose,
    db: Session = Depends(get_db)
):
    """
    Close a ticket.
    
    Requires current status to be RESOLVED and a resolution_code.
    Appends a log entry and sets status to CLOSED.
    
    Example request:
    ```json
    {
        "resolution_code": "VPN-RESET-OK"
    }
    ```
    """
    ticket = TicketService.close_ticket(db, ticket_id, close_data, actor="system")
    
    return TicketRead(
        id=ticket.id,
        issue=ticket.issue,
        status=ticket.status,
        assigned_to=ticket.assigned_to,
        logs=TicketService.parse_logs(ticket.logs),
        created_at=ticket.created_at,
        updated_at=ticket.updated_at
    )
