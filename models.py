"""
Data models for API responses
"""
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request model"""
    Username: str
    Password: str


class LoginResponse(BaseModel):
    """Login response model"""
    AccessToken: str
    Code: str
    Message: str
    ExpireIn: str = Field(description="Token expiration time (e.g., '8h')")
    
    @property
    def is_success(self) -> bool:
        """Check if login was successful"""
        return self.Code == "1"


class APIResponse(BaseModel):
    """Generic API response model"""
    result: Optional[dict] = None
    code: Optional[str] = None
    message: Optional[str] = None
