"""
Script to create the waiting_list table in the database.
"""

import sys
import os

# Add the parent directory to sys.path to allow imports from the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy import MetaData, Table, Column, String, Integer, TIMESTAMP, text
from uuid import uuid4
import uuid
from sqlalchemy.dialects.postgresql import UUID

def create_waiting_list_table():
    """Create the waiting_list table if it doesn't exist."""
    print("Creating waiting_list table...")
    
    metadata = MetaData()
    
    # Define PGUUID function to handle UUID fields
    def PGUUID(*args, **kwargs):
        if kwargs.get('as_uuid', False):
            return UUID(*args, **kwargs)
        else:
            return String(*args, **kwargs)
    
    # Define waiting_list table
    waiting_list = Table(
        "waiting_list",
        metadata,
        Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid4),
        Column("email", String, nullable=False, unique=True),
        Column("created_at", TIMESTAMP(timezone=True), server_default=text("NOW()")),
    )
    
    try:
        # Create the table
        waiting_list.create(engine, checkfirst=True)
        print("waiting_list table created successfully!")
    except Exception as e:
        print(f"Error creating waiting_list table: {str(e)}")
        raise

if __name__ == "__main__":
    create_waiting_list_table() 