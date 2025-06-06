from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form, Query, status, Path, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.crud import (
    create_video, get_video, list_videos, video_views_increment, 
    video_likes_increment, video_dislikes_increment, 
    search_videos, save_video_for_user, unsave_video_for_user, 
    get_saved_videos_for_user, check_video_saved, delete_video,
    get_user_videos, get_video_status
)
from app.utils.s3_utils import upload_to_s3, convert_to_hls_and_upload
from app.utils.youtube_utils import download_youtube_clip
from app.schemas import VideoCreate, VideoResponse, VideoStatus
from app.utils.auth import get_current_user, get_current_user_optional
from app.utils.background_tasks import process_video_background, process_youtube_video_background
from app.models import User, Video, WatchHistory, Like
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime
from sqlalchemy import not_
import tempfile
import os
import logging
import subprocess
import uuid

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["videos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define pagination parameters model for better validation
class PaginationParams:
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(20, ge=1, le=100, description="Maximum number of items to return")
    ):
        self.skip = skip
        self.limit = limit

# Search parameters validation model
class SearchParams(BaseModel):
    query: str = Field(..., min_length=1, max_length=100)
    type: str = Field("text", pattern="^(text|hashtag)$")
    
    @validator('query')
    def validate_query(cls, v):
        if v.strip() == "":
            raise ValueError("Search query cannot be empty or just whitespace")
        return v

@router.post("/videos/", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
def upload_video(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str = Form(...),
    vfile: UploadFile = File(...),
    tfile: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a new video with background processing.
    
    The video will be immediately accepted and processing will happen in the background.
    Use the /videos/{video_id}/status endpoint to check processing status.
    
    - **title**: Title of the video
    - **description**: Description of the video
    - **vfile**: Video file to upload
    - **tfile**: Thumbnail image for the video
    """
    try:
        # Check upload permission
        if not current_user.uploadFlag:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to upload videos"
            )
        
        # Create video entry in database with processing status
        video_data = {"title": title, "description": description}
        db_video = create_video(
            db, 
            video_data, 
            "processing",  # Temporary placeholder URL
            "processing",  # Temporary placeholder URL
            str(current_user.user_id),
            status='processing'
        )
        
        # Save uploaded files to temporary location for background processing
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        # Save video file
        video_path = os.path.join(temp_dir, f"{db_video.video_id}_{vfile.filename}")
        chunk_size = 1024 * 1024  # 1MB chunks
        with open(video_path, "wb") as buffer:
            while True:
                chunk = vfile.file.read(chunk_size)
                if not chunk:
                    break
                buffer.write(chunk)
        
        # Save thumbnail file
        thumbnail_path = os.path.join(temp_dir, f"{db_video.video_id}_{tfile.filename}")
        with open(thumbnail_path, "wb") as buffer:
            while True:
                chunk = tfile.file.read(chunk_size)
                if not chunk:
                    break
                buffer.write(chunk)
        
        # Add background task for video processing
        background_tasks.add_task(
            process_video_background,
            db_video.video_id,
            video_path,
            thumbnail_path,
            vfile.filename,
            tfile.filename
        )
        
        logger.info(f"Video upload accepted for background processing: {db_video.video_id}")
        
        return db_video
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload video: {str(e)}"
        )

@router.get("/videos/{video_id}/status", response_model=VideoStatus)
def get_video_processing_status(
    video_id: UUID = Path(..., description="The UUID of the video to check status"),
    db: Session = Depends(get_db)
):
    """
    Get the processing status of a video.
    
    - **video_id**: UUID of the video to check
    
    Returns:
    - **processing**: Video is being processed
    - **ready**: Video is ready for viewing
    - **failed**: Video processing failed
    - **published**: Video is published and ready
    - **draft**: Video is in draft state
    - **private**: Video is private
    """
    try:
        video_status = get_video_status(db, video_id)
        if video_status is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video with ID {video_id} not found"
            )
        
        return VideoStatus(
            video_id=video_status.video_id,
            status=video_status.status,
            title=video_status.title,
            created_at=video_status.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video status: {str(e)}"
        )

@router.get("/videos/search", response_model=List[VideoResponse])
def search_videos_endpoint(
    q: str = Query(..., min_length=1, description="Search query string"),
    type: str = Query("text", description="Search type: 'text' or 'hashtag'"),
    skip: int = Query(0, ge=0, description="Number of videos to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of videos to return"),
    db: Session = Depends(get_db)
):
    """
    Search for videos by query string.
    
    - **q**: Search query string
    - **type**: Search type ('text' or 'hashtag')
    - **skip**: Number of videos to skip (pagination offset)
    - **limit**: Maximum number of videos to return (pagination limit)
    """
    if not q or q.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query is required and cannot be empty"
        )
    
    if type not in ["text", "hashtag"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search type must be 'text' or 'hashtag'"
        )
    
    try:
        videos = search_videos(db, query=q, skip=skip, limit=limit, search_type=type)
        return videos
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/videos/", response_model=List[VideoResponse])
def read_videos(
    pagination: PaginationParams = Depends(),
    current_user: Optional[User] = Depends(get_current_user_optional),
    user_id: Optional[str] = Query(None, description="Filter videos by user ID"),
    db: Session = Depends(get_db)
):
    """
    Get a personalized list of videos.
    
    - **skip**: Number of videos to skip (pagination offset)
    - **limit**: Maximum number of videos to return (pagination limit)
    - **user_id**: Optional UUID of user to filter videos by (returns only this user's videos)
    
    For authenticated users, returns a personalized feed based on:
    - Watch history
    - Liked videos
    - Followed creators
    - Trending videos
    - New videos
    
    For unauthenticated users, returns trending videos.
    
    If user_id is provided, returns only videos from the specified user.
    """
    try:
        # If user_id is provided in query params, filter by user
        if user_id:
            try:
                videos = get_user_videos(db, user_id, skip=pagination.skip, limit=pagination.limit)
                
                if not videos and not db.query(User).filter(User.user_id == user_id).first():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"User with ID {user_id} not found"
                    )
                    
                return videos
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user ID format"
                )
        
        # Otherwise, use the standard personalized feed logic
        auth_user_id = str(current_user.user_id) if current_user else None
        videos = list_videos(db, skip=pagination.skip, limit=pagination.limit, user_id=auth_user_id)
        return videos
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve videos: {str(e)}"
        )

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
def read_video(
    video_id: UUID = Path(..., description="The UUID of the video to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get a specific video by its ID.
    
    - **video_id**: UUID of the video to retrieve
    """
    try:
        video = get_video(db, video_id)
        if video is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video with ID {video_id} not found"
            )
        return video
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve video: {str(e)}"
        )

@router.post("/videos/{video_id}/view", response_model=dict)
def increment_view(
    video_id: UUID = Path(..., description="The UUID of the video to increment views"),
    db: Session = Depends(get_db)
):
    """
    Increment the view count for a specific video.
    
    - **video_id**: UUID of the video to increment views
    """
    try:
        views = video_views_increment(db, video_id)
        return {"views": views}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to increment view count: {str(e)}"
        )

@router.post("/videos/{video_id}/like", response_model=dict)
def increment_like(
    video_id: UUID = Path(..., description="The UUID of the video to like"),
    db: Session = Depends(get_db)
):
    """
    Increment the like count for a specific video.
    
    - **video_id**: UUID of the video to like
    """
    try:
        likes = video_likes_increment(db, video_id)
        return {"likes": likes}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to increment like count: {str(e)}"
        )

@router.post("/videos/{video_id}/dislike", response_model=dict)
def increment_dislike(
    video_id: UUID = Path(..., description="The UUID of the video to dislike"),
    db: Session = Depends(get_db)
):
    """
    Increment the dislike count for a specific video.
    
    - **video_id**: UUID of the video to dislike
    """
    try:
        dislikes = video_dislikes_increment(db, video_id)
        return {"dislikes": dislikes}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to increment dislike count: {str(e)}"
        )

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
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Check if a video is saved by the current user"""
    # Check if video exists first
    db_video = get_video(db, video_id)
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # If user is not authenticated, video cannot be saved
    if current_user is None:
        return {"is_saved": False}
    
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

@router.get("/search")
def search_videos_route(
    q: str = Query(None, min_length=1, description="Search query string"),
    type: str = Query("text", description="Search type: 'text' or 'hashtag'"),
    skip: int = Query(0, ge=0, description="Number of videos to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of videos to return"),
    db: Session = Depends(get_db)
):
    """
    Search for videos by query string.
    
    - **q**: Search query string
    - **type**: Search type ('text' or 'hashtag')
    - **skip**: Number of videos to skip (pagination offset)
    - **limit**: Maximum number of videos to return (pagination limit)
    """
    if not q:
        raise HTTPException(status_code=400, detail="Search query is required")
    
    videos = search_videos(db, query=q, skip=skip, limit=limit, search_type=type)
    return videos

# Add this schema at an appropriate location
class WatchHistoryCreate(BaseModel):
    video_id: UUID
    watch_time: float
    watch_percentage: float = 0.0
    completed: bool = False
    last_position: float = 0.0
    like_flag: bool = False
    dislike_flag: bool = False
    saved_flag: bool = False
    shared_flag: bool = False
    device_type: Optional[str] = None

class WatchHistoryResponse(BaseModel):
    id: UUID
    video_id: UUID
    user_id: UUID
    watch_time: float
    watch_percentage: float
    completed: bool
    last_position: float
    like_flag: bool
    dislike_flag: bool
    saved_flag: bool
    shared_flag: bool
    watch_count: int
    first_watched_at: datetime
    last_watched_at: datetime
    device_type: Optional[str]

# Add these endpoints
@router.post("/videos/watch-history", response_model=WatchHistoryResponse)
async def update_watch_history(
    watch_data: WatchHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a user's watch history for a video.
    If no record exists for this user-video pair, a new one is created.
    """
    try:
        # Check if the video exists
        video = db.query(Video).filter(Video.video_id == watch_data.video_id).first()
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video with ID {watch_data.video_id} not found"
            )
        
        # Try to get existing watch record
        watch_record = db.query(WatchHistory).filter(
            WatchHistory.user_id == current_user.user_id,
            WatchHistory.video_id == watch_data.video_id
        ).first()
        
        # If no record exists, create a new one
        if not watch_record:
            watch_record = WatchHistory(
                user_id=current_user.user_id,
                video_id=watch_data.video_id,
                watch_time=watch_data.watch_time,
                watch_percentage=watch_data.watch_percentage,
                completed=watch_data.completed,
                last_position=watch_data.last_position,
                like_flag=watch_data.like_flag,
                dislike_flag=watch_data.dislike_flag,
                saved_flag=watch_data.saved_flag,
                shared_flag=watch_data.shared_flag,
                device_type=watch_data.device_type,
                watch_count=1
            )
            db.add(watch_record)
        else:
            # Update existing record with new data
            # Only update watch time if new time is greater
            if watch_data.watch_time > watch_record.watch_time:
                watch_record.watch_time = watch_data.watch_time
            
            # Only update percentage if new percentage is greater
            if watch_data.watch_percentage > watch_record.watch_percentage:
                watch_record.watch_percentage = watch_data.watch_percentage
            
            # Update completion status if completed
            if watch_data.completed and not watch_record.completed:
                watch_record.completed = True
            
            # Always update last position to most recent value
            watch_record.last_position = watch_data.last_position
            
            # Update engagement flags
            watch_record.like_flag = watch_data.like_flag
            watch_record.dislike_flag = watch_data.dislike_flag
            watch_record.saved_flag = watch_data.saved_flag
            watch_record.shared_flag = watch_data.shared_flag
            
            # Update device type if provided
            if watch_data.device_type:
                watch_record.device_type = watch_data.device_type
            
            # Increment watch count
            watch_record.watch_count += 1
            
            # last_watched_at will be updated automatically by the ORM due to onupdate=func.now()
        
        db.commit()
        db.refresh(watch_record)
        
        return watch_record
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update watch history: {str(e)}"
        )

@router.get("/videos/watch-history", response_model=List[WatchHistoryResponse])
async def get_watch_history(
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a user's watch history.
    Returns the most recently watched videos first.
    """
    try:
        history = db.query(WatchHistory).filter(
            WatchHistory.user_id == current_user.user_id
        ).order_by(
            WatchHistory.last_watched_at.desc()
        ).offset(skip).limit(limit).all()
        
        return history
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve watch history: {str(e)}"
        )

@router.get("/videos/{video_id}/watch-stats", response_model=WatchHistoryResponse)
async def get_video_watch_stats(
    video_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a user's watch statistics for a specific video.
    """
    try:
        watch_record = db.query(WatchHistory).filter(
            WatchHistory.user_id == current_user.user_id,
            WatchHistory.video_id == video_id
        ).first()
        
        if not watch_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No watch history found for video with ID {video_id}"
            )
        
        return watch_record
    
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No watch history found for video with ID {video_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve watch statistics: {str(e)}"
        )

@router.delete("/videos/watch-history/{video_id}")
async def delete_watch_history(
    video_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a user's watch history for a specific video.
    """
    try:
        watch_record = db.query(WatchHistory).filter(
            WatchHistory.user_id == current_user.user_id,
            WatchHistory.video_id == video_id
        ).first()
        
        if not watch_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No watch history found for video with ID {video_id}"
            )
        
        db.delete(watch_record)
        db.commit()
        
        return {"message": f"Watch history for video with ID {video_id} deleted successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete watch history: {str(e)}"
        )

@router.post("/videos/youtube", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_youtube_video(
    background_tasks: BackgroundTasks,
    youtube_url: str = Form(..., description="YouTube video URL"),
    title: str = Form(..., description="Video title"),
    description: str = Form(..., description="Video description"),
    start_time: Optional[int] = Form(0, description="Start time in seconds"),
    end_time: Optional[int] = Form(None, description="End time in seconds"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a YouTube video with background processing.
    
    The video will be immediately accepted and processing will happen in the background.
    Use the /videos/{video_id}/status endpoint to check processing status.
    
    - **youtube_url**: URL of the YouTube video
    - **title**: Title for the video
    - **description**: Description for the video
    - **start_time**: Start time in seconds (default: 0)
    - **end_time**: End time in seconds (optional)
    
    Notes:
    - Maximum video duration is 60 seconds
    - If end_time is not provided, it will be set to start_time + 60s or the video end, whichever is earlier
    - YouTube URL will not be stored in the database
    """
    try:
        # Check upload permission
        if not current_user.uploadFlag:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to upload videos"
            )
        
        # Validate inputs
        if not youtube_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="YouTube URL is required"
            )
        
        if start_time < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time cannot be negative"
            )
            
        if end_time is not None and end_time <= start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be greater than start time"
            )
        
        # Create video entry in database with processing status
        video_data = {"title": title, "description": description}
        db_video = create_video(
            db, 
            video_data, 
            "processing",  # Temporary placeholder URL
            "processing",  # Temporary placeholder URL
            str(current_user.user_id),
            status='processing'
        )
        
        # Add background task for YouTube video processing
        background_tasks.add_task(
            process_youtube_video_background,
            db_video.video_id,
            youtube_url,
            title,
            description,
            start_time,
            end_time
        )
        
        logger.info(f"YouTube video upload accepted for background processing: {db_video.video_id}")
        
        return db_video
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing YouTube video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process YouTube video: {str(e)}"
        )

@router.get("/users/{user_id}/videos", response_model=List[VideoResponse])
def get_videos_by_user_id(
    user_id: UUID = Path(..., description="The UUID of the user whose videos to retrieve"),
    skip: int = Query(0, ge=0, description="Number of videos to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of videos to return"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get videos uploaded by a specific user.
    
    - **user_id**: UUID of the user whose videos to retrieve
    - **skip**: Number of videos to skip (pagination offset)
    - **limit**: Maximum number of videos to return (pagination limit)
    """
    try:
        videos = get_user_videos(db, user_id, skip=skip, limit=limit)
        
        if not videos and not db.query(User).filter(User.user_id == user_id).first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
                
        return videos
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user videos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user videos: {str(e)}"
        )
