from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

# Simple string-based ID for Pydantic v2 compatibility
class User(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    email: EmailStr
    github_username: Optional[str] = None
    github_token: Optional[str] = None
    user_type: str = "developer"  # "developer" or "hr"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_scan: Optional[datetime] = None
    profile_visibility: str = "public"
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    github_username: Optional[str] = None
    github_token: Optional[str] = None
    user_type: str = "developer"

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    github_username: Optional[str] = None
    profile_visibility: Optional[str] = None

class UserInDB(User):
    pass

class HRUser(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    email: EmailStr
    company: str
    role: str
    hiring_needs: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    access_level: str = "basic"
    is_active: bool = True

class HRUserCreate(BaseModel):
    email: EmailStr
    company: str
    role: str
    hiring_needs: Optional[str] = None