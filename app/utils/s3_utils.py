import boto3
import os

AWS_ACCESS_KEY = "AKIA3RYC52TMTL26Q2CJ"
AWS_SECRET_KEY = "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"
S3_BUCKET = "mypov-videos"

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name="eu-north-1"
)

def upload_to_s3(file_path: str, file_name: str) -> str:
    if not S3_BUCKET:
        raise ValueError("S3_BUCKET is not defined. Check your environment variables.")
    print(f"https://{S3_BUCKET}.s3.eu-north-1.amazonaws.com/{file_name}")
    s3_client.upload_file(file_path, S3_BUCKET, file_name)
    
    return f"https://{S3_BUCKET}.s3.eu-north-1.amazonaws.com/{file_name}"