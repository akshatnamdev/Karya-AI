from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.support_service import SupportService


router = APIRouter(prefix="/api/support", tags=["Support"])


class CreateTicketReq(BaseModel):
    subject: str = Field(..., min_length=3, max_length=200)
    body: str = Field(..., min_length=1, max_length=4000)


class ReplyReq(BaseModel):
    body: str = Field(..., min_length=1, max_length=4000)


@router.get("/tickets")
def list_tickets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return SupportService.list_tickets(db, current_user)


@router.post("/tickets")
def create_ticket(
    payload: CreateTicketReq,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SupportService.create_ticket(db, current_user, payload.subject, payload.body)


@router.get("/tickets/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SupportService.get_ticket(db, current_user, ticket_id)


@router.post("/tickets/{ticket_id}/reply")
def reply(
    ticket_id: int,
    payload: ReplyReq,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SupportService.reply(db, current_user, ticket_id, payload.body)


@router.post("/tickets/{ticket_id}/escalate")
def escalate(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SupportService.escalate(db, current_user, ticket_id)


@router.post("/tickets/{ticket_id}/resolve")
def resolve(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SupportService.resolve(db, current_user, ticket_id)