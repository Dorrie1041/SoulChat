from fastapi import HTTPException, APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import get_db
from app.security import get_current_user
from google.cloud import storage
import os

router = APIRouter(prefix="/admin", tags=["admin"])

storage_client = storage.Client()
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "soulchat-images")

def require_admin(current_user: dict):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
@router.get("/users")
def list_all_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),

): 
    require_admin(current_user)
    
    rows = db.execute(
        text("""
             SELECT id, username, email, role, created_at 
             FROM users
             ORDER BY created_at DESC
             """)
    ).fetchall()

    return [
        {
            "user_id": str(r[0]),
            "username": r[1],
            "email": r[2],
            "role": r[3],
            "created_at": str(r[4]) if r[4] else None,
        }
        for r in rows
    ]

@router.delete("/users/{user_id}")
def admin_delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
): 
    require_admin(current_user)

    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = db.execute(
        text("""
            SELECT user_id
            FROM users
            WHERE user_id = :user_id
            LIMIT 1
        """),
        {"user_id": user_id}
    ).fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    image_rows = db.execute(
        text("""
            SELECT storage_path
            FROM images            
            WHERE uploaded_by_user_id = :user_id
        """),
        {"user_id": user_id}
    ).fetchall()

    conversation_rows = db.execute(
        text("""
            SELECT conversation_id
            FROM conversations            
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    ).fetchall()

    conversation_ids = [str(r[0]) for r in conversation_rows]

    for conversation_id in conversation_ids:
        db.execute(
            text("""
                DELETE FROM messages
                WHERE conversation_id = :conversation_id
            """),
            {"conversation_id": conversation_id}
        )

    db.execute(
        text("""
            DELETE FROM conversations
            WHERE user_id = :user_id
            """),
            {"user_id": user_id}
    )

    db.execute(
        text("""
            DELETE FROM character_meories
            WHERE user_id = :user_id
            """),
            {"user_id": user_id}
    )

    db.execute(
        text("""
            DELETE FROM relationship_state
            WHERE user_id = :user_id
            """),
            {"user_id": user_id},
    )

    db.execute(
        text("""
            DELETE FROM characters
            WHERE creator_user_id = :user_id
            """),
            {"user_id": user_id}
        )
    
    db.execute(
        text("""
            DELETE FROM images
            WHERE uploaded_by_user_id = :user_id
            """),
            {"user_id": user_id}
        )
    
    db.execute(
        text("""
            DELETE FROM user_profiles
            WHERE user_id = :user_id
            """),
            {"user_id": user_id}
    )

    db.execute(
        text("""
            DELETE FROM users
            WHERE user_id = :user_id
            """),
            {"user_id": user_id}
    )

    db.commit()

    deleted_gcs_count = 0
    failed_gcs_count = 0
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        
        for row in image_rows:
            storage_path = row[0]
            try:
                blob = bucket.blob(storage_path)
                if blob.exists():
                    blob.delete()
                    deleted_gcs_count += 1
            except Exception as e:
                failed_gcs_count += 1
                print(f"Failed to delete GCS object {storage_path}: {str(e)}")
    except Exception as e:
        failed_gcs_count += len(image_rows)
        print(f"Failed to access GCS bucket: {str(e)}")
    return {
        "message": "User deleted successfully",
        "user_id": user_id,
        "deleted_gcs_images": deleted_gcs_count,
        "failed_gcs_deletions": failed_gcs_count,
    }

@router.get("/images")
def list_all_images(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
): 
    require_admin(current_user)
    
    rows = db.execute(
        text("""
             SELECT image_id, storage_path, public_url, uploaded_by_user_id, created_at
             FROM images
             ORDER BY created_at DESC
             """)
    ).fetchall()

    return [
        {
            "image_id": str(r[0]),
            "storage_path": r[1],
            "public_url": r[2],
            "uploaded_by_user_id": str(r[3]),
            "created_at": str(r[4]) if r[4] else None,
        }
        for r in rows
    ]

@router.get("/characters")
def list_all_characters(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
): 
    require_admin(current_user)
    
    rows = db.execute(
        text("""
             SELECT character_id, character_name, creator_user_id, is_public, created_at
             FROM characters
             ORDER BY created_at DESC
             """)
    ).fetchall()

    return [
        {
            "character_id": str(r[0]),
            "character_name": r[1],
            "creator_user_id": str(r[2]),
            "is_public": r[3],
            "created_at": str(r[4]) if r[4] else None,
        }
        for r in rows
    ]