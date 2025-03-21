import sys
import os
from sqlalchemy import Column, Boolean, String, JSON, text

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import database connection
from app.database import engine, get_db_session

def run_migration():
    """Add missing columns to the users table"""
    
    print("Starting migration to add missing columns to users table...")
    
    # Create session
    with get_db_session() as session:
        connection = session.connection()
        
        # Check if is_active column exists
        check_is_active = connection.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='is_active'"
        )).fetchone()
        
        if not check_is_active:
            print("Adding is_active column to users table...")
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE"
            ))
            print("is_active column added successfully.")
        else:
            print("is_active column already exists.")
            
        # Check if bio column exists
        check_bio = connection.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='bio'"
        )).fetchone()
        
        if not check_bio:
            print("Adding bio column to users table...")
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN bio TEXT"
            ))
            print("bio column added successfully.")
        else:
            print("bio column already exists.")
            
        # Check if social column exists
        check_social = connection.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='social'"
        )).fetchone()
        
        if not check_social:
            print("Adding social column to users table...")
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN social JSONB DEFAULT '{}'::jsonb"
            ))
            print("social column added successfully.")
        else:
            print("social column already exists.")
            
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration() 