"""
Eleos Authentication & JWT Security Service
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.config import settings
from database.models import User, NGOProfile

# Demo personas mapped to database seed users
DEMO_PERSONAS = {
    "donor": "riya.sharma@example.com",
    "ngo_admin": "hoperelief@eleos.app",
    "reviewer": "reviewer@eleos.app",
    "volunteer": "kavya.patel@example.com",
    "admin": "admin@eleos.app",
    "ngo_annapurna": "annapurna@eleos.app",
    "ngo_teachforchange": "teachforchange@eleos.app",
    "ngo_fake": "globalaid.fake@eleos.app",
}


class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify plain password against bcrypt hash."""
        if not hashed_password:
            return False
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate bcrypt hash for password."""
        salt = bcrypt.gensalt(10)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create signed JWT access token with expiration."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT access token."""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError:
            return None

    def authenticate_user(
        self,
        db: Session,
        email: str,
        password: str
    ) -> Optional[User]:
        """Verify user credentials and return User if valid."""
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    def register_user(
        self,
        db: Session,
        email: str,
        password: str,
        name: str,
        role: str = "donor",
        phone: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> User:
        """Create and persist a new user in database."""
        normalized_email = email.strip().lower()
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            raise ValueError(f"User with email '{normalized_email}' already exists.")

        valid_roles = {"donor", "ngo_admin", "reviewer", "admin", "volunteer"}
        if role not in valid_roles:
            raise ValueError(f"Invalid role '{role}'. Must be one of {valid_roles}.")

        password_hash = self.get_password_hash(password)
        user = User(
            id=uuid.uuid4(),
            email=normalized_email,
            password_hash=password_hash,
            name=name.strip(),
            phone=phone,
            role=role,
            avatar_url=avatar_url or f"https://api.dicebear.com/7.x/avataaars/svg?seed={normalized_email}"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_demo_persona_token(
        self,
        db: Session,
        persona_key: str
    ) -> Dict[str, Any]:
        """Generate an instant JWT token for pre-seeded demo accounts."""
        normalized_key = persona_key.strip().lower()
        target_email = DEMO_PERSONAS.get(normalized_key)
        
        if not target_email:
            # Fallback: check if persona_key is a direct email
            target_email = normalized_key

        user = db.query(User).filter(User.email == target_email).first()
        if not user:
            raise ValueError(f"Demo persona '{persona_key}' (email: {target_email}) not found in seed dataset.")

        # If user is ngo_admin, fetch their NGO profile ID
        ngo_id = None
        if user.role == "ngo_admin":
            ngo = db.query(NGOProfile).filter(NGOProfile.user_id == user.id).first()
            if ngo:
                ngo_id = str(ngo.id)

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "ngo_id": ngo_id
        }
        access_token = self.create_access_token(data=token_data)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "avatar_url": user.avatar_url,
                "ngo_id": ngo_id
            }
        }


auth_service = AuthService()
