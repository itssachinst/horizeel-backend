from sqlalchemy import Column, String, TIMESTAMP, UUID, BIGINT, Integer, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ENUM
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class Video(Base):
    __tablename__ = "videos"

    video_id = Column(PGUUID(as_uuid=True), primary_key=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.user_id"))  # ForeignKey works now!
    user = relationship("User", backref="videos")  # Establish relationship with User model

    title = Column(String(255), nullable=False)
    description = Column(Text)
    video_url = Column(String(512), nullable=False)
    thumbnail_url = Column(String(512))
    duration = Column(Integer)
    views = Column(BIGINT, default=0)
    likes = Column(BIGINT, default=0)
    dislikes = Column(BIGINT, default=0)
    status = Column(ENUM('draft', 'published', 'private', name='video_status'), default='draft')

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"Video(video_id={self.video_id}, title={self.title}, user_id={self.user_id})"


class User(Base):
    __tablename__ = "users"

    user_id = Column(PGUUID(as_uuid=True), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    profile_picture = Column(String(512))
    cover_image = Column(String(512))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Add relationship to saved videos
    saved_videos = relationship("SavedVideo", back_populates="user")
    
    # Add relationships for followers and following
    followers = relationship(
        "UserFollow",
        foreign_keys="UserFollow.followed_id",
        backref="followed",
        cascade="all, delete-orphan"
    )
    
    following = relationship(
        "UserFollow",
        foreign_keys="UserFollow.follower_id",
        backref="follower",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"User(user_id={self.user_id}, username={self.username}, email={self.email})"


class SavedVideo(Base):
    __tablename__ = "saved_videos"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    video_id = Column(PGUUID(as_uuid=True), ForeignKey("videos.video_id"), nullable=False)
    saved_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="saved_videos")
    video = relationship("Video")

    def __repr__(self):
        return f"SavedVideo(id={self.id}, user_id={self.user_id}, video_id={self.video_id})"


class UserFollow(Base):
    __tablename__ = "user_follows"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    follower_id = Column(PGUUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    followed_id = Column(PGUUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"UserFollow(follower_id={self.follower_id}, followed_id={self.followed_id})"
