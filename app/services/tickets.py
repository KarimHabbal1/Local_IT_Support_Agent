from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException
import json

from app.db.models import Ticket, TicketStatus as ModelTicketStatus, User
from app.db.schemas import TicketCreate, TicketUpdate, TicketClose, LogEntry, TicketStatus as SchemaTicketStatus
from app.utils.logging import make_log_entry

class TicketService:
    
    @staticmethod
    def get_valid_status_transitions() -> Dict[ModelTicketStatus, List[ModelTicketStatus]]:
        """Define valid status transitions"""
        return {
            ModelTicketStatus.NEW: [ModelTicketStatus.IN_PROGRESS],
            ModelTicketStatus.IN_PROGRESS: [ModelTicketStatus.RESOLVED],
            ModelTicketStatus.RESOLVED: [ModelTicketStatus.CLOSED, ModelTicketStatus.IN_PROGRESS],  # Allow re-open
            ModelTicketStatus.CLOSED: []  # Cannot transition from CLOSED
        }
    
    @staticmethod
    def schema_to_model_status(schema_status: SchemaTicketStatus) -> ModelTicketStatus:
        """Convert schema status to model status"""
        return ModelTicketStatus(schema_status.value)
    
    @staticmethod
    def is_valid_transition(current_status: ModelTicketStatus, new_status: SchemaTicketStatus) -> bool:
        """Check if a status transition is valid"""
        valid_transitions = TicketService.get_valid_status_transitions()
        new_model_status = TicketService.schema_to_model_status(new_status)
        return new_model_status in valid_transitions.get(current_status, [])
    
    @staticmethod
    def parse_logs(logs_json: str) -> List[LogEntry]:
        """Parse logs from JSON string to LogEntry objects"""
        if not logs_json:
            return []
        try:
            logs_data = json.loads(logs_json)
            return [LogEntry(**log) for log in logs_data]
        except (json.JSONDecodeError, ValueError):
            return []
    
    @staticmethod
    def serialize_logs(logs: List[LogEntry]) -> str:
        """Serialize logs to JSON string"""
        logs_data = [log.model_dump() for log in logs]
        return json.dumps(logs_data)
    
    @staticmethod
    def append_log(ticket: Ticket, actor: str, action: str, details: Any) -> None:
        """Append a log entry to ticket logs"""
        current_logs = TicketService.parse_logs(ticket.logs or "[]")
        new_log = LogEntry(**make_log_entry(actor, action, details))
        current_logs.append(new_log)
        ticket.logs = TicketService.serialize_logs(current_logs)
    
    @staticmethod
    def create_ticket(db: Session, ticket_data: TicketCreate, actor: str = "system") -> Ticket:
        """Create a new ticket"""
        # Validate assigned user exists if provided
        if ticket_data.assigned_to:
            user = db.query(User).filter(User.id == ticket_data.assigned_to).first()
            if not user:
                raise HTTPException(status_code=400, detail="Assigned user does not exist")
        
        # Create ticket
        ticket = Ticket(
            issue=ticket_data.issue,
            assigned_to=ticket_data.assigned_to,
            status=ModelTicketStatus.NEW
        )
        
        db.add(ticket)
        db.flush()  # Get the ID
        
        # Add initial log
        TicketService.append_log(
            ticket, 
            actor, 
            "ticket_created", 
            {"issue": ticket_data.issue, "assigned_to": ticket_data.assigned_to}
        )
        
        db.commit()
        db.refresh(ticket)
        return ticket
    
    @staticmethod
    def get_ticket(db: Session, ticket_id: int) -> Optional[Ticket]:
        """Get a ticket by ID"""
        return db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    @staticmethod
    def list_tickets(
        db: Session, 
        status: Optional[SchemaTicketStatus] = None,
        assigned_to: Optional[int] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Ticket], int]:
        """List tickets with optional filtering and pagination"""
        query = db.query(Ticket)
        
        if status:
            model_status = TicketService.schema_to_model_status(status)
            query = query.filter(Ticket.status == model_status)
        if assigned_to:
            query = query.filter(Ticket.assigned_to == assigned_to)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        tickets = query.order_by(desc(Ticket.created_at)).offset(offset).limit(page_size).all()
        
        return tickets, total
    
    @staticmethod
    def update_ticket(
        db: Session, 
        ticket_id: int, 
        update_data: TicketUpdate, 
        actor: str = "system"
    ) -> Ticket:
        """Update a ticket"""
        ticket = TicketService.get_ticket(db, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Track changes for logging
        changes = {}
        
        # Update issue
        if update_data.issue is not None:
            changes["issue"] = {"from": ticket.issue, "to": update_data.issue}
            ticket.issue = update_data.issue
        
        # Update assigned_to
        if update_data.assigned_to is not None:
            if update_data.assigned_to != 0:  # 0 means unassign
                user = db.query(User).filter(User.id == update_data.assigned_to).first()
                if not user:
                    raise HTTPException(status_code=400, detail="Assigned user does not exist")
            
            changes["assigned_to"] = {"from": ticket.assigned_to, "to": update_data.assigned_to}
            ticket.assigned_to = update_data.assigned_to if update_data.assigned_to != 0 else None
        
        # Update status with validation
        if update_data.status is not None:
            new_model_status = TicketService.schema_to_model_status(update_data.status)
            if not TicketService.is_valid_transition(ticket.status, update_data.status):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid status transition from {ticket.status.value} to {update_data.status.value}"
                )
            changes["status"] = {"from": ticket.status.value, "to": update_data.status.value}
            ticket.status = new_model_status
        
        # Log the update if there were changes
        if changes:
            TicketService.append_log(ticket, actor, "ticket_updated", changes)
        
        db.commit()
        db.refresh(ticket)
        return ticket
    
    @staticmethod
    def close_ticket(
        db: Session, 
        ticket_id: int, 
        close_data: TicketClose, 
        actor: str = "system"
    ) -> Ticket:
        """Close a ticket"""
        ticket = TicketService.get_ticket(db, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        if ticket.status != ModelTicketStatus.RESOLVED:
            raise HTTPException(
                status_code=400, 
                detail="Can only close tickets with RESOLVED status"
            )
        
        ticket.status = ModelTicketStatus.CLOSED
        
        # Add close log
        TicketService.append_log(
            ticket, 
            actor, 
            "ticket_closed", 
            {"resolution_code": close_data.resolution_code}
        )
        
        db.commit()
        db.refresh(ticket)
        return ticket
