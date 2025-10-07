"""
Authentication Service
=====================
"""
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.user import UserDB, UserPreferenceDB, UserCreate, User, Token

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication and authorization service"""

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self,
        user_id: str,
        email: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire)

        to_encode = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow()
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"Token decode failed: {e}")
            return None

    def generate_user_id(self, email: str) -> str:
        """Generate unique user ID from email"""
        return hashlib.sha256(f"{email}{secrets.token_hex(8)}".encode()).hexdigest()[:16]

    def create_user(
        self,
        session: Session,
        user_data: UserCreate
    ) -> Optional[User]:
        """Create new user account"""

        try:
            # Check if user exists
            existing = session.query(UserDB).filter(
                (UserDB.email == user_data.email) | (UserDB.username == user_data.username)
            ).first()

            if existing:
                logger.warning(f"User already exists: {user_data.email}")
                return None

            # Create user
            user_id = self.generate_user_id(user_data.email)
            hashed_password = self.hash_password(user_data.password)

            db_user = UserDB(
                id=user_id,
                email=user_data.email,
                username=user_data.username.lower(),
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                is_active=True,
                is_verified=False,
                preferred_categories=[],
                preferred_sources=[]
            )

            session.add(db_user)

            # Create default preferences
            db_preferences = UserPreferenceDB(
                user_id=user_id,
                preferred_article_length="medium",
                reading_time_minutes=5,
                show_images=True,
                auto_summarize=True,
                summary_length="short",
                preferred_language="en",
                auto_translate=False,
                min_relevance_score=50,
                exclude_keywords=[],
                favorite_keywords=[]
            )

            session.add(db_preferences)
            session.commit()
            session.refresh(db_user)

            logger.info(f"User created: {user_data.email}")

            return User.from_orm(db_user)

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user: {e}")
            return None

    def authenticate_user(
        self,
        session: Session,
        email: str,
        password: str
    ) -> Optional[UserDB]:
        """Authenticate user with email and password"""

        user = session.query(UserDB).filter(UserDB.email == email).first()

        if not user:
            return None

        if not self.verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        session.commit()

        return user

    def get_user_by_id(self, session: Session, user_id: str) -> Optional[UserDB]:
        """Get user by ID"""
        return session.query(UserDB).filter(UserDB.id == user_id).first()

    def get_user_by_email(self, session: Session, email: str) -> Optional[UserDB]:
        """Get user by email"""
        return session.query(UserDB).filter(UserDB.email == email).first()

    def update_user_preferences(
        self,
        session: Session,
        user_id: str,
        update_data: dict
    ) -> bool:
        """Update user basic preferences"""

        try:
            user = session.query(UserDB).filter(UserDB.id == user_id).first()

            if not user:
                return False

            # Update allowed fields
            for key, value in update_data.items():
                if hasattr(user, key) and key not in ['id', 'email', 'hashed_password']:
                    setattr(user, key, value)

            user.updated_at = datetime.utcnow()
            session.commit()

            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error updating user preferences: {e}")
            return False

    def update_extended_preferences(
        self,
        session: Session,
        user_id: str,
        update_data: dict
    ) -> bool:
        """Update extended user preferences"""

        try:
            prefs = session.query(UserPreferenceDB).filter(
                UserPreferenceDB.user_id == user_id
            ).first()

            if not prefs:
                # Create if doesn't exist
                prefs = UserPreferenceDB(user_id=user_id)
                session.add(prefs)

            # Update fields
            for key, value in update_data.items():
                if hasattr(prefs, key) and key != 'id':
                    setattr(prefs, key, value)

            prefs.updated_at = datetime.utcnow()
            session.commit()

            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error updating extended preferences: {e}")
            return False

    def get_user_preferences(self, session: Session, user_id: str) -> Optional[UserPreferenceDB]:
        """Get extended user preferences"""
        return session.query(UserPreferenceDB).filter(
            UserPreferenceDB.user_id == user_id
        ).first()


# Global auth service instance
auth_service = AuthService()
