from app.database import engine, SessionLocal
from app.models import WatchedVideo, User, Video
import logging
from datetime import datetime, timedelta
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_watched_videos_table():
    """Check if the watched_videos table exists and print its contents."""
    try:
        db = SessionLocal()
        
        # Check if table exists
        with engine.connect() as conn:
            result = conn.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'watched_videos')")
            exists = result.scalar()
            
            if not exists:
                logger.error("The watched_videos table does not exist in the database.")
                return False
        
        # Count records
        count = db.query(WatchedVideo).count()
        logger.info(f"Found {count} records in the watched_videos table.")
        
        # Display sample data if available
        if count > 0:
            samples = db.query(WatchedVideo).limit(5).all()
            logger.info("\nSample records:")
            for sample in samples:
                logger.info(f"ID: {sample.id}")
                logger.info(f"User ID: {sample.user_id}, Video ID: {sample.video_id}")
                logger.info(f"Watch time: {sample.watch_time}s, Watch percentage: {sample.watch_percentage}%")
                logger.info(f"Engagement: Liked={sample.like_flag}, Disliked={sample.dislike_flag}, Saved={sample.saved_flag}, Shared={sample.shared_flag}")
                logger.info(f"Last watched: {sample.last_watched_at}")
                logger.info("-" * 40)
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking watched_videos table: {str(e)}")
        return False
    finally:
        db.close()

def insert_test_data():
    """Insert some test records into the watched_videos table."""
    try:
        db = SessionLocal()
        
        # Get some existing users and videos
        users = db.query(User).limit(2).all()
        videos = db.query(Video).limit(3).all()
        
        if not users or not videos:
            logger.warning("No users or videos found in the database. Cannot insert test data.")
            return False
        
        # Create some test watched videos records
        test_records = []
        for i, user in enumerate(users):
            for j, video in enumerate(videos):
                # Create different watch patterns
                watch_record = WatchedVideo(
                    user_id=user.user_id,
                    video_id=video.video_id,
                    like_flag=True if i % 2 == 0 else False,
                    dislike_flag=True if i % 2 == 1 else False,
                    saved_flag=True if j % 2 == 0 else False,
                    shared_flag=True if (i+j) % 3 == 0 else False,
                    watch_time=float(video.duration * (0.25 + (i+j) * 0.25)),  # Watch 25%, 50%, 75% or 100%
                    watch_percentage=25.0 + (i+j) * 25.0,
                    completed=True if (i+j) >= 3 else False,
                    last_position=float(video.duration * (0.25 + (i+j) * 0.25)),
                    first_watched_at=datetime.utcnow() - timedelta(days=(i+j)),
                    last_watched_at=datetime.utcnow() - timedelta(hours=(i+j)),
                    watch_count=i+j+1,
                    device_type="mobile" if i % 2 == 0 else "desktop"
                )
                test_records.append(watch_record)
        
        # Add the records to the database
        db.add_all(test_records)
        db.commit()
        
        logger.info(f"Successfully inserted {len(test_records)} test records into watched_videos table.")
        return True
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting test data: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # First check if the table exists
    if check_watched_videos_table():
        # Ask if the user wants to insert test data
        response = input("Do you want to insert test data? (y/n): ")
        if response.lower() == 'y':
            insert_test_data()
            # Check table again after inserting data
            check_watched_videos_table() 