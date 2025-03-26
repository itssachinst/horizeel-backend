from app.models import WatchHistory, User, Video
from app.database import engine, SessionLocal
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import inspect
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_watched_videos_table():
    """
    Check if the watched_videos table exists and contains data
    """
    try:
        # Create a session
        db = SessionLocal()
        
        # Check if the table exists
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if "watched_videos" not in tables:
            logger.error("watched_videos table does not exist!")
            return False
        
        # Check if there are records in the table
        count = db.query(WatchHistory).count()
        logger.info(f"Found {count} records in watched_videos table")
        
        # Show some sample records if they exist
        if count > 0:
            samples = db.query(WatchHistory).limit(5).all()
            logger.info("Sample records:")
            for sample in samples:
                logger.info(f"  - {sample}")
        
        # If no records exist, create a test record
        if count == 0:
            logger.info("Creating a test record...")
            
            # Get a user and a video
            user = db.query(User).first()
            video = db.query(Video).first()
            
            if not user:
                logger.error("No users found in the database!")
                return False
                
            if not video:
                logger.error("No videos found in the database!")
                return False
            
            # Create a watch record
            watch_record = WatchHistory(
                user_id=user.user_id,
                video_id=video.video_id,
                watch_time=120.0,
                watch_percentage=75.0,
                completed=False,
                last_position=120.0,
                watch_count=1,
                device_type="test_device"
            )
            
            db.add(watch_record)
            db.commit()
            
            logger.info(f"Test record created: {watch_record}")
            
        return True
    except Exception as e:
        logger.error(f"Error checking watched_videos table: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    check_watched_videos_table() 