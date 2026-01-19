"""
CloudNexus API - Database Layer
SQLAlchemy engine, session management, and model definitions for Amazon RDS.
"""

import os
import time
import logging
from datetime import datetime
from functools import wraps
from typing import Generator

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Configure logging for CloudWatch
logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()


# =============================================================================
# DATABASE MODELS
# =============================================================================

class Task(Base):
    """Sample Task model for demonstration."""
    
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def to_dict(self) -> dict:
        """Convert model to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active
        }


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

def get_database_url() -> str:
    """
    Construct database URL from environment variables.
    Supports PostgreSQL with pg8000 (default) and MySQL.
    """
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "cloudnexus")
    db_user = os.environ.get("DB_USER", "postgres")
    db_pass = os.environ.get("DB_PASS", "")
    db_driver = os.environ.get("DB_DRIVER", "postgresql")  # postgresql or mysql
    
    if db_driver == "mysql":
        return f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    # Default to PostgreSQL with pg8000 driver (pure Python, no Lambda Layer needed)
    return f"postgresql+pg8000://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"


def create_db_engine(max_retries: int = 3, retry_delay: float = 1.0):
    """
    Create SQLAlchemy engine with connection pooling optimized for Lambda.
    
    Includes retry logic to handle VPC cold starts and transient connection issues.
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Initial delay between retries (exponential backoff)
    
    Returns:
        SQLAlchemy Engine instance
    """
    database_url = get_database_url()
    
    # Engine configuration optimized for AWS Lambda
    engine_kwargs = {
        # Connection pool settings
        "pool_pre_ping": True,           # Verify connections before use
        "pool_recycle": 300,             # Recycle connections every 5 minutes
        "pool_size": 5,                  # Maintain 5 connections in pool
        "max_overflow": 10,              # Allow up to 10 additional connections
        
        # Connection timeout settings for pg8000
        "connect_args": {
            "timeout": 10  # 10 second connection timeout
        }
    }
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(database_url, **engine_kwargs)
            
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Database connection established on attempt {attempt + 1}")
            return engine
            
        except OperationalError as e:
            last_exception = e
            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
            
            logger.warning(
                f"Database connection attempt {attempt + 1}/{max_retries} failed. "
                f"Retrying in {wait_time:.1f}s. Error: {str(e)}"
            )
            
            if attempt < max_retries - 1:
                time.sleep(wait_time)
    
    logger.error(f"Failed to connect to database after {max_retries} attempts")
    raise last_exception


# Lazy initialization for Lambda cold starts
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine


def get_session_factory():
    """Get or create the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine()
        )
    return _SessionLocal


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.
    
    Yields a database session and ensures proper cleanup.
    Use with FastAPI's Depends() for automatic session management.
    
    Yields:
        SQLAlchemy Session
    
    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Task).all()
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    
    Creates all tables defined in Base.metadata if they don't exist.
    Call this during application startup or deployment.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully")


def test_db_connection() -> dict:
    """
    Test database connectivity and return status.
    
    Returns:
        dict: Connection status with details
    """
    try:
        start_time = time.time()
        engine = get_engine()
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "database": "connected",
            "latency_ms": round(latency_ms, 2)
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
