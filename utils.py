"""
CloudNexus API - AWS Utilities
S3 upload, backup logic, and helper functions using boto3.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, BinaryIO, List, Dict, Any

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging for CloudWatch
logger = logging.getLogger(__name__)


# =============================================================================
# AWS CONFIGURATION
# =============================================================================

def get_s3_client():
    """
    Get boto3 S3 client with proper configuration.
    
    Returns:
        boto3 S3 client
    """
    region = os.environ.get("AWS_REGION", "us-east-1")
    
    return boto3.client(
        "s3",
        region_name=region
    )


def get_s3_bucket() -> str:
    """Get S3 bucket name from environment variable."""
    bucket = os.environ.get("S3_BUCKET")
    if not bucket:
        raise ValueError("S3_BUCKET environment variable is not set")
    return bucket


# =============================================================================
# S3 UPLOAD FUNCTIONS
# =============================================================================

def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename to prevent collisions.
    
    Args:
        original_filename: Original name of the uploaded file
        
    Returns:
        Unique filename with UUID prefix
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    # Extract file extension
    if "." in original_filename:
        name, ext = original_filename.rsplit(".", 1)
        return f"{timestamp}_{unique_id}_{name}.{ext}"
    
    return f"{timestamp}_{unique_id}_{original_filename}"


def upload_file_to_s3(
    file_content: BinaryIO,
    original_filename: str,
    content_type: Optional[str] = None,
    prefix: str = "uploads"
) -> Dict[str, Any]:
    """
    Upload a file to S3 bucket.
    
    Args:
        file_content: File-like object with file content
        original_filename: Original filename from upload
        content_type: MIME type of the file (optional)
        prefix: S3 key prefix (folder path)
        
    Returns:
        dict: Upload result with S3 URL and metadata
        
    Raises:
        ValueError: If S3 bucket is not configured
        ClientError: If S3 upload fails
    """
    s3_client = get_s3_client()
    bucket = get_s3_bucket()
    
    # Generate unique filename
    unique_filename = generate_unique_filename(original_filename)
    s3_key = f"{prefix}/{unique_filename}"
    
    # Prepare upload parameters
    upload_params = {
        "Bucket": bucket,
        "Key": s3_key,
        "Body": file_content
    }
    
    # Add content type if provided
    if content_type:
        upload_params["ContentType"] = content_type
    
    try:
        logger.info(f"Uploading file to S3: {s3_key}")
        
        s3_client.upload_fileobj(**upload_params)
        
        # Construct S3 URL
        region = os.environ.get("AWS_REGION", "us-east-1")
        s3_url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
        
        logger.info(f"File uploaded successfully: {s3_url}")
        
        return {
            "success": True,
            "s3_key": s3_key,
            "s3_url": s3_url,
            "bucket": bucket,
            "original_filename": original_filename,
            "unique_filename": unique_filename,
            "content_type": content_type
        }
        
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        raise ValueError("AWS credentials are not configured")
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        
        logger.error(f"S3 upload failed: {error_code} - {error_message}")
        raise


def delete_file_from_s3(s3_key: str) -> bool:
    """
    Delete a file from S3 bucket.
    
    Args:
        s3_key: S3 object key to delete
        
    Returns:
        bool: True if deletion successful
    """
    s3_client = get_s3_client()
    bucket = get_s3_bucket()
    
    try:
        s3_client.delete_object(Bucket=bucket, Key=s3_key)
        logger.info(f"File deleted from S3: {s3_key}")
        return True
        
    except ClientError as e:
        logger.error(f"Failed to delete file from S3: {str(e)}")
        raise


# =============================================================================
# BACKUP FUNCTIONS
# =============================================================================

def create_backup(data: List[Dict[str, Any]], table_name: str = "tasks") -> Dict[str, Any]:
    """
    Create a backup of database data and save to S3.
    
    Converts data to JSON format and uploads to the /backups prefix.
    
    Args:
        data: List of dictionaries to backup
        table_name: Name of the table being backed up
        
    Returns:
        dict: Backup result with S3 URL and metadata
    """
    s3_client = get_s3_client()
    bucket = get_s3_bucket()
    
    # Generate backup filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{table_name}_backup_{timestamp}.json"
    s3_key = f"backups/{backup_filename}"
    
    # Prepare backup data with metadata
    backup_content = {
        "backup_timestamp": datetime.utcnow().isoformat(),
        "table_name": table_name,
        "record_count": len(data),
        "data": data
    }
    
    # Convert to JSON
    json_content = json.dumps(backup_content, indent=2, default=str)
    
    try:
        logger.info(f"Creating backup: {s3_key} ({len(data)} records)")
        
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=json_content.encode("utf-8"),
            ContentType="application/json"
        )
        
        # Construct S3 URL
        region = os.environ.get("AWS_REGION", "us-east-1")
        s3_url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
        
        logger.info(f"Backup created successfully: {s3_url}")
        
        return {
            "success": True,
            "s3_key": s3_key,
            "s3_url": s3_url,
            "bucket": bucket,
            "backup_filename": backup_filename,
            "table_name": table_name,
            "record_count": len(data),
            "backup_timestamp": backup_content["backup_timestamp"]
        }
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        
        logger.error(f"Backup creation failed: {error_code} - {error_message}")
        raise


def list_backups(max_items: int = 100) -> List[Dict[str, Any]]:
    """
    List all backup files in S3.
    
    Args:
        max_items: Maximum number of backups to return
        
    Returns:
        List of backup file metadata
    """
    s3_client = get_s3_client()
    bucket = get_s3_bucket()
    
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix="backups/",
            MaxKeys=max_items
        )
        
        backups = []
        for obj in response.get("Contents", []):
            backups.append({
                "key": obj["Key"],
                "size_bytes": obj["Size"],
                "last_modified": obj["LastModified"].isoformat()
            })
        
        return sorted(backups, key=lambda x: x["last_modified"], reverse=True)
        
    except ClientError as e:
        logger.error(f"Failed to list backups: {str(e)}")
        raise


# =============================================================================
# LOGGING UTILITIES
# =============================================================================

def setup_cloudwatch_logging(log_level: str = "INFO"):
    """
    Configure structured logging for AWS CloudWatch.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Set up root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Reduce noise from boto3 and botocore
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger.info("CloudWatch logging configured")


def log_request(method: str, path: str, status_code: int, duration_ms: float):
    """
    Log API request for CloudWatch metrics.
    
    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    """
    logger.info(
        f"API Request | method={method} | path={path} | "
        f"status={status_code} | duration_ms={duration_ms:.2f}"
    )
