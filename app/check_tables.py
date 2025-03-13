"""
Script to check if the saved_videos table exists in the database.
"""

import sys
import os

# Add the parent directory to sys.path to allow imports from the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine

def list_tables():
    """List all tables in the database."""
    with engine.connect() as connection:
        query = text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """
        )
        result = connection.execute(query)
        tables = [row[0] for row in result]
        return tables

if __name__ == "__main__":
    print("Checking database tables...")
    tables = list_tables()
    print("Tables in the database:")
    for table in tables:
        print(f"- {table}")
    
    if "saved_videos" in tables:
        print("\nThe saved_videos table exists in the database!")
    else:
        print("\nWARNING: The saved_videos table does NOT exist in the database!") 