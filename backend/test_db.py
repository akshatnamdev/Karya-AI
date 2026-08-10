import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 60)
print("🔌 KARYA AI - Database Connection Test")
print("=" * 60)

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found in .env file")
    exit(1)

print(f"📡 Connecting to Neon PostgreSQL...")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Test 1: Basic connection
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"\n✅ Connection Successful!")
        print(f"📊 PostgreSQL: {version[:50]}...")
        
        # Test 2: pgvector extension
        result = conn.execute(text(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
        ))
        vector_ext = result.fetchone()
        
        if vector_ext:
            print(f"✅ pgvector installed! Version: {vector_ext[0]}")
        else:
            print(f"⚠️  pgvector not enabled. Run: CREATE EXTENSION vector;")
        
        # Test 3: Create a test vector table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS connection_test (
                id SERIAL PRIMARY KEY,
                message TEXT,
                embedding vector(3)
            );
        """))
        
        # Insert test data
        conn.execute(text("""
            INSERT INTO connection_test (message, embedding) 
            VALUES ('Karya AI Test', '[1,2,3]');
        """))
        conn.commit()
        
        # Query back
        result = conn.execute(text("SELECT * FROM connection_test LIMIT 1;"))
        row = result.fetchone()
        print(f"✅ Vector storage working! Test row: {row[1]}")
        
        # Cleanup
        conn.execute(text("DROP TABLE connection_test;"))
        conn.commit()
        print(f"✅ Cleanup done!")
        
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED! Ready to build Karya AI!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Connection Failed: {e}")
    print("\n💡 Check:")
    print("  1. DATABASE_URL is correct in .env")
    print("  2. Neon database is active")
    print("  3. Internet connection is working")