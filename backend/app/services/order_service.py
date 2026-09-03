"""
Order Service - role-aware
"""
from datetime import date, timedelta
import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.order import Order, OrderItem
from app.models.customer import Customer
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.invoice import Invoice
from app.utils.formatters import safe_float, safe_iso


class OrderService:

    # ==================== READ ====================

    @staticmethod
    def get_all_orders(db: Session, scope: dict) -> list:
        try:
            q = db.query(Order).order_by(Order.order_date.desc())

            role = (scope or {}).get("scope")
            if role == "business":
                q = q.filter(Order.business_id == scope.get("business_id"))
            elif role == "customer":
                q = q.filter(Order.customer_id == scope.get("customer_id"))

            orders = q.all()
            result = []
            for o in orders:
                try:
                    result.append(OrderService._format_order_summary(o, db))
                except Exception as e:
                    print(f"[get_all_orders format error order_id={getattr(o, 'id', None)}] {e}")
                    result.append(
                        {
                            "id": o.id,
                            "order_number": o.order_number,
                            "customer_name": "Unknown",
                            "customer_phone": None,
                            "status": o.status,
                            "source": o.source,
                            "total": safe_float(o.total_amount),
                            "items_count": 0,
                            "order_date": safe_iso(o.order_date),
                            "delivery_date": safe_iso(getattr(o, "delivery_date", None)),
                            "whatsapp_message": getattr(o, "original_message", None),
                        }
                    )
            return result
        except Exception as e:
            print(f"[get_all_orders ERROR] {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load orders: {e}")

    @staticmethod
    def get_order_detail(db: Session, order_id: int, scope: dict) -> dict:
        q = db.query(Order).filter(Order.id == order_id)

        role = (scope or {}).get("scope")
        if role == "business":
            q = q.filter(Order.business_id == scope.get("business_id"))
        elif role == "customer":
            q = q.filter(Order.customer_id == scope.get("customer_id"))

        order = q.first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return OrderService._format_order_detail(order, db)

    @staticmethod
    def get_whatsapp_orders(db: Session, scope: dict) -> dict:
        if (scope or {}).get("scope") == "customer":
            return {"count": 0, "orders": []}

        q = db.query(Order).filter(Order.source == "whatsapp").order_by(Order.order_date.desc())

        if (scope or {}).get("scope") == "business":
            q = q.filter(Order.business_id == scope.get("business_id"))

        orders = q.all()
        return {
            "count": len(orders),
            "orders": [OrderService._format_whatsapp_order(o) for o in orders],
        }

    # ==================== CREATE ====================

    @staticmethod
    def create_unified_order(
        db: Session,
        business_id: int,
        customer_id: int,
        items_data: list,
        source: str = "manual",
        notes: str = None,
    ) -> dict:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        if not items_data:
            raise HTTPException(status_code=400, detail="Order must have at least one item")

        timestamp = int(datetime.datetime.now().timestamp())
        order_number = f"ORD-{timestamp}"

        new_order = Order(
            order_number=order_number,
            business_id=business_id,
            customer_id=customer_id,
            status="pending",
            source=source or "manual",
            notes=notes,
            subtotal=0,
            tax_amount=0,
            discount_amount=0,
            total_amount=0,
        )
        db.add(new_order)
        db.flush()

        subtotal = 0

        for item in items_data:
            product_id = item.get("product_id")
            qty = int(item.get("quantity") or 0)

            if not product_id or qty <= 0:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail="Each item needs a valid product_id and quantity > 0",
                )

            product = (
                db.query(Product)
                .filter(
                    Product.id == product_id,
                    Product.business_id == business_id,
                    Product.is_active == True,
                )
                .first()
            )
            if not product:
                db.rollback()
                raise HTTPException(
                    status_code=404,
                    detail=f"Product ID {product_id} not found or inactive",
                )

            inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
            available = int(inventory.current_stock) if inventory else 0
            if not inventory or available < qty:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Insufficient stock for '{product.name}'. "
                        f"Available: {available}, requested: {qty}"
                    ),
                )

            unit_price = product.selling_price
            item_total = unit_price * qty
            subtotal += item_total

            db.add(
                OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=unit_price,
                    discount=0,
                    tax_amount=0,
                    total=item_total,
                )
            )
            inventory.current_stock = available - qty

        new_order.subtotal = subtotal
        new_order.total_amount = subtotal

        try:
            db.commit()
            db.refresh(new_order)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error during order creation: {e}")

        return OrderService._format_order_detail(new_order, db)

    # ==================== STATUS / LIFECYCLE ====================

    @staticmethod
    def update_status(
        db: Session,
        order_id,
        new_status: str,
        scope: dict,
        note: str = None,
    ) -> dict:
        new_status = (new_status or "").lower().strip()
        allowed = {"confirmed", "cancelled", "delivered"}
        if new_status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"status must be one of: {', '.join(sorted(allowed))}",
            )

        role = (scope or {}).get("scope")
        business_id = (scope or {}).get("business_id")
        customer_id = (scope or {}).get("customer_id")

        target = str(order_id).strip()
        q = db.query(Order)

        if target.isdigit():
            q = q.filter(
                or_(
                    Order.id == int(target),
                    Order.order_number == target,
                    Order.order_number == f"ORD-{target}",
                )
            )
        else:
            q = q.filter(Order.order_number == target)

        if role == "business" and business_id:
            q = q.filter(Order.business_id == business_id)
        elif role == "customer" and customer_id:
            q = q.filter(Order.customer_id == customer_id)
        else:
            raise HTTPException(status_code=403, detail="Not allowed")

        order = q.first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        current = (order.status or "pending").lower()

        try:
            if new_status == "confirmed":
                if role != "business":
                    raise HTTPException(status_code=403, detail="Only business can confirm orders")
                if current != "pending":
                    raise HTTPException(
                        status_code=400,
                        detail=f"Only pending orders can be confirmed (current: {current})",
                    )

                order.status = "confirmed"
                if note:
                    order.internal_notes = ((order.internal_notes or "") + f"\n[confirm] {note}").strip()

                invoice = OrderService._create_invoice_for_order(db, order)
                OrderService._adjust_customer_outstanding(
                    db, order.customer_id, delta=safe_float(invoice.total_amount)
                )

            elif new_status == "cancelled":
                if current == "cancelled":
                    raise HTTPException(status_code=400, detail="Order already cancelled")
                if current == "delivered":
                    raise HTTPException(status_code=400, detail="Delivered orders cannot be cancelled")

                if role == "customer":
                    if current != "pending":
                        raise HTTPException(
                            status_code=400,
                            detail="Customers can cancel only pending orders",
                        )
                elif role != "business":
                    raise HTTPException(status_code=403, detail="Not allowed to cancel")

                if current == "confirmed":
                    OrderService._cancel_invoice_for_order(db, order)

                OrderService._restore_stock_for_order(db, order)
                order.status = "cancelled"
                if note:
                    order.internal_notes = ((order.internal_notes or "") + f"\n[cancel] {note}").strip()

            elif new_status == "delivered":
                if role != "business":
                    raise HTTPException(status_code=403, detail="Only business can mark delivered")
                if current not in ("confirmed", "processing", "shipped"):
                    raise HTTPException(
                        status_code=400,
                        detail="Order must be confirmed before delivery",
                    )
                order.status = "delivered"
                order.delivered_at = datetime.datetime.utcnow()
                if note:
                    order.internal_notes = ((order.internal_notes or "") + f"\n[deliver] {note}").strip()

            db.commit()
            db.refresh(order)
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            print(f"[update_status ERROR] {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update order status: {e}")

        try:
            return OrderService._format_order_detail(order, db)
        except Exception as e:
            print(f"[update_status format ERROR] {e}")
            return {
                "order": {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "total": safe_float(order.total_amount),
                },
                "items": [],
                "items_count": 0,
                "warning": f"Updated, but detail format failed: {e}",
            }

    @staticmethod
    def _create_invoice_for_order(db: Session, order: Order) -> Invoice:
        existing = db.query(Invoice).filter(Invoice.order_id == order.id).first()
        if existing:
            return existing

        today = date.today()
        due = today + timedelta(days=15)
        inv_number = f"INV-{order.id}-{int(datetime.datetime.now().timestamp())}"

        total = safe_float(order.total_amount)
        subtotal = safe_float(order.subtotal) if order.subtotal is not None else total
        tax = safe_float(order.tax_amount) if order.tax_amount is not None else 0
        discount = safe_float(order.discount_amount) if order.discount_amount is not None else 0

        invoice = Invoice(
            invoice_number=inv_number,
            status="sent",
            subtotal=subtotal,
            tax_amount=tax,
            discount_amount=discount,
            total_amount=total,
            paid_amount=0,
            balance_amount=total,
            invoice_date=today,
            due_date=due,
            order_id=order.id,
            notes=f"Auto-created on order confirm ({order.order_number})",
        )
        db.add(invoice)
        db.flush()
        return invoice

    @staticmethod
    def _cancel_invoice_for_order(db: Session, order: Order) -> None:
        invoice = db.query(Invoice).filter(Invoice.order_id == order.id).first()
        if not invoice:
            return
        if (invoice.status or "").lower() == "cancelled":
            return

        balance = safe_float(invoice.balance_amount)
        if balance > 0:
            OrderService._adjust_customer_outstanding(db, order.customer_id, delta=-balance)

        invoice.status = "cancelled"
        invoice.balance_amount = 0

    @staticmethod
    def _restore_stock_for_order(db: Session, order: Order) -> None:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        for item in items:
            inv = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
            if inv:
                inv.current_stock = int(inv.current_stock or 0) + int(item.quantity or 0)

    @staticmethod
    def _adjust_customer_outstanding(db: Session, customer_id: int, delta: float) -> None:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return
        current = safe_float(customer.outstanding_amount)
        new_val = current + float(delta or 0)
        customer.outstanding_amount = new_val if new_val > 0 else 0

    @staticmethod
    def delete_order(db: Session, order_id, scope: dict) -> dict:
        """
        Business only. Only pending or cancelled.
        Pending => restore stock. Confirmed/delivered => refuse (use cancel first).
        """
        if scope.get("scope") != "business":
            raise HTTPException(status_code=403, detail="Only business can delete orders")

        business_id = scope.get("business_id")
        if not business_id:
            raise HTTPException(status_code=400, detail="Business context missing")

        target = str(order_id).strip()
        q = db.query(Order).filter(Order.business_id == business_id)
        if target.isdigit():
            from sqlalchemy import or_
            q = q.filter(
                or_(
                    Order.id == int(target),
                    Order.order_number == target,
                    Order.order_number == f"ORD-{target}",
                )
            )
        else:
            q = q.filter(Order.order_number == target)

        order = q.first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        status_now = (order.status or "").lower()
        if status_now not in ("pending", "cancelled"):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot delete order in status '{status_now}'. "
                    "Cancel it first if needed, or only delete pending/cancelled orders."
                ),
            )

        # Block if invoice exists and not cancelled
        inv = db.query(Invoice).filter(Invoice.order_id == order.id).first()
        if inv and (inv.status or "").lower() not in ("cancelled",):
            raise HTTPException(
                status_code=400,
                detail="Order has an active invoice. Cancel the order/invoice before delete.",
            )

        order_number = order.order_number
        oid = order.id

        if status_now == "pending":
            OrderService._restore_stock_for_order(db, order)

        # Remove items then order (cascade may already handle items)
        db.query(OrderItem).filter(OrderItem.order_id == order.id).delete()
        if inv:
            db.delete(inv)
        db.delete(order)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete order: {e}")

        return {
            "ok": True,
            "id": oid,
            "order_number": order_number,
            "message": f"Order {order_number} deleted",
        }   

    # ==================== PRIVATE HELPERS ====================

    @staticmethod
    def _format_order_summary(order, db):
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        items_count = db.query(OrderItem).filter(OrderItem.order_id == order.id).count()

        return {
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": customer.name if customer else "Unknown",
            "customer_phone": customer.phone if customer else None,
            "status": order.status,
            "source": order.source,
            "total": safe_float(order.total_amount),
            "items_count": items_count,
            "order_date": safe_iso(order.order_date),
            "delivery_date": safe_iso(getattr(order, "delivery_date", None)),
            "whatsapp_message": getattr(order, "original_message", None),
        }

    @staticmethod
    def _format_order_detail(order, db):
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        items_detail = [OrderService._format_order_item(item, db) for item in items]

        invoice_id = None
        invoice_number = None
        invoice_status = None
        invoice_balance = None
        try:
            invoice = db.query(Invoice).filter(Invoice.order_id == order.id).first()
            if invoice:
                invoice_id = invoice.id
                invoice_number = invoice.invoice_number
                invoice_status = invoice.status
                invoice_balance = safe_float(invoice.balance_amount)
        except Exception as e:
            print(f"[order_detail invoice attach] {e}")

        return {
            "order": {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "source": order.source,
                "subtotal": safe_float(order.subtotal),
                "tax": safe_float(order.tax_amount),
                "discount": safe_float(order.discount_amount),
                "total": safe_float(order.total_amount),
                "order_date": safe_iso(order.order_date),
                "delivery_date": safe_iso(getattr(order, "delivery_date", None)),
                "delivered_at": safe_iso(getattr(order, "delivered_at", None)),
                "original_message": getattr(order, "original_message", None),
                "notes": order.notes,
                "invoice_id": invoice_id,
                "invoice_number": invoice_number,
                "invoice_status": invoice_status,
                "invoice_balance": invoice_balance,
            },
            "customer": {
                "id": customer.id if customer else None,
                "name": customer.name if customer else "Unknown",
                "phone": customer.phone if customer else None,
                "whatsapp": getattr(customer, "whatsapp_number", None) if customer else None,
                "city": getattr(customer, "city", None) if customer else None,
                "type": getattr(customer, "customer_type", None) if customer else None,
                "outstanding_amount": safe_float(getattr(customer, "outstanding_amount", 0))
                if customer
                else 0,
            }
            if customer
            else None,
            "items": items_detail,
            "items_count": len(items_detail),
        }

    @staticmethod
    def _format_order_item(item, db):
        product = db.query(Product).filter(Product.id == item.product_id).first()
        return {
            "product_id": item.product_id,
            "product_name": product.name if product else "Unknown",
            "sku": product.sku if product else None,
            "quantity": item.quantity,
            "unit_price": safe_float(item.unit_price),
            "discount": safe_float(getattr(item, "discount", 0)),
            "total": safe_float(item.total),
        }

    @staticmethod
    def _format_whatsapp_order(order):
        return {
            "order_number": order.order_number,
            "customer_id": order.customer_id,
            "original_whatsapp_message": getattr(order, "original_message", None),
            "total": safe_float(order.total_amount),
            "status": order.status,
            "date": safe_iso(order.order_date),
        }