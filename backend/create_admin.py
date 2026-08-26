"""
Create the first platform admin.
Run once after migration.
"""
from app.db.database import SessionLocal
from app.services.auth_service import AuthService

if __name__ == "__main__":
    db = SessionLocal()
    try:
        admin = AuthService.create_platform_admin(
            db=db,
            name="Akshat Namdev",
            email="admin@karyaai.com",
            password="Admin@123",  # CHANGE THIS
        )
        print(f"✓ Platform admin created: {admin.email}")
        print(f"  Password: Admin@123 (change immediately!)")
    except ValueError as e:
        print(f"✗ {e}")
    finally:
        db.close()