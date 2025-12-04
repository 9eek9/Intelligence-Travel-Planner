"""
Database configuration and session management (PostgreSQL version)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# -------------------------------------------------------------
# PostgreSQL Connection (Local Development)
# -------------------------------------------------------------
# DATABASE_URL = "postgresql://postgres:admin123@localhost:5433/SmartTravelDB" #local
DATABASE_URL = "postgresql://dbadmin:ChangeMe123!@capstone-project-postgresql.cj04aqs6srh6.ca-central-1.rds.amazonaws.com:5432/SmartTravelDB" 

# -------------------------------------------------------------
# Create engine (SQLAlchemy 2.0 config)
# -------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    echo=True,
    future=True
)

# -------------------------------------------------------------
# Session factory
# -------------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for ORM models
Base = declarative_base()


# -------------------------------------------------------------
# Dependency for FastAPI routes
# -------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------------------
# Create all tables on startup
# -------------------------------------------------------------
def create_tables():
    """
    Imports all ORM model files so SQLAlchemy recognizes them,
    then creates tables if they don't exist.
    """
    import models.user
    import models.itinerary
    import models.sentiment_review

    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")
