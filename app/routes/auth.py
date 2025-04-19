from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse
from app.crud import (
    get_user_by_email,
    create_user,
    authenticate_user,
    create_access_token,
    get_password_hash
)
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import timedelta

router = APIRouter(tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class PasswordResetRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=6)
    
    @validator('new_password')
    def password_strength(cls, v):
        # Simplified validation to check only minimum length and at least one digit
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(
            data={"sub": str(user.user_id)}  # Always store UUID as string
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        )

@router.post("/login")
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login endpoint that matches the frontend API call"""
    try:
        user = authenticate_user(db, request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(
            data={"sub": str(user.user_id)}  # Always store UUID as string
        )
        return {"access_token": access_token, "token_type": "bearer", "user_id": str(user.user_id)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        )

@router.post("/direct-reset-password", response_model=dict)
async def reset_password(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Reset a user's password directly without email verification.
    """
    try:
        # Parse the request body manually
        body = await request.json()
        print(f"Received password reset request: {body}")
        
        # Manual validation
        if 'email' not in body:
            return {
                "message": "Email field is required",
                "status": "error",
                "detail": "validation_error"
            }
        
        if 'new_password' not in body:
            return {
                "message": "new_password field is required",
                "status": "error",
                "detail": "validation_error"
            }
        
        email = body['email']
        new_password = body['new_password']
        
        # Basic password validation
        if len(new_password) < 6:
            return {
                "message": "Password must be at least 6 characters",
                "status": "error",
                "detail": "validation_error"
            }
        
        # Find the user by email
        user = get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email not found"
            )

        # Hash the new password
        hashed_password = get_password_hash(new_password)

        # Update the user's password
        user.password_hash = hashed_password
        db.commit()

        return {
            "message": "Password has been reset successfully",
            "status": "success"
        }
    except HTTPException:
        # Re-raise HTTP exceptions to preserve status codes
        raise
    except Exception as e:
        db.rollback()
        print(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )

# You can add more authentication-related endpoints here if needed 