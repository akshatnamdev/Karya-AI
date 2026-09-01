"""
Karya AI - AI Assistant Service
Handles all interactions with the Users
"""

import json
import re
import time
import os
from typing import Optional, List, Any

from sqlalchemy.orm import Session


from app.services.ai_service import ai_service
from app.services.ai_cache_service import AICache
from app.services.demo_mode_service import DemoModeService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.models.product import Product
from app.models.customer import Customer
from app.rag.business_context import BusinessContextBuilder
from app.schemas.ai import AIQuery, AIResponse
from app.services.invoice_service import InvoiceService
from app.models.order import Order
from app.models.invoice import Invoice

class AIAssistantService:
    """AI Business Assistant with caching, demo mode, actions, and fallback"""

    @staticmethod
    def ask_question(db: Session, query: AIQuery, scope: dict, use_demo: bool = False) -> AIResponse:
        """Main method with protection, RBAC, and optional create/update actions"""
        start_time = time.time()

        # ==================== LAYER 1: DEMO MODE ====================
        if use_demo or os.getenv("DEMO_MODE", "false").lower() == "true":
            demo_response = DemoModeService.get_demo_response(query.question)
            if demo_response:
                return AIResponse(**demo_response)

        # ==================== LAYER 1.5: ACTIONS ====================
        # Mutations run BEFORE cache and must NOT be cached.
        try:
            action_response = AIAssistantService._try_handle_action(db, query, scope, start_time)
            if action_response is not None:
                return action_response
        except Exception as e:
            print(f"[AI ACTION ERROR] {e}")
            return AIAssistantService._action_answer(
                query,
                start_time,
                f"I couldn't complete that action: {getattr(e, 'detail', None) or str(e)}",
            )

        # ==================== LAYER 2: CACHE CHECK ====================
        cache_scope_key = f"{scope.get('scope')}_{scope.get('business_id')}_{scope.get('customer_id')}"
        try:
            cached = AICache.get(query.question, query.language, cache_scope_key)
            if cached:
                return AIResponse(**cached)
        except Exception as e:
            print(f"[AI CACHE GET ERROR] {e}")

        # ==================== LAYER 3: FRESH API CALL ====================
        try:
            business_context = BusinessContextBuilder.build_full_context(db, scope)
        except Exception as e:
            print(f"Error building context: {e}")
            business_context = "Data temporarily unavailable."

        prompt = AIAssistantService._build_prompt(
            business_context=business_context,
            user_question=query.question,
            language=query.language,
            role=scope.get("scope") or "business",
        )

        # ==================== LAYER 4: MODEL FALLBACK ====================
        ai_result = ai_service.generate(prompt=prompt, model_type="fast", max_retries=2)

        if ai_result.get("status") == "error":
            ai_result = ai_service.generate(prompt=prompt, model_type="smart", max_retries=2)

        response_time_ms = int((time.time() - start_time) * 1000)

        if ai_result.get("status") == "error":
            error_msg = ai_result.get("message", "AI is temporarily unavailable")
            demo_response = DemoModeService.get_demo_response(query.question)
            if demo_response:
                return AIResponse(**demo_response)

            return AIResponse(
                question=query.question,
                answer=AIAssistantService._get_friendly_error_message(error_msg),
                model_used=ai_result.get("model", "unknown"),
                response_time_ms=response_time_ms,
                sources=[],
                detected_language="english",
            )

        detected_language = AIAssistantService._detect_language(query.question)

        response_data = {
            "question": query.question,
            "answer": (ai_result.get("response") or "").strip(),
            "model_used": ai_result.get("model", "unknown"),
            "response_time_ms": response_time_ms,
            "sources": AIAssistantService._get_sources(),
            "detected_language": detected_language,
        }

        try:
            AICache.set(query.question, query.language, cache_scope_key, response_data)
        except Exception as e:
            print(f"[AI CACHE SET ERROR] {e}")

        return AIResponse(**response_data)

    @staticmethod
    def get_business_summary(db: Session, scope: dict) -> AIResponse:
        """Get AI business summary"""
        query = AIQuery(
            question=(
                "Give me a brief business summary. Include total customers, revenue, "
                "outstanding payments, and any critical alerts. Keep it under 150 words."
            ),
            language="hinglish",
        )
        return AIAssistantService.ask_question(db, query, scope)

    # ==================== ACTION HANDLING ====================

    @staticmethod
    def _try_handle_action(db: Session, query: AIQuery, scope: dict, start_time: float):
        intent = AIAssistantService._detect_action_intent(query.question, scope.get("scope"))
        if not intent:
            return None

        if intent == "add_product":
            return AIAssistantService._handle_add_product(db, query, scope, start_time)

        if intent == "place_order":
            return AIAssistantService._handle_place_order(db, query, scope, start_time)

        if intent == "update_stock":
            return AIAssistantService._handle_update_stock(db, query, scope, start_time)

        if intent == "confirm_order":
            return AIAssistantService._handle_order_status(db, query, scope, start_time, "confirmed")

        if intent == "deliver_order":
            return AIAssistantService._handle_order_status(db, query, scope, start_time, "delivered")

        if intent == "cancel_order":
            return AIAssistantService._handle_order_status(db, query, scope, start_time, "cancelled")

        if intent == "record_payment":
            return AIAssistantService._handle_record_payment(db, query, scope, start_time)

        return None

    @staticmethod
    def _extract_order_ref(text: str):
        """Find ORD-xxxxx, bare timestamp, or #id from text."""
        if not text:
            return None
        t = text.strip()

        m = re.search(r"ord[-\s]?(\d{3,})", t, re.IGNORECASE)
        if m:
            return f"ORD-{m.group(1)}"

        m = re.search(r"\border\s+#?(\d{1,6})\b", t, re.IGNORECASE)
        if m:
            return m.group(1)

        m = re.search(r"\b(\d{6,})\b", t)  # long timestamp
        if m:
            return m.group(1)

        m = re.search(r"#(\d{1,6})\b", t)
        if m:
            return m.group(1)

        return None

    @staticmethod
    def _extract_invoice_ref(text: str):
        if not text:
            return None
        t = text.strip()
        m = re.search(r"inv[-\s]?([\w-]+)", t, re.IGNORECASE)
        if m:
            return f"INV-{m.group(1)}" if not m.group(1).upper().startswith("INV") else m.group(1)
        m = re.search(r"invoice\s+#?(\d{1,6})", t, re.IGNORECASE)
        if m:
            return m.group(1)
        return None

    @staticmethod
    def _extract_amount(text: str):
        if not text:
            return None
        # ₹300, 300, 300.50, "rs 300"
        m = re.search(r"(?:₹|rs\.?\s*)?(\d+(?:\.\d{1,2})?)", text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                return None
        return None

    @staticmethod
    def _resolve_order_pk(db, business_id, customer_id, role, ref):
        """Return DB order id from ref (ORD-.. / timestamp / id)."""
        if not ref:
            return None
        ref = str(ref).strip()

        q = db.query(Order)
        if role == "business" and business_id:
            q = q.filter(Order.business_id == business_id)
        elif role == "customer" and customer_id:
            q = q.filter(Order.customer_id == customer_id)

        # by order_number
        o = q.filter(Order.order_number == ref).first()
        if o:
            return o.id
        if not ref.upper().startswith("ORD-"):
            o2 = q.filter(Order.order_number == f"ORD-{ref}").first()
            if o2:
                return o2.id
        if ref.isdigit():
            o3 = q.filter(Order.id == int(ref)).first()
            if o3:
                return o3.id
        return None

    @staticmethod
    def _resolve_invoice_pk(db, business_id, ref):
        if not ref:
            return None
        ref = str(ref).strip()
        q = (
            db.query(Invoice)
            .join(Order, Invoice.order_id == Order.id)
            .filter(Order.business_id == business_id)
        )
        inv = q.filter(Invoice.invoice_number == ref).first()
        if inv:
            return inv.id
        if not ref.upper().startswith("INV-"):
            inv2 = q.filter(Invoice.invoice_number == f"INV-{ref}").first()
            if inv2:
                return inv2.id
        if ref.isdigit():
            inv3 = q.filter(Invoice.id == int(ref)).first()
            if inv3:
                return inv3.id
        return None

    @staticmethod
    def _handle_order_status(db, query, scope, start_time, new_status):
        role = scope.get("scope")
        business_id = scope.get("business_id")
        customer_id = scope.get("customer_id")

        ref = AIAssistantService._extract_order_ref(query.question)
        if not ref:
            return AIAssistantService._action_answer(
                query,
                start_time,
                f"Which order should I {new_status.replace('ed','')}? "
                f"Please give the order number.\nExample: {new_status} order ORD-1787868587",
            )

        order_pk = AIAssistantService._resolve_order_pk(
            db, business_id, customer_id, role, ref
        )
        if not order_pk:
            return AIAssistantService._action_answer(
                query, start_time, f"I couldn't find order '{ref}' in your account."
            )

        try:
            result = OrderService.update_status(
                db=db,
                order_id=order_pk,
                new_status=new_status,
                scope=scope,
                note="via AI assistant",
            )
            AIAssistantService._invalidate_cache(scope)
        except Exception as e:
            detail = getattr(e, "detail", None) or str(e)
            return AIAssistantService._action_answer(
                query, start_time, f"Could not update order: {detail}"
            )

        order = result.get("order") or {}
        lines = [
            f"✅ Order {new_status}.",
            f"- **Order:** {order.get('order_number')}",
            f"- **Status:** {order.get('status')}",
            f"- **Total:** ₹{order.get('total')}",
        ]
        if order.get("invoice_number"):
            lines.append(f"- **Invoice:** {order.get('invoice_number')}")
            if order.get("invoice_balance") is not None:
                lines.append(f"- **Invoice balance:** ₹{order.get('invoice_balance')}")

        return AIAssistantService._action_answer(
            query,
            start_time,
            "\n".join(lines),
            sources=["orders table", "invoices table"],
        )

    @staticmethod
    def _handle_record_payment(db, query, scope, start_time):
        if scope.get("scope") != "business":
            return AIAssistantService._action_answer(
                query, start_time, "Only business can record payments."
            )

        business_id = scope.get("business_id")
        if not business_id:
            return AIAssistantService._action_answer(
                query, start_time, "Business context missing. Please log in again."
            )

        inv_ref = AIAssistantService._extract_invoice_ref(query.question)
        amount = AIAssistantService._extract_amount(query.question)

        missing = []
        if not inv_ref:
            missing.append("invoice number")
        if not amount:
            missing.append("amount")

        if missing:
            return AIAssistantService._action_answer(
                query,
                start_time,
                f"Need {', '.join(missing)}.\n"
                "Example: record payment of 300 on INV-1788246151",
            )

        invoice_pk = AIAssistantService._resolve_invoice_pk(db, business_id, inv_ref)
        if not invoice_pk:
            return AIAssistantService._action_answer(
                query, start_time, f"I couldn't find invoice '{inv_ref}'."
            )

        try:
            result = InvoiceService.record_payment(
                db=db,
                invoice_id=invoice_pk,
                amount=amount,
                scope=scope,
                payment_method="ai",
                note="via AI assistant",
            )
            AIAssistantService._invalidate_cache(scope)
        except Exception as e:
            detail = getattr(e, "detail", None) or str(e)
            return AIAssistantService._action_answer(
                query, start_time, f"Could not record payment: {detail}"
            )

        inv = result.get("invoice") or {}
        answer = (
            f"✅ Payment recorded.\n"
            f"- **Invoice:** {inv.get('invoice_number')}\n"
            f"- **Paid now:** ₹{amount}\n"
            f"- **Total paid:** ₹{inv.get('paid')}\n"
            f"- **Balance:** ₹{inv.get('balance')}\n"
            f"- **Status:** {inv.get('status')}"
        )
        return AIAssistantService._action_answer(
            query,
            start_time,
            answer,
            sources=["invoices table", "customers table"],
        )

    @staticmethod
    def _detect_action_intent(question: str, role: str):
        q = (question or "").lower().strip()
        role = role or ""

        add_product_keys = [
            "add product",
            "create product",
            "new product",
            "product add",
            "add a product",
            "product banao",
            "product add karo",
            "naya product",
        ]

        place_order_keys = [
            "place order",
            "create order",
            "new order",
            "order karo",
            "order place",
            "book order",
            "i want to order",
            "want to order",
            "order please",
            "place an order",
            "mujhe order",
            "order chahiye",
            "order karna",
            "i want to place",
            "order of",
            "i need",
            "i want",
            "mujhe",
            "chahiye",
            "buy",
            "purchase",
            "get me",
        ]

        stock_keys = [
            "update stock",
            "restock",
            "add stock",
            "set stock",
            "stock add",
            "stock update",
            "increase stock",
            "reduce stock",
            "remove stock",
            "inventory update",
            "stock badhao",
            "stock kam",
            "stock set",
        ]

        history_keys = [
            "show my order",
            "show all my order",
            "my orders",
            "order history",
            "list my order",
            "pending order",
            "where is my order",
            "order status",
            "show all products",
            "show products",
            "product catalog",
            "recent orders",
            "show me my recent",
        ]

        # Never treat pure history/catalog questions as mutations
        if any(h in q for h in history_keys):
            return None

        if role == "business" and any(k in q for k in add_product_keys):
            return "add_product"

        if role == "business" and any(k in q for k in stock_keys):
            return "update_stock"
        
        confirm_keys = ["confirm order", "confirm the order", "approve order", "confirm ord"]
        deliver_keys = ["mark delivered", "deliver order", "order delivered", "mark order delivered", "delivered order"]
        cancel_keys = ["cancel order", "cancel the order", "cancel ord"]
        payment_keys = ["record payment", "add payment", "mark payment", "payment received", "received payment", "pay invoice", "record a payment"]

        # Business: confirm / deliver / payment
        if role == "business":
            if any(k in q for k in confirm_keys):
                return "confirm_order"
            if any(k in q for k in deliver_keys):
                return "deliver_order"
            if any(k in q for k in payment_keys):
                return "record_payment"

        # Both roles: cancel
        if role in ("business", "customer") and any(k in q for k in cancel_keys):
            return "cancel_order"
        
        if role in ("business", "customer") and any(k in q for k in place_order_keys):
            return "place_order"

        return None

    @staticmethod
    def _handle_add_product(db: Session, query: AIQuery, scope: dict, start_time: float) -> AIResponse:
        if scope.get("scope") != "business":
            return AIAssistantService._action_answer(
                query, start_time, "Only business users can add products."
            )

        business_id = scope.get("business_id")
        if not business_id:
            return AIAssistantService._action_answer(
                query, start_time, "Business context missing. Please log in again."
            )

        extracted = AIAssistantService._extract_json_with_ai(
            instruction=AIAssistantService._add_product_extract_prompt(query.question)
        )

        if not extracted:
            return AIAssistantService._action_answer(
                query,
                start_time,
                "I can add a product. Please share: **name**, **selling price**, and optional stock/SKU/category.\n"
                "Example: Add product Notebook, price 50, stock 100, sku NB-01, category Stationery",
            )

        name = (extracted.get("name") or "").strip()
        selling_price = extracted.get("selling_price")

        missing = []
        if not name:
            missing.append("name")
        if selling_price is None or selling_price == "":
            missing.append("selling_price")

        if missing:
            return AIAssistantService._action_answer(
                query,
                start_time,
                f"To add the product I still need: **{', '.join(missing)}**.\n"
                "Example: Add product Notebook, selling price 50, stock 100",
            )

        try:
            selling_price = float(selling_price)
        except (TypeError, ValueError):
            return AIAssistantService._action_answer(
                query, start_time, "Selling price must be a valid number."
            )

        product_data = {
            "name": name,
            "selling_price": selling_price,
            "sku": extracted.get("sku"),
            "category": extracted.get("category"),
            "description": extracted.get("description"),
            "cost_price": extracted.get("cost_price") or 0,
            "mrp": extracted.get("mrp"),
            "unit": extracted.get("unit") or "pcs",
            "initial_stock": int(extracted.get("initial_stock") or 0),
            "reorder_level": int(extracted.get("reorder_level") or 10),
            "reorder_quantity": int(extracted.get("reorder_quantity") or 50),
        }

        try:
            created = ProductService.create_product(
                db=db,
                business_id=business_id,
                product_data=product_data,
            )
            AIAssistantService._invalidate_cache(scope)
        except Exception as e:
            detail = getattr(e, "detail", None) or str(e)
            return AIAssistantService._action_answer(
                query, start_time, f"Could not add product: {detail}"
            )

        answer = (
            f"✅ Product added successfully.\n"
            f"- **Name:** {created.get('name')}\n"
            f"- **SKU:** {created.get('sku') or '—'}\n"
            f"- **Price:** ₹{created.get('selling_price')}\n"
            f"- **Stock:** {created.get('stock', 0)}\n"
            f"- **ID:** {created.get('id')}"
        )
        return AIAssistantService._action_answer(
            query,
            start_time,
            answer,
            sources=["products table", "inventory table"],
        )

    @staticmethod
    def _handle_place_order(db: Session, query: AIQuery, scope: dict, start_time: float) -> AIResponse:
        role = scope.get("scope")
        business_id = scope.get("business_id")

        if role not in ("business", "customer"):
            return AIAssistantService._action_answer(
                query, start_time, "You are not allowed to place orders."
            )
        if not business_id:
            return AIAssistantService._action_answer(
                query, start_time, "Business context missing. Please log in again."
            )

        products = (
            db.query(Product)
            .filter(Product.business_id == business_id, Product.is_active == True)
            .all()
        )
        catalog_lines = [
            f"id={p.id} | name={p.name} | price={p.selling_price}" for p in products[:80]
        ]
        catalog_text = "\n".join(catalog_lines) if catalog_lines else "No products available."

        customers_text = "N/A"
        if role == "business":
            try:
                customers = (
                    db.query(Customer)
                    .filter(Customer.business_id == business_id)
                    .limit(50)
                    .all()
                )
            except Exception:
                customers = db.query(Customer).limit(50).all()
            customers_text = "\n".join(
                [f"id={c.id} | name={getattr(c, 'name', '')}" for c in customers]
            ) or "No customers found."

        extracted = AIAssistantService._extract_json_with_ai(
            instruction=AIAssistantService._place_order_extract_prompt(
                question=query.question,
                role=role,
                catalog_text=catalog_text,
                customers_text=customers_text,
            )
        )

        if not extracted:
            hint = (
                "I can place an order. Please share product name(s) and quantity.\n"
                "Example: Place order for 2 Notebook and 1 Pen"
            )
            if role == "business":
                hint = (
                    "I can place an order. Please share **customer**, **product(s)** and **quantity**.\n"
                    "Example: Place order for customer Ramesh: 2 Notebook, 1 Pen"
                )
            return AIAssistantService._action_answer(query, start_time, hint)

        # Resolve customer
        if role == "customer":
            customer_id = scope.get("customer_id")
            if not customer_id:
                return AIAssistantService._action_answer(
                    query, start_time, "Customer context missing. Please log in again."
                )
        else:
            customer_id = extracted.get("customer_id")
            customer_name = (extracted.get("customer_name") or "").strip()
            if not customer_id and customer_name:
                customer_id = AIAssistantService._resolve_customer_id(
                    db, business_id, customer_name
                )
            if not customer_id:
                return AIAssistantService._action_answer(
                    query,
                    start_time,
                    "Please specify the **customer** for this order.\n"
                    "Example: Place order for customer Ramesh: 2 Notebook",
                )
            try:
                customer_id = int(customer_id)
            except (TypeError, ValueError):
                return AIAssistantService._action_answer(
                    query, start_time, "Invalid customer. Please use a valid customer name or id."
                )

        raw_items = extracted.get("items") or []
        if not raw_items:
            return AIAssistantService._action_answer(
                query,
                start_time,
                "Please specify at least one **product** and **quantity**.\n"
                "Example: Place order for 2 Notebook",
            )

        items_data = []
        unresolved = []
        for item in raw_items:
            qty = item.get("quantity", 1)
            try:
                qty = int(qty)
            except (TypeError, ValueError):
                qty = 0
            if qty <= 0:
                unresolved.append(str(item))
                continue

            product_id = item.get("product_id")
            product_name = (item.get("product_name") or "").strip()

            if not product_id and product_name:
                product_id = AIAssistantService._resolve_product_id(db, business_id, product_name)

            if not product_id:
                unresolved.append(product_name or str(item))
                continue

            try:
                product_id = int(product_id)
            except (TypeError, ValueError):
                unresolved.append(product_name or str(item))
                continue

            items_data.append({"product_id": product_id, "quantity": qty})

        if unresolved:
            return AIAssistantService._action_answer(
                query,
                start_time,
                "I could not match these products: "
                + ", ".join([str(x) for x in unresolved])
                + ".\nPlease use exact catalog names or product ids.",
            )

        if not items_data:
            return AIAssistantService._action_answer(
                query,
                start_time,
                "No valid order items found. Please try again with product and quantity.",
            )

        notes = extracted.get("notes") or None

        try:
            result = OrderService.create_unified_order(
                db=db,
                business_id=business_id,
                customer_id=customer_id,
                items_data=items_data,
                source="ai",
                notes=notes,
            )
            AIAssistantService._invalidate_cache(scope)
        except Exception as e:
            detail = getattr(e, "detail", None) or str(e)
            return AIAssistantService._action_answer(
                query, start_time, f"Could not place order: {detail}"
            )

        order = result.get("order") or {}
        items = result.get("items") or []
        item_lines = "\n".join(
            [
                f"  - {it.get('product_name')} x {it.get('quantity')} = ₹{it.get('total')}"
                for it in items
            ]
        )

        answer = (
            f"✅ Order placed successfully.\n"
            f"- **Order:** {order.get('order_number')}\n"
            f"- **Status:** {order.get('status')}\n"
            f"- **Total:** ₹{order.get('total')}\n"
            f"- **Items:**\n{item_lines}"
        )
        return AIAssistantService._action_answer(
            query,
            start_time,
            answer,
            sources=["orders table", "products table", "inventory table"],
        )

    @staticmethod
    def _handle_update_stock(db: Session, query: AIQuery, scope: dict, start_time: float) -> AIResponse:
        if scope.get("scope") != "business":
            return AIAssistantService._action_answer(
                query, start_time, "Only business users can update stock."
            )

        business_id = scope.get("business_id")
        if not business_id:
            return AIAssistantService._action_answer(
                query, start_time, "Business context missing. Please log in again."
            )

        # If update_stock is not implemented yet, fail softly
        if not hasattr(ProductService, "update_stock"):
            return AIAssistantService._action_answer(
                query,
                start_time,
                "Stock update service is not available yet. Please use Inventory page or add ProductService.update_stock.",
            )

        products = db.query(Product).filter(Product.business_id == business_id).all()
        catalog_text = "\n".join([f"id={p.id} | name={p.name}" for p in products[:80]]) or "No products."

        extracted = AIAssistantService._extract_json_with_ai(
            instruction=(
                "Extract stock update details from the user message.\n"
                "Return ONLY valid JSON:\n"
                "{\n"
                '  "product_id": number or null,\n'
                '  "product_name": string or null,\n'
                '  "mode": "set" or "add" or "remove",\n'
                '  "quantity": number or null,\n'
                '  "reason": string or null\n'
                "}\n"
                'Rules:\n'
                '- "restock", "add stock", "increase" => mode "add"\n'
                '- "set stock to X" => mode "set"\n'
                '- "remove", "reduce", "deduct" => mode "remove"\n'
                f"CATALOG:\n{catalog_text}\n"
                f"USER MESSAGE:\n{query.question}\n"
            )
        )

        if not extracted:
            return AIAssistantService._action_answer(
                query,
                start_time,
                "I can update stock. Try:\n"
                "- Restock Paracetamol by 50\n"
                "- Set stock of Notebook to 100\n"
                "- Remove 10 from Pencil stock",
            )

        mode = (extracted.get("mode") or "add").lower()
        qty = extracted.get("quantity")
        product_id = extracted.get("product_id")
        product_name = (extracted.get("product_name") or "").strip()

        if not product_id and product_name:
            product_id = AIAssistantService._resolve_product_id(db, business_id, product_name)

        missing = []
        if not product_id:
            missing.append("product")
        if qty is None or qty == "":
            missing.append("quantity")
        if mode not in ("set", "add", "remove"):
            missing.append("mode (set/add/remove)")

        if missing:
            return AIAssistantService._action_answer(
                query,
                start_time,
                f"Need more details: **{', '.join(missing)}**.\n"
                "Example: Restock Paracetamol by 50",
            )

        try:
            updated = ProductService.update_stock(
                db=db,
                business_id=business_id,
                product_id=int(product_id),
                mode=mode,
                quantity=int(qty),
                reason=extracted.get("reason") or "ai_stock_update",
            )
            AIAssistantService._invalidate_cache(scope)
        except Exception as e:
            detail = getattr(e, "detail", None) or str(e)
            return AIAssistantService._action_answer(
                query, start_time, f"Could not update stock: {detail}"
            )

        answer = (
            f"✅ Stock updated.\n"
            f"- **Product:** {updated.get('name')}\n"
            f"- **Mode:** {mode}\n"
            f"- **Qty applied:** {qty}\n"
            f"- **Current stock:** {updated.get('stock')}"
        )
        return AIAssistantService._action_answer(
            query,
            start_time,
            answer,
            sources=["products table", "inventory table"],
        )

    # ==================== EXTRACTION HELPERS ====================

    @staticmethod
    def _add_product_extract_prompt(question: str) -> str:
        return f"""Extract product creation details from the user message.
Return ONLY valid JSON (no markdown, no extra text) with keys:
{{
  "name": string or null,
  "selling_price": number or null,
  "sku": string or null,
  "category": string or null,
  "description": string or null,
  "cost_price": number or null,
  "mrp": number or null,
  "unit": string or null,
  "initial_stock": number or null,
  "reorder_level": number or null,
  "reorder_quantity": number or null
}}

USER MESSAGE:
{question}
"""

    @staticmethod
    def _place_order_extract_prompt(question: str, role: str, catalog_text: str, customers_text: str) -> str:
        customer_rules = (
            'Include "customer_id" and/or "customer_name".'
            if role == "business"
            else 'Set "customer_id" to null (system will use logged-in customer).'
        )
        return f"""Extract order details from the user message.
Match products to the catalog when possible.
{customer_rules}
Return ONLY valid JSON (no markdown, no extra text):
{{
  "customer_id": number or null,
  "customer_name": string or null,
  "notes": string or null,
  "items": [
    {{"product_id": number or null, "product_name": string or null, "quantity": number}}
  ]
}}

CATALOG:
{catalog_text}

CUSTOMERS:
{customers_text or "N/A"}

USER MESSAGE:
{question}
"""

    @staticmethod
    def _extract_json_with_ai(instruction: str) -> Optional[dict]:
        result = ai_service.generate(prompt=instruction, model_type="fast", max_retries=2)
        if result.get("status") == "error":
            result = ai_service.generate(prompt=instruction, model_type="smart", max_retries=1)
        if result.get("status") == "error":
            return None

        text = (result.get("response") or "").strip()
        return AIAssistantService._parse_json_loose(text)

    @staticmethod
    def _parse_json_loose(text: str) -> Optional[dict]:
        if not text:
            return None
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        try:
            data = json.loads(text)
            return data if isinstance(data, dict) else None
        except Exception:
            pass
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    @staticmethod
    def _resolve_product_id(db: Session, business_id: int, name: str):
        if not name:
            return None
        name = name.strip()
        p = (
            db.query(Product)
            .filter(
                Product.business_id == business_id,
                Product.is_active == True,
                Product.name.ilike(name),
            )
            .first()
        )
        if p:
            return p.id
        p = (
            db.query(Product)
            .filter(
                Product.business_id == business_id,
                Product.is_active == True,
                Product.name.ilike(f"%{name}%"),
            )
            .first()
        )
        return p.id if p else None

    @staticmethod
    def _resolve_customer_id(db: Session, business_id: int, name: str):
        if not name:
            return None
        name = name.strip()
        try:
            c = (
                db.query(Customer)
                .filter(Customer.business_id == business_id, Customer.name.ilike(name))
                .first()
            )
            if c:
                return c.id
            c = (
                db.query(Customer)
                .filter(Customer.business_id == business_id, Customer.name.ilike(f"%{name}%"))
                .first()
            )
            return c.id if c else None
        except Exception:
            c = db.query(Customer).filter(Customer.name.ilike(name)).first()
            if c:
                return c.id
            c = db.query(Customer).filter(Customer.name.ilike(f"%{name}%")).first()
            return c.id if c else None

    @staticmethod
    def _invalidate_cache(scope: dict):
        """Best-effort cache clear so next questions fetch fresh DB data."""
        try:
            cache_scope_key = f"{scope.get('scope')}_{scope.get('business_id')}_{scope.get('customer_id')}"
            if hasattr(AICache, "clear_scope"):
                AICache.clear_scope(cache_scope_key)
            elif hasattr(AICache, "delete"):
                AICache.delete(cache_scope_key)
            elif hasattr(AICache, "clear"):
                AICache.clear()
            elif hasattr(AICache, "_cache") and isinstance(getattr(AICache, "_cache"), dict):
                getattr(AICache, "_cache").clear()
        except Exception as e:
            print(f"Cache invalidation warning: {e}")

    @staticmethod
    def _action_answer(
        query: AIQuery,
        start_time: float,
        answer: str,
        sources: Optional[List[str]] = None,
    ) -> AIResponse:
        response_time_ms = int((time.time() - start_time) * 1000)
        return AIResponse(
            question=query.question,
            answer=answer,
            model_used="action+gemini",
            response_time_ms=response_time_ms,
            sources=sources or ["orders table", "products table"],
            detected_language=AIAssistantService._detect_language(query.question),
        )

    # ==================== PRIVATE HELPERS ====================

    @staticmethod
    def _build_prompt(business_context: str, user_question: str, language: str, role: str) -> str:
        language_instruction = AIAssistantService._get_language_instruction(language)

        if role == "customer":
            persona = """You are Karya, a helpful shopping and account assistant for this business. You are talking to a CUSTOMER.
Your job is to help them check their order status, pending invoices, or browse available products in the catalog.
If the customer says hello, asks for help, or asks general questions, be welcoming and let them know you can help them check their orders, pending bills, or product catalog.
They can also place orders by saying things like "place order for 2 Notebook".
When order placement is handled by the system action layer, do not invent fake order confirmations in normal Q&A.
If they ask about other customers or business internal data, politely inform them you can only share details related to their own account.
They can cancel their own pending order ("cancel order ORD-123")."""
        elif role == "business":
            persona = """You are Karya, an intelligent business assistant for the BUSINESS OWNER.
You have access to the full business performance data, financials, inventory, and customer account details. Help the owner manage their business effectively.
They can add products ("add product Notebook price 50 stock 100"), place orders ("place order for customer Ramesh: 2 Notebook"), and update stock ("restock Paracetamol by 50").
Never pretend an order/product/stock change succeeded unless the system action layer already did it.
They can also confirm/deliver/cancel orders ("confirm order ORD-123", "mark ORD-123 delivered") and record payments ("record payment of 300 on INV-456")."""
        else:
            persona = "You are Karya, a Platform Admin assistant with system-wide visibility."

        prompt = f"""{persona}

BUSINESS & ACCOUNT DATA:
{business_context}

USER QUESTION: {user_question}

INSTRUCTIONS:
1. Answer ONLY from the data above. Never invent numbers.
2. Answer ONLY based on the data above.
3. Be minimal and direct. Prefer short lines over long paragraphs.
4. {language_instruction}
5. Use ₹ with Indian number formatting (e.g. ₹12,320).
6. STATUS DOT RULES (STRICT - ACCORDING TO REAL STATUS):
   - 🔴 = Any OVERDUE invoice/payment, or CRITICAL low stock (stock < 50% of reorder level).
   - 🟡 = Any pending payment that is NOT overdue yet, or WARNING low stock (stock <= reorder level).
   - 🟢 = Fully paid, zero dues, or healthy stock (> reorder level).
7. Structure:
   - Lead with the answer in 1–2 lines
   - Then short bullet or numbered facts if needed
8. Labels can be bold Markdown (**Label:**) but keep the message compact.
9. No greetings like "Namaste!" unless the user greeted first.
10. No filler phrases ("Based on our data", "Here is the record").
11. FORMATTING FOR LISTS (CRITICAL):
    - ALWAYS format lists of orders or products as separate markdown bullet points (one item per line starting with "- ").
    - NEVER merge or collapse multiple orders/products into a single paragraph or inline text.
12. NEVER say an order/product/stock change was completed unless it already happened via system action.

ANSWER:"""
        return prompt

    @staticmethod
    def _get_language_instruction(language: str) -> str:
        instructions = {
            "hindi": "Answer in Hindi (Devanagari script)",
            "english": "Answer in English",
            "hinglish": "Answer in Hinglish (Hindi words in Roman script)",
            "auto": "Match the language of the question",
        }
        return instructions.get(language, instructions["auto"])

    @staticmethod
    def _detect_language(text: str) -> str:
        hindi_chars = ["ा", "ि", "ी", "क", "ख", "ग", "च", "ज", "त", "न", "र", "स", "ह"]
        hinglish_words = ["kitne", "kitna", "hai", "hain", "kya", "ka", "ki", "ke", "aur", "aaj"]

        text_lower = (text or "").lower()
        if any(char in (text or "") for char in hindi_chars):
            return "hindi"
        if any(word in text_lower for word in hinglish_words):
            return "hinglish"
        return "english"

    @staticmethod
    def _get_sources() -> list:
        return [
            "customers table",
            "products table",
            "inventory table",
            "orders table",
            "invoices table",
        ]

    @staticmethod
    def _get_friendly_error_message(error: str) -> str:
        error_lower = (error or "").lower()
        if "503" in (error or "") or "unavailable" in error_lower:
            return "Karya AI is experiencing high demand. Please try again in a few moments."
        if "429" in (error or "") or "quota" in error_lower:
            return "API quota reached. Please wait a minute and try again."
        return "AI temporarily unavailable. Please try again."