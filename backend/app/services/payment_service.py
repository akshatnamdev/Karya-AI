"""
Payment Service — provider-agnostic (Razorpay first).

RULES:
- Never mark invoice paid from frontend alone.
- record_payment / Payment rows only after signature or webhook verification.
- Missing credentials => 503 with clear message (no fake success).
- Full remaining balance only on payment links.
"""
from __future__ import annotations

import hmac
import hashlib
import secrets
import json
from datetime import datetime, timedelta, timezone, date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.order import Order
from app.models.customer import Customer
from app.models.payment import Payment, PaymentLink
from app.services.invoice_service import InvoiceService
from app.utils.formatters import safe_float

try:
    from app.core.config import settings

    def _cfg(name, default=""):
        return getattr(settings, name, default) or default
except Exception:
    import os

    def _cfg(name, default=""):
        return os.getenv(name, default) or default


class PaymentConfigError(Exception):
    pass


class BasePaymentProvider:
    name = "base"

    def is_configured(self) -> bool:
        raise NotImplementedError

    def create_order(self, amount_paise: int, currency: str, receipt: str, notes: dict) -> dict:
        raise NotImplementedError

    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        raise NotImplementedError

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        raise NotImplementedError


class RazorpayProvider(BasePaymentProvider):
    name = "razorpay"

    def __init__(self):
        self.key_id = str(_cfg("RAZORPAY_KEY_ID", "")).strip()
        self.key_secret = str(_cfg("RAZORPAY_KEY_SECRET", "")).strip()
        self.webhook_secret = str(_cfg("RAZORPAY_WEBHOOK_SECRET", "")).strip()
        self._client = None

    def is_configured(self) -> bool:
        return bool(self.key_id and self.key_secret)

    def _client_or_raise(self):
        if not self.is_configured():
            raise PaymentConfigError(
                "Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env"
            )
        if self._client is None:
            import razorpay

            self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
        return self._client

    def create_order(self, amount_paise: int, currency: str, receipt: str, notes: dict) -> dict:
        client = self._client_or_raise()
        try:
            order = client.order.create(
                {
                    "amount": int(amount_paise),
                    "currency": currency or "INR",
                    "receipt": (receipt or "")[:40],
                    "notes": notes or {},
                    "payment_capture": 1,
                }
            )
        except Exception as e:
            msg = str(e)
            low = msg.lower()
            if "auth" in low:
                raise PaymentConfigError(
                    "Razorpay authentication failed. Check RAZORPAY_KEY_ID and "
                    "RAZORPAY_KEY_SECRET (test keys, no quotes/spaces). "
                    f"Details: {msg}"
                )
            raise
        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": self.key_id,
        }

    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        if not self.is_configured():
            return False
        client = self._client_or_raise()
        try:
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": order_id,
                    "razorpay_payment_id": payment_id,
                    "razorpay_signature": signature,
                }
            )
            return True
        except Exception:
            return False

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        if not self.webhook_secret:
            return False
        expected = hmac.new(
            self.webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, (signature or "").strip())


def get_provider(name: Optional[str] = None) -> BasePaymentProvider:
    provider_name = (name or _cfg("PAYMENT_PROVIDER", "razorpay") or "razorpay").lower()
    if provider_name in ("", "none", "off", "disabled"):
        raise PaymentConfigError(
            "Payments are disabled. Set PAYMENT_PROVIDER=razorpay and gateway credentials."
        )
    if provider_name == "razorpay":
        return RazorpayProvider()
    raise PaymentConfigError(f"Unsupported payment provider: {provider_name}")


def _new_payment_number() -> str:
    return f"PAY-{int(datetime.now().timestamp())}-{secrets.token_hex(3)}"


class PaymentService:

    @staticmethod
    def provider_status() -> dict:
        try:
            p = get_provider()
            configured = p.is_configured()
            return {
                "provider": p.name,
                "configured": configured,
                "message": None
                if configured
                else "Payment gateway credentials missing. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.",
            }
        except PaymentConfigError as e:
            return {
                "provider": _cfg("PAYMENT_PROVIDER", "none"),
                "configured": False,
                "message": str(e),
            }

    @staticmethod
    def _public_base() -> str:
        return str(_cfg("PAYMENT_PUBLIC_BASE_URL", "http://localhost:5173")).rstrip("/")

    @staticmethod
    def _expiry_hours() -> int:
        try:
            return int(_cfg("PAYMENT_LINK_EXPIRY_HOURS", "72") or 72)
        except Exception:
            return 72

    @staticmethod
    def _get_invoice_for_business(db: Session, invoice_id: int, business_id: int) -> Invoice:
        inv = (
            db.query(Invoice)
            .join(Order, Invoice.order_id == Order.id)
            .filter(Invoice.id == invoice_id, Order.business_id == business_id)
            .first()
        )
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return inv

    @staticmethod
    @staticmethod
    def create_payment_link(
        db: Session,
        invoice_id: int,
        scope: dict,
        created_by_user_id: int = None,
    ) -> dict:
        role = scope.get("scope")
        business_id = scope.get("business_id")
        customer_id = scope.get("customer_id")

        if role not in ("business", "customer"):
            raise HTTPException(status_code=403, detail="Not allowed to create payment links")

        if not business_id:
            raise HTTPException(status_code=400, detail="Business context missing")

        st = PaymentService.provider_status()
        if not st["configured"]:
            raise HTTPException(
                status_code=503,
                detail=st["message"] or "Payment gateway not configured",
            )

        # ---- load invoice with RBAC ----
        q = (
            db.query(Invoice)
            .join(Order, Invoice.order_id == Order.id)
            .filter(Invoice.id == invoice_id, Order.business_id == business_id)
        )
        if role == "customer":
            if not customer_id:
                raise HTTPException(status_code=400, detail="Customer context missing")
            q = q.filter(Order.customer_id == customer_id)

        invoice = q.first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        inv_status = (invoice.status or "").lower()
        if inv_status in ("paid", "cancelled"):
            raise HTTPException(status_code=400, detail=f"Cannot create link for {inv_status} invoice")

        balance = safe_float(invoice.balance_amount)
        if balance <= 0:
            raise HTTPException(status_code=400, detail="Invoice has no outstanding balance")

        # ... rest of method UNCHANGED from amount_paise / provider.create_order onward ...

        amount_paise = int(round(balance * 100))
        if amount_paise < 100:
            raise HTTPException(status_code=400, detail="Amount too small for gateway (min ₹1)")

        provider = get_provider()
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=PaymentService._expiry_hours())

        receipt = f"inv-{invoice.id}-{token[:8]}"
        notes = {
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number or "",
            "business_id": str(business_id),
        }

        try:
            order_info = provider.create_order(
                amount_paise=amount_paise,
                currency="INR",
                receipt=receipt,
                notes=notes,
            )
        except PaymentConfigError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Gateway order failed: {e}")

        link = PaymentLink(
            token=token,
            invoice_id=invoice.id,
            business_id=business_id,
            amount=balance,
            currency="INR",
            status="created",
            provider=provider.name,
            provider_order_id=order_info["order_id"],
            expires_at=expires_at,
            created_by_user_id=created_by_user_id,
        )
        db.add(link)
        db.flush()

        order = db.query(Order).filter(Order.id == invoice.order_id).first()

        # Respect EXISTING required Payment columns
        pay = Payment(
            payment_number=_new_payment_number(),
            amount=balance,
            payment_method="razorpay",
            transaction_id=None,
            reference_number=order_info["order_id"],
            payment_date=date.today(),
            notes="Payment link created — awaiting gateway capture",
            invoice_id=invoice.id,
            # new gateway fields
            payment_link_id=link.id,
            business_id=business_id,
            customer_id=order.customer_id if order else None,
            currency="INR",
            status="created",
            provider=provider.name,
            provider_order_id=order_info["order_id"],
            signature_verified=False,
        )
        db.add(pay)

        try:
            db.commit()
            db.refresh(link)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save payment link: {e}")

        url = f"{PaymentService._public_base()}/pay/{token}"
        return {
            "token": token,
            "url": url,
            "amount": balance,
            "currency": "INR",
            "expires_at": expires_at.isoformat(),
            "provider": provider.name,
            "provider_order_id": order_info["order_id"],
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "status": link.status,
        }

    @staticmethod
    def get_public_pay_session(db: Session, token: str) -> dict:
        link = db.query(PaymentLink).filter(PaymentLink.token == token).first()
        if not link:
            raise HTTPException(status_code=404, detail="Payment link not found")

        now = datetime.now(timezone.utc)
        exp = link.expires_at
        if exp is not None:
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < now and link.status not in ("paid",):
                link.status = "expired"
                db.commit()
                raise HTTPException(status_code=410, detail="Payment link has expired")

        if link.status == "paid":
            invoice = db.query(Invoice).filter(Invoice.id == link.invoice_id).first()
            return {
                "status": "already_paid",
                "message": "This invoice is already paid.",
                "invoice_number": invoice.invoice_number if invoice else None,
                "amount": safe_float(link.amount),
                "paid": True,
            }

        if link.status == "cancelled":
            raise HTTPException(status_code=400, detail="Payment link cancelled")

        st = PaymentService.provider_status()
        if not st["configured"]:
            raise HTTPException(status_code=503, detail=st["message"] or "Payment gateway not configured")

        invoice = db.query(Invoice).filter(Invoice.id == link.invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        order = db.query(Order).filter(Order.id == invoice.order_id).first()
        customer = None
        if order:
            customer = db.query(Customer).filter(Customer.id == order.customer_id).first()

        if link.status == "created":
            link.status = "opened"
            db.commit()

        provider = get_provider(link.provider)
        key_id = getattr(provider, "key_id", "") or ""

        return {
            "status": "ready",
            "token": token,
            "amount": safe_float(link.amount),
            "currency": link.currency or "INR",
            "invoice_number": invoice.invoice_number,
            "invoice_id": invoice.id,
            "customer_name": customer.name if customer else None,
            "customer_email": getattr(customer, "email", None) if customer else None,
            "customer_phone": customer.phone if customer else None,
            "provider": link.provider,
            "provider_order_id": link.provider_order_id,
            "key_id": key_id,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "paid": False,
            "message": "Complete payment via gateway. Invoice updates only after verification.",
        }

    @staticmethod
    def verify_checkout_payment(
        db: Session,
        token: str,
        provider_order_id: str,
        provider_payment_id: str,
        signature: str,
    ) -> dict:
        link = db.query(PaymentLink).filter(PaymentLink.token == token).first()
        if not link:
            raise HTTPException(status_code=404, detail="Payment link not found")

        if link.provider_order_id and provider_order_id != link.provider_order_id:
            raise HTTPException(status_code=400, detail="Order ID mismatch")

        provider = get_provider(link.provider)
        if not provider.is_configured():
            raise HTTPException(status_code=503, detail="Payment gateway not configured")

        if not provider.verify_payment_signature(
            order_id=provider_order_id,
            payment_id=provider_payment_id,
            signature=signature,
        ):
            raise HTTPException(status_code=400, detail="Invalid payment signature")

        return PaymentService._capture_verified_payment(
            db=db,
            link=link,
            provider_order_id=provider_order_id,
            provider_payment_id=provider_payment_id,
            raw_event={
                "source": "checkout_verify",
                "order_id": provider_order_id,
                "payment_id": provider_payment_id,
            },
        )

    @staticmethod
    def handle_razorpay_webhook(db: Session, body: bytes, signature_header: str) -> dict:
        provider = RazorpayProvider()
        if not provider.webhook_secret:
            raise HTTPException(status_code=503, detail="RAZORPAY_WEBHOOK_SECRET not configured")
        if not provider.verify_webhook_signature(body, signature_header):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid webhook JSON")

        event = payload.get("event") or ""
        if event not in ("payment.captured", "payment.authorized"):
            return {"ok": True, "ignored": True, "event": event}

        entity = (payload.get("payload") or {}).get("payment", {}).get("entity", {}) or {}
        provider_payment_id = entity.get("id")
        provider_order_id = entity.get("order_id")
        amount_paise = entity.get("amount")

        if not provider_order_id or not provider_payment_id:
            return {"ok": True, "ignored": True, "reason": "missing ids"}

        link = (
            db.query(PaymentLink)
            .filter(PaymentLink.provider_order_id == provider_order_id)
            .first()
        )
        if not link:
            print(f"[webhook] no PaymentLink for order {provider_order_id}")
            return {"ok": True, "ignored": True, "reason": "unknown_order"}

        return PaymentService._capture_verified_payment(
            db=db,
            link=link,
            provider_order_id=provider_order_id,
            provider_payment_id=provider_payment_id,
            raw_event={"source": "webhook", "event": event, "payment": entity},
            expected_amount_paise=amount_paise,
        )

    @staticmethod
    def _capture_verified_payment(
        db: Session,
        link: PaymentLink,
        provider_order_id: str,
        provider_payment_id: str,
        raw_event: dict,
        expected_amount_paise: int = None,
    ) -> dict:
        # Idempotent by provider_payment_id
        existing = (
            db.query(Payment)
            .filter(Payment.provider_payment_id == provider_payment_id)
            .first()
        )
        if existing and existing.signature_verified and (existing.status or "") == "captured":
            invoice = db.query(Invoice).filter(Invoice.id == link.invoice_id).first()
            return {
                "ok": True,
                "idempotent": True,
                "payment_id": existing.id,
                "payment_number": existing.payment_number,
                "invoice_status": invoice.status if invoice else None,
                "message": "Payment already recorded",
            }

        if link.status == "paid":
            return {
                "ok": True,
                "idempotent": True,
                "message": "Link already paid",
                "invoice_id": link.invoice_id,
            }

        amount = safe_float(link.amount)
        if expected_amount_paise is not None:
            expected = safe_float(expected_amount_paise) / 100.0
            if abs(expected - amount) > 0.05:
                raise HTTPException(
                    status_code=400,
                    detail=f"Amount mismatch: link={amount} gateway={expected}",
                )

        invoice = db.query(Invoice).filter(Invoice.id == link.invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        order = db.query(Order).filter(Order.id == invoice.order_id).first()

        pay = existing
        if not pay:
            pay = (
                db.query(Payment)
                .filter(
                    Payment.provider_order_id == provider_order_id,
                    Payment.invoice_id == link.invoice_id,
                )
                .order_by(Payment.id.desc())
                .first()
            )

        if not pay:
            pay = Payment(
                payment_number=_new_payment_number(),
                amount=amount,
                payment_method="razorpay",
                payment_date=date.today(),
                invoice_id=link.invoice_id,
                business_id=link.business_id,
                customer_id=order.customer_id if order else None,
                currency=link.currency or "INR",
                provider=link.provider,
            )
            db.add(pay)

        pay.payment_link_id = link.id
        pay.amount = amount
        pay.payment_method = "razorpay"
        pay.transaction_id = provider_payment_id
        pay.reference_number = provider_payment_id
        pay.payment_date = date.today()
        pay.notes = f"Verified gateway payment {provider_payment_id}"
        pay.provider_order_id = provider_order_id
        pay.provider_payment_id = provider_payment_id
        pay.status = "captured"
        pay.signature_verified = True
        pay.provider = link.provider
        pay.raw_event = raw_event
        pay.verified_at = datetime.now(timezone.utc)
        pay.business_id = link.business_id
        if order:
            pay.customer_id = order.customer_id

        link.status = "paid"
        link.paid_at = datetime.now(timezone.utc)

        db.flush()

        scope = {"scope": "business", "business_id": link.business_id}
        try:
            bal = safe_float(invoice.balance_amount)
            if bal > 0:
                apply_amt = min(amount, bal)
                InvoiceService.record_payment(
                    db=db,
                    invoice_id=invoice.id,
                    amount=apply_amt,
                    scope=scope,
                    payment_method="razorpay",
                    note=f"Verified gateway payment {provider_payment_id}",
                    reference=provider_payment_id,
                )
            else:
                db.commit()
        except HTTPException as e:
            detail = str(getattr(e, "detail", e)).lower()
            if "already" in detail:
                try:
                    db.commit()
                except Exception:
                    db.rollback()
            else:
                db.rollback()
                raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to apply payment: {e}")

        db.refresh(invoice)
        db.refresh(pay)
        return {
            "ok": True,
            "payment_id": pay.id,
            "payment_number": pay.payment_number,
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_status": invoice.status,
            "balance": safe_float(invoice.balance_amount),
            "paid_amount": safe_float(invoice.paid_amount),
            "message": "Payment verified and recorded",
        }

    @staticmethod
    def get_link_status(db: Session, token: str) -> dict:
        link = db.query(PaymentLink).filter(PaymentLink.token == token).first()
        if not link:
            raise HTTPException(status_code=404, detail="Not found")
        invoice = db.query(Invoice).filter(Invoice.id == link.invoice_id).first()
        return {
            "link_status": link.status,
            "invoice_status": invoice.status if invoice else None,
            "balance": safe_float(invoice.balance_amount) if invoice else None,
            "paid": ((invoice.status or "").lower() == "paid") if invoice else False,
            "amount": safe_float(link.amount),
            "invoice_number": invoice.invoice_number if invoice else None,
        }