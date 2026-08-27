<div align="center">

# 🧠 Karya AI

### *AI Operating System for Indian Small Businesses*

**Turn a WhatsApp message into a completed business transaction — with just one tap.**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Gemini AI](https://img.shields.io/badge/Gemini_AI-Latest-4285F4.svg?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

[Features](#-features) • [Tech Stack](#-tech-stack) • [Installation](#-installation) • [Demo](#-demo-flow) • [Roadmap](#-roadmap)

---

</div>

## 🎯 The Problem

Small Indian businesses run on a scattered mess of:
- 📱 WhatsApp for orders
- 📊 Excel for tracking
- 📚 Tally for accounting
- 📓 Notebooks for everything else

This fragmentation leads to **manual work, missed orders, lost payments, and lost opportunities**.

## 💡 The Solution

**Karya AI** is not just another dashboard — it's an AI that **executes business operations**:

- 📥 **Reads** WhatsApp orders automatically
- 🧾 **Creates** invoices and updates inventory
- 💰 **Chases** overdue payments intelligently
- 📊 **Analyzes** business performance
- 🎯 **Predicts** demand and reorder cycles
- 🧠 **Learns** your business patterns over time

All with **owner approval** where needed — AI proposes, you approve, action executes. ✅

---

## ✨ Features

### 🧠 AI Business Assistant
Natural language Q&A over your business data with source citations.
```
You: "Raj Traders ne pichle 3 mahine mein kya kharida?"
Karya: "Raj Traders bought ₹2,45,000 worth of products including:
        • 500 units of XYZ (Aug)
        • 300 units of ABC (Jul)
        Source: Orders #1023, #1045, #1067"
```

### 📱 WhatsApp Message Parser
Extracts structured orders from informal chat messages.
```
Input: "Raj bhai 50 XYZ bhej dena Friday ko"

Karya extracts:
✓ Customer: Raj Traders
✓ Product: XYZ  
✓ Quantity: 50
✓ Delivery: Friday
```

### 🔒 Owner Approval Layer
Every AI action requires your approval before execution.
- ✅ Approve → Action executes
- ✏️ Edit → Modify details first
- ❌ Reject → Discard suggestion

### 📦 Smart Inventory
- Real-time stock tracking
- Low-stock alerts
- Demand forecasting (moving average)
- Reorder recommendations

### 💰 Payment Intelligence
- Automatic overdue detection
- Auto-drafted reminder messages
- Outstanding amount tracking
- Customer payment history

### 🤖 AI Agents
- **Sales Agent** — Reorder detection, customer follow-ups
- **Operations Agent** — Inventory alerts, daily summaries

### 🇮🇳 Hindi + English Support
Understands Hinglish business language naturally.

### 🛡️ Anti-Hallucination Architecture
- Structured data first (SQL queries for numbers)
- RAG grounding with source attribution
- Confidence scoring
- Validation before actions

---

## 🏗️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.11** | Core language |
| **FastAPI** | High-performance web framework |
| **SQLAlchemy** | Database ORM |
| **Pydantic** | Data validation |
| **JWT** | Authentication |

### Database
| Technology | Purpose |
|------------|---------|
| **PostgreSQL 16** | Primary database (Neon Cloud) |
| **pgvector** | Vector embeddings for RAG |

### AI/ML
| Technology | Purpose |
|------------|---------|
| **Google Gemini** | Primary LLM (Flash + Flash-Lite) |
| **Sentence Transformers** | Text embeddings |
| **Custom RAG Pipeline** | Grounded responses |

### Frontend *(Coming Soon)*
| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework |
| **TypeScript** | Type safety |
| **Vite** | Build tool |
| **Tailwind CSS** | Styling |
| **shadcn/ui** | UI components |
| **Recharts** | Data visualization |
| **Framer Motion** | Animations |

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────┐
│         REACT + VITE FRONTEND               │
│  Dashboard | WhatsApp Sim | AI Chat | CRUD  │
└──────────────────┬──────────────────────────┘
                   │ REST + WebSocket
                   ↓
┌─────────────────────────────────────────────┐
│            FASTAPI BACKEND                  │
│  Auth | Business APIs | AI Router | RAG     │
└──────────────────┬──────────────────────────┘
                   │
       ┌───────────┼───────────┐
       ↓           ↓           ↓
   ┌────────┐ ┌────────┐ ┌──────────┐
   │Business│ │   AI   │ │  Agents  │
   │Services│ │ Router │ │Sales+Ops │
   └────────┘ └────┬───┘ └──────────┘
                   ↓
            ┌──────────────┐
            │  GEMINI API  │
            │Flash / Lite  │
            └──────┬───────┘
                   ↓
       ┌───────────┴───────────┐
       ↓                       ↓
┌─────────────┐         ┌─────────────┐
│ POSTGRESQL  │◄────────│  pgvector   │
│Business Data│         │ Embeddings  │
└─────────────┘         └─────────────┘
```

---

## 🚀 Installation

### Prerequisites

- ✅ Python 3.11 or higher
- ✅ Node.js 20 or higher *(for frontend)*
- ✅ Neon.tech account (free PostgreSQL)
- ✅ Google Gemini API key (free tier)
- ✅ Git

### Backend Setup

**1. Clone the repository**
```bash
git clone https://github.com/akshatnamdev/Karya-AI.git
cd Karya-AI/backend
```

**2. Create virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Setup environment variables**

Create a `.env` file in the `backend/` folder:
```env
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@host/database?sslmode=require

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# JWT Authentication
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# App Config
APP_NAME=Karya AI
DEBUG=True
```

**5. Get your credentials**
- **Neon PostgreSQL:** [neon.tech](https://neon.tech) → Create free project → Enable pgvector extension
- **Gemini API:** [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → Create API key

**6. Run the server**
```bash
python main.py
```

**7. Access the API**
- 🌐 **API:** http://localhost:8000
- 📚 **Swagger Docs:** http://localhost:8000/docs
- 📖 **ReDoc:** http://localhost:8000/redoc

---

## 🧪 Testing the Setup

Once the server is running, test these endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /` | Welcome message |
| `GET /health` | Health check |
| `GET /test-db` | Database + pgvector status |
| `GET /test-gemini` | Gemini AI integration test |
| `GET /list-models` | Available Gemini models |

**Example response from `/test-gemini`:**
```json
{
  "status": "success",
  "model": "models/gemini-flash-latest",
  "response": "Namaste! Hello! I am Karya AI, an AI assistant for Indian small businesses.",
  "attempts": 1
}
```

---

## 🎬 Demo Flow

### The "Wow" Moment

```
┌─────────────────────────────────────────────┐
│  1. Owner opens Karya AI Dashboard          │
│     🔴 3 products low on stock              │
│     🟠 ₹1.4L nding payments           │
│     🟢 5 customers due for reorder          │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  2. Asks in Hindi:                          │
│     "Aaj kitne orders aaye?"                │
│                                             │
│  Karya: "Today you received 12 orders       │
│         worth ₹84,500."                     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  3. Pastes WhatsApp message:                │
│     "Raj bhai 50 XYZ bhej dena Friday ko"   │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  4. Karya shows Approval Card:              │
│     ┌───────────────────────────┐           │
│     │ 🆕 New Order Detected     │           │
│     │ Customer: Raj Traders     │           │
│     │ Product: XYZ × 50         │           │
│     │ Delivery: Friday          │           │
│     │ Stock: 72 available ✅    │           │
│     │                           │           │
│     │ [✅ Approve] [✏️] [❌]    │           │
│     └───────────────────────────┘           │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  5. One-tap Approve:                        │
│     ✓ Order created                         │
│     ✓ Invoice generated                     │
│     ✓ Stock updated                         │
│     ✓ Customer history logged               │
└─────────────────────────────────────────────┘
```

---

## 📊 Roadmap

### 🗓️ 30-Day Sprint Plan

- [x] **Day 1:** Environment setup, FastAPI, Neon PostgreSQL, Gemini integration ✅
- [ ] **Day 2-3:** Database schema, SQLAlchemy models, Alembic migrations
- [ ] **Day 4-7:** Authentication, User/Business setup, Core APIs
- [ ] **Day 8-14:** Business logic (Customers, Products, Orders, Invoices, Payments)
- [ ] **Day 15-17:** RAG pipeline, Business Memory, Vector embeddings
- [ ] **Day 18-19:** WhatsApp parser, Owner approval workflow
- [ ] **Day 20-21:** AI Agents (Sales + Operations), Hindi/English support
- [ ] **Day 22-27:** React frontend (Dashboard, WhatsApp Sim, AI Chat)
- [ ] **Day 28-29:** Testing, Bug fixes, Deployment
- [ ] **Day 30:** Demo video, Documentation, Launch 🚀

### 🔮 Future Enhancements

- 📱 Real WhatsApp Business API integration
- 🎤 Voice input support (Whisper)
- 📸 Invoice OCR (image → structured data)
- 💳 Payment gateway integration (UPI, Razorpay)
- 🏦 Bank account reconciliation
- 📊 Advanced ML forecasting
- 📱 Mobile apps (Android + iOS)
- 🌐 Multi-language (Tamil, Telugu, Marathi, Bengali)
- 🔌 Third-party integrations (Tally, Zoho, QuickBooks)

---

## 🎯 Why Karya AI?

| Traditional Tools | Karya AI |
|-------------------|----------|
| 📊 Static dashboards | 🤖 AI executes actions |
| ✍️ Manual data entry | 📱 AI extracts from WhatsApp |
| 🇬🇧 English only | 🇮🇳 Hindi + English + Hinglish |
| 🔀 Multiple apps | 🎯 One integrated platform |
| 🚨 Reactive alerts | 🔮 Predictive intelligence |
| 💸 Expensive SaaS | 💰 Affordable for Indian SMBs |
| 🔒 Data in cloud | 🛡️ Privacy-first architecture |

---

## 🛠️ Project Structure

```
karya-ai/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Config, security
│   │   ├── db/            # Database setup
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   │   └── ai_service.py
│   │   ├── agents/        # AI agents
│   │   ├── rag/           # RAG pipeline
│   │   └── utils/         # Utilities
│   ├── .env               # Environment variables (not in git)
│   ├── .gitignore
│   ├── main.py            # FastAPI entry point
│   ├── test_db.py         # Database test script
│   └── requirements.txt
├── frontend/              # React app (coming soon)
├── docs/                  # Documentation
├── .gitignore
└── README.md
```

---

## 📸 Screenshots

*(Coming soon as development progresses)*

- [ ] Dashboard view
- [ ] WhatsApp order simulator
- [ ] AI chat interface
- [ ] Approval workflow
- [ ] Inventory management
- [ ] Analytics & reports

---

## 🤝 Contributing

This is currently a solo project as part of a 30-day sprint. Once the MVP is complete, contributions will be welcomed!

**Planned contribution areas:**
- 🎨 UI/UX improvements
- 🌐 Additional language support
- 🧪 Testing coverage
- 📚 Documentation
- 🐛 Bug fixes

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

<div align="center">

### **Akshat Namdev**

*Python Developer • AI Enthusiast • Building for Indian SMBs*

[![GitHub](https://img.shields.io/badge/GitHub-akshatnamdev-181717?style=for-the-badge&logo=github)](https://github.com/akshatnamdev)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin)](https://linkedin.com/in/YOUR-LINKEDIN)
[![Email](https://img.shields.io/badge/Email-Contact-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:your-email@example.com)

</div>

---

## 🙏 Acknowledgments

- 🇮🇳 **Indian Small Businesses** — for the inspiration
- 🤖 **Google Gemini** — for the AI capabilities
- 🐘 **Neon.tech** — for the amazing free PostgreSQL
- 💚 **FastAPI Community** — for the incredible framework
- 🌟 **Open Source Community** — for making this possible

---

## 📞 Support

Have questions, feedback, or want to collaborate?

- 📧 Email: akshatnamdev23@gmail.com
- 💼 LinkedIn: https://www.linkedin.com/in/akshatnamdev23/
- 🐛 Issues: [GitHub Issues](https://github.com/akshatnamdev/Karya-AI/issues)

---

<div align="center">

### ⭐ Star this repository if you find it interesting!

**Built with ❤️ for Indian small businesses**

*"AI that doesn't just chat — it works."*

---

**© 2026 Akshat Namdev. All rights reserved.**

</div>
