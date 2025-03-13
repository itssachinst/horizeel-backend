import ffmpeg
from fastapi import HTTPException, status
import os

def validate_video(file_path: str) -> bool:
    """
    Validates if a video meets the requirements:
    - Must be horizontal (width > height)
    - Duration must be 60 seconds or less
    
    Args:
        file_path: Path to the video file
        
    Returns:
        bool: True if video meets requirements
        
    Raises:
        HTTPException: If video doesn't meet requirements
    """
    try:
        # Get video information using ffmpeg
        probe = ffmpeg.probe(file_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        
        # Get video dimensions
        width = int(video_info['width'])
        height = int(video_info['height'])
        
        # Get duration
        duration = float(probe['format']['duration'])
        
        # Check if video is horizontal
        if width <= height:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only horizontal videos are allowed (width must be greater than height)"
            )
        
        # Check duration (60 seconds = 1 minute)
        if duration > 60:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video duration must be 1 minute or less"
            )
            
        return True
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error in production
        print(f"Error validating video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error validating video file. Please ensure it's a valid video file."
        )
    finally:
        # Clean up the temporary file if it exists
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up temporary file: {str(e)}") 