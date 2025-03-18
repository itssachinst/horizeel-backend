from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from elasticsearch import Elasticsearch

# Define PostgreSQL connection
DATABASE_URL = "postgresql+psycopg2://sachin:sachin56@horizeel-db.cbs2ca4ao43p.eu-north-1.rds.amazonaws.com:5432/postgres"

# Create the engine
engine = create_engine(DATABASE_URL)

# Create a session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define Base here to avoid circular imports
Base = declarative_base()

# Elasticsearch Connection
ELASTICSEARCH_HOST = "http://localhost:9200"
es = Elasticsearch([ELASTICSEARCH_HOST])

# Add get_db dependency function
def get_db():
    """
    Dependency function to get a database session.
    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database and create tables."""
    from app.models import Base  # Import here to avoid circular import
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")

def init_elasticsearch():
    """Ensure Elasticsearch is running and check connectivity."""
    try:
        if es.ping():
            print("Connected to Elasticsearch successfully.")
        else:
            print("Failed to connect to Elasticsearch.")
    except Exception as e:
        print(f"Elasticsearch connection error: {e}")

if __name__ == "__main__":
    init_db()
    init_elasticsearch()
