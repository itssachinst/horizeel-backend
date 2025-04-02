from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.utils.auth import get_current_user
from app import crud, schemas
from pydantic import EmailStr

router = APIRouter(tags=["waiting_list"])

@router.post("/", response_model=schemas.WaitingListResponse, status_code=status.HTTP_201_CREATED)
def add_to_waiting_list(email_data: schemas.WaitingListCreate, db: Session = Depends(get_db)):
    """
    Add an email to the waiting list
    
    - **email**: Valid email address to add to the waiting list
    """
    try:
        waiting_list_entry = crud.add_to_waiting_list(db, email=email_data.email)
        return waiting_list_entry
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add email to waiting list: {str(e)}"
        )

@router.get("/", response_model=List[schemas.WaitingListResponse])
def get_waiting_list(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all emails in the waiting list (admin only)
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (pagination)
    """
    # In a real app, you'd add admin permission check here
    try:
        waiting_list = crud.get_waiting_list(db, skip=skip, limit=limit)
        return waiting_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve waiting list: {str(e)}"
        ) 