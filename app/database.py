from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import time
import logging
from elasticsearch import Elasticsearch
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define PostgreSQL connection
# For production, get these from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://sachin:sachin56@horizeel-db.cbs2ca4ao43p.eu-north-1.rds.amazonaws.com:5432/postgres")

# Maximum number of connection attempts
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds

# Create engine with retry mechanism
def get_engine():
    """
    Create the SQLAlchemy engine with retry mechanism
    """
    retry_count = 0
    last_exception = None
    
    while retry_count < MAX_RETRIES:
        try:
            engine = create_engine(
                DATABASE_URL,
                pool_size=20,               # Maximum number of connections in the pool
                max_overflow=30,            # Allow up to 30 connections to overflow the pool
                pool_timeout=30,            # Timeout for getting a connection from the pool
                pool_recycle=1800,          # Recycle connections after 30 minutes
                pool_pre_ping=True,         # Verify connections before using them
                echo=False                  # Set to True for debugging SQL queries
            )
            # Test connection with proper SQLAlchemy text object
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully")
            return engine
        except Exception as e:
            retry_count += 1
            last_exception = e
            logger.warning(f"Database connection attempt {retry_count} failed: {str(e)}")
            if retry_count < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
    
    # If we get here, all retries failed
    logger.error(f"Failed to connect to database after {MAX_RETRIES} attempts. Last error: {str(last_exception)}")
    raise last_exception

try:
    engine = get_engine()
    # Session factory with optimized settings
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # Base class for all models
    Base = declarative_base()
except Exception as e:
    logger.critical(f"Fatal error connecting to database: {str(e)}")
    # In production, you might want to fallback to a different database or exit
    raise

# Elasticsearch Connection
ELASTICSEARCH_HOST = "http://localhost:9200"
try:
    es = Elasticsearch([ELASTICSEARCH_HOST], retry_on_timeout=True)
except Exception as e:
    logger.error(f"Error connecting to Elasticsearch: {str(e)}")
    es = None

# Database dependency with error handling
def get_db():
    """
    Get a database session.
    This function should be used as a FastAPI dependency to get a database session.
    """
    db = None
    try:
        db = SessionLocal()
        # Test connection with proper SQLAlchemy text object
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        if db:
            db.rollback()  # Roll back any pending transactions
        raise
    finally:
        if db:
            db.close()

# Context manager for database sessions (for scripts)
@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Useful for scripts that need to interact with the database.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

def init_db():
    """Initialize the database and create tables."""
    from app.models import Base  # Import here to avoid circular import
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")

def init_elasticsearch():
    """Ensure Elasticsearch is running and check connectivity."""
    if not es:
        logger.warning("Elasticsearch client not initialized")
        return

    try:
        if es.ping():
            logger.info("Connected to Elasticsearch successfully.")
        else:
            logger.warning("Failed to connect to Elasticsearch.")
    except Exception as e:
        logger.error(f"Elasticsearch connection error: {str(e)}")

if __name__ == "__main__":
    init_db()
    init_elasticsearch()
