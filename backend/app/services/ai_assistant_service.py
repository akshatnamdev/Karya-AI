"""
Karya AI - AI Assistant Service
Handles all interactions with the Users
"""

import json
import re
import time
import os
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


class AIAssistantService:
    """AI Business Assistant with caching, demo mode, actions, and fallback"""
    @staticmethod
    def _invalidate_cache(scope: dict):
        """Purges cached AI responses so next clicks/questions fetch fresh DB data"""
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
    def ask_question(db: Session, query: AIQuery, scope: dict, use_demo: bool = False) -> AIResponse:
        """Main method with protection, RBAC, and optional create actions"""
        start_time = time.time()

        # ==================== LAYER 1: DEMO MODE ====================
        if use_demo or os.getenv("DEMO_MODE", "false").lower() == "true":
            demo_response = DemoModeService.get_demo_response(query.question)
            if demo_response:
                return AIResponse(**demo_response)

        # ==================== LAYER 1.5: ACTIONS (order / product) ====================
        # Mutations must run BEFORE cache and must NOT be cached.
        action_response = AIAssistantService._try_handle_action(db, query, scope, start_time)
        if action_response is not None:
            return action_response

        # ==================== LAYER 2: CACHE CHECK ====================
        cache_scope_key = f"{scope.get('scope')}_{scope.get('business_id')}_{scope.get('customer_id')}"
        cached = AICache.get(query.question, query.language, cache_scope_key)
        if cached:
            return AIResponse(**cached)

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
            role=scope["scope"],
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
            "answer": ai_result.get("response", "").strip(),
            "model_used": ai_result.get("model", "unknown"),
            "response_time_ms": response_time_ms,
            "sources": AIAssistantService._get_sources(),
            "detected_language": detected_language,
        }

        AICache.set(query.question, query.language, cache_scope_key, response_data)

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

    # ==================== ACTION HANDLING (NEW) ====================

    @staticmethod
    def _try_handle_action(db: Session, query: AIQuery, scope: dict, start_time: float):
        """
        If user wants to place order or add product:
        - extract details
        - ask for missing info OR
        - call existing ProductService / OrderService
        Returns AIResponse or None (fall through to normal Q&A).
        """
        intent = AIAssistantService._detect_action_intent(query.question, scope.get("scope"))
        if not intent:
            return None

        if intent == "add_product":
            return AIAssistantService._handle_add_product(db, query, scope, start_time)

        if intent == "place_order":
            return AIAssistantService._handle_place_order(db, query, scope, start_time)

        return None

    @staticmethod
    def _detect_action_intent(question: str, role: str):
        q = (question or "").lower().strip()

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

        # Broad place-order intent (customer + business)
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
            "place an order",
            "order of",
            "i need",
            "i want",
            "mujhe",
            "chahiye",
            "book",
            "buy",
            "purchase",
            "get me",
        ]

        if role == "business" and any(k in q for k in add_product_keys):
            return "add_product"

        if role in ("business", "customer") and any(k in q for k in place_order_keys):
            # Avoid treating pure history questions as place-order
            history_keys = [
                "show my order",
                "show all my order",
                "my orders",
                "order history",
                "list my order",
                "pending order",
                "where is my order",
                "order status",
            ]
            if any(h in q for h in history_keys):
                return None
            return "place_order"

        return None

    @staticmethod
    def _handle_add_product(db: Session, query: AIQuery, scope: dict, start_time: float) -> AIResponse:
        if scope.get("scope") != "business":
            return AIAssistantService._action_answer(
                query,
                start_time,
                "Only business users can add products.",
            )

        business_id = scope.get("business_id")
        if not business_id:
            return AIAssistantService._action_answer(
                query, start_time, "Business context missing. Please log in again."
            )

        extracted = AIAssistantService._extract_json_with_ai(
            instruction=AIAssistantService._add_product_extract_prompt(query.question),
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
        return AIAssistantService._action_answer(query, start_time, answer, sources=["products table", "inventory table"])

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

        # Catalog snapshot for name → id resolution (and for extraction context)
        products = (
            db.query(Product)
            .filter(Product.business_id == business_id, Product.is_active == True)
            .all()
        )
        catalog_lines = [
            f"id={p.id} | name={p.name} | price={p.selling_price}"
            for p in products[:80]
        ]
        catalog_text = "\n".join(catalog_lines) if catalog_lines else "No products available."

        customers_text = ""
        if role == "business":
            customers = db.query(Customer).limit(50).all()
            # Prefer business-linked customers if model has business_id
            try:
                customers = (
                    db.query(Customer)
                    .filter(Customer.business_id == business_id)
                    .limit(50)
                    .all()
                )
            except Exception:
                pass
            customers_text = "\n".join(
                [f"id={c.id} | name={getattr(c, 'name', '')}" for c in customers]
            ) or "No customers found."

        extracted = AIAssistantService._extract_json_with_ai(
            instruction=AIAssistantService._place_order_extract_prompt(
                question=query.question,
                role=role,
                catalog_text=catalog_text,
                customers_text=customers_text,
            ),
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
                product_id = AIAssistantService._resolve_product_id(
                    db, business_id, product_name
                )

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
                + ", ".join(unresolved)
                + ".\nPlease use exact catalog names or product ids.",
            )

        if not items_data:
            return AIAssistantService._action_answer(
                query, start_time, "No valid order items found. Please try again with product and quantity."
            )

        notes = extracted.get("notes") or None
        source = "ai"

        try:
            result = OrderService.create_unified_order(
                db=db,
                business_id=business_id,
                customer_id=customer_id,
                items_data=items_data,
                source=source,
                notes=notes,
            )
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
    def _extract_json_with_ai(instruction: str) -> dict | None:
        result = ai_service.generate(prompt=instruction, model_type="fast", max_retries=2)
        if result.get("status") == "error":
            result = ai_service.generate(prompt=instruction, model_type="smart", max_retries=1)
        if result.get("status") == "error":
            return None

        text = (result.get("response") or "").strip()
        return AIAssistantService._parse_json_loose(text)

    @staticmethod
    def _parse_json_loose(text: str) -> dict | None:
        if not text:
            return None
        # Strip markdown fences if model adds them
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        # First object in text
        try:
            return json.loads(text)
        except Exception:
            pass
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except Exception:
            return None

    @staticmethod
    def _resolve_product_id(db: Session, business_id: int, name: str):
        if not name:
            return None
        name = name.strip()
        # exact
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
        # partial
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
        q = db.query(Customer).filter(Customer.name.ilike(name))
        try:
            q = db.query(Customer).filter(
                Customer.business_id == business_id,
                Customer.name.ilike(name),
            )
        except Exception:
            q = db.query(Customer).filter(Customer.name.ilike(name))
        c = q.first()
        if c:
            return c.id
        q = db.query(Customer).filter(Customer.name.ilike(f"%{name}%"))
        try:
            q = db.query(Customer).filter(
                Customer.business_id == business_id,
                Customer.name.ilike(f"%{name}%"),
            )
        except Exception:
            pass
        c = q.first()
        return c.id if c else None

    @staticmethod
    def _action_answer(query: AIQuery, start_time: float, answer: str, sources: list | None = None) -> AIResponse:
        response_time_ms = int((time.time() - start_time) * 1000)
        return AIResponse(
            question=query.question,
            answer=answer,
            model_used="action+gemini",
            response_time_ms=response_time_ms,
            sources=sources or ["orders table", "products table"],
            detected_language=AIAssistantService._detect_language(query.question),
        )

    # ==================== PRIVATE HELPERS (EXISTING) ====================

    @staticmethod
    def _build_prompt(business_context: str, user_question: str, language: str, role: str) -> str:
        language_instruction = AIAssistantService._get_language_instruction(language)

        if role == "customer":
            persona = """You are Karya, a helpful shopping and account assistant for this business. You are talking to a CUSTOMER.
Your job is to help them check their order status, pending invoices, or browse available products in the catalog.
If the customer says hello, asks for help, or asks general questions, be welcoming and let them know you can help them check their orders, pending bills, or product catalog.
They can also place orders by saying things like "place order for 2 Notebook".
When the customer wants to buy/order items (e.g. "i want 2 vitamin C"), the system will handle real order placement separately. Do not pretend an order was placed in normal Q&A.
If they ask about other customers or business internal data, politely inform them you can only share details related to their own account."""
        elif role == "business":
            persona = """You are Karya, an intelligent business assistant for the BUSINESS OWNER.
You have access to the full business performance data, financials, inventory, and customer account details. Help the owner manage their business effectively.
They can add products ("add product Notebook price 50 stock 100") and place orders ("place order for customer Ramesh: 2 Notebook")."""
        else:
            persona = "You are Karya, a Platform Admin assistant with system-wide visibility."

        prompt = f"""{persona}

BUSINESS & ACCOUNT DATA:
{business_context}

USER QUESTION: {user_question}

INSTRUCTIONS:
1. Answer ONLY from the data above. Never invent numbers .
2. Answer ONLY based on the data above.
3. Be minimal and direct. Prefer short lines over long paragraphs.
4. {language_instruction}
5. Use ₹ with Indian number formatting (e.g. ₹12,320).
6. STATUS DOT RULES (STRICT - ACCORDING TO REAL STATUS):
   - 🔴 = Any OVERDUE invoice/payment, or CRITICAL low stock (stock < 50% of reorder level).
   - 🟡 = Any pending payment that is NOT overdue yet, or WARNING low stock (stock <= reorder level).
   - 🟢 = Fully paid, zero dues, or healthy stock (> reorder level).
   - Rules per section:
     * Overdue customer -> MUST use 🔴
     * Pending customer (no overdue) -> MUST use 🟡
     * No dues customer -> MUST use 🟢
     * Critical stock -> MUST use 🔴
     * Low stock -> MUST use 🟡
     * Healthy stock -> MUST use 🟢
7. Structure:
   - Lead with the answer in 1–2 lines
   - Then short bullet or numbered facts if needed
   - Optional one-line action at the end (no emoji unless status)
8. Labels can be bold Markdown (**Label:**) but keep the message compact.
9. No greetings like "Namaste!" unless the user greeted first.
10. No filler phrases ("Based on our data", "Here is the record").
11. NEVER say an order was placed, created, or confirmed unless the system already executed a real order action in this turn.
12. NEVER invent order IDs, totals, or item lines.
13. If the user wants to order something but details are incomplete, ask for product name and quantity only.

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

        text_lower = text.lower()
        if any(char in text for char in hindi_chars):
            return "hindi"
        if any(word in text_lower for word in hinglish_words):
            return "hinglish"
        return "english"

    @staticmethod
    def _get_sources() -> list:
        return ["customers table", "products table", "inventory table", "orders table", "invoices table"]

    @staticmethod
    def _get_friendly_error_message(error: str) -> str:
        error_lower = error.lower()
        if "503" in error or "unavailable" in error_lower:
            return "Karya AI is experiencing high demand. Please try again in a few moments."
        if "429" in error or "quota" in error_lower:
            return "API quota reached. Please wait a minute and try again."
        return "AI temporarily unavailable. Please try again."