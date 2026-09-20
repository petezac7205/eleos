"""
FastAPI Router for Authentication & Role-Based Access Control
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User, NGOProfile
from backend.services.auth_service import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication & User Management"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2)
    role: str = Field(default="donor", description="Role: donor, volunteer, or ngo_admin")
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class DemoSwitchRequest(BaseModel):
    persona: Optional[str] = None
    role: Optional[str] = None

    @property
    def key(self) -> str:
        return self.persona or self.role or "donor"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    ngo_id: Optional[str] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# -----------------------------------------------------------------------------
# Dependency Providers for Route Protection
# -----------------------------------------------------------------------------

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate user from JWT token."""
    raw_token = token
    if not raw_token and authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = auth_service.decode_access_token(raw_token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account associated with this token no longer exists."
        )

    return user


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optionally extract user if token present; return None otherwise."""
    try:
        return get_current_user(token=token, authorization=authorization, db=db)
    except HTTPException:
        return None


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = set(allowed_roles)

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role in {list(self.allowed_roles)}, current role: '{current_user.role}'."
            )
        return current_user


# Role-specific dependency shortcuts
require_admin = RoleChecker(["admin"])
require_ngo_admin = RoleChecker(["ngo_admin", "admin"])
require_reviewer = RoleChecker(["reviewer", "admin"])
require_volunteer = RoleChecker(["volunteer", "admin"])
require_donor = RoleChecker(["donor", "admin"])


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with email and password, returning signed JWT token."""
    user = auth_service.authenticate_user(db=db, email=req.email, password=req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

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
    access_token = auth_service.create_access_token(data=token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "ngo_id": ngo_id
        }
    }


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    try:
        user = auth_service.register_user(
            db=db,
            email=req.email,
            password=req.password,
            name=req.name,
            role=req.role,
            phone=req.phone,
            avatar_url=req.avatar_url
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "ngo_id": None
    }
    access_token = auth_service.create_access_token(data=token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "ngo_id": None
        }
    }


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch current user profile and permissions from JWT token."""
    ngo_id = None
    if current_user.role == "ngo_admin":
        ngo = db.query(NGOProfile).filter(NGOProfile.user_id == current_user.id).first()
        if ngo:
            ngo_id = str(ngo.id)

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "phone": current_user.phone,
        "avatar_url": current_user.avatar_url,
        "ngo_id": ngo_id
    }


@router.post("/demo-switch", response_model=AuthResponse)
def demo_switch(req: DemoSwitchRequest, db: Session = Depends(get_db)):
    """
    1-Click Persona Switcher for Hackathons and Live Demos.
    Instantly returns authenticated JWT for pre-seeded test personas:
    - 'donor' -> Riya Sharma (verified donor)
    - 'ngo_admin' -> HopeRelief Foundation Admin
    - 'reviewer' -> Vikram Mehra (Senior Auditor)
    - 'volunteer' -> Kavya Patel (Active volunteer)
    - 'admin' -> Eleos Platform Admin
    """
    try:
        return auth_service.get_demo_persona_token(db=db, persona_key=req.key)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
