"""
Object-storage helper.
Uploads binary data to S3 (if configured) or saves to a local directory.
Returns a public-facing URL.
"""
import os
import uuid
import logging
from typing import Optional

logger = logging.getLogger(__name__)

S3_BUCKET        = os.getenv("S3_BUCKET", "")
S3_REGION        = os.getenv("S3_REGION", "us-east-1")
AWS_ACCESS_KEY   = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_KEY   = os.getenv("AWS_SECRET_ACCESS_KEY", "")
LOCAL_ASSET_DIR  = os.getenv("LOCAL_ASSET_DIR", "assets")
API_BASE_URL     = os.getenv("API_BASE_URL", "http://localhost:8000")

os.makedirs(LOCAL_ASSET_DIR, exist_ok=True)


async def upload_asset(
    data: bytes,
    filename: str,
    content_type: str = "image/png",
    subfolder: str = "generated",
) -> str:
    """
    Upload raw bytes and return a URL.
    Uses S3 when S3_BUCKET is set, otherwise falls back to local disk.
    """
    if S3_BUCKET and AWS_ACCESS_KEY and AWS_SECRET_KEY:
        return await _upload_s3(data, filename, content_type, subfolder)
    return _save_local(data, filename, subfolder)


async def _upload_s3(
    data: bytes,
    filename: str,
    content_type: str,
    subfolder: str,
) -> str:
    try:
        import boto3

        key = f"{subfolder}/{filename}"
        s3 = boto3.client(
            "s3",
            region_name=S3_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
        )
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=data,
            ContentType=content_type,
            ACL="public-read",
        )
        url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{key}"
        logger.info("Uploaded to S3: %s", url)
        return url
    except Exception as exc:
        logger.error("S3 upload failed, falling back to local: %s", exc)
        return _save_local(data, filename, subfolder)


def _save_local(data: bytes, filename: str, subfolder: str) -> str:
    folder = os.path.join(LOCAL_ASSET_DIR, subfolder)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, "wb") as f:
        f.write(data)
    url = f"{API_BASE_URL}/static/{subfolder}/{filename}"
    logger.info("Saved locally: %s", path)
    return url


def unique_filename(ext: str = "png") -> str:
    return f"{uuid.uuid4().hex}.{ext}"
