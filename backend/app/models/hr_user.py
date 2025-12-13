"""
HR User Models for HR Dashboard Authentication and Management
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from bson import ObjectId


class HRUser(BaseModel):
    """HR User model with Google OAuth fields"""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    email: EmailStr
    google_id: str
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    email_verified: bool = True
    is_approved: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True


class HRUserCreate(BaseModel):
    """Model for creating HR user"""
    
    email: EmailStr
    google_id: str
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    email_verified: bool = True


class HRUserUpdate(BaseModel):
    """Model for updating HR user"""
    
    full_name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    last_login: Optional[datetime] = None
    is_active: Optional[bool] = None


class HRUserInDB(HRUser):
    """HR User model as stored in database"""
    pass


class HRRegistration(BaseModel):
    """HR Registration form submission model"""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    email: EmailStr
    company: str
    role: str
    contact_info: Optional[str] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed: bool = False
    approved: bool = False
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None


class HRRegistrationCreate(BaseModel):
    """Model for creating HR registration"""
    
    email: EmailStr
    company: str
    role: str
    contact_info: Optional[str] = None


class ApprovedHRUser(BaseModel):
    """Approved HR user model for access control"""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    email: EmailStr
    approved_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by: str
    notes: Optional[str] = None


class ApprovedHRUserCreate(BaseModel):
    """Model for creating approved HR user"""
    
    email: EmailStr
    approved_by: str
    notes: Optional[str] = None


# Response Models for API

class HRUserResponse(BaseModel):
    """HR User response model for API"""
    
    id: str
    email: str
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    is_approved: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class HRRegistrationResponse(BaseModel):
    """HR Registration response model for API"""
    
    id: str
    email: str
    company: str
    role: str
    submitted_at: datetime
    reviewed: bool
    approved: bool


class ApprovalStatusResponse(BaseModel):
    """Response model for checking approval status"""
    
    email: str
    is_approved: bool
    message: str
