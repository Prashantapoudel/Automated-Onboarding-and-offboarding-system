import boto3
import os
from dotenv import load_dotenv

load_dotenv() 
# Load environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_REGION = os.getenv("AWS_S3_REGION")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")

# Check if bucket name is correctly loaded
if not AWS_S3_BUCKET_NAME:
    raise ValueError("❌ ERROR: AWS_S3_BUCKET_NAME is not set in environment variables!")

# Initialize S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION
)

# Upload File
file_name = "test.txt"
s3_client.upload_file(file_name, AWS_S3_BUCKET_NAME, file_name)


print(f"✅ File {file_name} uploaded successfully to {AWS_S3_BUCKET_NAME}")
