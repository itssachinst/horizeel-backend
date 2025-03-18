from sqlalchemy.orm import Session
from app.models import Video, User, SavedVideo, UserFollow
from app.schemas import VideoCreate, UserCreate, UserUpdate
from sqlalchemy import or_, func, and_
from uuid import uuid4
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional
from fastapi import HTTPException, status

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT setup
SECRET_KEY = "your-secret-key-keep-it-secret"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_video(db: Session, video: VideoCreate, vfile_url: str, tfile_url: str, user_id: str = None):
    db_video = Video(
        video_id=uuid4(),
        title=video["title"], 
        description=video["description"], 
        video_url=vfile_url,
        thumbnail_url=tfile_url,
        user_id=user_id
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

def get_video(db: Session, video_id: int):
    # Query the video and join with the user table to get username
    video = db.query(Video).filter(Video.video_id == video_id).first()
    if video and video.user_id:
        # Get the username if user is associated
        user = db.query(User).filter(User.user_id == video.user_id).first()
        if user:
            video.username = user.username
    return video

def list_videos(db: Session):
    # Get all videos 
    videos = db.query(Video).all()
    
    # For each video, fetch the username if user_id is present
    for video in videos:
        if video.user_id:
            user = db.query(User).filter(User.user_id == video.user_id).first()
            if user:
                video.username = user.username
    
    return videos

def video_views_increment(db: Session, video_id: int):
    video = db.query(Video).filter(Video.video_id == video_id).first()
    # Increment views
    video.views += 1
    db.commit()
    return video.views

def video_likes_increment(db: Session, video_id: int):
    video = db.query(Video).filter(Video.video_id == video_id).first()
    # Increment views
    video.likes += 1
    db.commit()
    return video.likes

def video_dislikes_increment(db: Session, video_id: int):
    video = db.query(Video).filter(Video.video_id == video_id).first()
    # Increment views
    video.dislikes += 1
    db.commit()
    return video.dislikes

def video_subscribers_increment(db: Session, video_id: int):
    video = db.query(Video).filter(Video.video_id == video_id).first()
    # Increment views
    video.subscribers += 1
    db.commit()
    return video.subscribers

def search_videos(db: Session, query: str):
    """
    Search for videos based on title, description, or hashtags.
    Returns a list of matching videos.
    """
    if not query:
        return []
        
    # Clean the query string
    query = query.strip()
    
    # Create the base query
    base_query = db.query(Video)
    
    # If query is a hashtag (starts with #), search in description
    if query.startswith('#'):
        # Remove the # symbol and search for the hashtag in description
        hashtag = query[1:]
        videos = base_query.filter(Video.description.ilike(f"%#{hashtag}%")).all()
    else:
        # Search in both title and description
        videos = base_query.filter(
            or_(
                Video.title.ilike(f"%{query}%"),
                Video.description.ilike(f"%{query}%")
            )
        ).all()
    
    # For each video, fetch the username if user_id is present
    for video in videos:
        if video.user_id:
            user = db.query(User).filter(User.user_id == video.user_id).first()
            if user:
                video.username = user.username
    
    return videos

# User CRUD operations
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    users = db.query(User).offset(skip).limit(limit).all()
    
    # Get follower and following counts for each user
    for user in users:
        followers_count = db.query(func.count(UserFollow.id)).filter(
            UserFollow.followed_id == user.user_id
        ).scalar()
        
        following_count = db.query(func.count(UserFollow.id)).filter(
            UserFollow.follower_id == user.user_id
        ).scalar()
        
        # Set the counts as attributes
        user.followers_count = followers_count
        user.following_count = following_count
    
    return users

def create_user(db: Session, user: UserCreate):
    """Create a new user."""
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        user_id=uuid4(),
        username=user.username,
        email=user.email,
        password_hash=hashed_password
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
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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
    
    # First delete any saved video references
    db.query(SavedVideo).filter(SavedVideo.video_id == video_id).delete()
    
    # Then delete the video itself
    db.delete(video)
    db.commit()
    
    return True

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