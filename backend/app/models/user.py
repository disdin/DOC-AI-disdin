from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Model for user registration."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Model for user login."""
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    """User model stored in database."""
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    

class UserResponse(BaseModel):
    """User model for API responses (no password)."""
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    email: Optional[str] = None
