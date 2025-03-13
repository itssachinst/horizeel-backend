"""
Script to initialize the entire database.
This will create all tables defined in the models.
"""

import sys
import os

# Add the current directory to sys.path to allow imports from the app package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization completed successfully.") 