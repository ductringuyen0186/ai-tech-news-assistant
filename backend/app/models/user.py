"""
User and Preference Models
===========================
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from . import Base


class TechCategory(str, Enum):
    """Technology categories for user preferences"""
    AI_ML = "ai_ml"
    SOFTWARE_DEV = "software_dev"
    BIG_TECH = "big_tech"
    MILITARY_TECH = "military_tech"
    HOME_TECH = "home_tech"
    AUTO_TECH = "auto_tech"
    BLOCKCHAIN = "blockchain"
    CYBERSECURITY = "cybersecurity"
    CLOUD = "cloud"
    IOT = "iot"
    ROBOTICS = "robotics"
    QUANTUM = "quantum"
    BIOTECH = "biotech"
    FINTECH = "fintech"
    GAMING = "gaming"
    AR_VR = "ar_vr"
    SPACE_TECH = "space_tech"
    GREEN_TECH = "green_tech"
    STARTUP = "startup"
    GENERAL = "general"


# Association table for user-article bookmarks
user_bookmarks = Table(
    'user_bookmarks',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id', ondelete='CASCADE')),
    Column('article_id', String, ForeignKey('articles.id', ondelete='CASCADE')),
    Column('bookmarked_at', DateTime, default=func.now())
)


# Association table for reading history
reading_history = Table(
    'reading_history',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id', ondelete='CASCADE')),
    Column('article_id', String, ForeignKey('articles.id', ondelete='CASCADE')),
    Column('read_at', DateTime, default=func.now()),
    Column('read_duration_seconds', Integer, default=0)
)


class UserDB(Base):
    """SQLAlchemy User model"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)

    # Preferences (stored as JSON)
    preferred_categories = Column(JSON, default=list)  # List of TechCategory values
    preferred_sources = Column(JSON, default=list)  # List of news source names
    email_notifications = Column(Boolean, default=True)
    digest_frequency = Column(String(20), default="daily")  # daily, weekly, none

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

    # Relationships
    # bookmarks and reading_history will be accessed via association tables

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class UserPreferenceDB(Base):
    """Extended user preferences"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Reading preferences
    preferred_article_length = Column(String(20), default="medium")  # short, medium, long
    reading_time_minutes = Column(Integer, default=5)  # avg time willing to read

    # Content preferences
    show_images = Column(Boolean, default=True)
    auto_summarize = Column(Boolean, default=True)
    summary_length = Column(String(20), default="short")  # short, medium, detailed

    # Language preferences
    preferred_language = Column(String(10), default="en")
    auto_translate = Column(Boolean, default=False)

    # Feed customization
    min_relevance_score = Column(Integer, default=50)  # 0-100
    exclude_keywords = Column(JSON, default=list)  # List of keywords to exclude
    favorite_keywords = Column(JSON, default=list)  # Boost articles with these keywords

    # Notification settings
    push_notifications = Column(Boolean, default=False)
    notification_time = Column(String(10), default="09:00")  # HH:MM format

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# Pydantic models for API

class UserCreate(BaseModel):
    """User registration model"""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

    @validator('username')
    def username_valid(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be between 3 and 50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()

    @validator('password')
    def password_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User update model"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    preferred_categories: Optional[List[TechCategory]] = None
    preferred_sources: Optional[List[str]] = None
    email_notifications: Optional[bool] = None
    digest_frequency: Optional[str] = None


class User(BaseModel):
    """User response model"""
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_premium: bool
    preferred_categories: List[str] = []
    preferred_sources: List[str] = []
    email_notifications: bool
    digest_frequency: str
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserPreferenceUpdate(BaseModel):
    """User preference update model"""
    preferred_article_length: Optional[str] = None
    reading_time_minutes: Optional[int] = None
    show_images: Optional[bool] = None
    auto_summarize: Optional[bool] = None
    summary_length: Optional[str] = None
    preferred_language: Optional[str] = None
    auto_translate: Optional[bool] = None
    min_relevance_score: Optional[int] = None
    exclude_keywords: Optional[List[str]] = None
    favorite_keywords: Optional[List[str]] = None
    push_notifications: Optional[bool] = None
    notification_time: Optional[str] = None


class UserPreference(BaseModel):
    """User preference response model"""
    user_id: str
    preferred_article_length: str
    reading_time_minutes: int
    show_images: bool
    auto_summarize: bool
    summary_length: str
    preferred_language: str
    auto_translate: bool
    min_relevance_score: int
    exclude_keywords: List[str]
    favorite_keywords: List[str]
    push_notifications: bool
    notification_time: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[str] = None
    email: Optional[str] = None
