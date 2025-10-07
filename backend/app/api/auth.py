"""
Authentication API Endpoints
============================
"""
import logging
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..models.user import UserCreate, UserLogin, User, Token, UserUpdate
from ..services.auth_service import auth_service
from ..services.database import db_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Dependency to get current authenticated user"""
    token = credentials.credentials

    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


@router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    """Register a new user"""
    session = db_service.get_session()

    try:
        user = auth_service.create_user(session, user_data)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists or registration failed"
            )

        # Create access token
        access_token = auth_service.create_access_token(
            user_id=user.id,
            email=user.email
        )

        return {
            "success": True,
            "message": "User registered successfully",
            "user": user.dict(),
            "access_token": access_token,
            "token_type": "bearer"
        }

    finally:
        session.close()


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login user and return access token"""
    session = db_service.get_session()

    try:
        user = auth_service.authenticate_user(
            session,
            credentials.email,
            credentials.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token = auth_service.create_access_token(
            user_id=user.id,
            email=user.email
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire * 60
        )

    finally:
        session.close()


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    session = db_service.get_session()

    try:
        user_id = current_user.get("sub")
        user = auth_service.get_user_by_id(session, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return User.from_orm(user)

    finally:
        session.close()


@router.put("/me", response_model=dict)
async def update_user_profile(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    session = db_service.get_session()

    try:
        user_id = current_user.get("sub")

        # Convert Pydantic model to dict, exclude None values
        update_dict = update_data.dict(exclude_none=True)

        success = auth_service.update_user_preferences(
            session,
            user_id,
            update_dict
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update profile"
            )

        return {
            "success": True,
            "message": "Profile updated successfully"
        }

    finally:
        session.close()


@router.post("/logout", response_model=dict)
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (client should discard token)"""
    return {
        "success": True,
        "message": "Logged out successfully"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """Refresh access token"""
    session = db_service.get_session()

    try:
        user_id = current_user.get("sub")
        user = auth_service.get_user_by_id(session, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Create new access token
        access_token = auth_service.create_access_token(
            user_id=user.id,
            email=user.email
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire * 60
        )

    finally:
        session.close()
