"""
Simple direct connection test - bypass all frameworks
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("DATABASE_URL")
print(f"Testing: {url[:80]}...")

try:
    # Try direct psycopg2 connection
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"✅ CONNECTED! Version: {version[:60]}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ FAILED: {e}")
    print(f"\n💡 Full error type: {type(e).__name__}")