from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models import User
from app.db.schemas import UserCreate, UserRead, UserListResponse

router = APIRouter()

@router.post("/", response_model=UserRead, status_code=201)
def create_user(
    user_data: UserCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new user.
    
    Example request:
    ```json
    {
        "username": "alice"
    }
    ```
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = User(username=user_data.username)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.get("/", response_model=UserListResponse)
def list_users(db: Session = Depends(get_db)):
    """
    List all users.
    """
    users = db.query(User).all()
    return UserListResponse(users=users)

@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get a user by ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
