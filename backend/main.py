from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="Karya AI",
    description="AI Operating System for Indian Small Businesses",
    version="0.1.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ROUTES ====================

@app.get("/")
def read_root():
    return {
        "app": "Karya AI 🇮🇳",
        "message": "AI Operating System for Indian Small Businesses",
        "status": "running",
        "version": "0.1.0",
        "developer": "Akshat Namdev"
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "All systems operational ✅"}

@app.get("/test-db")
def test_database():
    """Test database connection"""
    from sqlalchemy import create_engine, text
    
    try:
        engine = create_engine(os.getenv("DATABASE_URL"))
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            
            result = conn.execute(text(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
            ))
            vector = result.fetchone()
            
            return {
                "status": "connected",
                "database": "Neon PostgreSQL",
                "version": version[:50],
                "pgvector": vector[0] if vector else "not installed"
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/test-gemini")
def test_gemini():
    """Test Gemini AI with our service"""
    from app.services.ai_service import ai_service
    
    result = ai_service.generate(
        prompt="Say hello in Hindi and English. Introduce yourself as Karya AI, "
               "an AI assistant for Indian small businesses. Keep it under 50 words.",
        model_type="smart"
    )
    return result

@app.get("/test-gemini-fast")
def test_gemini_fast():
    """Test with fast/lite model"""
    from app.services.ai_service import ai_service
    
    result = ai_service.generate(
        prompt="What is 2+2? Answer in one word.",
        model_type="fast"
    )
    return result

@app.get("/list-models")
def list_models():
    """List all available models"""
    from app.services.ai_service import ai_service
    return {"models": ai_service.list_available_models()}

# ==================== STARTUP ====================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("🚀 Starting Karya AI Backend...")
    print("=" * 60)
    print("📍 API: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("=" * 60 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)