import html
import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.services import email_service, fraud_service, rate_limit

logger = logging.getLogger("summit_bank.support")

CATEGORIES = ("general", "payment", "card", "account", "other")
TICKETS_PER_HOUR = 5


def create_ticket(db: Session, user: User, category: str, subject: str, message: str) -> SupportTicket:
    if category not in CATEGORIES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown category")
    if not rate_limit.allow(f"ticket:{user.id}", TICKETS_PER_HOUR, 3600):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "You've sent several messages recently. Please wait a while.")
    ticket = SupportTicket(
        user_id=user.id, category=category, subject=subject.strip(), message=message.strip(), status="open"
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Best effort and after the commit: a failed email never loses the ticket.
    try:
        body = (
            f"<p><b>{html.escape(user.full_name)}</b> ({html.escape(user.email)}) opened ticket #{ticket.id} "
            f"[{html.escape(category)}]</p><p><b>{html.escape(ticket.subject)}</b></p>"
            f"<p>{html.escape(ticket.message).replace(chr(10), '<br>')}</p>"
            "<p>Reply from the Admin console → Support.</p>"
        )
        for admin_email in fraud_service.get_admin_emails(db):
            email_service.send_email(admin_email, f"New support ticket #{ticket.id}: {ticket.subject}"[:150], body)
    except Exception:
        logger.exception("Support alert email failed for ticket %s", ticket.id)
    return ticket


def list_mine(db: Session, user: User) -> list[SupportTicket]:
    return (
        db.query(SupportTicket)
        .filter(SupportTicket.user_id == user.id)
        .order_by(SupportTicket.created_at.desc(), SupportTicket.id.desc())
        .limit(100)
        .all()
    )


def list_for_admin(db: Session, status_filter: str | None) -> list[dict]:
    query = db.query(SupportTicket, User).join(User, User.id == SupportTicket.user_id)
    if status_filter:
        query = query.filter(SupportTicket.status == status_filter)
    rows = query.order_by(SupportTicket.created_at.desc(), SupportTicket.id.desc()).limit(200).all()
    return [
        {
            "id": t.id, "category": t.category, "subject": t.subject, "message": t.message, "status": t.status,
            "admin_reply": t.admin_reply, "replied_at": t.replied_at, "created_at": t.created_at,
            "user_name": u.full_name, "user_email": u.email,
        }
        for t, u in rows
    ]


def _get(db: Session, ticket_id: int) -> SupportTicket:
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")
    return ticket


def reply(db: Session, ticket_id: int, text: str) -> SupportTicket:
    ticket = _get(db, ticket_id)
    if ticket.status == "closed":
        raise HTTPException(status.HTTP_409_CONFLICT, "This ticket is closed")
    ticket.admin_reply = text.strip()
    ticket.replied_at = datetime.now(timezone.utc)
    ticket.status = "answered"
    db.commit()
    db.refresh(ticket)
    try:
        owner = db.query(User).filter(User.id == ticket.user_id).first()
        if owner:
            email_service.send_email(
                owner.email,
                f"Summit Bank replied to your message #{ticket.id}",
                f"<p>Hello {html.escape(owner.full_name)},</p><p>{html.escape(ticket.admin_reply).replace(chr(10), '<br>')}</p>"
                "<p>You can also see this reply under Contact us in the app.</p>",
            )
    except Exception:
        logger.exception("Support reply email failed for ticket %s", ticket.id)
    return ticket


def close(db: Session, ticket_id: int) -> SupportTicket:
    ticket = _get(db, ticket_id)
    ticket.status = "closed"
    db.commit()
    db.refresh(ticket)
    return ticket
