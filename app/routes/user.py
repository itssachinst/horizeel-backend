from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import timedelta
from typing import List, Optional

from app import crud, schemas
from app.crud import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY, update_user_feedback, get_all_user_feedback
from app.utils.auth import get_current_user, get_db
from app.utils.s3_utils import upload_profile_image_to_s3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User registration endpoint
@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create new user
    return crud.create_user(db=db, user=user)

# User login endpoint
@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crud.create_access_token(
        data={"sub": str(user.user_id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Get current user profile
@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user = Depends(get_current_user)):
    return current_user

# Get all users (admin only in a real app)
@router.get("/", response_model=List[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

# Get specific user by ID
@router.get("/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id: str, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Update user profile
@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: str, 
    user_update: schemas.UserUpdate, 
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user is modifying their own profile
    if str(current_user.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    
    updated_user = crud.update_user(db, user_id=user_id, user_update=user_update)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

# Delete user
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str, 
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user is deleting their own account
    if str(current_user.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")
    
    success = crud.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# Follow system endpoints

# Follow a user
@router.post("/{user_id}/follow", response_model=schemas.FollowResponse)
def follow_user(
    user_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Follow a user
    """
    # Check if the user exists
    user_to_follow = crud.get_user_by_id(db, user_id=user_id)
    if not user_to_follow:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check that the user is not trying to follow themselves
    if str(current_user.user_id) == user_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")
    
    # Create the follow relationship
    follow = crud.follow_user(db, 
                            follower_id=str(current_user.user_id), 
                            followed_id=user_id)
    
    if not follow:
        raise HTTPException(status_code=400, detail="Could not create follow relationship")
    
    return follow

# Unfollow a user
@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    user_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unfollow a user
    """
    # Check if the user exists
    user_to_unfollow = crud.get_user_by_id(db, user_id=user_id)
    if not user_to_unfollow:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove the follow relationship
    success = crud.unfollow_user(db, 
                               follower_id=str(current_user.user_id), 
                               followed_id=user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Follow relationship not found")
    
    return {"detail": "Successfully unfollowed user"}

# Get followers of a user
@router.get("/{user_id}/followers", response_model=List[schemas.FollowerResponse])
def get_followers(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all users who follow the specified user
    """
    # Check if the user exists
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get the followers
    followers = crud.get_followers(db, user_id=user_id, skip=skip, limit=limit)
    return followers

# Get users that a user is following
@router.get("/{user_id}/following", response_model=List[schemas.FollowerResponse])
def get_following(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all users that the specified user follows
    """
    # Check if the user exists
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get the following
    following = crud.get_following(db, user_id=user_id, skip=skip, limit=limit)
    return following

# Check if current user follows a specific user
@router.get("/{user_id}/is-following", response_model=dict)
def check_following(
    user_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if the current user follows the specified user
    """
    # Check if the user exists
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if following
    is_following = crud.is_following(db, 
                                   follower_id=str(current_user.user_id), 
                                   followed_id=user_id)
    
    return {"is_following": is_following}

# Get follow stats for a user
@router.get("/{user_id}/follow-stats", response_model=schemas.FollowStats)
def get_follow_stats(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get follower and following counts for a user
    """
    # Check if the user exists
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get stats
    stats = crud.get_follow_stats(db, user_id=user_id)
    return stats

@router.put("/profile", response_model=schemas.UserResponse)
async def update_user_profile(
    profile: schemas.UserProfile,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Update the current user's profile information
    """
    try:
        updated_user = crud.update_user_profile(
            db=db, 
            user_id=current_user.user_id, 
            profile_data=profile.dict(exclude_unset=True)
        )
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return updated_user
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@router.post("/upload-profile-image", response_model=dict)
async def upload_profile_image(
    profileImage: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user)
):
    """
    Upload a profile image for the current user
    """
    try:
        # Check file type
        if not profileImage.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
            
        # Upload image to S3
        profile_image_url = await upload_profile_image_to_s3(
            file=profileImage,
            user_id=str(current_user.user_id)
        )
        
        # Update user's profile_picture field in database
        updated_user = crud.update_user_profile(
            db=db,
            user_id=current_user.user_id,
            profile_data={"profile_picture": profile_image_url}
        )
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"profileImageUrl": profile_image_url}
    except Exception as e:
        logger.error(f"Error uploading profile image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload profile image: {str(e)}")

@router.get("/{user_id}/follow-stats", response_model=dict)
def get_follow_stats(user_id: int, db: Session = Depends(get_db)):
    """
    Get the follower and following counts for a user
    """
    follower_count = crud.get_follower_count(db, user_id)
    following_count = crud.get_following_count(db, user_id)
    
    return {
        "followers_count": follower_count,
        "following_count": following_count
    }

@router.post("/feedback", response_model=schemas.UserResponse)
async def submit_user_feedback(
    feedback_data: schemas.UserFeedback,
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback for the current user
    
    - **feedback**: Feedback text from the user
    
    Returns:
        Updated user object with feedback
    """
    try:
        updated_user = update_user_feedback(
            db=db,
            user_id=current_user.user_id,
            feedback=feedback_data.feedback
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        logger.info(f"User {current_user.user_id} submitted feedback")
        return updated_user
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@router.get("/feedback", response_model=List[schemas.UserResponse])
async def get_all_feedback(
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all user feedback
    
    This endpoint allows users to retrieve all user feedback.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (pagination)
    
    Returns:
        List of user objects with feedback
    """
    try:
        users_with_feedback = get_all_user_feedback(db, skip=skip, limit=limit)
        return users_with_feedback
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback: {str(e)}"
        ) 