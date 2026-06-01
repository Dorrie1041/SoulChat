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
from PIL import Image as PILImage
from io import BytesIO
from sqlalchemy import text

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

router = APIRouter(prefix="/images", tags=["images"])


storage_client = storage.Client()
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "soulchat-images")


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
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
        storage_path = f"images/{current_user['user_id']}/{unique_filename}"
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE / (1024 * 1024)} MB"
            )
        
        # Get bucket and upload file
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(storage_path)
        blob.upload_from_string(
            file_content,
            content_type=file.content_type
        )
        
        # Make blob publicly accessible (optional, depending on your needs)
        # blob.make_public()
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{storage_path}"
        
        # Here you could add image processing to get width and height
        # PIL/Pillow
        image = PILImage.open(BytesIO(file_content))
        width, height = image.size
        
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
            uploaded_by_user_id=current_user["user_id"]
        )
        
        db.execute(
            text("""
                INSERT INTO images (
                    image_id,
                    storage_path,
                    public_url,
                    mime_type,
                    file_size,
                    width,
                    height,
                    uploaded_by_user_id,
                    created_at
                )
                VALUES (
                    :image_id,
                    :storage_path,
                    :public_url,
                    :mime_type,
                    :file_size,
                    :width,
                    :height,
                    :uploaded_by_user_id,
                    NOW()
                )
            """),
            {
                "image_id": image_id,
                "storage_path": storage_path,
                "public_url": public_url,
                "mime_type": file.content_type,
                "file_size": file_size,
                "width": width,
                "height": height,
                "uploaded_by_user_id": current_user["user_id"],
            },
        )
        db.commit()
        
        response = ImageUploadResponse(
            image_id=image_id,
            storage_path=storage_path,
            public_url=public_url,
            mime_type=file.content_type,
            file_size=file_size,
            width=width,
            height=height,
            uploaded_by_user_id=current_user["user_id"]
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image: {str(e)}"
        )

@router.get("", response_model=list[ImageItemResponse])
def get_all_images(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    rows = db.execute(
        text("""
            SELECT
                image_id,
                storage_path,
                public_url,
                mime_type,
                file_size,
                width,
                height,
                uploaded_by_user_id,
                created_at
            FROM images
            WHERE uploaded_by_user_id = :user_id
            ORDER BY created_at DESC
        """),
        {
            "user_id": current_user["user_id"],
        }
    ).fetchall()

    images = []

    for row in rows:
        images.append({
            "image_id": row[0],
            "storage_path": row[1],
            "public_url": row[2],
            "mime_type": row[3],
            "file_size": row[4],
            "width": row[5],
            "height": row[6],
            "uploaded_by_user_id": row[7],
            "created_at": row[8] if row[8] else None
        })
    return images

@router.get("/{image_id}", response_model=ImageItemResponse)
async def get_image(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    row = db.execute(
        text("""
            SELECT
                image_id,
                storage_path,
                public_url,
                mime_type,
                file_size,
                width,
                height,
                uploaded_by_user_id,
                created_at
            FROM images
            WHERE image_id = :image_id
            LIMIT 1 
        """),
        {
            "image_id": image_id,
        }
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Image not found")
    
    if str(row[7]) != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this image")
    
    return ImageItemResponse(
        image_id=row[0],
        storage_path=row[1],
        public_url=row[2],
        mime_type=row[3],
        file_size=row[4],
        width=row[5],
        height=row[6],
        uploaded_by_user_id=row[7] if row[7] else None,
        created_at=row[8] if row[8] else None
    )

@router.delete("/{image_id}")
async def delete_image(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    row = db.execute(
        text("""
            SELECT
                storage_path,
                uploaded_by_user_id
            FROM images
            WHERE image_id = :image_id
            LIMIT 1
        """),
        {
            "image_id": image_id,
        }
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Image not found")
    
    storage_path, uploaded_by_user_id = row[0], str(row[1])

    if uploaded_by_user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this image")
    
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(storage_path)
        blob.delete()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image from storage: {str(e)}")
    
    db.execute(
        text("""
            DELETE FROM images
            WHERE image_id = :image_id
        """),
        {
            "image_id": image_id,
        }
    )
    db.commit()

    return {
        "message": "Image deleted successfully",
        "image_id": image_id,
    }

    

