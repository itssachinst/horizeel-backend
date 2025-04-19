"""
Script to create the likes table in the database.
"""

import sys
import os

# Add the parent directory to sys.path to allow imports from the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy import MetaData, Table, Column, String, TIMESTAMP, text
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID

def create_likes_table():
    """Create the likes table if it doesn't exist."""
    print("Creating likes table...")

    metadata = MetaData()

    # Define likes table without foreign key constraints
    likes = Table(
        "likes",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
        Column("user_id", UUID(as_uuid=True), nullable=False),
        Column("video_id", UUID(as_uuid=True), nullable=False),
        Column("created_at", TIMESTAMP(timezone=True), server_default=text("NOW()")),
    )

    try:
        # Create the table
        likes.create(engine, checkfirst=True)
        
        # Create indexes after table creation
        conn = engine.connect()
        
        # Create index on user_id
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_likes_user_id ON likes (user_id)"))
        
        # Create index on video_id
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_likes_video_id ON likes (video_id)"))
        
        # Create unique index on user_id and video_id
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_likes_user_video ON likes (user_id, video_id)"))
        
        conn.close()
        
        print("likes table created successfully with all required indexes!")
    except Exception as e:
        print(f"Error creating likes table: {str(e)}")
        raise

if __name__ == "__main__":
    create_likes_table() 