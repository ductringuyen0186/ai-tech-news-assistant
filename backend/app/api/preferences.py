"""
User Preferences API Endpoints
==============================
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status

from ..models.user import (
    UserPreferenceUpdate, UserPreference, TechCategory,
    User
)
from ..services.auth_service import auth_service
from ..services.database import db_service
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("/", response_model=dict)
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    """Get all user preferences"""
    session = db_service.get_session()

    try:
        user_id = current_user.get("sub")

        # Get basic user info
        user = auth_service.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get extended preferences
        prefs = auth_service.get_user_preferences(session, user_id)

        return {
            "success": True,
            "basic": {
                "preferred_categories": user.preferred_categories,
                "preferred_sources": user.preferred_sources,
                "email_notifications": user.email_notifications,
                "digest_frequency": user.digest_frequency
            },
            "extended": UserPreference.from_orm(prefs) if prefs else None
        }

    finally:
        session.close()


@router.put("/", response_model=dict)
async def update_user_preferences(
    update_data: UserPreferenceUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update extended user preferences"""
    session = db_service.get_session()

    try:
        user_id = current_user.get("sub")

        update_dict = update_data.dict(exclude_none=True)

        success = auth_service.update_extended_preferences(
            session,
            user_id,
            update_dict
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update preferences"
            )

        return {
            "success": True,
            "message": "Preferences updated successfully"
        }

    finally:
        session.close()


@router.post("/categories", response_model=dict)
async def set_preferred_categories(
    categories: List[TechCategory],
    current_user: dict = Depends(get_current_user)
):
    """Set user's preferred tech categories"""
    session = db_service.get_session()

    try:
        user_id = current_user.get("sub")

        # Convert enum to values
        category_values = [cat.value for cat in categories]

        success = auth_service.update_user_preferences(
            session,
            user_id,
            {"preferred_categories": category_values}
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update categories"
            )

        return {
            "success": True,
            "message": f"Updated {len(categories)} preferred categories",
            "categories": category_values
        }

    finally:
        session.close()


@router.post("/sources", response_model=dict)
async def set_preferred_sources(
    sources: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Set user's preferred news sources"""
    session = db_service.get_session()

    try:
        user_id = current_user.get("sub")

        success = auth_service.update_user_preferences(
            session,
            user_id,
            {"preferred_sources": sources}
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update sources"
            )

        return {
            "success": True,
            "message": f"Updated {len(sources)} preferred sources",
            "sources": sources
        }

    finally:
        session.close()


@router.get("/categories/available", response_model=dict)
async def get_available_categories():
    """Get list of all available tech categories"""
    categories = [
        {
            "value": cat.value,
            "label": cat.value.replace('_', ' ').title(),
            "description": get_category_description(cat)
        }
        for cat in TechCategory
    ]

    return {
        "success": True,
        "categories": categories,
        "total": len(categories)
    }


def get_category_description(category: TechCategory) -> str:
    """Get description for each category"""
    descriptions = {
        TechCategory.AI_ML: "Artificial Intelligence and Machine Learning news",
        TechCategory.SOFTWARE_DEV: "Software development, programming, and tools",
        TechCategory.BIG_TECH: "News from major tech companies (FAANG, etc.)",
        TechCategory.MILITARY_TECH: "Defense and military technology",
        TechCategory.HOME_TECH: "Smart home and IoT devices",
        TechCategory.AUTO_TECH: "Automotive technology and self-driving cars",
        TechCategory.BLOCKCHAIN: "Blockchain, crypto, and Web3",
        TechCategory.CYBERSECURITY: "Cybersecurity and data privacy",
        TechCategory.CLOUD: "Cloud computing and infrastructure",
        TechCategory.IOT: "Internet of Things",
        TechCategory.ROBOTICS: "Robotics and automation",
        TechCategory.QUANTUM: "Quantum computing",
        TechCategory.BIOTECH: "Biotechnology and life sciences",
        TechCategory.FINTECH: "Financial technology",
        TechCategory.GAMING: "Gaming and esports",
        TechCategory.AR_VR: "AR, VR, and spatial computing",
        TechCategory.SPACE_TECH: "Space exploration and satellite tech",
        TechCategory.GREEN_TECH: "Clean energy and sustainability",
        TechCategory.STARTUP: "Startups and venture capital",
        TechCategory.GENERAL: "General technology news"
    }

    return descriptions.get(category, "Technology news")


@router.post("/keywords/favorite", response_model=dict)
async def add_favorite_keyword(
    keyword: str,
    current_user: dict = Depends(get_current_user)
):
    """Add a favorite keyword to boost related articles"""
    session = db_service.get_session()

    try:
        user_id = current_user.get("sub")
        prefs = auth_service.get_user_preferences(session, user_id)

        if prefs:
            favorite_keywords = prefs.favorite_keywords or []
            if keyword.lower() not in [k.lower() for k in favorite_keywords]:
                favorite_keywords.append(keyword.lower())

                auth_service.update_extended_preferences(
                    session,
                    user_id,
                    {"favorite_keywords": favorite_keywords}
                )

        return {
            "success": True,
            "message": f"Added '{keyword}' to favorites"
        }

    finally:
        session.close()


@router.delete("/keywords/favorite/{keyword}", response_model=dict)
async def remove_favorite_keyword(
    keyword: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a favorite keyword"""
    session = db_service.get_session()

    try:
        user_id = current_user.get("sub")
        prefs = auth_service.get_user_preferences(session, user_id)

        if prefs:
            favorite_keywords = prefs.favorite_keywords or []
            favorite_keywords = [k for k in favorite_keywords if k.lower() != keyword.lower()]

            auth_service.update_extended_preferences(
                session,
                user_id,
                {"favorite_keywords": favorite_keywords}
            )

        return {
            "success": True,
            "message": f"Removed '{keyword}' from favorites"
        }

    finally:
        session.close()
