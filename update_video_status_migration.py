#!/usr/bin/env python3
"""
Migration script to update video status enum to include processing states.
This script adds 'processing', 'ready', and 'failed' to the existing enum.
"""

import sys
import os
from sqlalchemy import create_engine, text, inspect
import logging
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.database import engine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_video_status_enum():
    """
    Update the video_status enum to include new processing states.
    """
    try:
        # Create a connection
        conn = engine.connect()
        
        # Determine the database dialect
        dialect = engine.dialect.name
        logger.info(f"Database dialect: {dialect}")
        
        if dialect == 'postgresql':
            # PostgreSQL: Add new values to existing enum
            logger.info("Updating video_status enum for PostgreSQL")
            
            # Add new enum values
            try:
                conn.execute(text("ALTER TYPE video_status ADD VALUE 'processing'"))
                logger.info("Added 'processing' to video_status enum")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("'processing' already exists in enum")
                else:
                    logger.warning(f"Error adding 'processing': {e}")
            
            try:
                conn.execute(text("ALTER TYPE video_status ADD VALUE 'ready'"))
                logger.info("Added 'ready' to video_status enum")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("'ready' already exists in enum")
                else:
                    logger.warning(f"Error adding 'ready': {e}")
            
            try:
                conn.execute(text("ALTER TYPE video_status ADD VALUE 'failed'"))
                logger.info("Added 'failed' to video_status enum")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("'failed' already exists in enum")
                else:
                    logger.warning(f"Error adding 'failed': {e}")
            
            conn.commit()
            
        elif dialect == 'sqlite':
            # SQLite doesn't have native enum support, so we need to check constraints
            logger.info("SQLite detected - checking if constraints need updating")
            
            # For SQLite, we might need to recreate the table or update constraints
            # This is more complex and depends on how the enum was implemented
            logger.info("SQLite enum handling may require manual intervention")
            
        else:
            # Generic approach - try to alter the enum
            logger.info(f"Generic enum update for dialect: {dialect}")
            try:
                conn.execute(text("ALTER TYPE video_status ADD VALUE 'processing'"))
                conn.execute(text("ALTER TYPE video_status ADD VALUE 'ready'"))
                conn.execute(text("ALTER TYPE video_status ADD VALUE 'failed'"))
                conn.commit()
            except Exception as e:
                logger.warning(f"Generic enum update failed: {e}")
        
        # Update existing videos to have 'ready' status instead of 'published'
        # This ensures backward compatibility
        try:
            result = conn.execute(text("""
                UPDATE videos 
                SET status = 'ready' 
                WHERE status = 'published'
            """))
            updated_count = result.rowcount
            logger.info(f"Updated {updated_count} videos from 'published' to 'ready' status")
            conn.commit()
        except Exception as e:
            logger.warning(f"Error updating existing video statuses: {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error updating video status enum: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_migration():
    """
    Verify that the enum update was successful
    """
    try:
        conn = engine.connect()
        
        # Try to insert a test record with new status values
        test_video_id = "00000000-0000-0000-0000-000000000000"
        
        # Test each new status value
        for status in ['processing', 'ready', 'failed']:
            try:
                conn.execute(text(f"""
                    INSERT INTO videos (video_id, title, description, video_url, thumbnail_url, status)
                    VALUES ('{test_video_id}', 'Test Video', 'Test Description', 'test_url', 'test_thumb', '{status}')
                    ON CONFLICT (video_id) DO UPDATE SET status = '{status}'
                """))
                logger.info(f"✅ Status '{status}' is valid")
            except Exception as e:
                logger.error(f"❌ Status '{status}' failed: {e}")
                return False
        
        # Clean up test record
        try:
            conn.execute(text(f"DELETE FROM videos WHERE video_id = '{test_video_id}'"))
        except:
            pass
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error verifying migration: {e}")
        return False

def main():
    """
    Main function to run the migration
    """
    logger.info("Starting video status enum migration...")
    
    # Update the enum
    if update_video_status_enum():
        logger.info("Enum update completed successfully")
        
        # Verify the migration
        if verify_migration():
            logger.info("Migration verification completed successfully")
            logger.info("✅ Migration completed successfully!")
            return 0
        else:
            logger.error("❌ Migration verification failed")
            return 1
    else:
        logger.error("❌ Migration failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 