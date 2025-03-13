"""
Script to check users in the database.
"""

import sys
import os

# Add the parent directory to sys.path to allow imports from the app package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine

def check_users():
    """Check users in the database."""
    print("Checking users in the database...")
    
    with engine.connect() as connection:
        # Check if the users table exists
        exists_query = text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
            """
        )
        exists = connection.execute(exists_query).scalar()
        
        if not exists:
            print("The users table does not exist!")
            return
        
        print("The users table exists.")
        
        # Get the users
        users_query = text(
            """
            SELECT user_id, username, email
            FROM users
            LIMIT 10;
            """
        )
        users = connection.execute(users_query).fetchall()
        
        if not users:
            print("No users found in the database.")
            return
        
        print(f"\nFound {len(users)} users:")
        print("------------------------------")
        for user in users:
            print(f"User ID: {user[0]}")
            print(f"Username: {user[1]}")
            print(f"Email: {user[2]}")
            print("------------------------------")

if __name__ == "__main__":
    check_users() 