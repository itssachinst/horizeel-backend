from sqlalchemy import Column, String, TIMESTAMP, UUID, BIGINT, Integer, Text, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ENUM
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class Video(Base):
    __tablename__ = "videos"

    video_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    status = Column(ENUM('draft', 'published', 'private', name='video_status'), default='published')

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"Video(video_id={self.video_id}, title={self.title}, user_id={self.user_id})"

    # Add indexes for common query patterns
    __table_args__ = (
        Index('ix_videos_user_id', user_id),  # For querying videos by user
        Index('ix_videos_created_at', created_at.desc()),  # For sorting by newest
        Index('ix_videos_title', title),  # For searching by title
    )


class User(Base):
    __tablename__ = "users"

    user_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    # Add indexes for common query patterns
    __table_args__ = (
        Index('ix_users_username', username),  # For searching by username
        Index('ix_users_email', email),  # For authentication by email
    )


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

    # Add indexes and unique constraint
    __table_args__ = (
        Index('ix_saved_videos_user_id', user_id),  # For querying saved videos by user
        Index('ix_saved_videos_video_id', video_id),  # For querying who saved a video
        Index('ix_saved_videos_user_video', user_id, video_id, unique=True),  # Ensure user can save a video only once
    )


class UserFollow(Base):
    __tablename__ = "user_follows"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    follower_id = Column(PGUUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    followed_id = Column(PGUUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"UserFollow(follower_id={self.follower_id}, followed_id={self.followed_id})"

    # Add indexes and unique constraint
    __table_args__ = (
        Index('ix_user_follows_follower_id', follower_id),  # For finding who a user follows
        Index('ix_user_follows_followed_id', followed_id),  # For finding a user's followers
        Index('ix_user_follows_follower_followed', follower_id, followed_id, unique=True),  # Ensure unique follow relationship
    )
