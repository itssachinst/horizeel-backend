"""
Script to test the save video endpoint.
"""

import sys
import os
import requests
import json

# Add the parent directory to sys.path to allow imports from the app package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.crud import get_video, check_video_saved
from app.routes.user import get_current_user

def test_save_video():
    """Test the save video endpoint."""
    print("Testing save video endpoint...")
    
    # Get a database session
    db = SessionLocal()
    
    try:
        # Get the first video from the database
        videos = db.execute("SELECT video_id FROM videos LIMIT 1").fetchall()
        if not videos:
            print("No videos found in the database.")
            return
        
        video_id = str(videos[0][0])
        print(f"Using video ID: {video_id}")
        
        # Get a user token (you'll need to replace this with a valid token)
        token = input("Enter a valid JWT token: ")
        
        # Test the save video endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"http://localhost:8000/api/videos/{video_id}/save", headers=headers)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("Video saved successfully!")
        else:
            print(f"Failed to save video: {response.text}")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_save_video() 