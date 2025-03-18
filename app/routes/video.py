from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form, Query, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.crud import (
    create_video, get_video, list_videos, video_views_increment, 
    video_likes_increment, video_dislikes_increment, video_subscribers_increment, 
    search_videos, save_video_for_user, unsave_video_for_user, 
    get_saved_videos_for_user, check_video_saved, delete_video
)
from app.utils.s3_utils import upload_to_s3
from app.schemas import VideoCreate, VideoResponse
from app.routes.user import get_current_user
from app.models import User
from typing import List, Optional
from uuid import UUID

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/videos/", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
def upload_video(
    title: str = Form(...),
    description: str = Form(...),
    vfile: UploadFile = File(...),
    tfile: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    video = {"title": title, "description": description}
    print(tfile.filename)
    vfile_path = f"C:\\mobileapp\\myapp\\backend\\tmp\\{vfile.filename}"
    with open(vfile_path, "wb") as buffer:
        buffer.write(vfile.file.read())
    vfile_url = upload_to_s3(vfile_path, vfile.filename)
    tfile_path = f"C:\\mobileapp\\myapp\\backend\\tmp\\{tfile.filename}"
    with open(tfile_path, "wb") as buffer:
        buffer.write(tfile.file.read())
    tfile_url = upload_to_s3(tfile_path, tfile.filename)
    return create_video(db, video, vfile_url, tfile_url, str(current_user.user_id))

@router.get("/videos/search", response_model=List[VideoResponse])
def search_videos_api(
    q: str = Query(..., description="Search query string"),
    type: Optional[str] = Query(None, description="Search type (e.g., 'hashtag')"),
    db: Session = Depends(get_db)
):
    """
    Search for videos based on query string.
    If type is 'hashtag', searches in hashtags only.
    """
    try:
        videos = search_videos(db, q)
        return videos
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching videos: {str(e)}"
        )

@router.get("/videos/", response_model=List[VideoResponse])
def read_videos(db: Session = Depends(get_db)):
    return list_videos(db)

@router.get("/videos/saved", response_model=List[VideoResponse])
def get_user_saved_videos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all videos saved by the current user
    """
    # Get the saved videos for the user
    saved_videos = get_saved_videos_for_user(db, str(current_user.user_id))
    return saved_videos

@router.get("/videos/{video_id}", response_model=VideoResponse)
def read_video(video_id: UUID, db: Session = Depends(get_db)):
    db_video = get_video(db, str(video_id))
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found")
    return db_video

@router.post("/videos/{video_id}/view")
def increment_video_views(video_id: str, db: Session = Depends(get_db)):
    # Fetch the video by ID
    views = video_views_increment(db,video_id=video_id)
    return {"message": "View count incremented successfully", "views": views}

@router.post("/videos/{video_id}/like")
def increment_video_views(video_id: str, db: Session = Depends(get_db)):
    # Fetch the video by ID
    likes = video_likes_increment(db,video_id=video_id)
    return {"message": "View count incremented successfully", "likes": likes}

@router.post("/videos/{video_id}/dislike")
def increment_video_views(video_id: str, db: Session = Depends(get_db)):
    # Fetch the video by ID
    dislikes = video_dislikes_increment(db,video_id=video_id)
    return {"message": "View count incremented successfully", "dislikes": dislikes}

@router.post("/videos/{video_id}/subscribe")
def increment_video_subscribers(video_id: str, db: Session = Depends(get_db)):
    # Fetch the video by ID
    db_video = get_video(db, video_id)
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video_subscribers_increment(db, video_id)

# New routes for saved videos

@router.post("/videos/{video_id}/save", status_code=status.HTTP_201_CREATED)
def save_video(
    video_id: str, 
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a video for the current user"""
    # Check if video exists
    db_video = get_video(db, video_id)
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Save the video
    saved_video = save_video_for_user(db, str(current_user.user_id), video_id)
    return {"message": "Video saved successfully"}

@router.delete("/videos/{video_id}/save", status_code=status.HTTP_200_OK)
def unsave_video(
    video_id: str, 
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unsave a video for the current user"""
    # Check if video exists
    db_video = get_video(db, video_id)
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Unsave the video
    result = unsave_video_for_user(db, str(current_user.user_id), video_id)
    if not result:
        raise HTTPException(status_code=404, detail="Video was not saved")
    
    return {"message": "Video removed from saved videos"}

@router.get("/videos/{video_id}/saved")
def check_if_video_saved(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a video is saved by the current user"""
    # Check if video exists first
    db_video = get_video(db, video_id)
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check if the video is saved
    is_saved = check_video_saved(db, str(current_user.user_id), video_id)
    return {"is_saved": is_saved}

@router.delete("/videos/{video_id}", status_code=status.HTTP_200_OK)
def delete_video_endpoint(
    video_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a video
    
    Only the owner of the video can delete it.
    """
    # Check if video exists first
    db_video = get_video(db, video_id)
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Try to delete the video
    result = delete_video(db, video_id, str(current_user.user_id))
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this video"
        )
    
    return {"message": "Video deleted successfully"}