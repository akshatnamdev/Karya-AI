"""
Support ticket service
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.support import SupportTicket, SupportMessage, TicketStatus
from app.models.user import User, UserRole
from app.utils.formatters import safe_iso


class SupportService:

    @staticmethod
    def _serialize_ticket(t: SupportTicket, db: Session, include_messages=False) -> dict:
        opener = db.query(User).filter(User.id == t.opened_by_id).first()
        data = {
            "id": t.id,
            "subject": t.subject,
            "status": t.status.value if hasattr(t.status, "value") else t.status,
            "opened_by": {
                "id": opener.id if opener else None,
                "name": opener.name if opener else "Unknown",
                "email": opener.email if opener else "",
                "role": (opener.role.value if hasattr(opener.role, "value") else opener.role)
                if opener else "",
            },
            "business_id": t.business_id,
            "assigned_to_role": t.assigned_to_role,
            "created_at": safe_iso(t.created_at),
            "updated_at": safe_iso(t.updated_at),
        }
        if include_messages:
            msgs = sorted(t.messages, key=lambda m: m.created_at)
            data["messages"] = [
                {
                    "id": m.id,
                    "body": m.body,
                    "sender_id": m.sender_id,
                    "sender_role": m.sender_role,
                    "created_at": safe_iso(m.created_at),
                }
                for m in msgs
            ]
        return data

    @staticmethod
    def list_tickets(db: Session, user: User) -> list:
        role = user.role.value if hasattr(user.role, "value") else user.role
        q = db.query(SupportTicket).order_by(SupportTicket.updated_at.desc())

        if role == UserRole.CUSTOMER.value:
            q = q.filter(SupportTicket.opened_by_id == user.id)
        elif role == UserRole.BUSINESS_OWNER.value:
            q = q.filter(SupportTicket.business_id == user.business_id)
        # platform_admin sees all

        return [SupportService._serialize_ticket(t, db) for t in q.all()]

    @staticmethod
    def get_ticket(db: Session, user: User, ticket_id: int) -> dict:
        t = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")

        role = user.role.value if hasattr(user.role, "value") else user.role
        if role == UserRole.CUSTOMER.value and t.opened_by_id != user.id:
            raise HTTPException(status_code=403, detail="Not your ticket")
        if role == UserRole.BUSINESS_OWNER.value and t.business_id != user.business_id:
            raise HTTPException(status_code=403, detail="Not your business")

        return SupportService._serialize_ticket(t, db, include_messages=True)

    @staticmethod
    def create_ticket(db: Session, user: User, subject: str, body: str) -> dict:
        role = user.role.value if hasattr(user.role, "value") else user.role

        if role == UserRole.CUSTOMER.value:
            # customer opens ticket -> goes to their business owner
            biz_id = user.business_id
            assigned_to = "business_owner"
        elif role == UserRole.BUSINESS_OWNER.value:
            # business owner opens ticket -> goes to platform admin
            biz_id = user.business_id
            assigned_to = "platform_admin"
        else:
            raise HTTPException(status_code=400, detail="Admin cannot open tickets")

        t = SupportTicket(
            subject=subject,
            opened_by_id=user.id,
            business_id=biz_id,
            assigned_to_role=assigned_to,
            status=TicketStatus.OPEN,
        )
        db.add(t)
        db.flush()

        m = SupportMessage(
            ticket_id=t.id,
            sender_id=user.id,
            sender_role=role,
            body=body,
        )
        db.add(m)
        db.commit()
        db.refresh(t)
        return SupportService._serialize_ticket(t, db, include_messages=True)

    @staticmethod
    def reply(db: Session, user: User, ticket_id: int, body: str) -> dict:
        t = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")

        role = user.role.value if hasattr(user.role, "value") else user.role

        if role == UserRole.CUSTOMER.value and t.opened_by_id != user.id:
            raise HTTPException(status_code=403, detail="Not your ticket")
        if role == UserRole.BUSINESS_OWNER.value and t.business_id != user.business_id:
            raise HTTPException(status_code=403, detail="Not your business")

        m = SupportMessage(
            ticket_id=t.id,
            sender_id=user.id,
            sender_role=role,
            body=body,
        )
        db.add(m)
        t.updated_at = datetime.utcnow()
        db.commit()
        return SupportService.get_ticket(db, user, ticket_id)

    @staticmethod
    def escalate(db: Session, user: User, ticket_id: int) -> dict:
        t = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")
        role = user.role.value if hasattr(user.role, "value") else user.role
        if role != UserRole.BUSINESS_OWNER.value:
            raise HTTPException(status_code=403, detail="Only business can escalate")
        if t.business_id != user.business_id:
            raise HTTPException(status_code=403, detail="Not your business")

        t.assigned_to_role = "platform_admin"
        t.status = TicketStatus.PENDING_ADMIN
        db.commit()
        return SupportService.get_ticket(db, user, ticket_id)

    @staticmethod
    def resolve(db: Session, user: User, ticket_id: int) -> dict:
        t = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")
        t.status = TicketStatus.RESOLVED
        db.commit()
        return SupportService.get_ticket(db, user, ticket_id)