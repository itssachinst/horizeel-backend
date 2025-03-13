import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable

# Add parent directory to path to import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import database connection string and Base from app's settings
from app.database import DATABASE_URL, Base, engine
from app.models import UserFollow  # Import the UserFollow model that was already defined

def create_user_follows_table():
    # Create the table using the metadata and model definitions already imported
    try:
        # Check if the table already exists
        inspector = engine.dialect.has_table(engine.connect(), "user_follows")
        
        if not inspector:
            # Create the table
            Base.metadata.tables["user_follows"].create(bind=engine, checkfirst=True)
            print("User follows table created successfully!")
        else:
            print("User follows table already exists.")
    except Exception as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    create_user_follows_table()
