"""
Karya AI - Database Connection Diagnostic Tool
Tests different connection scenarios
"""
import os
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 70)
print("🔍 KARYA AI - Database Connection Diagnostics")
print("=" * 70)

# Check if DATABASE_URL exists
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found in .env file!")
    exit(1)

# Mask password in display
display_url = DATABASE_URL
if "@" in display_url:
    parts = display_url.split("@")
    creds = parts[0].split("//")[-1]
    if ":" in creds:
        user = creds.split(":")[0]
        display_url = display_url.replace(creds, f"{user}:****")
print(f"\n📡 Database URL: {display_url}")
print(f"🌐 Host: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'unknown'}")

# Check SSL mode
if "sslmode=require" not in DATABASE_URL:
    print("⚠️  WARNING: 'sslmode=require' not found in DATABASE_URL")
    print("   This may cause connection issues with Neon")

print("\n" + "-" * 70)
print("🧪 TEST 1: Attempting connection (attempt 1/3)...")
print("-" * 70)

max_attempts = 3
for attempt in range(1, max_attempts + 1):
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 30,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            }
        )
        
        print(f"⏳ Attempt {attempt}: Connecting...")
        
        with engine.connect() as conn:
            # Test 1: Basic query
            result = conn.execute(text("SELECT NOW();"))
            now = result.fetchone()[0]
            print(f"✅ Connected successfully!")
            print(f"🕐 Database time: {now}")
            
            # Test 2: Get PostgreSQL version
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"📊 Version: {version[:60]}...")
            
            # Test 3: Check pgvector
            result = conn.execute(text(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
            ))
            vector = result.fetchone()
            if vector:
                print(f"✅ pgvector installed: version {vector[0]}")
            else:
                print(f"⚠️  pgvector NOT installed")
            
            # Test 4: Count tables
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
            ))
            table_count = result.fetchone()[0]
            print(f"📁 Tables in database: {table_count}")
            
            # Test 5: Check data
            result = conn.execute(text("SELECT COUNT(*) FROM customers;"))
            customer_count = result.fetchone()[0]
            print(f"👥 Customers: {customer_count}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM products;"))
            product_count = result.fetchone()[0]
            print(f"📦 Products: {product_count}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM orders;"))
            order_count = result.fetchone()[0]
            print(f"🛒 Orders: {order_count}")
        
        print("\n" + "=" * 70)
        print("🎉 SUCCESS! Database is working perfectly!")
        print("=" * 70)
        break
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Attempt {attempt} FAILED:")
        print(f"   Error: {error_msg[:200]}")
        
        if attempt < max_attempts:
            wait_time = 5 * attempt
            print(f"\n⏳ Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
        else:
            print("\n" + "=" * 70)
            print("💡 TROUBLESHOOTING TIPS:")
            print("=" * 70)
            print("1. Wake up Neon: Go to https://console.neon.tech/")
            print("   → Click your project → SQL Editor → Run 'SELECT 1;'")
            print()
            print("2. Check your .env file has correct DATABASE_URL")
            print()
            print("3. Ensure URL has '?sslmode=require' at the end")
            print()
            print("4. Try getting a fresh connection string from Neon:")
            print("   → Neon Dashboard → Connect button → Copy URI")
            print()
            print("5. Check your internet connection")
            print("=" * 70)