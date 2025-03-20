from pydantic import BaseModel, validator, EmailStr
from datetime import datetime
from uuid import UUID
from typing import Optional, List

class VideoCreate(BaseModel):
    title: str
    description: str

class VideoResponse(VideoCreate):
    video_id: str  # Define it as a string
    video_url: str
    created_at: datetime
    views: int
    likes: int
    dislikes: int
    thumbnail_url: str
    user_id: Optional[str] = None
    username: Optional[str] = None

    @validator("video_id", "user_id", pre=True)  # ✅ Convert UUID to string before validation
    def convert_uuid(cls, value):
        if isinstance(value, UUID):
            return str(value)
        return value

    class Config:
        orm_mode = True  # Allows working with SQLAlchemy ORM objects

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

class UserResponse(UserBase):
    user_id: str
    profile_picture: Optional[str] = None
    cover_image: Optional[str] = None
    created_at: datetime
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
    
    @validator("user_id", pre=True)
    def convert_uuid(cls, value):
        if isinstance(value, UUID):
            return str(value)
        return value

    class Config:
        orm_mode = True
        
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
        orm_mode = True

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
        orm_mode = True

class FollowStats(BaseModel):
    followers_count: int
    following_count: int
