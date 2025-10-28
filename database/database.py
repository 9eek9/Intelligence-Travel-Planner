"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database URL (file-based, no setup required)
# For production, replace with PostgreSQL: 'postgresql://user:password@localhost/dbname'
SQLALCHEMY_DATABASE_URL = "sqlite:///./smart_travel.db"

# Create engine
# connect_args={"check_same_thread": False} is needed only for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    """
    Dependency function to get database session
    Usage in FastAPI endpoints:
    
    @app.get("/items/")
    def read_items(db: Session = Depends(get_db)):
        ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create all tables
def create_tables():
    """
    Create all tables in the database
    Call this when starting the application
    """
    Base.metadata.create_all(bind=engine)