import boto3
import os
from botocore.exceptions import ClientError
import logging
from fastapi import UploadFile, HTTPException
import subprocess
import tempfile
import shutil
import uuid
import json

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

def validate_video_file(file_path: str) -> dict:
    """
    Validate a video file using ffprobe and return its metadata
    
    Args:
        file_path: Path to the video file
        
    Returns:
        dict with video metadata or raises an exception if invalid
    """
    try:
        cmd = [
            'ffprobe', 
            '-v', 'error',
            '-show_entries', 'stream=codec_type,codec_name,width,height,duration,bit_rate,pix_fmt',
            '-show_entries', 'format=duration,size,bit_rate',
            '-of', 'json',
            file_path
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        metadata = json.loads(result.stdout)
        
        # Check if file has video streams
        has_video = False
        has_audio = False
        
        for stream in metadata.get('streams', []):
            if stream.get('codec_type') == 'video':
                has_video = True
            elif stream.get('codec_type') == 'audio':
                has_audio = True
        
        if not has_video:
            raise ValueError("File does not contain a valid video stream")
            
        return metadata
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8', errors='replace')
        logger.error(f"Error validating video file: {error_message}")
        raise ValueError(f"Invalid video file: {error_message}")
    except json.JSONDecodeError:
        raise ValueError("Could not parse video metadata")
    except Exception as e:
        raise ValueError(f"Error analyzing video: {str(e)}")

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
    
    # Validate video before processing
    try:
        # Check file size before processing
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
        logger.info(f"Processing video file: {filename}, Size: {file_size_mb:.2f} MB")
        
        metadata = validate_video_file(input_path)
        logger.info(f"Video validated successfully: {filename}")
        
        # Extract video duration and dimensions for logging
        duration = None
        width = None
        height = None
        
        for stream in metadata.get('streams', []):
            if stream.get('codec_type') == 'video':
                width = stream.get('width')
                height = stream.get('height')
                if not duration and 'duration' in stream:
                    duration = stream.get('duration')
        
        if not duration and 'format' in metadata and 'duration' in metadata['format']:
            duration = metadata['format']['duration']
        
        if duration:
            logger.info(f"Video duration: {float(duration):.2f} seconds")
        if width and height:
            logger.info(f"Video dimensions: {width}x{height}")
        
    except ValueError as e:
        logger.error(f"Video validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid video file: {str(e)}")
    
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
            '-c:v', 'libx264',
            '-crf', '18',  # Lower CRF means higher quality (18 is visually lossless)
            '-preset', 'slow',  # Better compression efficiency
            '-c:a', 'aac',
            '-b:a', '192k',  # Higher audio bitrate
            '-pix_fmt', 'yuv420p',
            '-max_muxing_queue_size', '9999',
            '-hls_time', '4',
            '-hls_list_size', '0',
            '-hls_segment_filename', f"{output_path}/segment_%03d.ts",
            '-start_number', '0',
            '-f', 'hls',
            hls_playlist
        ]
        
        logger.info(f"Starting FFmpeg conversion for {filename}")
        try:
            process = subprocess.run(ffmpeg_cmd, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            if process.returncode != 0:
                error_msg = process.stderr.decode('utf-8', errors='replace')
                logger.error(f"FFmpeg conversion failed with code {process.returncode}: {error_msg}")
                
                # Try fallback conversion with simpler parameters but still high quality
                logger.info("Attempting fallback conversion with simpler parameters")
                fallback_cmd = [
                    'ffmpeg', '-y',
                    '-i', input_path,
                    '-c:v', 'libx264',
                    '-crf', '23',  # Still good quality
                    '-preset', 'medium',
                    '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-f', 'hls',
                    '-hls_time', '4',
                    '-hls_list_size', '0',
                    '-hls_segment_filename', f"{output_path}/segment_%03d.ts",
                    '-start_number', '0',
                    hls_playlist
                ]
                
                fallback_process = subprocess.run(fallback_cmd, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                if fallback_process.returncode != 0:
                    fallback_error = fallback_process.stderr.decode('utf-8', errors='replace')
                    logger.error(f"Fallback FFmpeg conversion also failed: {fallback_error}")
                    raise HTTPException(status_code=500, detail=f"Failed to convert video to HLS format: {error_msg[:200]}")
                else:
                    logger.info(f"Fallback conversion successful for {filename}")
            else:
                logger.info(f"Successfully converted {filename} to HLS format")
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode('utf-8', errors='replace') if e.stderr else str(e)
            logger.error(f"FFmpeg conversion failed: {error_output}")
            raise HTTPException(status_code=500, detail=f"Failed to convert video to HLS format: {error_output[:300]}")
        except Exception as e:
            logger.error(f"Unexpected error during video conversion: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Video conversion error: {str(e)}")
        
        # S3 prefix for this video
        s3_prefix = f"{HLS_FOLDER}{video_id}/"
        
        # Count files to upload
        file_count = sum(len(files) for _, _, files in os.walk(output_path))
        logger.info(f"Uploading {file_count} HLS files to S3")
        
        # Upload all HLS files to S3
        uploaded_count = 0
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
                    uploaded_count += 1
                    if uploaded_count % 10 == 0 or uploaded_count == file_count:
                        logger.info(f"Uploaded {uploaded_count}/{file_count} files to S3")
                except ClientError as e:
                    logger.error(f"Error uploading {s3_key} to S3: {e}")
                    raise HTTPException(status_code=500, detail="Failed to upload HLS files to S3")
        
        # Return the URL to the HLS playlist
        url = f"https://{S3_BUCKET}.s3.eu-north-1.amazonaws.com/{s3_prefix}index.m3u8"
        logger.info(f"HLS conversion and upload complete. URL: {url}")
        return url

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