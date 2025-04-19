import os
import tempfile
import subprocess
from typing import Optional, Tuple
from pytube import YouTube
from fastapi import HTTPException, status
import logging
from app.utils.s3_utils import convert_to_hls_and_upload
from datetime import timedelta

logger = logging.getLogger(__name__)

MAX_DURATION_SECONDS = 60  # 1 minute maximum

def download_youtube_clip(
    youtube_url: str, 
    output_path: str, 
    start_time: int = 0, 
    end_time: Optional[int] = None
) -> Tuple[str, str, int]:
    """
    Download a clip from YouTube and return the file path
    
    Args:
        youtube_url: URL of the YouTube video
        output_path: Path to save the downloaded video
        start_time: Start time in seconds
        end_time: End time in seconds
        
    Returns:
        tuple: (file_path, video_title, duration_seconds)
    """
    try:
        # Get YouTube video
        yt = YouTube(youtube_url)
        
        # Get video duration in seconds
        duration = yt.length
        
        # Validate duration
        if duration > MAX_DURATION_SECONDS and (end_time is None or start_time is None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Video duration ({duration}s) exceeds the maximum allowed duration of {MAX_DURATION_SECONDS} seconds"
            )
            
        if end_time and end_time - start_time > MAX_DURATION_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested clip length ({end_time - start_time}s) exceeds the maximum allowed duration of {MAX_DURATION_SECONDS} seconds"
            )
            
        # Get the highest resolution stream
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        if not stream:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No suitable video stream found for this YouTube URL"
            )
        
        # Download the complete video
        temp_path = stream.download(output_path=output_path, filename="full_video.mp4")
        logger.info(f"Downloaded YouTube video to {temp_path}")
        
        # Extract the clip if start or end times are specified
        if start_time > 0 or (end_time and end_time < duration):
            clip_path = os.path.join(output_path, "clip.mp4")
            
            # Set default end time if not provided
            if not end_time:
                end_time = min(start_time + MAX_DURATION_SECONDS, duration)
                
            # Check if clip exceeds maximum allowed duration
            if end_time - start_time > MAX_DURATION_SECONDS:
                end_time = start_time + MAX_DURATION_SECONDS
                
            # Create ffmpeg command to extract the clip
            clip_cmd = [
                'ffmpeg', '-y',
                '-i', temp_path,
                '-ss', str(timedelta(seconds=start_time)),
                '-to', str(timedelta(seconds=end_time)),
                '-c:v', 'copy',
                '-c:a', 'copy',
                clip_path
            ]
            
            # Run the command
            subprocess.run(clip_cmd, check=True)
            logger.info(f"Extracted clip to {clip_path}")
            
            # Remove the full video
            os.remove(temp_path)
            
            # Return the clip path and actual duration
            return clip_path, yt.title, end_time - start_time
        
        # If no clipping needed, return the full video
        return temp_path, yt.title, min(duration, MAX_DURATION_SECONDS)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download YouTube video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download YouTube video: {str(e)}"
        ) 