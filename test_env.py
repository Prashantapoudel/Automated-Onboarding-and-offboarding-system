import os

AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")

if AWS_S3_BUCKET_NAME:
    print(f"✅ AWS_S3_BUCKET_NAME: {AWS_S3_BUCKET_NAME}")
else:
    print("❌ ERROR: AWS_S3_BUCKET_NAME is NOT set!")
