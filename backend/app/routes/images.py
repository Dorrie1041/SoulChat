from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from google.cloud import storage
import os
import uuid
from datetime import datetime
from typing import Optional
from app.schemas import ImageItemResponse, ImageUploadResponse
from app.security import get_current_user
from app.models import Image
from app.db import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/images", tags=["images"])


storage_client = storage.Client()
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "soulchat-images")


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload an image file to Google Cloud Storage
    
    Args:
        file: Image file to upload
        current_user_id: ID of the user uploading the image
        
    Returns:
        ImageUploadResponse with upload details
    """
    try:
        allowed_mime_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_mime_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(allowed_mime_types)}"
            )
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        storage_path = f"images/{current_user_id}/{unique_filename}"
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Get bucket and upload file
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(storage_path)
        blob.upload_from_string(
            file_content,
            content_type=file.content_type
        )
        
        # Make blob publicly accessible (optional, depending on your needs)
        blob.make_public()
        public_url = blob.public_url
        
        # Here you could add image processing to get width and height
        # For now, we'll set them as None or you could use PIL/Pillow
        width = None
        height = None
        
        image_id = str(uuid.uuid4())
        
        # Save image record to database
        image_record = Image(
            image_id=image_id,
            storage_path=storage_path,
            public_url=public_url,
            mime_type=file.content_type,
            file_size=file_size,
            width=width,
            height=height,
            uploaded_by_user_id=current_user_id
        )
        
        db.add(image_record)
        db.commit()
        db.refresh(image_record)
        
        response = ImageUploadResponse(
            image_id=image_id,
            storage_path=storage_path,
            public_url=public_url,
            mime_type=file.content_type,
            file_size=file_size,
            width=width,
            height=height,
            uploaded_by_user_id=current_user_id
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image: {str(e)}"
        )


@router.get("/{image_id}", response_model=ImageItemResponse)
async def get_image(
    image_id: str,
    db: Session = Depends(get_db),
):
    """
    Get image details by image_id
    
    Args:
        image_id: The ID of the image to retrieve
        db: Database session
        
    Returns:
        ImageItemResponse with image details including created_at
        
    Raises:
        HTTPException: 404 if image not found
    """
    try:
        image = db.query(Image).filter(Image.image_id == image_id).first()
        
        if not image:
            raise HTTPException(
                status_code=404,
                detail=f"Image with id {image_id} not found"
            )
        
        response = ImageItemResponse(
            image_id=image.image_id,
            storage_path=image.storage_path,
            public_url=image.public_url,
            mime_type=image.mime_type,
            file_size=image.file_size,
            width=image.width,
            height=image.height,
            uploaded_by_user_id=image.uploaded_by_user_id,
            created_at=image.created_at.isoformat() if image.created_at else None
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve image: {str(e)}"
        )


@router.delete("/{image_id}")
async def delete_image(
    image_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a specific image by image_id
    
    Args:
        image_id: The ID of the image to delete
        current_user_id: ID of the user requesting deletion
        db: Database session
        
    Returns:
        Message confirming deletion
        
    Raises:
        HTTPException: 404 if image not found, 403 if user doesn't own the image
    """
    try:
        image = db.query(Image).filter(Image.image_id == image_id).first()
        
        if not image:
            raise HTTPException(
                status_code=404,
                detail=f"Image with id {image_id} not found"
            )
        
        # Check if user owns the image
        if image.uploaded_by_user_id != current_user_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this image"
            )
        
        # Delete from Google Cloud Storage
        try:
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(image.storage_path)
            blob.delete()
        except Exception as gcs_error:
            # Log the error but don't fail the delete operation
            print(f"Warning: Failed to delete GCS blob {image.storage_path}: {str(gcs_error)}")
        
        # Delete from database
        db.delete(image)
        db.commit()
        
        return {
            "message": f"Image {image_id} deleted successfully",
            "image_id": image_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete image: {str(e)}"
        )


@router.get("", response_model=list[ImageItemResponse])
async def get_all_images(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """
    Get all images with pagination
    
    Args:
        skip: Number of images to skip (default: 0)
        limit: Maximum number of images to return (default: 10)
        db: Database session
        
    Returns:
        List of ImageItemResponse objects
    """
    try:
        images = db.query(Image).offset(skip).limit(limit).all()
        
        response = []
        for image in images:
            response.append(
                ImageItemResponse(
                    image_id=image.image_id,
                    storage_path=image.storage_path,
                    public_url=image.public_url,
                    mime_type=image.mime_type,
                    file_size=image.file_size,
                    width=image.width,
                    height=image.height,
                    uploaded_by_user_id=image.uploaded_by_user_id,
                    created_at=image.created_at.isoformat() if image.created_at else None
                )
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve images: {str(e)}"
        )

