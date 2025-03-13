"""
Script to add the saved_videos table to the database.
Run this script to create the saved_videos table if it doesn't exist.
"""

import sys
import os

# Add the parent directory to sys.path to allow imports from the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine
import time

def check_if_table_exists(table_name):
    """Check if a table exists in the database."""
    with engine.connect() as connection:
        query = text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = :table_name
            );
            """
        )
        result = connection.execute(query, {"table_name": table_name})
        return result.scalar()

def create_saved_videos_table():
    """Create the saved_videos table if it doesn't exist."""
    # First check if the table already exists
    if check_if_table_exists("saved_videos"):
        print("The saved_videos table already exists.")
        return
    
    # If it doesn't exist, create it using SQLAlchemy's create_all method
    print("Creating saved_videos table...")
    # Make sure we import the models
    from app.models import SavedVideo, Base
    # Create the table using the Base metadata
    SavedVideo.__table__.create(engine, checkfirst=True)
    print("saved_videos table created successfully.")

if __name__ == "__main__":
    print("Checking database tables...")
    create_saved_videos_table()
    print("Database update completed.") 