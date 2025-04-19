from sqlalchemy.orm import Session
from app.models import Video, User, SavedVideo, UserFollow, WatchHistory, Like, WaitingList
from app.schemas import VideoCreate, UserCreate, UserUpdate
from sqlalchemy import or_, func, and_, not_
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional, List, Dict, Any, Union
from fastapi import HTTPException, status
from functools import lru_cache
import logging
import uuid
import random

# Configure logging
logger = logging.getLogger(__name__)

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT setup
SECRET_KEY = "your-secret-key-keep-it-secret"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_video(db: Session, video: VideoCreate, vfile_url: str, tfile_url: str, user_id: str = None):
    """Create a new video entry in the database"""
    try:
        # Convert user_id to UUID if it's a string
        user_id_uuid = None
        if user_id:
            try:
                user_id_uuid = UUID(user_id)
            except ValueError:
                logger.warning(f"Invalid UUID format for user_id: {user_id}")
        
        # Create the video object
        db_video = Video(
            video_id=uuid4(),
            title=video["title"],
            description=video["description"],
            video_url=vfile_url,
            thumbnail_url=tfile_url,
            user_id=user_id_uuid,
            duration=video.get("duration", 0)  # Set duration if provided
        )
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        # Add username and profile_picture to the video object
        if user_id_uuid:
            user = db.query(User).filter(User.user_id == user_id_uuid).first()
            if user:
                db_video.username = user.username
                db_video.profile_picture = user.profile_picture
            else:
                db_video.username = "Unknown"
                db_video.profile_picture = None
        else:
            db_video.username = "Unknown"
            db_video.profile_picture = None
        
        return db_video
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create video: {str(e)}")
        raise

def get_video(db: Session, video_id: Union[str, uuid4]):
    """
    Get a video by its ID with username.
    If the video has a user_id, the username will be included.
    """
    try:
        # Convert video_id to UUID if it's a string
        video_id_uuid = video_id
        if isinstance(video_id, str):
            try:
                video_id_uuid = UUID(video_id)
            except ValueError:
                logger.warning(f"Invalid UUID format for video_id: {video_id}")
                return None
        
        # Query the video
        video = db.query(Video).filter(Video.video_id == video_id_uuid).first()
        
        # If video exists
        if video:
            # Initialize username and profile_picture fields with default values
            video.username = "Unknown"
            video.profile_picture = None
            
            # Try to get the actual username and profile_picture if user_id exists
            if video.user_id:
                user = db.query(User).filter(User.user_id == video.user_id).first()
                if user:
                    video.username = user.username
                    video.profile_picture = user.profile_picture
        
        return video
    except Exception as e:
        logger.error(f"Failed to get video {video_id}: {str(e)}")
        raise

# Cache frequently accessed video lists to improve performance
@lru_cache(maxsize=10)
def list_videos(db: Session, skip: int = 0, limit: int = 20, user_id: str = None):
    """
    Get a personalized list of videos with user data.
    Results are cached to improve performance under high load.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        user_id: Optional user ID for personalized recommendations
        
    Returns:
        List of Video objects
    """
    try:
        # Convert user_id to UUID if it's a string
        user_id_uuid = None
        if user_id:
            try:
                user_id_uuid = UUID(user_id)
            except ValueError:
                logger.warning(f"Invalid UUID format for user_id: {user_id}")
        
        # If no user_id provided, return regular trending videos
        if not user_id_uuid:
            videos = db.query(Video).order_by(
                Video.views.desc(), 
                Video.likes.desc(), 
                Video.created_at.desc()
            ).offset(skip).limit(limit).all()
            
            # Get all user IDs for videos in one query to minimize database calls
            user_ids = [video.user_id for video in videos if video.user_id]
            
            if user_ids:
                # Get all users in a single query
                users = {
                    str(user.user_id): user 
                    for user in db.query(User).filter(User.user_id.in_(user_ids)).all()
                }
                
                # Add username and profile_picture to videos
                for video in videos:
                    # Initialize with default values
                    video.username = "Unknown"
                    video.profile_picture = None
                    # Try to get the actual username and profile_picture if possible
                    if video.user_id and str(video.user_id) in users:
                        video.username = users[str(video.user_id)].username
                        video.profile_picture = users[str(video.user_id)].profile_picture
            else:
                # Set default values if no users were found
                for video in videos:
                    video.username = "Unknown"
                    video.profile_picture = None
            
            return videos

        # For authenticated users, provide personalized recommendations
        # Fetch user's watch history & liked videos in a single query
        watched_video_ids = set()
        liked_video_ids = set()
        
        # Get watch history and liked videos in parallel
        watch_history = db.query(WatchHistory.video_id).filter_by(user_id=user_id_uuid).all()
        liked_videos = db.query(Like.video_id).filter_by(user_id=user_id_uuid).all()
        
        watched_video_ids = {video.video_id for video in watch_history}
        liked_video_ids = {video.video_id for video in liked_videos}
        
        # Get followed users
        followed_users = [
            follow.followed_id for follow in db.query(UserFollow).filter_by(follower_id=user_id_uuid).all()
        ]
        
        # Get videos from different sources with optimized queries
        trending_videos = db.query(Video).order_by(
            Video.views.desc(), 
            Video.likes.desc()
        ).limit(limit * 2).all()
        
        followed_videos = []
        if followed_users:
            followed_videos = db.query(Video).filter(
                Video.user_id.in_(followed_users)
            ).order_by(
                Video.created_at.desc()
            ).limit(limit).all()

        # Get new videos (not watched yet)
        new_videos = []
        if watched_video_ids:
            new_videos = db.query(Video).filter(
                not_(Video.video_id.in_(watched_video_ids))
            ).order_by(
                Video.created_at.desc()
            ).limit(limit).all()

        # Merge results, ensuring diversity
        video_list = []
        video_set = set()  # To track unique videos
        
        # Add videos in order of priority
        for video in trending_videos:
            if video.video_id not in video_set:
                video_list.append(video)
                video_set.add(video.video_id)
                
        for video in followed_videos:
            if video.video_id not in video_set:
                video_list.append(video)
                video_set.add(video.video_id)
                
        for video in new_videos:
            if video.video_id not in video_set:
                video_list.append(video)
                video_set.add(video.video_id)
        
        # Shuffle to avoid monotony
        random.shuffle(video_list)
        
        # Apply pagination
        videos = video_list[skip: skip + limit]
        
        # Get all user IDs for videos in one query to minimize database calls
        user_ids = [video.user_id for video in videos if video.user_id]
        
        if user_ids:
            # Get all users in a single query
            users = {
                str(user.user_id): user 
                for user in db.query(User).filter(User.user_id.in_(user_ids)).all()
            }
            
            # Add username and profile_picture to videos
            for video in videos:
                # Initialize with default values
                video.username = "Unknown"
                video.profile_picture = None
                # Try to get the actual username and profile_picture if possible
                if video.user_id and str(video.user_id) in users:
                    video.username = users[str(video.user_id)].username
                    video.profile_picture = users[str(video.user_id)].profile_picture
        else:
            # Set default values if no users were found
            for video in videos:
                video.username = "Unknown"
                video.profile_picture = None
        
        return videos
    except Exception as e:
        logger.error(f"Failed to list videos: {str(e)}")
        raise

def video_views_increment(db: Session, video_id: Union[str, uuid4]):
    """Increment view count for a video"""
    try:
        video = db.query(Video).filter(Video.video_id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
            
    # Increment views
        video.views += 1
        db.commit()
        return video.views
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to increment views for video {video_id}: {str(e)}")
        raise

def video_likes_increment(db: Session, video_id: Union[str, uuid4]):
    """Increment like count for a video"""
    try:
        video = db.query(Video).filter(Video.video_id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
            
        # Increment likes
        video.likes += 1
        db.commit()
        return video.likes
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to increment likes for video {video_id}: {str(e)}")
        raise

def video_dislikes_increment(db: Session, video_id: Union[str, uuid4]):
    """Increment dislike count for a video"""
    try:
        video = db.query(Video).filter(Video.video_id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
            
        # Increment dislikes
        video.dislikes += 1
        db.commit()
        return video.dislikes
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to increment dislikes for video {video_id}: {str(e)}")
        raise

def search_videos(db: Session, query: str, skip: int = 0, limit: int = 20, search_type: str = "text"):
    """
    Search for videos with pagination and query optimization.
    
    Args:
        db: Database session
        query: Search query string
        skip: Number of records to skip
        limit: Maximum number of records to return
        search_type: Type of search ('text' or 'hashtag')
        
    Returns:
        List of Video objects matching search criteria
    """
    if not query:
        return []

    try:
        # Clean the query string
        query = query.strip()
        
        # Base query with pagination
        base_query = db.query(Video)
        
        # Different search strategies based on search type
        if search_type == "hashtag":
            # For hashtag searches, use a more specific LIKE pattern
            search_pattern = f"%#{query}%"
            results = base_query.filter(
                or_(
                    Video.description.ilike(search_pattern),
                    Video.title.ilike(search_pattern)
                )
            ).order_by(Video.created_at.desc()).offset(skip).limit(limit).all()
        else:
            # For text searches, split query into keywords for better matching
            keywords = query.split()
            conditions = []
            
            for keyword in keywords:
                pattern = f"%{keyword}%"
                conditions.append(or_(
                    Video.title.ilike(pattern),
                    Video.description.ilike(pattern)
                ))
            
            # Combine all conditions with OR
            results = base_query.filter(or_(*conditions)).order_by(
                Video.created_at.desc()
            ).offset(skip).limit(limit).all()
        
        # Populate usernames
        user_ids = [video.user_id for video in results if video.user_id]
        
        if user_ids:
            users = {
                str(user.user_id): user.username
                for user in db.query(User).filter(User.user_id.in_(user_ids)).all()
            }
            
            for video in results:
                if video.user_id and str(video.user_id) in users:
                    video.username = users[str(video.user_id)]
        
        return results
    except Exception as e:
        logger.error(f"Failed to search videos with query '{query}': {str(e)}")
        raise

# User CRUD operations
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    try:
        return db.query(User).filter(User.email == email).first()
    except Exception as e:
        logger.error(f"Failed to get user by email '{email}': {str(e)}")
        raise

def get_user_by_username(db: Session, username: str):
    """Get a user by username."""
    try:
        return db.query(User).filter(User.username == username).first()
    except Exception as e:
        logger.error(f"Failed to get user by username '{username}': {str(e)}")
        raise

def get_user_by_id(db: Session, user_id: Union[str, uuid4]) -> Optional[User]:
    """Get a user by ID."""
    try:
        # Validate user_id is a proper UUID
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                logger.error(f"Invalid UUID format for user_id: {user_id}")
                return None
                
        return db.query(User).filter(User.user_id == user_id).first()
    except Exception as e:
        logger.error(f"Failed to get user by ID '{user_id}': {str(e)}")
        raise

def get_users(db: Session, skip: int = 0, limit: int = 20):
    """Get a paginated list of users."""
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        
        # Get follower and following counts for users in a single query
        user_ids = [user.user_id for user in users]
        
        if user_ids:
            # Get follower counts in a single query
            follower_counts = db.query(
                UserFollow.followed_id, 
                func.count(UserFollow.id).label('count')
            ).filter(
                UserFollow.followed_id.in_(user_ids)
            ).group_by(
                UserFollow.followed_id
            ).all()
            
            follower_map = {str(followed_id): count for followed_id, count in follower_counts}
            
            # Get following counts in a single query
            following_counts = db.query(
                UserFollow.follower_id, 
                func.count(UserFollow.id).label('count')
            ).filter(
                UserFollow.follower_id.in_(user_ids)
            ).group_by(
                UserFollow.follower_id
            ).all()
            
            following_map = {str(follower_id): count for follower_id, count in following_counts}
            
            # Add counts to user objects
            for user in users:
                user_id_str = str(user.user_id)
                user.followers_count = follower_map.get(user_id_str, 0)
                user.following_count = following_map.get(user_id_str, 0)
                
        return users
    except Exception as e:
        logger.error(f"Failed to get users: {str(e)}")
        raise

def create_user(db: Session, user: UserCreate):
    """Create a new user."""
    hashed_password = pwd_context.hash(user.password)
    current_time = datetime.utcnow()
    db_user = User(
        user_id=uuid4(),
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        created_at=current_time,
        updated_at=current_time
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: str, user_update: UserUpdate):
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    # Update user fields if provided
    update_data = user_update.dict(exclude_unset=True)
    
    # Hash password if it's being updated
    if "password" in update_data:
        update_data["password_hash"] = pwd_context.hash(update_data.pop("password"))
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: str):
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

# Authentication functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    try:
        user = get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
    except Exception as e:
        logger.error(f"Failed to authenticate user: {str(e)}")
        raise

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to create access token: {str(e)}")
        raise

# New functions for saved videos

def save_video_for_user(db: Session, user_id: str, video_id: str):
    """Save a video for a user"""
    # Check if already saved
    existing = db.query(SavedVideo).filter(
        SavedVideo.user_id == user_id,
        SavedVideo.video_id == video_id
    ).first()
    
    if existing:
        return existing
    
    # Create new saved video entry
    saved_video = SavedVideo(
        user_id=user_id,
        video_id=video_id
    )
    db.add(saved_video)
    db.commit()
    db.refresh(saved_video)
    return saved_video

def unsave_video_for_user(db: Session, user_id: str, video_id: str):
    """Remove a saved video for a user"""
    saved_video = db.query(SavedVideo).filter(
        SavedVideo.user_id == user_id,
        SavedVideo.video_id == video_id
    ).first()
    
    if saved_video:
        db.delete(saved_video)
        db.commit()
        return True
    return False

def get_saved_videos_for_user(db: Session, user_id: str):
    """Get all saved videos for a user"""
    # Query saved videos and join with video table to get video details
    saved_videos = db.query(SavedVideo).filter(SavedVideo.user_id == user_id).all()
    
    # Get the actual video objects
    video_ids = [sv.video_id for sv in saved_videos]
    videos = db.query(Video).filter(Video.video_id.in_(video_ids)).all()
    
    # For each video, fetch the username if user_id is present
    for video in videos:
        if video.user_id:
            user = db.query(User).filter(User.user_id == video.user_id).first()
            if user:
                video.username = user.username
                video.profile_picture = user.profile_picture
    
    return videos

def check_video_saved(db: Session, user_id: str, video_id: str):
    """Check if a video is saved by a user"""
    saved_video = db.query(SavedVideo).filter(
        SavedVideo.user_id == user_id,
        SavedVideo.video_id == video_id
    ).first()
    
    return saved_video is not None

def delete_video(db: Session, video_id: str, user_id: str):
    """Delete a video by its ID
    
    Args:
        db: Database session
        video_id: ID of the video to delete
        user_id: ID of the user requesting deletion (for permission check)
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    # Get the video
    video = db.query(Video).filter(Video.video_id == video_id).first()
    
    # Check if video exists
    if not video:
        return False
    
    # Check if user is the owner of the video
    if str(video.user_id) != user_id:
        return False
    
    try:
        # Try to delete any like records first
        from sqlalchemy import text
        try:
            # First attempt to delete from likes table if it exists
            db.execute(text(f"DELETE FROM likes WHERE video_id = '{video_id}'"))
        except Exception as e:
            # If the likes table doesn't exist or any other error occurs, log it but continue
            logger.warning(f"Could not delete from likes table for video {video_id}: {str(e)}")
        
        # Delete any saved video references
        db.query(SavedVideo).filter(SavedVideo.video_id == video_id).delete()
        
        # Delete any watch history records
        try:
            db.query(WatchHistory).filter(WatchHistory.video_id == video_id).delete()
        except Exception as e:
            logger.warning(f"Could not delete from watch_history for video {video_id}: {str(e)}")
        
        # Then delete the video itself
        db.delete(video)
        db.commit()
        
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting video {video_id}: {str(e)}")
        return False

# Follow system functions
def follow_user(db: Session, follower_id: str, followed_id: str):
    """Create a follow relationship between users
    
    Args:
        db: Database session
        follower_id: ID of the user who is following
        followed_id: ID of the user being followed
        
    Returns:
        UserFollow: The created follow relationship
    """
    # First check if the follow relationship already exists
    existing_follow = db.query(UserFollow).filter(
        and_(
            UserFollow.follower_id == follower_id,
            UserFollow.followed_id == followed_id
        )
    ).first()
    
    if existing_follow:
        return existing_follow
    
    # Check that users can't follow themselves
    if follower_id == followed_id:
        return None
        
    # Create new follow relationship
    follow = UserFollow(
        follower_id=follower_id,
        followed_id=followed_id
    )
    
    db.add(follow)
    db.commit()
    db.refresh(follow)
    return follow

def unfollow_user(db: Session, follower_id: str, followed_id: str):
    """Remove a follow relationship between users
    
    Args:
        db: Database session
        follower_id: ID of the user who is following
        followed_id: ID of the user being followed
        
    Returns:
        bool: True if unfollow was successful, False otherwise
    """
    follow = db.query(UserFollow).filter(
        and_(
            UserFollow.follower_id == follower_id,
            UserFollow.followed_id == followed_id
        )
    ).first()
    
    if follow:
        db.delete(follow)
        db.commit()
        return True
    
    return False

def get_followers(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    """Get users who follow a specific user
    
    Args:
        db: Database session
        user_id: ID of the user whose followers to retrieve
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (pagination)
        
    Returns:
        list: List of User objects who follow the specified user
    """
    followers = db.query(User).join(
        UserFollow, User.user_id == UserFollow.follower_id
    ).filter(
        UserFollow.followed_id == user_id
    ).offset(skip).limit(limit).all()
    
    return followers

def get_following(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    """Get users that a specific user follows
    
    Args:
        db: Database session
        user_id: ID of the user whose followings to retrieve
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (pagination)
        
    Returns:
        list: List of User objects the specified user follows
    """
    following = db.query(User).join(
        UserFollow, User.user_id == UserFollow.followed_id
    ).filter(
        UserFollow.follower_id == user_id
    ).offset(skip).limit(limit).all()
    
    return following

def is_following(db: Session, follower_id: str, followed_id: str):
    """Check if a user follows another user
    
    Args:
        db: Database session
        follower_id: ID of the potential follower
        followed_id: ID of the potentially followed user
        
    Returns:
        bool: True if the follow relationship exists, False otherwise
    """
    follow = db.query(UserFollow).filter(
        and_(
            UserFollow.follower_id == follower_id,
            UserFollow.followed_id == followed_id
        )
    ).first()
    
    return follow is not None

def get_follow_stats(db: Session, user_id: str):
    """Get the follower and following counts for a user
    
    Args:
        db: Database session
        user_id: ID of the user
        
    Returns:
        dict: Dictionary with follower_count and following_count
    """
    followers_count = db.query(func.count(UserFollow.id)).filter(
        UserFollow.followed_id == user_id
    ).scalar()
    
    following_count = db.query(func.count(UserFollow.id)).filter(
        UserFollow.follower_id == user_id
    ).scalar()
    
    return {
        "followers_count": followers_count,
        "following_count": following_count
    }

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def update_user_profile(db: Session, user_id: Union[str, uuid.UUID], profile_data: dict):
    """
    Update a user's profile information
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        return None
    
    # Update basic fields
    if "username" in profile_data:
        user.username = profile_data["username"]
    if "email" in profile_data:
        user.email = profile_data["email"]
    if "bio" in profile_data:
        user.bio = profile_data["bio"]
    if "profile_picture" in profile_data:
        user.profile_picture = profile_data["profile_picture"]
    
    # Update social media fields if they exist in the model
    if "social" in profile_data and hasattr(user, "social"):
        social_data = profile_data["social"]
        if not user.social:
            user.social = {}
        
        # Update each social field
        for key in ["instagram", "twitter", "facebook", "linkedin"]:
            if key in social_data:
                if not user.social:
                    user.social = {}
                user.social[key] = social_data[key]
    
    # Commit changes
    db.commit()
    db.refresh(user)

    return user

def update_user_feedback(db: Session, user_id: Union[str, uuid4], feedback: str):
    """
    Update a user's feedback
    
    Args:
        db: Database session
        user_id: ID of the user to update
        feedback: The feedback text to store
        
    Returns:
        Updated User object or None if user not found
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None
            
        user.feedback = feedback
        user.feedback_updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update feedback for user {user_id}: {str(e)}")
        raise

def get_all_user_feedback(db: Session, skip: int = 0, limit: int = 100):
    """
    Get all user feedback with pagination
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (pagination)
        
    Returns:
        List of User objects that have feedback
    """
    try:
        # Query users that have feedback (not null)
        users_with_feedback = db.query(User).filter(
            User.feedback.isnot(None)
        ).order_by(
            User.feedback_updated_at.desc()
        ).offset(skip).limit(limit).all()
        
        return users_with_feedback
    except Exception as e:
        logger.error(f"Failed to get user feedback: {str(e)}")
        raise

# Waiting List functions
def add_to_waiting_list(db: Session, email: str):
    """
    Add an email to the waiting list
    
    Args:
        db: Database session
        email: Email to add to the waiting list
        
    Returns:
        WaitingList: Created waiting list entry or existing entry if email already exists
    """
    try:
        # Check if email already exists in the waiting list
        existing = db.query(WaitingList).filter(WaitingList.email == email).first()
        if existing:
            return existing
            
        # Create new waiting list entry
        waiting_list_entry = WaitingList(
            id=uuid4(),
            email=email
        )
        
        db.add(waiting_list_entry)
        db.commit()
        db.refresh(waiting_list_entry)
        return waiting_list_entry
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add email {email} to waiting list: {str(e)}")
        raise

def get_waiting_list(db: Session, skip: int = 0, limit: int = 100):
    """
    Get all waiting list entries with pagination
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (pagination)
        
    Returns:
        List of WaitingList objects
    """
    try:
        return db.query(WaitingList).order_by(WaitingList.created_at.desc()).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Failed to get waiting list: {str(e)}")
        raise

def get_user_videos(db: Session, user_id: Union[str, UUID], skip: int = 0, limit: int = 20):
    """
    Get videos uploaded by a specific user
    
    Args:
        db: Database session
        user_id: ID of the user whose videos to retrieve
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (pagination)
        
    Returns:
        List of Video objects uploaded by the specified user
    """
    try:
        # Ensure user_id is a UUID
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                logger.warning(f"Invalid UUID format for user_id: {user_id}")
                return []

        # First check if the user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            logger.warning(f"User not found with ID: {user_id}")
            return []
            
        # Query videos by this user
        videos = db.query(Video).filter(
            Video.user_id == user_id
        ).order_by(
            Video.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        # Set username for all videos
        for video in videos:
            video.username = user.username
            video.profile_picture = user.profile_picture
            
        return videos
    except Exception as e:
        logger.error(f"Error getting user videos: {str(e)}")
        raise