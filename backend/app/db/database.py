"""
Karya AI - Database Connection
Sets up SQLAlchemy engine and session
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings


# Create SQLAlchemy engine with better connection handling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,          # Test connection before using
    pool_size=5,                  # Number of connections
    max_overflow=10,              # Extra connections when needed
    pool_recycle=300,             # Recycle connections every 5 minutes
    pool_timeout=30,              # Wait 30s for a connection
    # connect_args={
    #     "connect_timeout": 30,    # PostgreSQL connect timeout
    #     "keepalives": 1,          # Enable TCP keepalives
    #     "keepalives_idle": 30,    # Idle time before sending keepalive
    #     "keepalives_interval": 10,# Time between keepalives  
    #     "keepalives_count": 5,    # Number of keepalives before timeout
    # },
    echo=settings.DEBUG           # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all models
Base = declarative_base()


# Dependency to get database session
def get_db():
    """Provides a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()