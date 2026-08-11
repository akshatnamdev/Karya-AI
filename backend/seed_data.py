"""
Karya AI - Demo Data Seeder

Creates realistic sample data for local development and product demos.

Run:
    python seed_data.py
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from app.db.database import Base, SessionLocal, engine
from app.db.base import *  # noqa: F401,F403 - loads all SQLAlchemy models

from app.models.user import User
from app.models.business import Business
from app.models.customer import Customer
from app.models.product import Product
from app.models.inventory import Inventory, StockMovement
from app.models.order import Order, OrderItem
from app.models.invoice import Invoice
from app.models.payment import Payment


def seed_database():
    db = SessionLocal()

    try:
        # Do not duplicate demo data
        existing_business = (
            db.query(Business)
            .filter(Business.name == "Namdev Pharma & Distributors")
            .first()
        )

        if existing_business:
            print("⚠️ Demo data already exists. Nothing was added.")
            print(f"Business ID: {existing_business.id}")
            return

        print("🌱 Creating Karya AI demo data...")

            # -------------------------------------------------------
        # 1. Business + Owner
        # -------------------------------------------------------

        business = Business(
            name="Namdev Pharma & Distributors",
            business_type="pharmacy_wholesaler",
            gst_number="23ABCDE1234F1Z5",
            pan_number="ABCDE1234F",
            email="contact@namdevpharma.demo",
            phone="9876543210",
            address="12, Main Market, Vijay Nagar",
            city="Indore",
            state="Madhya Pradesh",
            pincode="452010",
            currency="INR",
            timezone="Asia/Kolkata",
        )

        db.add(business)
        db.flush()

        owner = User(
            name="Akshat Namdev",
            email="akshat@karya.demo",
            phone="9876543210",
            password_hash="demo-password-not-for-production",
            role="owner",
            is_active=True,
            is_verified=True,
            business_id=business.id,
        )

        db.add(owner)
        db.flush()
        # Link owner to business
        owner.business_id = business.id
        db.flush()

        # -------------------------------------------------------
        # 2. Customers
        # -------------------------------------------------------
        raj_traders = Customer(
            name="Raj Traders",
            phone="9988776655",
            whatsapp_number="9988776655",
            email="raj@rajtraders.demo",
            address="45, Wholesale Market",
            city="Indore",
            state="Madhya Pradesh",
            pincode="452001",
            customer_type="wholesale",
            credit_limit=Decimal("150000.00"),
            outstanding_amount=Decimal("42500.00"),
            notes="Regular customer. Usually orders every 20-25 days.",
            tags="regular,wholesale,high-value",
            business_id=business.id,
            last_order_date=datetime.now() - timedelta(days=24),
        )

        sharma_medical = Customer(
            name="Sharma Medical Store",
            phone="9877001122",
            whatsapp_number="9877001122",
            city="Indore",
            state="Madhya Pradesh",
            customer_type="retail",
            credit_limit=Decimal("50000.00"),
            outstanding_amount=Decimal("18500.00"),
            notes="Prefers UPI payment. Orders mostly on weekends.",
            tags="retail,medical",
            business_id=business.id,
            last_order_date=datetime.now() - timedelta(days=12),
        )

        gupta_agencies = Customer(
            name="Gupta Agencies",
            phone="9765432109",
            whatsapp_number="9765432109",
            city="Dewas",
            state="Madhya Pradesh",
            customer_type="distributor",
            credit_limit=Decimal("200000.00"),
            outstanding_amount=Decimal("0.00"),
            notes="Reliable distributor. Usually pays on time.",
            tags="distributor,reliable",
            business_id=business.id,
            last_order_date=datetime.now() - timedelta(days=35),
        )

        db.add_all([raj_traders, sharma_medical, gupta_agencies])
        db.flush()

        # -------------------------------------------------------
        # 3. Products
        # -------------------------------------------------------
        xyz_tablet = Product(
            name="XYZ Tablet 500mg",
            sku="XYZ-500-TAB",
            description="Pain and fever relief tablets, strip of 10",
            category="Tablets",
            cost_price=Decimal("42.00"),
            selling_price=Decimal("55.00"),
            mrp=Decimal("60.00"),
            gst_rate=Decimal("12.00"),
            hsn_code="30049099",
            unit="box",
            business_id=business.id,
        )

        abc_syrup = Product(
            name="ABC Cough Syrup 100ml",
            sku="ABC-SYR-100",
            description="Cough syrup, 100 ml bottle",
            category="Syrups",
            cost_price=Decimal("65.00"),
            selling_price=Decimal("85.00"),
            mrp=Decimal("95.00"),
            gst_rate=Decimal("12.00"),
            hsn_code="30049099",
            unit="bottle",
            business_id=business.id,
        )

        paracetamol = Product(
            name="Paracetamol 650mg",
            sku="PCM-650-STRIP",
            description="Paracetamol tablets, strip of 15",
            category="Tablets",
            cost_price=Decimal("18.00"),
            selling_price=Decimal("25.00"),
            mrp=Decimal("30.00"),
            gst_rate=Decimal("5.00"),
            hsn_code="30049099",
            unit="strip",
            business_id=business.id,
        )

        vitamin_c = Product(
            name="Vitamin C 500mg",
            sku="VITC-500-BOX",
            description="Vitamin C tablets, box of 30",
            category="Supplements",
            cost_price=Decimal("80.00"),
            selling_price=Decimal("110.00"),
            mrp=Decimal("125.00"),
            gst_rate=Decimal("12.00"),
            hsn_code="21069099",
            unit="box",
            business_id=business.id,
        )

        db.add_all([xyz_tablet, abc_syrup, paracetamol, vitamin_c])
        db.flush()

        # -------------------------------------------------------
        # 4. Inventory
        # XYZ and ABC are deliberately low for dashboard alerts.
        # -------------------------------------------------------
        inventories = [
            Inventory(
                product_id=xyz_tablet.id,
                current_stock=72,
                reserved_stock=0,
                reorder_level=100,
                reorder_quantity=300,
                warehouse_location="Rack A-01",
            ),
            Inventory(
                product_id=abc_syrup.id,
                current_stock=18,
                reserved_stock=0,
                reorder_level=40,
                reorder_quantity=120,
                warehouse_location="Rack B-03",
            ),
            Inventory(
                product_id=paracetamol.id,
                current_stock=450,
                reserved_stock=0,
                reorder_level=100,
                reorder_quantity=500,
                warehouse_location="Rack A-05",
            ),
            Inventory(
                product_id=vitamin_c.id,
                current_stock=32,
                reserved_stock=0,
                reorder_level=50,
                reorder_quantity=150,
                warehouse_location="Rack C-02",
            ),
        ]
        db.add_all(inventories)
        db.flush()

        stock_movements = [
            StockMovement(
                product_id=xyz_tablet.id,
                movement_type="in",
                quantity=200,
                reason="Initial demo stock",
                stock_before=0,
                stock_after=200,
            ),
            StockMovement(
                product_id=xyz_tablet.id,
                movement_type="out",
                quantity=128,
                reason="Historical sales",
                stock_before=200,
                stock_after=72,
            ),
            StockMovement(
                product_id=abc_syrup.id,
                movement_type="in",
                quantity=100,
                reason="Initial demo stock",
                stock_before=0,
                stock_after=100,
            ),
            StockMovement(
                product_id=abc_syrup.id,
                movement_type="out",
                quantity=82,
                reason="Historical sales",
                stock_before=100,
                stock_after=18,
            ),
        ]
        db.add_all(stock_movements)

        # -------------------------------------------------------
        # 5. Orders
        # -------------------------------------------------------
        order_1 = Order(
            order_number="ORD-2026-0001",
            status="delivered",
            source="whatsapp",
            subtotal=Decimal("15000.00"),
            tax_amount=Decimal("1800.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("16800.00"),
            order_date=datetime.now() - timedelta(days=60),
            delivery_date=date.today() - timedelta(days=57),
            delivered_at=datetime.now() - timedelta(days=57),
            original_message="Bhai XYZ tablet ke 200 box bhej dena.",
            business_id=business.id,
            customer_id=raj_traders.id,
        )

        order_2 = Order(
            order_number="ORD-2026-0002",
            status="delivered",
            source="whatsapp",
            subtotal=Decimal("11000.00"),
            tax_amount=Decimal("1320.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("12320.00"),
            order_date=datetime.now() - timedelta(days=24),
            delivery_date=date.today() - timedelta(days=21),
            delivered_at=datetime.now() - timedelta(days=21),
            original_message="Raj bhai 200 XYZ aur 20 ABC syrup bhej dena.",
            business_id=business.id,
            customer_id=raj_traders.id,
        )

        order_3 = Order(
            order_number="ORD-2026-0003",
            status="delivered",
            source="manual",
            subtotal=Decimal("7000.00"),
            tax_amount=Decimal("840.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("7840.00"),
            order_date=datetime.now() - timedelta(days=12),
            delivery_date=date.today() - timedelta(days=10),
            delivered_at=datetime.now() - timedelta(days=10),
            business_id=business.id,
            customer_id=sharma_medical.id,
        )

        db.add_all([order_1, order_2, order_3])
        db.flush()

        order_items = [
            OrderItem(
                order_id=order_1.id,
                product_id=xyz_tablet.id,
                quantity=200,
                unit_price=Decimal("75.00"),
                total=Decimal("15000.00"),
            ),
            OrderItem(
                order_id=order_2.id,
                product_id=xyz_tablet.id,
                quantity=200,
                unit_price=Decimal("55.00"),
                total=Decimal("11000.00"),
            ),
            OrderItem(
                order_id=order_3.id,
                product_id=abc_syrup.id,
                quantity=80,
                unit_price=Decimal("85.00"),
                total=Decimal("6800.00"),
            ),
            OrderItem(
                order_id=order_3.id,
                product_id=paracetamol.id,
                quantity=8,
                unit_price=Decimal("25.00"),
                total=Decimal("200.00"),
            ),
        ]
        db.add_all(order_items)
        db.flush()

        # -------------------------------------------------------
        # 6. Invoices + Payments
        # -------------------------------------------------------
        invoice_1 = Invoice(
            invoice_number="INV-2026-0001",
            status="paid",
            subtotal=Decimal("15000.00"),
            tax_amount=Decimal("1800.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("16800.00"),
            paid_amount=Decimal("16800.00"),
            balance_amount=Decimal("0.00"),
            invoice_date=date.today() - timedelta(days=60),
            due_date=date.today() - timedelta(days=45),
            paid_date=date.today() - timedelta(days=40),
            order_id=order_1.id,
        )

        invoice_2 = Invoice(
            invoice_number="INV-2026-0002",
            status="overdue",
            subtotal=Decimal("11000.00"),
            tax_amount=Decimal("1320.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("12320.00"),
            paid_amount=Decimal("0.00"),
            balance_amount=Decimal("12320.00"),
            invoice_date=date.today() - timedelta(days=24),
            due_date=date.today() - timedelta(days=8),
            order_id=order_2.id,
        )

        invoice_3 = Invoice(
            invoice_number="INV-2026-0003",
            status="partially_paid",
            subtotal=Decimal("7000.00"),
            tax_amount=Decimal("840.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("7840.00"),
            paid_amount=Decimal("2000.00"),
            balance_amount=Decimal("5840.00"),
            invoice_date=date.today() - timedelta(days=12),
            due_date=date.today() + timedelta(days=3),
            order_id=order_3.id,
        )

        db.add_all([invoice_1, invoice_2, invoice_3])
        db.flush()

        payment_1 = Payment(
            payment_number="PAY-2026-0001",
            amount=Decimal("16800.00"),
            payment_method="upi",
            transaction_id="UPI-DEMO-001",
            payment_date=date.today() - timedelta(days=40),
            notes="Payment received from Raj Traders",
            invoice_id=invoice_1.id,
        )

        payment_2 = Payment(
            payment_number="PAY-2026-0002",
            amount=Decimal("2000.00"),
            payment_method="cash",
            reference_number="CASH-DEMO-001",
            payment_date=date.today() - timedelta(days=5),
            notes="Partial payment from Sharma Medical Store",
            invoice_id=invoice_3.id,
        )

        db.add_all([payment_1, payment_2])

        db.commit()

        print("\n" + "=" * 60)
        print("✅ KARYA AI DEMO DATA CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Business: {business.name}")
        print("Owner: Akshat Namdev")
        print("Customers: 3")
        print("Products: 4")
        print("Orders: 3")
        print("Invoices: 3")
        print("Payments: 2")
        print("Low-stock products: XYZ Tablet, ABC Syrup, Vitamin C")
        print("Overdue invoice: INV-2026-0002")
        print("=" * 60)

    except Exception as error:
        db.rollback()
        print("\n❌ Failed to create demo data:")
        print(error)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()