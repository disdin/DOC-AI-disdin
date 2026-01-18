from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.db.mongo import mongo_db
from app.models.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_user_by_email
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """
    Register a new user.
    
    - Creates a new user account with hashed password
    - Email must be unique
    """
    # Check if user already exists
    existing_user = await get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    user_doc = {
        "email": user.email,
        "hashed_password": get_password_hash(user.password),
        "full_name": user.full_name,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    # Insert into database
    result = await mongo_db.db.users.insert_one(user_doc)
    
    # Return user response
    return UserResponse(
        email=user.email,
        full_name=user.full_name,
        is_active=True,
        created_at=user_doc["created_at"]
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login to get JWT access token.
    
    - Authenticates user with email (username) and password
    - Returns JWT token for subsequent requests
    """
    # Authenticate user
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_active_user)):
    """
    Get current authenticated user information.
    
    - Requires valid JWT token
    - Returns user profile
    """
    return UserResponse(
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )
