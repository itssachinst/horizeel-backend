"""
Script to check the saved_videos table structure.
"""

import sys
import os

# Add the parent directory to sys.path to allow imports from the app package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine

def check_table_structure():
    """Check the structure of the saved_videos table."""
    print("Checking saved_videos table structure...")
    
    with engine.connect() as connection:
        # Check if the table exists
        exists_query = text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'saved_videos'
            );
            """
        )
        exists = connection.execute(exists_query).scalar()
        
        if not exists:
            print("The saved_videos table does not exist!")
            return
        
        print("The saved_videos table exists.")
        
        # Get the table structure
        columns_query = text(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'saved_videos'
            ORDER BY ordinal_position;
            """
        )
        columns = connection.execute(columns_query).fetchall()
        
        print("\nTable structure:")
        for column in columns:
            print(f"- {column[0]}: {column[1]} (Nullable: {column[2]})")
        
        # Check if there are any rows in the table
        count_query = text("SELECT COUNT(*) FROM saved_videos;")
        count = connection.execute(count_query).scalar()
        
        print(f"\nNumber of rows in the table: {count}")

if __name__ == "__main__":
    check_table_structure() 