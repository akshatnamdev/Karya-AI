from datetime import datetime


class DemoModeService:
    """Pre-cached responses for demos - never uses API calls"""
    
    DEMO_RESPONSES = {
        "kitne customers hain": {
            "answer": """🎯 **Aapke paas total 3 customers registered hain:**

1. **Raj Traders** (Wholesale)
   📞 Phone: 9988776655
   💰 Outstanding: ₹42,500 (Credit Limit: ₹1,50,000)

2. **Sharma Medical Store** (Retail)
   📞 Phone: 9877001122
   💰 Outstanding: ₹18,500 (Credit Limit: ₹50,000)

3. **Gupta Agencies** (Distributor)
   📞 Phone: 9765432109
   💰 Outstanding: Nil ✅ (Credit Limit: ₹2,00,000)

📌 **Summary:** Total outstanding amount **₹61,000** hai, jisme se Raj Traders ka ₹12,320 overdue chal raha hai.""",
            "language": "hinglish"
        },
        
        "which products are running low": {
            "answer": """⚠️ **3 products need reordering:**

🔴 **Critical: ABC Cough Syrup 100ml**
   - Current Stock: 18 units
   - Reorder Level: 40 units
   - Recommended Order: 120 units
   - Estimated Cost: ₹7,800

🟡 **Warning: XYZ Tablet 500mg**
   - Current Stock: 72 units
   - Reorder Level: 100 units
   - Recommended Order: 300 units
   - Estimated Cost: ₹12,600

🟡 **Warning: Vitamin C 500mg**
   - Current Stock: 32 units
   - Reorder Level: 50 units
   - Recommended Order: 150 units
   - Estimated Cost: ₹12,000

💰 **Total Reorder Investment:** ₹32,400

💡 **Suggestion:** Order ABC Cough Syrup first - it's critical!""",
            "language": "english"
        },
        
        "show me overdue payments": {
            "answer": """🔴 **1 overdue payment worth ₹12,320**

**Customer:** Raj Traders
📞 **Phone:** 9988776655
💰 **Amount Due:** ₹12,320
📋 **Invoice:** INV-2026-0002
📅 **Due Date:** 3 August 2026
⏰ **Days Overdue:** 10 days
🎯 **Urgency:** 🟡 Medium

📱 **Suggested WhatsApp Message:**
_"Namaste Raj Traders, aapka payment ₹12,320.00 (Invoice INV-2026-0002) 10 days se pending hai. Kripya payment karein. Dhanyawad! 🙏"_

💡 **Action:** Send reminder today via WhatsApp""",
            "language": "english"
        },
        
        "aaj kitna sale hua": {
            "answer": """📊 **Aaj (14 August 2026) ka sales report:**

Aaj koi order abhi tak nahi aaya hai. 

📅 **Last order:** 30 July 2026 (15 days ago)
   - Customer: Sharma Medical Store
   - Amount: ₹7,840
   - Order: ORD-2026-0003

💡 **Insight:** Recent activity kam hai. Consider:
- Regular customers ko follow-up call karein
- WhatsApp par offers bhejein
- Reorder cycle ke basis par outreach karein""",
            "language": "hinglish"
        },
        
        "raj traders ka status kya hai": {
            "answer": """👤 **Raj Traders - Complete Status:**

📋 **Customer Details:**
- **Type:** Wholesale
- **Phone:** 9988776655
- **City:** Indore
- **Notes:** Regular customer, orders every 20-25 days

💰 **Financial Status:**
- **Total Outstanding:** ₹42,500
- **Credit Limit:** ₹1,50,000
- **Available Credit:** ₹1,07,500

⚠️ **Alert:** ₹12,320 overdue for 10 days!

📊 **Order History:**
1. ORD-2026-0002: ₹12,320 (Delivered 19 July 2026) - ⚠️ Payment pending
2. ORD-2026-0001: ₹16,800 (Delivered 13 June 2026) - ✅ Paid

💡 **Recommendation:** 
- Send payment reminder immediately
- Total business: ₹29,120
- High-value customer - maintain good relationship""",
            "language": "hinglish"
        },
        
        "what should i focus on today": {
            "answer": """🎯 **Aaj ke top 3 priorities:**

**1. 🔴 URGENT: Payment Recovery**
   - Raj Traders se ₹12,320 pending (10 days overdue)
   - Action: WhatsApp reminder bhejein
   - Impact: Cash flow improvement

**2. 🟠 IMPORTANT: Stock Reorder**
   - ABC Cough Syrup CRITICAL level pe hai (18/40)
   - Action: Supplier ko order karein
   - Cost: ₹7,800

**3. 🟡 STRATEGIC: Customer Follow-up**
   - Gupta Agencies ka koi recent order nahi
   - Action: Courtesy call karein
   - Opportunity: New order possibility

⏰ **Time Estimate:**
- Payment reminder: 5 minutes
- Stock ordering: 15 minutes
- Customer call: 10 minutes

**Total: 30 minutes for critical business tasks!**""",
            "language": "hinglish"
        },
        
        "business summary": {
            "answer": """🏪 **Namdev Pharma & Distributors - Business Overview**

📊 **Overall Health: 🟡 Good (needs attention)**

💰 **Financial Snapshot:**
- Total Revenue: ₹36,960
- Total Received: ₹18,800  
- Outstanding: ₹61,000
- Stock Value: ₹20,260

👥 **Customer Base: 3 active**
- Wholesale: 1 (Raj Traders)
- Retail: 1 (Sharma Medical)
- Distributor: 1 (Gupta Agencies)

📦 **Inventory Status:**
- Total Products: 4
- Low Stock: 3 items ⚠️
- Total Stock Value: ₹20,260

⚠️ **Critical Alerts:**
1. ₹12,320 overdue from Raj Traders (10 days)
2. ABC Cough Syrup CRITICALLY low
3. 2 other products need reordering

💡 **Top Actions:**
1. Recover overdue payments
2. Reorder critical stock
3. Follow up with distributors

🎯 **Overall:** Business chal raha hai but immediate attention chahiye payments aur stock ke liye!""",
            "language": "hinglish"
        }
    }
    
    @staticmethod
    def get_demo_response(question: str) -> dict:
        """Get pre-cached demo response if question matches"""
        question_lower = question.lower().strip()
        
        # Direct match
        if question_lower in DemoModeService.DEMO_RESPONSES:
            demo = DemoModeService.DEMO_RESPONSES[question_lower]
            return DemoModeService._format_response(question, demo)
        
        # Partial match
        for key, demo in DemoModeService.DEMO_RESPONSES.items():
            if key in question_lower or DemoModeService._similar_words(question_lower, key):
                return DemoModeService._format_response(question, demo)
        
        return None
    
    @staticmethod
    def _similar_words(question: str, demo_key: str) -> bool:
        """Check if questions have similar keywords"""
        keywords_map = {
            "kitne customers hain": ["customer", "customers", "grahak", "kitne"],
            "which products are running low": ["low stock", "stock", "reorder", "running low", "products low"],
            "show me overdue payments": ["overdue", "pending payment", "due", "outstanding"],
            "aaj kitna sale hua": ["today sale", "aaj sale", "today revenue", "today order"],
            "raj traders ka status": ["raj traders", "raj bhai"],
            "what should i focus on today": ["focus", "priority", "today do", "aaj kya"],
            "business summary": ["summary", "overview", "business report", "overall"]
        }
        
        if demo_key in keywords_map:
            for keyword in keywords_map[demo_key]:
                if keyword in question:
                    return True
        return False
    
    @staticmethod
    def _format_response(question: str, demo: dict) -> dict:
        """Format demo response to match API structure"""
        return {
            "question": question,
            "answer": demo["answer"],
            "model_used": "demo_mode",
            "response_time_ms": 50,
            "sources": ["cached_demo_data"],
            "detected_language": demo["language"],
            "from_cache": True,
            "demo_mode": True
        }
    
    @staticmethod
    def list_demo_questions() -> list:
        """List all pre-cached questions"""
        return list(DemoModeService.DEMO_RESPONSES.keys())