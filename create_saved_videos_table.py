import sys
import os

# Add the parent directory to sys.path for imports from app package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base, engine
from app.models import SavedVideo

def create_saved_videos_table():
    """
    Create the saved_videos table in the database
    """
    print("Creating saved_videos table...")
    
    # Create the table
    Base.metadata.create_all(bind=engine, tables=[SavedVideo.__table__])
    
    print("saved_videos table created successfully.")

if __name__ == "__main__":
    create_saved_videos_table() 