from pydantic import BaseModel, validator, EmailStr
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Literal

class VideoCreate(BaseModel):
    title: str
    description: str

class VideoStatus(BaseModel):
    video_id: UUID
    status: Literal['draft', 'published', 'private', 'processing', 'ready', 'failed']
    title: str
    created_at: datetime
    
    @validator('video_id', pre=True)
    def convert_uuid(cls, v):
        if isinstance(v, str):
            try:
                return UUID(v)
            except ValueError:
                return v
        return v

class VideoResponse(VideoCreate):
    video_id: UUID
    video_url: str
    thumbnail_url: str
    title: str
    description: str
    user_id: UUID
    username: str
    profile_picture: Optional[str] = None
    views: int
    likes: int
    status: Literal['draft', 'published', 'private', 'processing', 'ready', 'failed']
    created_at: datetime
    is_liked: bool = False

    @validator('video_url', 'thumbnail_url')
    def format_url(cls, v):
        if not v:
            return v
        if v.startswith(('http://', 'https://')):
            return v
        # Remove any leading slash to avoid double slashes
        clean_url = v[1:] if v.startswith('/') else v
        return f"http://localhost:8000/api/{clean_url}"

    @validator('video_id', 'user_id', pre=True)
    def convert_uuid(cls, v):
        if isinstance(v, str):
            try:
                return UUID(v)
            except ValueError:
                return v
        return v

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    profile_picture: Optional[str] = None
    cover_image: Optional[str] = None
    uploadFlag: Optional[bool] = None

class UserResponse(BaseModel):
    user_id: UUID
    username: str
    email: str
    is_active: bool
    uploadFlag: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    social: Optional[Dict[str, str]] = None
    feedback: Optional[str] = None
    feedback_updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str  # Contains the user's UUID as a string

# Follow schemas
class FollowCreate(BaseModel):
    followed_id: str

class FollowResponse(BaseModel):
    id: str
    follower_id: str
    followed_id: str
    created_at: datetime
    
    @validator("id", "follower_id", "followed_id", pre=True)
    def convert_uuid(cls, value):
        if isinstance(value, UUID):
            return str(value)
        return value
    
    class Config:
        from_attributes = True

class FollowerResponse(BaseModel):
    user_id: str
    username: str
    profile_picture: Optional[str] = None
    
    @validator("user_id", pre=True)
    def convert_uuid(cls, value):
        if isinstance(value, UUID):
            return str(value)
        return value
    
    class Config:
        from_attributes = True

class FollowStats(BaseModel):
    followers_count: int
    following_count: int

class UserProfile(BaseModel):
    """Schema for user profile updates"""
    username: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    social: Optional[Dict[str, str]] = None
    uploadFlag: Optional[bool] = None
    
    class Config:
        from_attributes = True

class UserFeedback(BaseModel):
    """Schema for updating user feedback"""
    feedback: str

    class Config:
        json_schema_extra = {
            "example": {
                "feedback": "I love this app! It's very intuitive and fun to use."
            }
        }

class WaitingListCreate(BaseModel):
    """Schema for adding email to waiting list"""
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }

class WaitingListResponse(BaseModel):
    """Schema for waiting list response"""
    id: UUID
    email: EmailStr
    created_at: datetime
    
    @validator("id", pre=True)
    def convert_uuid(cls, value):
        if isinstance(value, UUID):
            return str(value)
        return value
    
    class Config:
        from_attributes = True
