"""
User Profile and Regional Comparison Models
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class UserProfile(BaseModel):
    """User profile information for regional/university comparison"""
    
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="User ID from auth system")
    github_username: str = Field(..., description="GitHub username")
    full_name: str = Field(..., description="User's full name")
    university: str = Field(..., description="University name")
    university_short: str = Field(..., description="University short name/code")
    description: Optional[str] = Field(None, description="User description/bio")
    nationality: str = Field(..., description="User's nationality")
    state: str = Field(..., description="State/Province")
    district: str = Field(..., description="District/City")
    region: str = Field(..., description="Region/Country code")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Scoring system fields
    overall_score: Optional[float] = Field(None, description="Overall developer score (0-100)")
    flagship_count: int = Field(default=0, description="Number of flagship repositories")
    significant_count: int = Field(default=0, description="Number of significant repositories")
    supporting_count: int = Field(default=0, description="Number of supporting repositories")
    
    # Scan and analysis status
    scan_completed: bool = Field(default=False, description="Stage 1 scan completed")
    scanned_at: Optional[datetime] = Field(None, description="Last scan timestamp")
    analysis_completed: bool = Field(default=False, description="Stage 2 analysis completed")
    analyzed_at: Optional[datetime] = Field(None, description="Last analysis timestamp")
    
    class Config:
        populate_by_name = True

class UserProfileCreate(BaseModel):
    """Model for creating user profile"""
    
    full_name: str = Field(..., min_length=2, max_length=100)
    github_username: str = Field(..., min_length=1, max_length=100)
    university: str = Field(..., min_length=2, max_length=200)
    university_short: Optional[str] = Field(None, min_length=2, max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    nationality: str = Field(..., min_length=2, max_length=50)
    state: str = Field(..., min_length=2, max_length=100)
    district: str = Field(..., min_length=2, max_length=100)
    region: Optional[str] = Field(None, min_length=2, max_length=10)

class UserProfileUpdate(BaseModel):
    """Model for updating user profile"""
    
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    github_username: Optional[str] = Field(None, min_length=1, max_length=100)
    university: Optional[str] = Field(None, min_length=2, max_length=200)
    university_short: Optional[str] = Field(None, min_length=2, max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    nationality: Optional[str] = Field(None, min_length=2, max_length=50)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    district: Optional[str] = Field(None, min_length=2, max_length=100)
    region: Optional[str] = Field(None, min_length=2, max_length=10)

class UserOverallDetails(BaseModel):
    """Overall user details for comparison"""
    
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="User's name")
    github_username: str = Field(..., description="GitHub username")
    repositories_count: int = Field(default=0)
    overall_score: float = Field(default=0.0)
    acid_scores: Dict[str, float] = Field(default_factory=dict)
    account_details: Dict[str, Any] = Field(default_factory=dict)
    last_scan_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

class RegionalScore(BaseModel):
    """Regional comparison scores"""
    
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="User ID")
    github_username: str = Field(..., description="GitHub username")
    name: str = Field(..., description="User's name")
    region: str = Field(..., description="Region/Country code")
    state: str = Field(..., description="State")
    district: str = Field(..., description="District")
    overall_score: float = Field(..., description="User's overall score")
    percentile_region: float = Field(..., description="Percentile in region")
    rank_in_region: int = Field(..., description="Rank in region")
    total_users_in_region: int = Field(..., description="Total users in region")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

class UniversityScore(BaseModel):
    """University comparison scores"""
    
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="User ID")
    github_username: str = Field(..., description="GitHub username")
    name: str = Field(..., description="User's name")
    university: str = Field(..., description="University name")
    university_short: str = Field(..., description="University short name")
    overall_score: float = Field(..., description="User's overall score")
    percentile_university: float = Field(..., description="Percentile in university")
    rank_in_university: int = Field(..., description="Rank in university")
    total_users_in_university: int = Field(..., description="Total users in university")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True



# Predefined data for dropdowns
COUNTRIES = {
    "IN": "India",
    "US": "United States",
    "UK": "United Kingdom",
    "CA": "Canada",
    "AU": "Australia",
    "DE": "Germany",
    "FR": "France",
    "JP": "Japan",
    "CN": "China",
    "SG": "Singapore"
}

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry", "Chandigarh",
    "Andaman and Nicobar Islands", "Dadra and Nagar Haveli and Daman and Diu",
    "Lakshadweep"
]

POPULAR_UNIVERSITIES = [
    {"name": "Indian Institute of Technology Delhi", "short": "IIT Delhi"},
    {"name": "Indian Institute of Technology Bombay", "short": "IIT Bombay"},
    {"name": "Indian Institute of Technology Madras", "short": "IIT Madras"},
    {"name": "Indian Institute of Technology Kanpur", "short": "IIT Kanpur"},
    {"name": "Indian Institute of Technology Kharagpur", "short": "IIT Kharagpur"},
    {"name": "Indian Institute of Science", "short": "IISc"},
    {"name": "Thiagarajar College of Engineering", "short": "TCE"},
    {"name": "Anna University", "short": "AU"},
    {"name": "Vellore Institute of Technology", "short": "VIT"},
    {"name": "SRM Institute of Science and Technology", "short": "SRM"},
    {"name": "Manipal Institute of Technology", "short": "MIT Manipal"},
    {"name": "Birla Institute of Technology and Science", "short": "BITS"},
    {"name": "National Institute of Technology Trichy", "short": "NIT Trichy"},
    {"name": "Delhi Technological University", "short": "DTU"},
    {"name": "Netaji Subhas University of Technology", "short": "NSUT"}
]

# Optimized: Load Indian colleges from JSON file with lazy loading and caching
_INDIAN_COLLEGES_CACHE = None

def load_indian_colleges():
    """Load Indian colleges from JSON file with caching"""
    global _INDIAN_COLLEGES_CACHE
    
    # Return cached data if available
    if _INDIAN_COLLEGES_CACHE is not None:
        return _INDIAN_COLLEGES_CACHE
    
    import json
    import os
    
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'indian_colleges.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            colleges_data = json.load(f)
        
        # Optimized: Use set for deduplication, then sort once
        unique_colleges = {item['college'] for item in colleges_data if 'college' in item}
        _INDIAN_COLLEGES_CACHE = sorted(unique_colleges)
        
        return _INDIAN_COLLEGES_CACHE
    except Exception as e:
        print(f"Error loading colleges: {e}")
        # Return fallback list if file not found
        fallback = [uni['name'] for uni in POPULAR_UNIVERSITIES]
        _INDIAN_COLLEGES_CACHE = fallback
        return fallback

# Lazy load colleges list (only loaded when accessed)
def get_indian_colleges():
    """Get Indian colleges list (lazy loaded)"""
    return load_indian_colleges()

# For backward compatibility
# Expose valid list for consumers
INDIAN_COLLEGES = get_indian_colleges()