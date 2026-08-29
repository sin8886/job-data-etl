import logging
import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_s3_client():
    """Create and return an S3 client."""
    aws_region = os.getenv("AWS_REGION")

    if not aws_region:
        raise ValueError("AWS_REGION is not configured")

    return boto3.client(
        "s3",
        region_name=aws_region,
    )


def get_bucket_name():
    """Get the S3 bucket name from environment variables."""
    bucket_name = os.getenv("S3_BUCKET_NAME")

    if not bucket_name:
        raise ValueError("S3_BUCKET_NAME is not configured")

    return bucket_name


def upload_file(local_path, s3_key):
    """Upload a local file to S3."""
    local_path = Path(local_path)

    if not local_path.exists():
        raise FileNotFoundError(f"Local file not found: {local_path}")

    bucket_name = get_bucket_name()
    s3 = get_s3_client()

    logger.info(
        "Uploading file to S3: local=%s bucket=%s key=%s",
        local_path,
        bucket_name,
        s3_key,
    )

    s3.upload_file(
        str(local_path),
        bucket_name,
        s3_key,
    )

    logger.info(
        "Upload completed: s3://%s/%s",
        bucket_name,
        s3_key,
    )
