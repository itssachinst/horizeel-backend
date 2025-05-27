import os
import tempfile
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Video
from app.utils.s3_utils import convert_to_hls_and_upload, upload_to_s3
from uuid import UUID
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

def get_db_session():
    """Get a database session for background tasks"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        db.close()
        raise

def update_video_status(video_id: UUID, status: str, video_url: Optional[str] = None, thumbnail_url: Optional[str] = None):
    """Update video status in database"""
    db = get_db_session()
    try:
        video = db.query(Video).filter(Video.video_id == video_id).first()
        if video:
            video.status = status
            if video_url:
                video.video_url = video_url
            if thumbnail_url:
                video.thumbnail_url = thumbnail_url
            db.commit()
            logger.info(f"Updated video {video_id} status to {status}")
        else:
            logger.error(f"Video {video_id} not found for status update")
    except Exception as e:
        logger.error(f"Failed to update video status: {e}")
        db.rollback()
    finally:
        db.close()

def process_video_background(
    video_id: UUID,
    video_file_path: str,
    thumbnail_file_path: str,
    video_filename: str,
    thumbnail_filename: str
):
    """
    Background task to process video files
    
    Args:
        video_id: UUID of the video in database
        video_file_path: Path to the temporary video file
        thumbnail_file_path: Path to the temporary thumbnail file
        video_filename: Original video filename
        thumbnail_filename: Original thumbnail filename
    """
    logger.info(f"Starting background processing for video {video_id}")
    
    try:
        # Update status to processing
        update_video_status(video_id, 'processing')
        
        # Check if files exist
        if not os.path.exists(video_file_path):
            logger.error(f"Video file not found: {video_file_path}")
            update_video_status(video_id, 'failed')
            return
            
        if not os.path.exists(thumbnail_file_path):
            logger.error(f"Thumbnail file not found: {thumbnail_file_path}")
            update_video_status(video_id, 'failed')
            return
        
        # Get file sizes for logging
        video_size_mb = os.path.getsize(video_file_path) / (1024 * 1024)
        thumbnail_size_mb = os.path.getsize(thumbnail_file_path) / (1024 * 1024)
        
        logger.info(f"Processing video: {video_filename} ({video_size_mb:.2f} MB)")
        logger.info(f"Processing thumbnail: {thumbnail_filename} ({thumbnail_size_mb:.2f} MB)")
        
        # Process video - convert to HLS and upload to S3
        logger.info(f"Converting video {video_id} to HLS format")
        video_url = convert_to_hls_and_upload(video_file_path, video_filename)
        logger.info(f"Video conversion completed: {video_url}")
        
        # Upload thumbnail to S3
        logger.info(f"Uploading thumbnail for video {video_id}")
        thumbnail_url = upload_to_s3(thumbnail_file_path, thumbnail_filename)
        logger.info(f"Thumbnail upload completed: {thumbnail_url}")
        
        # Update video status to ready with URLs
        update_video_status(video_id, 'ready', video_url, thumbnail_url)
        
        logger.info(f"Background processing completed successfully for video {video_id}")
        
    except Exception as e:
        logger.error(f"Background processing failed for video {video_id}: {str(e)}")
        update_video_status(video_id, 'failed')
        
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(video_file_path):
                os.remove(video_file_path)
                logger.info(f"Cleaned up video file: {video_file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up video file {video_file_path}: {e}")
            
        try:
            if os.path.exists(thumbnail_file_path):
                os.remove(thumbnail_file_path)
                logger.info(f"Cleaned up thumbnail file: {thumbnail_file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up thumbnail file {thumbnail_file_path}: {e}")

def process_youtube_video_background(
    video_id: UUID,
    youtube_url: str,
    title: str,
    description: str,
    start_time: int = 0,
    end_time: Optional[int] = None
):
    """
    Background task to process YouTube video downloads
    
    Args:
        video_id: UUID of the video in database
        youtube_url: YouTube video URL
        title: Video title
        description: Video description
        start_time: Start time in seconds
        end_time: End time in seconds (optional)
    """
    logger.info(f"Starting background YouTube processing for video {video_id}")
    
    try:
        # Update status to processing
        update_video_status(video_id, 'processing')
        
        # Import here to avoid circular imports
        from app.utils.youtube_utils import download_youtube_clip
        import subprocess
        import uuid
        
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download video from YouTube
            video_path, video_title, duration = download_youtube_clip(
                youtube_url, 
                temp_dir, 
                start_time, 
                end_time
            )
            
            # If no title provided, use the YouTube video title
            if not title.strip():
                title = video_title
                
            # Convert the video to HLS and upload to S3
            video_url = convert_to_hls_and_upload(video_path, f"{uuid.uuid4()}.mp4")
            
            # Create a thumbnail from the video
            thumbnail_path = os.path.join(temp_dir, "thumbnail.jpg")
            thumbnail_cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-ss', '00:00:01',
                '-vframes', '1',
                thumbnail_path
            ]
            subprocess.run(thumbnail_cmd, check=True)
            
            # Upload thumbnail to S3
            thumbnail_url = upload_to_s3(thumbnail_path, f"thumbnail_{uuid.uuid4()}.jpg")
            
            # Update video status to ready with URLs
            update_video_status(video_id, 'ready', video_url, thumbnail_url)
            
            logger.info(f"Background YouTube processing completed successfully for video {video_id}")
            
    except Exception as e:
        logger.error(f"Background YouTube processing failed for video {video_id}: {str(e)}")
        update_video_status(video_id, 'failed') 