from sqlalchemy import create_engine, MetaData, Table, Column, Text, Boolean, DateTime, inspect
import sys
import logging
from datetime import datetime
from app.database import Base, engine, get_db
from app.models import User

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_user_columns():
    """
    Add new columns to the user table:
    - feedback (Text)
    - feedback_updated_at (DateTime)
    - is_admin (Boolean)
    """
    try:
        # Create a metadata object
        metadata = MetaData()
        
        # Reflect the users table from the database
        users_table = Table('users', metadata, autoload_with=engine)
        
        # Create a connection
        conn = engine.connect()
        
        # Determine the database dialect
        dialect = engine.dialect.name
        logger.info(f"Database dialect: {dialect}")
        
        # Check if each column exists, and if not, add it
        columns_to_add = {
            'feedback': {
                'name': 'feedback',
                'type': Text,
                'sql_type': 'TEXT',
                'nullable': True
            },
            'feedback_updated_at': {
                'name': 'feedback_updated_at',
                'type': DateTime,
                'sql_type': 'TIMESTAMP',
                'nullable': True
            },
            'is_admin': {
                'name': 'is_admin',
                'type': Boolean,
                'sql_type': 'BOOLEAN',
                'nullable': False,
                'default': False
            }
        }
        
        # Get existing columns
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('users')]
        
        for column_name, column_info in columns_to_add.items():
            if column_name not in existing_columns:
                logger.info(f"Adding column '{column_name}' to users table")
                
                # Construct SQL based on dialect
                if dialect == 'postgresql':
                    # PostgreSQL syntax
                    default_str = f"DEFAULT {column_info.get('default')}" if 'default' in column_info else ""
                    nullable_str = "NULL" if column_info.get('nullable', True) else "NOT NULL"
                    type_str = column_info['sql_type']
                    
                    sql = f"ALTER TABLE users ADD COLUMN {column_name} {type_str} {nullable_str} {default_str}".strip()
                    
                elif dialect == 'sqlite':
                    # SQLite syntax (more limited)
                    type_str = column_info['sql_type']
                    default_str = f"DEFAULT {column_info.get('default')}" if 'default' in column_info else ""
                    
                    sql = f"ALTER TABLE users ADD COLUMN {column_name} {type_str} {default_str}".strip()
                    
                else:
                    # Generic SQL (may not work on all dialects)
                    type_str = column_info['sql_type']
                    nullable_str = "NULL" if column_info.get('nullable', True) else "NOT NULL"
                    default_str = f"DEFAULT {column_info.get('default')}" if 'default' in column_info else ""
                    
                    sql = f"ALTER TABLE users ADD COLUMN {column_name} {type_str} {nullable_str} {default_str}".strip()
                
                # Execute the SQL
                logger.info(f"Executing SQL: {sql}")
                conn.execute(sql)
                logger.info(f"Column '{column_name}' added successfully")
            else:
                logger.info(f"Column '{column_name}' already exists in users table")
        
        # Commit the transaction
        conn.commit()
        
        logger.info("All columns have been added to the users table")
        return True
    except Exception as e:
        logger.error(f"Error adding columns to users table: {e}")
        return False
    finally:
        # Close the connection
        if 'conn' in locals():
            conn.close()

def add_admin_user():
    """
    Promote a user to admin (first user or specified by email)
    """
    try:
        db = next(get_db())
        
        # Get the first user or a specified user
        user = db.query(User).first()
        
        if user:
            user.is_admin = True
            db.commit()
            logger.info(f"User {user.username} (ID: {user.user_id}) has been promoted to admin")
            return True
        else:
            logger.warning("No users found in the database")
            return False
    except Exception as e:
        logger.error(f"Error setting admin user: {e}")
        return False

if __name__ == "__main__":
    columns_success = add_user_columns()
    admin_success = False
    
    if columns_success:
        logger.info("Column migration completed successfully")
        # Only try to add admin user if columns were added successfully
        admin_success = add_admin_user()
    else:
        logger.error("Column migration failed")
    
    if admin_success:
        logger.info("Admin user setup completed successfully")
    else:
        logger.warning("Admin user setup did not complete")
    
    sys.exit(0 if columns_success else 1) 