from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.round2 import AdminTicketResponse, TicketCreate, TicketReply, TicketResponse
from app.services import support_service

router = APIRouter(tags=["Support"])


@router.post("/support/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return support_service.create_ticket(db, current_user, payload.category, payload.subject, payload.message)


@router.get("/support/tickets", response_model=list[TicketResponse])
def my_tickets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return support_service.list_mine(db, current_user)


@router.get("/admin/support/tickets", response_model=list[AdminTicketResponse])
def admin_tickets(
    status_filter: Optional[str] = Query(default=None, alias="status", max_length=20),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return support_service.list_for_admin(db, status_filter)


@router.post("/admin/support/tickets/{ticket_id}/reply", response_model=TicketResponse)
def admin_reply(
    ticket_id: int,
    payload: TicketReply,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return support_service.reply(db, ticket_id, payload.reply)


@router.post("/admin/support/tickets/{ticket_id}/close", response_model=TicketResponse)
def admin_close(
    ticket_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return support_service.close(db, ticket_id)
