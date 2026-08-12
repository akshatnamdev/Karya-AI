"""
Quick script to wake up Neon database
Run: python wake_db.py
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

print("😴 Waking up Neon database...")

try:
    engine = create_engine(os.getenv("DATABASE_URL"))
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1;"))
        print("✅ Database is awake and ready!")
        
        # Show some stats
        result = conn.execute(text("SELECT COUNT(*) FROM customers;"))
        count = result.fetchone()[0]
        print(f"📊 Customers in database: {count}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("💡 Check your DATABASE_URL in .env file")