import boto3
import os
from botocore.exceptions import ClientError
import logging
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

AWS_ACCESS_KEY = "AKIA3RYC52TMTL26Q2CJ"
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

def upload_to_s3(file_path: str, file_name: str) -> str:
    if not S3_BUCKET:
        raise ValueError("S3_BUCKET is not defined. Check your environment variables.")
    print(f"https://{S3_BUCKET}.s3.eu-north-1.amazonaws.com/{file_name}")
    s3_client.upload_file(file_path, S3_BUCKET, file_name)
    
    return f"https://{S3_BUCKET}.s3.eu-north-1.amazonaws.com/{file_name}"

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