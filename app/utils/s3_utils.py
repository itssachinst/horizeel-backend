import boto3
import os
from botocore.exceptions import ClientError
import logging
from fastapi import UploadFile, HTTPException
import subprocess
import tempfile
import shutil
import uuid

logger = logging.getLogger(__name__)

AWS_ACCESS_KEY = "AKIA3RYC52TM7MKGCFUU"
AWS_SECRET_KEY = "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"
S3_BUCKET = "mypov-videos"

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name="eu-north-1"
)

PROFILE_IMAGES_FOLDER = 'profile-images/'
VIDEOS_FOLDER = 'videos/'
THUMBNAILS_FOLDER = 'thumbnails/'
HLS_FOLDER = 'hls/'

def upload_to_s3(file_path: str, file_name: str) -> str:
    if not S3_BUCKET:
        raise ValueError("S3_BUCKET is not defined. Check your environment variables.")
    logger.info(f"Uploading file to S3: {file_name}")
    s3_client.upload_file(file_path, S3_BUCKET, file_name, ExtraArgs={"ContentType": "video/mp4"})
    
    return f"https://{S3_BUCKET}.s3.eu-north-1.amazonaws.com/{file_name}"

def convert_to_hls_and_upload(input_path: str, filename: str) -> str:
    """
    Convert a video file to HLS format and upload to S3
    
    Args:
        input_path: Path to the input video file
        filename: Original filename (without path)
        
    Returns:
        URL to the HLS playlist
    """
    # Create a unique ID for this video
    video_id = str(uuid.uuid4())
    
    # Create temporary directory for HLS output
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract base name without extension
        base_name = os.path.splitext(filename)[0]
        
        # Create output directory for HLS files
        output_path = os.path.join(temp_dir, base_name)
        os.makedirs(output_path, exist_ok=True)
        
        # Path to the HLS playlist
        hls_playlist = os.path.join(output_path, "index.m3u8")
        
        # Run FFmpeg to convert to HLS
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-c:v', 'libx264',             # Force H.264
            '-c:a', 'aac',                 # Force AAC audio
            '-b:a', '128k',                # Audio bitrate
            '-profile:v', 'baseline',
            '-level', '3.0',
            '-x264-params', 'keyint=48:min-keyint=48:no-scenecut',  # Force keyframe every 2s (for 24fps)
            '-hls_time', '6',              # Try smaller segments (6s)
            '-hls_segment_filename', f'{output_dir}/index%d.ts',  # Clean segment naming
            '-hls_list_size', '0',
            '-start_number', '0',
            '-f', 'hls',
            hls_playlist
        ]
        
        try:
            subprocess.run(ffmpeg_cmd, check=True)
            logger.info(f"Successfully converted {filename} to HLS format")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to convert video to HLS format")
        
        # S3 prefix for this video
        s3_prefix = f"{HLS_FOLDER}{video_id}/"
        
        # Upload all HLS files to S3
        for root, _, files in os.walk(output_path):
            for file in files:
                local_file_path = os.path.join(root, file)
                s3_key = f"{s3_prefix}{file}"
                
                # Set appropriate content type
                content_type = 'application/vnd.apple.mpegurl' if file.endswith('.m3u8') else 'video/MP2T'
                
                try:
                    s3_client.upload_file(
                        local_file_path, 
                        S3_BUCKET, 
                        s3_key,
                        ExtraArgs={'ContentType': content_type}
                    )
                    logger.info(f"Uploaded {s3_key} to S3")
                except ClientError as e:
                    logger.error(f"Error uploading {s3_key} to S3: {e}")
                    raise HTTPException(status_code=500, detail="Failed to upload HLS files to S3")
        
        # Return the URL to the HLS playlist
        return f"https://{S3_BUCKET}.s3.eu-north-1.amazonaws.com/{s3_prefix}index.m3u8"

async def upload_video_to_s3(file: UploadFile, video_id: str):
    """Upload a video file to S3"""
    try:
        file_key = f"{VIDEOS_FOLDER}{video_id}/{file.filename}"
        response = s3_client.upload_fileobj(
            file.file, 
            S3_BUCKET, 
            file_key
        )
        
        # Generate the URL for the uploaded file
        url = f"https://{S3_BUCKET}.s3.amazonaws.com/{file_key}"
        return url
    except ClientError as e:
        logger.error(f"Error uploading file to S3: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload video to storage")
    finally:
        # Reset file position
        file.file.seek(0)

async def upload_thumbnail_to_s3(file: UploadFile, video_id: str):
    """Upload a thumbnail file to S3"""
    try:
        file_key = f"{THUMBNAILS_FOLDER}{video_id}/{file.filename}"
        response = s3_client.upload_fileobj(
            file.file, 
            S3_BUCKET, 
            file_key
        )
        
        # Generate the URL for the uploaded file
        url = f"https://{S3_BUCKET}.s3.amazonaws.com/{file_key}"
        return url
    except ClientError as e:
        logger.error(f"Error uploading thumbnail to S3: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload thumbnail to storage")
    finally:
        # Reset file position
        file.file.seek(0)

async def upload_profile_image_to_s3(file: UploadFile, user_id: str):
    """Upload a profile image to S3"""
    try:
        # Create a filename using the user_id to make it unique
        filename = f"{user_id}_{file.filename}"
        file_key = f"{PROFILE_IMAGES_FOLDER}{filename}"
        
        # Reset file position before reading
        file.file.seek(0)
        
        # Create a temporary copy of the file content
        content = file.file.read()
        
        # Upload the file to S3 using the content
        from io import BytesIO
        with BytesIO(content) as file_obj:
            s3_client.upload_fileobj(
                file_obj,
                S3_BUCKET, 
                file_key
            )
        
        # Generate the URL for the uploaded file
        url = f"https://{S3_BUCKET}.s3.amazonaws.com/{file_key}"
        return url
    except ClientError as e:
        logger.error(f"Error uploading profile image to S3: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload profile image to storage")
    except Exception as e:
        logger.error(f"Unexpected error uploading profile image: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")