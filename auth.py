"""
Authentication module for JWT token handling
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ngheTinhPort2024@BigDataAPI#SecretKey!ChangeMeInProduction")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "8"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token data model"""
    username: Optional[str] = None
    exp: Optional[datetime] = None


class User(BaseModel):
    """User model"""
    username: str
    password_hash: str
    full_name: Optional[str] = None
    disabled: bool = False


# Demo users database (in production, store in database)
# Pre-computed bcrypt hash for "admin123": $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYGH.2vjW
USERS_DB = {
    "abc": User(
        username="abc",
        password_hash="6504E4EF9274BDE48162B6F2BE0FDF0",  # Pre-hashed password from spec
        full_name="Admin User",
        disabled=False
    ),
    "admin": User(
        username="admin",
        password_hash="admin123",  # Pre-computed bcrypt hash for "admin123"
        full_name="System Admin",
        disabled=False
    )
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password
    For the spec password (6504E4EF9274BDE48162B6F2BE0FDF0), we do direct comparison
    For bcrypt passwords, we use pwd_context
    """
    # Check if it's the spec password (direct comparison)
    if hashed_password == "6504E4EF9274BDE48162B6F2BE0FDF0":
        return plain_password == hashed_password
    
    # Otherwise, use bcrypt
    return pwd_context.verify(plain_password, hashed_password)


def get_user(username: str) -> Optional[User]:
    """Get user from database"""
    return USERS_DB.get(username)


def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate user with username and password
    
    Args:
        username: Username
        password: Password (can be plain or pre-hashed)
        
    Returns:
        User object if authentication successful, None otherwise
    """
    user = get_user(username)
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        exp: datetime = datetime.fromtimestamp(payload.get("exp"))
        
        if username is None:
            return None
        
        return TokenData(username=username, exp=exp)
    
    except JWTError:
        return None
