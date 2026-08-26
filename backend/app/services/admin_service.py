"""
Admin Service - Platform-wide operations (Smart Owner Lookup & Business Disable)
"""
from sqlalchemy import func
from sqlalchemy.orm import Session
import traceback

from app.models.business import Business
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.inventory import Inventory

class AdminService:
    
    @staticmethod
    def _safe_float(val):
        try:
            return float(val) if val else 0.0
        except:
            return 0.0

    @staticmethod
    def _safe_str(val):
        if val is None:
            return "—"
        return str(val)

    @staticmethod
    def platform_stats(db: Session) -> dict:
        total_businesses = db.query(Business).count()
        total_users = db.query(User).count()
        total_customers = db.query(Customer).count()
        total_orders = db.query(Order).count()
        total_invoices = db.query(Invoice).count()
        
        rev = db.query(func.sum(Order.total_amount)).scalar()
        out = db.query(func.sum(Invoice.balance_amount)).filter(
            Invoice.status.in_(["overdue", "partially_paid", "sent"])
        ).scalar()

        open_tickets = 0
        try:
            from app.models.support import SupportTicket
            open_tickets = db.query(SupportTicket).filter(SupportTicket.status == 'open').count()
        except:
            pass

        return {
            "total_businesses": total_businesses,
            "active_businesses": total_businesses,
            "total_users": total_users,
            "total_customers": total_customers,
            "total_orders": total_orders,
            "total_invoices": total_invoices,
            "total_revenue": AdminService._safe_float(rev),
            "total_outstanding": AdminService._safe_float(out),
            "open_tickets": open_tickets
        }

    @staticmethod
    def _get_owner_for_business(db: Session, business: Business) -> User:
        """Smart Owner Finder: Checks owner_id first, then falls back to searching users by business_id"""
        owner = None
        if getattr(business, 'owner_id', None):
            owner = db.query(User).filter(User.id == business.owner_id).first()
            
        if not owner:
            # Fallback: Find the user linked to this business
            owner = db.query(User).filter(User.business_id == business.id).first()
            if owner:
                # Auto-repair DB link so it stays fixed
                business.owner_id = owner.id
                db.commit()
        return owner

    @staticmethod
    def list_businesses(db: Session) -> list:
        businesses = db.query(Business).order_by(Business.id.desc()).all()
        results = []
        for b in businesses:
            try:
                customers = db.query(Customer).filter(Customer.business_id == b.id).count()
                users = db.query(User).filter(User.business_id == b.id).count()
                orders = db.query(Order).filter(Order.business_id == b.id).count()
                rev = db.query(func.sum(Order.total_amount)).filter(Order.business_id == b.id).scalar()
                
                # Smart owner resolution
                owner = AdminService._get_owner_for_business(db, b)
                owner_name = owner.name if (owner and owner.name) else "No Owner"
                
                # Check active status based on owner or users
                is_active = owner.is_active if owner else True

                results.append({
                    "id": b.id,
                    "name": AdminService._safe_str(b.name),
                    "type": AdminService._safe_str(b.business_type).replace('_', ' ').title(),
                    "city": b.city if b.city else "—",
                    "owner_name": owner_name,
                    "owner_email": owner.email if owner else "—",
                    "customers": customers,
                    "users": users,
                    "orders": orders,
                    "revenue": AdminService._safe_float(rev),
                    "is_active": is_active,
                    "created_at": AdminService._safe_str(b.created_at)
                })
            except Exception as e:
                print(f"⚠️ Error loading business {b.id} in list: {e}")
                results.append({
                    "id": getattr(b, 'id', 0),
                    "name": getattr(b, 'name', 'Unknown'),
                    "type": "—", "city": "—", "owner_name": "—", "owner_email": "—",
                    "customers": 0, "users": 0, "orders": 0, "revenue": 0.0, "is_active": True
                })
        return results

    @staticmethod
    def business_detail(db: Session, business_id: int) -> dict:
        try:
            b = db.query(Business).filter(Business.id == business_id).first()
            if not b:
                return None

            owner = AdminService._get_owner_for_business(db, b)
            users = db.query(User).filter(User.business_id == b.id).all()
            customers = db.query(Customer).filter(Customer.business_id == b.id).all()
            products = db.query(Product).filter(Product.business_id == b.id).all()
            orders = db.query(Order).filter(Order.business_id == b.id).order_by(Order.order_date.desc()).limit(5).all()
            total_orders_count = db.query(Order).filter(Order.business_id == b.id).count()
            
            invoices_count = 0
            revenue = 0.0
            payments_count = 0
            
            if total_orders_count > 0:
                revenue = AdminService._safe_float(db.query(func.sum(Order.total_amount)).filter(Order.business_id == b.id).scalar())
                order_ids = [o.id for o in db.query(Order.id).filter(Order.business_id == b.id).all()]
                if order_ids:
                    invoices_count = db.query(Invoice).filter(Invoice.order_id.in_(order_ids)).count()
                    invoice_ids = [i.id for i in db.query(Invoice.id).filter(Invoice.order_id.in_(order_ids)).all()]
                    if invoice_ids:
                        payments_count = db.query(Payment).filter(Payment.invoice_id.in_(invoice_ids)).count()

            outstanding = sum([AdminService._safe_float(c.outstanding_amount) for c in customers])
            
            stock_value = 0.0
            if products:
                stock_val_query = db.query(func.sum(Inventory.current_stock * Product.selling_price)).join(
                    Product, Inventory.product_id == Product.id
                ).filter(Product.business_id == b.id).scalar()
                stock_value = AdminService._safe_float(stock_val_query)

            wa_orders = [o for o in orders if getattr(o, 'source', '') == 'whatsapp']
            wa_status = "Connected (Active)" if len(wa_orders) > 0 else "Not Used Yet"

            tickets_count = 0
            try:
                from app.models.support import SupportTicket
                tickets_count = db.query(SupportTicket).filter(SupportTicket.business_id == b.id).count()
            except:
                pass

            is_active = owner.is_active if owner else True

            return {
                "business": {
                    "id": b.id,
                    "name": AdminService._safe_str(b.name),
                    "type": AdminService._safe_str(b.business_type).replace('_', ' ').title(),
                    "city": b.city if b.city else "—",
                    "gst": AdminService._safe_str(b.gst_number),
                    "created_at": str(b.created_at)[:10] if getattr(b, 'created_at', None) else "—",
                    "whatsapp_status": wa_status,
                    "is_active": is_active
                },
                "financials": {
                    "revenue": revenue,
                    "outstanding": outstanding,
                    "stock_value": stock_value
                },
                "owner": {
                    "name": owner.name if (owner and owner.name) else "No Owner Attached",
                    "email": owner.email if (owner and owner.email) else "—",
                    "phone": owner.phone if (owner and owner.phone) else "—"
                },
                "counts": {
                    "users": len(users),
                    "customers": len(customers),
                    "products": len(products),
                    "orders": total_orders_count,
                    "invoices": invoices_count,
                    "payments": payments_count,
                    "tickets": tickets_count
                },
                "team": [
                    {"name": u.name, "role": str(u.role).replace('UserRole.', '').replace('_', ' ').title()} 
                    for u in users
                ],
                "recent_orders": [
                    {
                        "order_number": o.order_number,
                        "total": AdminService._safe_float(o.total_amount),
                        "status": o.status
                    }
                    for o in orders
                ]
            }
        except Exception as e:
            print(f"⚠️ Error loading details for business {business_id}: {e}")
            traceback.print_exc()
            return None

    @staticmethod
    def toggle_business_active(db: Session, business_id: int, active: bool) -> dict:
        """Disables or enables all users associated with this business"""
        users = db.query(User).filter(User.business_id == business_id).all()
        for u in users:
            u.is_active = active
        db.commit()
        return {"business_id": business_id, "is_active": active, "affected_users": len(users)}

    @staticmethod
    def list_users(db: Session) -> list:
        users = db.query(User).order_by(User.id.desc()).all()
        result = []
        for u in users:
            b_name = "Platform"
            if getattr(u, 'business_id', None):
                b = db.query(Business).filter(Business.id == u.business_id).first()
                if b: b_name = b.name
            
            role_str = u.role.value if hasattr(u.role, "value") else str(u.role)
            if "UserRole" in role_str:
                role_str = role_str.split('.')[-1]

            result.append({
                "id": u.id,
                "name": AdminService._safe_str(u.name),
                "email": AdminService._safe_str(u.email),
                "role": role_str.replace('_', ' ').title(),
                "business_name": b_name,
                "is_active": u.is_active,
                "created_at": str(u.created_at)[:10] if getattr(u, 'created_at', None) else "—"
            })
        return result

    @staticmethod
    def toggle_user_active(db: Session, user_id: int, active: bool) -> dict:
        u = db.query(User).filter(User.id == user_id).first()
        if u:
            u.is_active = active
            db.commit()
            return {"id": u.id, "is_active": u.is_active}
        return {"error": "Not found"}

    @staticmethod
    def delete_business(db: Session, business_id: int) -> dict:
        b = db.query(Business).filter(Business.id == business_id).first()
        if not b: return {"error": "Business not found"}
        
        db.query(User).filter(User.business_id == business_id).update({User.business_id: None, User.is_active: False}, synchronize_session=False)
        
        try:
            from app.models.order import OrderItem
            orders = db.query(Order).filter(Order.business_id == business_id).all()
            for o in orders:
                db.query(OrderItem).filter(OrderItem.order_id == o.id).delete()
                invs = db.query(Invoice).filter(Invoice.order_id == o.id).all()
                for i in invs:
                    db.query(Payment).filter(Payment.invoice_id == i.id).delete()
                    db.delete(i)
                db.delete(o)
                
            prods = db.query(Product).filter(Product.business_id == business_id).all()
            for p in prods:
                db.query(Inventory).filter(Inventory.product_id == p.id).delete()
                db.delete(p)
                
            db.query(Customer).filter(Customer.business_id == business_id).delete()
            db.delete(b)
            db.commit()
            return {"deleted": True}
        except Exception as e:
            db.rollback()
            return {"error": str(e)}

