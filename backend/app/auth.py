import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .models import UserModel, UserRole

SECRET_KEY = "security_research_adaptive_least_privilege_key_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


def hash_password(password: str) -> str:
    salt = "adaptive_salt_2026"
    return hashlib.sha256((salt + password).encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[dict]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None


def get_current_user_required(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    if not token:
        # For convenience in playground testing, return default Researcher session if unauthenticated
        return {"sub": "researcher", "role": UserRole.RESEARCHER.value, "email": "researcher@security.lab"}
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(min_role: UserRole):
    hierarchy = {
        UserRole.VIEWER: 1,
        UserRole.TESTER: 2,
        UserRole.RESEARCHER: 3,
        UserRole.ADMIN: 4
    }

    def role_checker(user: dict = Depends(get_current_user_required)):
        user_role_str = user.get("role", UserRole.VIEWER.value)
        try:
            user_role = UserRole(user_role_str)
        except ValueError:
            user_role = UserRole.VIEWER

        if hierarchy.get(user_role, 1) < hierarchy.get(min_role, 1):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires '{min_role.value}' role privileges."
            )
        return user

    return role_checker
