from app.database import Base, engine, get_db
from app.models import WatchedVideo
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_watched_videos_table():
    """Create the watched_videos table in the database."""
    try:
        # Create table based on the SQLAlchemy model
        Base.metadata.create_all(bind=engine, tables=[WatchedVideo.__table__])
        logger.info("WatchedVideo table created successfully!")
        
        # Verify the table was created
        with engine.connect() as conn:
            result = conn.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'watched_videos')")
            exists = result.scalar()
            
            if exists:
                logger.info("Verified: watched_videos table exists in the database.")
                logger.info("Table columns:")
                
                # Query and display table columns for verification
                column_query = """
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'watched_videos'
                ORDER BY ordinal_position;
                """
                columns = conn.execute(column_query)
                for column in columns:
                    logger.info(f"  - {column[0]} ({column[1]}, nullable: {column[2]})")
                
                return True
            else:
                logger.error("Table creation may have failed - table does not exist in database.")
                return False
    
    except Exception as e:
        logger.error(f"Error creating watched_videos table: {str(e)}")
        return False

if __name__ == "__main__":
    result = create_watched_videos_table()
    sys.exit(0 if result else 1) 