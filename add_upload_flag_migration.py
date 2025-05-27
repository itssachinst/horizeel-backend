#!/usr/bin/env python3
"""
Migration script to add uploadFlag column to users table.
This script adds the uploadFlag column with a default value of False.
"""

import sys
import os
from sqlalchemy import create_engine, MetaData, Table, Column, Boolean, inspect, text
import logging
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.database import engine, get_db
from app.models import User

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_upload_flag_column():
    """
    Add uploadFlag column to the users table.
    - uploadFlag (Boolean, default=False, nullable=False)
    """
    try:
        # Create a connection
        conn = engine.connect()
        
        # Determine the database dialect
        dialect = engine.dialect.name
        logger.info(f"Database dialect: {dialect}")
        
        # Check if uploadFlag column exists
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('users')]
        
        if 'uploadFlag' not in existing_columns:
            logger.info("Adding 'uploadFlag' column to users table")
            
            # Construct SQL based on dialect
            if dialect == 'postgresql':
                # PostgreSQL syntax
                sql = "ALTER TABLE users ADD COLUMN uploadFlag BOOLEAN NOT NULL DEFAULT FALSE"
            elif dialect == 'sqlite':
                # SQLite syntax
                sql = "ALTER TABLE users ADD COLUMN uploadFlag BOOLEAN DEFAULT FALSE"
            else:
                # Generic SQL
                sql = "ALTER TABLE users ADD COLUMN uploadFlag BOOLEAN NOT NULL DEFAULT FALSE"
            
            # Execute the SQL
            logger.info(f"Executing SQL: {sql}")
            conn.execute(text(sql))
            conn.commit()
            logger.info("Column 'uploadFlag' added successfully")
        else:
            logger.info("Column 'uploadFlag' already exists")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error adding uploadFlag column: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_migration():
    """
    Verify that the uploadFlag column was added successfully
    """
    try:
        # Get a database session
        db = next(get_db())
        
        # Try to query a user and check if uploadFlag is accessible
        user = db.query(User).first()
        if user:
            # Try to access the uploadFlag attribute
            upload_flag_value = user.uploadFlag
            logger.info(f"Migration verified: uploadFlag = {upload_flag_value}")
            return True
        else:
            logger.info("No users found to verify migration, but column should be available")
            return True
            
    except Exception as e:
        logger.error(f"Error verifying migration: {e}")
        return False
    finally:
        db.close()

def main():
    """
    Main function to run the migration
    """
    logger.info("Starting uploadFlag column migration...")
    
    # Add the column
    if add_upload_flag_column():
        logger.info("Column addition completed successfully")
        
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