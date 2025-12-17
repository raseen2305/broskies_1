"""
Database Schema Definitions for GitHub Comprehensive Integration

This module defines the MongoDB schemas and indexes for storing
comprehensive GitHub data including user profiles, repositories,
scan results, and analytics data.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class GitHubUserProfileSchema(BaseModel):
    """Schema for GitHub user profile data"""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str = Field(..., description="Internal user ID (external_username for external scans)")
    login: str = Field(..., description="GitHub username")
    name: Optional[str] = Field(None, description="Full name")
    bio: Optional[str] = Field(None, description="User bio")
    location: Optional[str] = Field(None, description="User location")
    company: Optional[str] = Field(None, description="User company")
    blog: Optional[str] = Field(None, description="User blog/website")
    email: Optional[str] = Field(None, description="Public email")
    twitter_username: Optional[str] = Field(None, description="Twitter handle")
    public_repos: int = Field(0, description="Number of public repositories")
    public_gists: int = Field(0, description="Number of public gists")
    followers: int = Field(0, description="Number of followers")
    following: int = Field(0, description="Number of following")
    created_at: Optional[datetime] = Field(None, description="GitHub account creation date")
    updated_at: Optional[datetime] = Field(None, description="Last GitHub profile update")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    gravatar_id: Optional[str] = Field(None