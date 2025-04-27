import os
import boto3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create S3 clients for all configured AWS buckets
def create_s3_client(access_key_env, secret_key_env, region_env):
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv(access_key_env),
        aws_secret_access_key=os.getenv(secret_key_env),
        region_name=os.getenv(region_env)
    )

# S3 Clients and Buckets
aws_clients_info = {
    "Admin/IT Offboarding": {
        "client": create_s3_client("AWS_OFFBOARDING_ACCESS_KEY", "AWS_OFFBOARDING_SECRET_KEY", "AWS_S3_REGION"),
        "bucket": os.getenv("AWS_OFFBOARDING_BUCKET")
    },
    "Onboarding": {
        "client": create_s3_client("AWS_ONBOARDING_ACCESS_KEY", "AWS_ONBOARDING_SECRET_KEY", "AWS_S3_REGION"),
        "bucket": os.getenv("AWS_ONBOARDING_BUCKET")
    },
    "User Offboarding": {
        "client": create_s3_client("AWS_OFFBOARDING_USER_ACCESS_KEY", "AWS_OFFBOARDING_USER_SECRET_KEY", "AWS_S3_REGION"),
        "bucket": os.getenv("AWS_OFFBOARDING_USER_BUCKET")
    }
}

# Function to test all AWS configurations
def test_all_aws_connections():
    results = {}
    for name, config in aws_clients_info.items():
        try:
            config["client"].list_objects_v2(Bucket=config["bucket"])
            results[name] = f" Connected to bucket: {config['bucket']}"
        except Exception as e:
            results[name] = f" Failed to connect to bucket: {config['bucket']} - Error: {str(e)}"
    return results

# Save results to file
results = test_all_aws_connections()
with open("aws_s3_config_test_results.txt", "w") as f:
    for name, result in results.items():
        f.write(f"{name}: {result}\n")

print("Test completed. Results saved to aws_s3_config_test_results.txt")
