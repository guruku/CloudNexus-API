"""
CloudNexus API - FastAPI Backend for AWS Lambda
Main application entry point with routes and Mangum handler.
"""

import os
import time
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from mangum import Mangum
from sqlalchemy.orm import Session

from database import get_db, Task, init_db, test_db_connection
from utils import (
    upload_file_to_s3,
    create_backup,
    setup_cloudwatch_logging,
    log_request
)

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Initialize CloudWatch logging
setup_cloudwatch_logging(os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="CloudNexus API",
    description="Robust Python Backend API for Mobile Applications on AWS Lambda",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware - Enable for mobile/web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# PYDANTIC MODELS (Request/Response Schemas)
# =============================================================================

class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: str = Field("pending", description="Task status: pending, in_progress, completed")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Complete project documentation",
                "description": "Write comprehensive API documentation",
                "status": "pending"
            }
        }


class TaskResponse(BaseModel):
    """Schema for task response."""
    id: int
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: str
    database: dict
    version: str


class UploadResponse(BaseModel):
    """Schema for file upload response."""
    success: bool
    s3_url: str
    original_filename: str
    message: str


class BackupResponse(BaseModel):
    """Schema for backup response."""
    success: bool
    s3_url: str
    record_count: int
    backup_timestamp: str
    message: str


# =============================================================================
# LIFECYCLE EVENTS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize resources on application startup."""
    logger.info("CloudNexus API starting up...")
    
    # Initialize database tables (optional - can be done separately)
    try:
        init_db()
        logger.info("Database initialization complete")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on application shutdown."""
    logger.info("CloudNexus API shutting down...")


# =============================================================================
# API ROUTES
# =============================================================================

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check API and database health"
)
async def health_check():
    """
    Health check endpoint.
    
    Returns API status and tests RDS database connectivity.
    Useful for load balancer health checks and monitoring.
    """
    start_time = time.time()
    
    # Test database connection
    db_status = test_db_connection()
    
    response = {
        "status": "healthy" if db_status["status"] == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "version": "1.0.0"
    }
    
    duration_ms = (time.time() - start_time) * 1000
    log_request("GET", "/health", 200, duration_ms)
    
    return response


# -----------------------------------------------------------------------------
# Items (Tasks) CRUD
# -----------------------------------------------------------------------------

@app.get(
    "/items",
    response_model=List[TaskResponse],
    tags=["Items"],
    summary="Fetch all tasks"
)
async def get_items(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    Fetch all task records from the database.
    
    Supports pagination and optional status filtering.
    """
    start_time = time.time()
    
    try:
        query = db.query(Task).filter(Task.is_active == True)
        
        if status:
            query = query.filter(Task.status == status)
        
        tasks = query.offset(skip).limit(limit).all()
        
        duration_ms = (time.time() - start_time) * 1000
        log_request("GET", "/items", 200, duration_ms)
        
        return tasks
        
    except Exception as e:
        logger.error(f"Error fetching items: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch items: {str(e)}"
        )


@app.post(
    "/items",
    response_model=TaskResponse,
    status_code=201,
    tags=["Items"],
    summary="Create a new task"
)
async def create_item(
    task: TaskCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new task record in the database.
    
    Returns the created task with its assigned ID.
    """
    start_time = time.time()
    
    try:
        # Validate status
        valid_statuses = ["pending", "in_progress", "completed"]
        if task.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Create new task
        db_task = Task(
            title=task.title,
            description=task.description,
            status=task.status
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        duration_ms = (time.time() - start_time) * 1000
        log_request("POST", "/items", 201, duration_ms)
        
        logger.info(f"Created new task: id={db_task.id}, title={db_task.title}")
        
        return db_task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create item: {str(e)}"
        )


@app.get(
    "/items/{item_id}",
    response_model=TaskResponse,
    tags=["Items"],
    summary="Get a specific task"
)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """
    Fetch a specific task by ID.
    """
    task = db.query(Task).filter(Task.id == item_id, Task.is_active == True).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


# -----------------------------------------------------------------------------
# File Upload
# -----------------------------------------------------------------------------

@app.post(
    "/upload",
    response_model=UploadResponse,
    tags=["Storage"],
    summary="Upload a file to S3"
)
async def upload_file(
    file: UploadFile = File(..., description="File to upload")
):
    """
    Upload a file to S3 bucket.
    
    Receives a file via multipart/form-data and uploads it to the configured
    S3 bucket. Returns the S3 object URL for accessing the file.
    """
    start_time = time.time()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is 10MB"
            )
        
        # Upload to S3
        from io import BytesIO
        result = upload_file_to_s3(
            file_content=BytesIO(file_content),
            original_filename=file.filename,
            content_type=file.content_type
        )
        
        duration_ms = (time.time() - start_time) * 1000
        log_request("POST", "/upload", 200, duration_ms)
        
        return UploadResponse(
            success=True,
            s3_url=result["s3_url"],
            original_filename=file.filename,
            message="File uploaded successfully"
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Configuration error during upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )


# -----------------------------------------------------------------------------
# Backup System
# -----------------------------------------------------------------------------

@app.post(
    "/backup",
    response_model=BackupResponse,
    tags=["Backup"],
    summary="Trigger manual backup"
)
async def trigger_backup(
    db: Session = Depends(get_db)
):
    """
    Trigger a manual backup of the tasks table.
    
    Queries all active tasks, converts the data to JSON, and saves it
    as a .json file in the /backups prefix of the S3 bucket.
    """
    start_time = time.time()
    
    try:
        # Query all active tasks
        tasks = db.query(Task).filter(Task.is_active == True).all()
        
        # Convert to list of dictionaries
        tasks_data = [task.to_dict() for task in tasks]
        
        # Create backup in S3
        result = create_backup(data=tasks_data, table_name="tasks")
        
        duration_ms = (time.time() - start_time) * 1000
        log_request("POST", "/backup", 200, duration_ms)
        
        logger.info(
            f"Backup created successfully: {result['s3_url']} "
            f"({result['record_count']} records)"
        )
        
        return BackupResponse(
            success=True,
            s3_url=result["s3_url"],
            record_count=result["record_count"],
            backup_timestamp=result["backup_timestamp"],
            message="Backup created successfully"
        )
        
    except ValueError as e:
        logger.error(f"Configuration error during backup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create backup: {str(e)}"
        )


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc) if os.environ.get("DEBUG", "false").lower() == "true" else None
        }
    )


# =============================================================================
# MANGUM HANDLER (AWS Lambda)
# =============================================================================

# Create Mangum handler for AWS Lambda
handler = Mangum(app, lifespan="off")


# =============================================================================
# LOCAL DEVELOPMENT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
