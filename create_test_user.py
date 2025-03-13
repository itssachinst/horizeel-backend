"""
Script to create a test user with a known password.
"""

import sys
import os
import uuid

# Add the parent directory to sys.path to allow imports from the app package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.crud import create_user
from app.schemas import UserCreate

def create_test_user():
    """Create a test user with a known password."""
    print("Creating a test user...")
    
    # Create a test user
    test_user = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="testpassword"
    )
    
    # Get a database session
    db = SessionLocal()
    
    try:
        # Check if the user already exists
        from app.crud import get_user_by_email
        existing_user = get_user_by_email(db, test_user.email)
        
        if existing_user:
            print(f"User with email {test_user.email} already exists.")
            print("User ID:", existing_user.user_id)
            print("Username:", existing_user.username)
            print("Email:", existing_user.email)
            print("\nYou can use these credentials to log in:")
            print(f"Email: {test_user.email}")
            print(f"Password: testpassword")
            return
        
        # Create the user
        user = create_user(db, test_user)
        
        print("Test user created successfully!")
        print("User ID:", user.user_id)
        print("Username:", user.username)
        print("Email:", user.email)
        
        print("\nYou can use these credentials to log in:")
        print(f"Email: {test_user.email}")
        print(f"Password: testpassword")
    
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user() 