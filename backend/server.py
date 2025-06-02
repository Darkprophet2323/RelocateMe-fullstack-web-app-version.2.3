from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
import hashlib
import requests
import asyncio
from passlib.context import CryptContext


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = "relocate-me-secret-key-2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="Relocate Me API", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    current_step: int = 1
    completed_steps: List[int] = Field(default_factory=list)

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ProgressUpdate(BaseModel):
    step_id: int
    completed: bool
    notes: Optional[str] = None

class TimelineStep(BaseModel):
    id: int
    title: str
    description: str
    category: str
    estimated_days: int
    dependencies: List[int] = Field(default_factory=list)
    resources: List[str] = Field(default_factory=list)
    is_completed: bool = False
    completion_date: Optional[datetime] = None

class PasswordReset(BaseModel):
    username: str
    
class PasswordResetComplete(BaseModel):
    username: str
    new_password: str
    reset_code: str

# Comprehensive relocation timeline data
RELOCATION_TIMELINE = [
    # Planning Phase (Days -180 to -90)
    {"id": 1, "title": "Initial Research & Decision", "description": "Research Peak District areas, cost of living, and lifestyle", "category": "Planning", "estimated_days": 7, "dependencies": [], "resources": ["Peak District National Park Authority", "UK Government Moving Guide"]},
    {"id": 2, "title": "Create Relocation Budget", "description": "Calculate moving costs, visa fees, initial living expenses", "category": "Planning", "estimated_days": 3, "dependencies": [1], "resources": ["UK Cost Calculator", "Moving Cost Estimator"]},
    {"id": 3, "title": "Timeline & Milestones", "description": "Set target dates for visa, job search, housing, and moving", "category": "Planning", "estimated_days": 2, "dependencies": [2], "resources": ["Project Management Templates"]},
    
    # Visa & Legal (Days -150 to -60)
    {"id": 4, "title": "Visa Research", "description": "Determine visa type needed (work, skilled worker, family, etc.)", "category": "Visa & Legal", "estimated_days": 5, "dependencies": [1], "resources": ["UK Government Visa Guide", "Immigration Lawyer Directory"]},
    {"id": 5, "title": "Document Preparation", "description": "Gather birth certificate, passport, education certificates, etc.", "category": "Visa & Legal", "estimated_days": 14, "dependencies": [4], "resources": ["Document Checklist", "Apostille Services"]},
    {"id": 6, "title": "Visa Application", "description": "Submit visa application with all required documents", "category": "Visa & Legal", "estimated_days": 21, "dependencies": [5], "resources": ["UK Visa Application Centre"]},
    {"id": 7, "title": "Background Checks", "description": "Police clearance, criminal record checks, medical exams", "category": "Visa & Legal", "estimated_days": 30, "dependencies": [6], "resources": ["FBI Background Check", "Medical Exam Centers"]},
    
    # Employment (Days -120 to -30)
    {"id": 8, "title": "Job Market Research", "description": "Research job opportunities in Peak District area", "category": "Employment", "estimated_days": 7, "dependencies": [1], "resources": ["Indeed UK", "LinkedIn UK Jobs", "Reed.co.uk"]},
    {"id": 9, "title": "CV/Resume Update", "description": "Adapt resume for UK format and standards", "category": "Employment", "estimated_days": 3, "dependencies": [8], "resources": ["UK CV Templates", "Career Services"]},
    {"id": 10, "title": "Job Applications", "description": "Apply for positions in target area", "category": "Employment", "estimated_days": 45, "dependencies": [9], "resources": ["Job Search Platforms", "Recruitment Agencies"]},
    {"id": 11, "title": "Interviews & Offers", "description": "Participate in interviews and negotiate offers", "category": "Employment", "estimated_days": 30, "dependencies": [10], "resources": ["Interview Preparation", "Salary Negotiation Guide"]},
    
    # Housing (Days -90 to -14)
    {"id": 12, "title": "Housing Research", "description": "Research neighborhoods, property types, rental market", "category": "Housing", "estimated_days": 14, "dependencies": [1], "resources": ["Rightmove", "Zoopla", "SpareRoom"]},
    {"id": 13, "title": "Virtual Viewings", "description": "Arrange virtual property viewings", "category": "Housing", "estimated_days": 21, "dependencies": [12], "resources": ["Property Viewing Apps", "Estate Agents"]},
    {"id": 14, "title": "Housing Applications", "description": "Apply for rental properties or purchase", "category": "Housing", "estimated_days": 30, "dependencies": [13], "resources": ["Rental Application Forms", "Mortgage Brokers"]},
    {"id": 15, "title": "Lease/Purchase Agreement", "description": "Finalize housing arrangements", "category": "Housing", "estimated_days": 14, "dependencies": [14], "resources": ["Legal Services", "Property Lawyers"]},
    
    # Financial (Days -60 to -7)
    {"id": 16, "title": "UK Bank Account Setup", "description": "Research and apply for UK bank accounts", "category": "Financial", "estimated_days": 21, "dependencies": [6], "resources": ["Barclays", "HSBC", "Lloyds", "Monzo"]},
    {"id": 17, "title": "Credit History Transfer", "description": "Establish UK credit history and financial profile", "category": "Financial", "estimated_days": 14, "dependencies": [16], "resources": ["Expat Credit Services", "Credit Reference Agencies"]},
    {"id": 18, "title": "International Money Transfer", "description": "Set up currency exchange and money transfer services", "category": "Financial", "estimated_days": 7, "dependencies": [16], "resources": ["Wise", "Western Union", "CurrencyFair"]},
    {"id": 19, "title": "Insurance Setup", "description": "Health, contents, and travel insurance", "category": "Financial", "estimated_days": 7, "dependencies": [15], "resources": ["NHS Registration", "Insurance Brokers"]},
    
    # Logistics (Days -30 to +7)
    {"id": 20, "title": "Moving Company Research", "description": "Get quotes from international moving companies", "category": "Logistics", "estimated_days": 14, "dependencies": [15], "resources": ["International Movers", "Shipping Companies"]},
    {"id": 21, "title": "Shipping Arrangements", "description": "Book moving services and arrange shipping", "category": "Logistics", "estimated_days": 7, "dependencies": [20], "resources": ["Moving Contracts", "Shipping Insurance"]},
    {"id": 22, "title": "Travel Booking", "description": "Book flights and initial accommodation", "category": "Logistics", "estimated_days": 3, "dependencies": [6], "resources": ["Flight Booking Sites", "Temporary Accommodation"]},
    {"id": 23, "title": "Packing & Shipping", "description": "Pack belongings and ship to UK", "category": "Logistics", "estimated_days": 7, "dependencies": [21], "resources": ["Packing Services", "Customs Documentation"]},
    
    # US Exit Procedures (Days -14 to 0)
    {"id": 24, "title": "US Affairs Settlement", "description": "Cancel utilities, close accounts, notify services", "category": "US Exit", "estimated_days": 14, "dependencies": [22], "resources": ["Utility Companies", "Service Providers"]},
    {"id": 25, "title": "Address Changes", "description": "Update address with IRS, banks, subscriptions", "category": "US Exit", "estimated_days": 7, "dependencies": [24], "resources": ["USPS Mail Forwarding", "IRS Forms"]},
    {"id": 26, "title": "Final Preparations", "description": "Last-minute arrangements and goodbyes", "category": "US Exit", "estimated_days": 3, "dependencies": [25], "resources": ["Farewell Checklist"]},
    
    # UK Arrival (Days 1 to 30)
    {"id": 27, "title": "Arrival & Quarantine", "description": "Arrive in UK, complete any quarantine requirements", "category": "UK Arrival", "estimated_days": 14, "dependencies": [26], "resources": ["UK Border Control", "COVID Guidelines"]},
    {"id": 28, "title": "Temporary Accommodation", "description": "Check into temporary housing while waiting for permanent", "category": "UK Arrival", "estimated_days": 7, "dependencies": [27], "resources": ["Hotels", "Airbnb", "Serviced Apartments"]},
    {"id": 29, "title": "Essential Registrations", "description": "Register with GP, council, utilities", "category": "UK Arrival", "estimated_days": 7, "dependencies": [28], "resources": ["NHS Registration", "Council Tax", "Utility Providers"]},
    {"id": 30, "title": "National Insurance Number", "description": "Apply for National Insurance number", "category": "UK Arrival", "estimated_days": 14, "dependencies": [29], "resources": ["HMRC", "Job Centre Plus"]},
    
    # Settlement (Days 15 to 60)
    {"id": 31, "title": "Permanent Housing Move", "description": "Move into permanent accommodation", "category": "Settlement", "estimated_days": 3, "dependencies": [15, 28], "resources": ["Moving Services", "Utility Connections"]},
    {"id": 32, "title": "Work Commencement", "description": "Start new job or business", "category": "Settlement", "estimated_days": 1, "dependencies": [11, 30], "resources": ["Employment Contracts", "Tax Information"]},
    {"id": 33, "title": "Local Integration", "description": "Join local groups, find services, explore area", "category": "Settlement", "estimated_days": 30, "dependencies": [31], "resources": ["Community Groups", "Local Services", "Tourism Information"]},
    {"id": 34, "title": "Long-term Setup", "description": "Establish routines, friendships, local connections", "category": "Settlement", "estimated_days": 60, "dependencies": [33], "resources": ["Social Groups", "Hobby Clubs", "Professional Networks"]}
]

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return User(**user)

# Initialize default user on startup
async def create_default_user():
    existing_user = await db.users.find_one({"username": "relocate_user"})
    if not existing_user:
        hashed_password = get_password_hash("SecurePass2025!")
        default_user = User(
            username="relocate_user",
            email="relocate@example.com",
            hashed_password=hashed_password,
            current_step=1,
            completed_steps=[1, 2, 3, 8, 12]  # Some example completed steps
        )
        await db.users.insert_one(default_user.dict())
        print("Default user created successfully")

# Password reset endpoints
@api_router.post("/auth/reset-password")
async def request_password_reset(reset_request: PasswordReset):
    user = await db.users.find_one({"username": reset_request.username})
    if not user:
        return {"message": "If the username exists, a reset code will be provided."}
    
    reset_code = "RESET2025"
    await db.password_resets.insert_one({
        "username": reset_request.username,
        "reset_code": reset_code,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    })
    
    return {
        "message": "Reset code generated successfully.",
        "reset_code": reset_code,
        "note": "In production, this code would be sent to your email address."
    }

@api_router.post("/auth/complete-password-reset")
async def complete_password_reset(reset_data: PasswordResetComplete):
    reset_record = await db.password_resets.find_one({
        "username": reset_data.username,
        "reset_code": reset_data.reset_code
    })
    
    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset code"
        )
    
    if datetime.utcnow() > reset_record["expires_at"]:
        await db.password_resets.delete_one({"_id": reset_record["_id"]})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code has expired"
        )
    
    hashed_password = get_password_hash(reset_data.new_password)
    await db.users.update_one(
        {"username": reset_data.username},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    await db.password_resets.delete_one({"_id": reset_record["_id"]})
    return {"message": "Password reset successfully"}

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"username": user_credentials.username})
    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Timeline and Progress endpoints
@api_router.get("/timeline/full")
async def get_full_timeline(current_user: User = Depends(get_current_user)):
    user_completed_steps = current_user.completed_steps
    timeline_with_status = []
    
    for step in RELOCATION_TIMELINE:
        step_copy = step.copy()
        step_copy["is_completed"] = step["id"] in user_completed_steps
        timeline_with_status.append(step_copy)
    
    return {
        "timeline": timeline_with_status,
        "total_steps": len(RELOCATION_TIMELINE),
        "completed_steps": len(user_completed_steps),
        "completion_percentage": (len(user_completed_steps) / len(RELOCATION_TIMELINE)) * 100,
        "current_phase": get_current_phase(user_completed_steps)
    }

@api_router.get("/timeline/by-category")
async def get_timeline_by_category(current_user: User = Depends(get_current_user)):
    user_completed_steps = current_user.completed_steps
    categories = {}
    
    for step in RELOCATION_TIMELINE:
        category = step["category"]
        if category not in categories:
            categories[category] = {
                "name": category,
                "steps": [],
                "total_steps": 0,
                "completed_steps": 0
            }
        
        step_copy = step.copy()
        step_copy["is_completed"] = step["id"] in user_completed_steps
        categories[category]["steps"].append(step_copy)
        categories[category]["total_steps"] += 1
        
        if step["id"] in user_completed_steps:
            categories[category]["completed_steps"] += 1
    
    # Calculate completion percentage for each category
    for category in categories.values():
        if category["total_steps"] > 0:
            category["completion_percentage"] = (category["completed_steps"] / category["total_steps"]) * 100
        else:
            category["completion_percentage"] = 0
    
    return categories

@api_router.post("/timeline/update-progress")
async def update_step_progress(progress: ProgressUpdate, current_user: User = Depends(get_current_user)):
    user_completed_steps = current_user.completed_steps.copy()
    
    if progress.completed and progress.step_id not in user_completed_steps:
        user_completed_steps.append(progress.step_id)
    elif not progress.completed and progress.step_id in user_completed_steps:
        user_completed_steps.remove(progress.step_id)
    
    # Update user in database
    await db.users.update_one(
        {"username": current_user.username},
        {"$set": {"completed_steps": user_completed_steps}}
    )
    
    # Log progress update
    await db.progress_logs.insert_one({
        "user_id": current_user.id,
        "step_id": progress.step_id,
        "completed": progress.completed,
        "notes": progress.notes,
        "timestamp": datetime.utcnow()
    })
    
    return {
        "message": "Progress updated successfully",
        "total_completed": len(user_completed_steps),
        "completion_percentage": (len(user_completed_steps) / len(RELOCATION_TIMELINE)) * 100
    }

def get_current_phase(completed_steps):
    """Determine current phase based on completed steps"""
    if not completed_steps:
        return "Planning"
    
    max_completed = max(completed_steps)
    
    if max_completed <= 3:
        return "Planning"
    elif max_completed <= 7:
        return "Visa & Legal"
    elif max_completed <= 11:
        return "Employment"
    elif max_completed <= 15:
        return "Housing"
    elif max_completed <= 19:
        return "Financial"
    elif max_completed <= 23:
        return "Logistics"
    elif max_completed <= 26:
        return "US Exit"
    elif max_completed <= 30:
        return "UK Arrival"
    else:
        return "Settlement"

# Resources and Links endpoints
@api_router.get("/resources/all")
async def get_all_resources():
    return {
        "visa_legal": [
            {"name": "UK Government Visa Guide", "url": "https://www.gov.uk/browse/visas-immigration", "description": "Official UK visa information"},
            {"name": "Immigration Lawyer Directory", "url": "https://www.lawsociety.org.uk", "description": "Find qualified immigration lawyers"},
            {"name": "Document Apostille Services", "url": "https://www.gov.uk/get-document-legalised", "description": "Document legalization services"}
        ],
        "housing": [
            {"name": "Rightmove", "url": "https://www.rightmove.co.uk", "description": "UK's largest property portal"},
            {"name": "Zoopla", "url": "https://www.zoopla.co.uk", "description": "Property search and valuation"},
            {"name": "SpareRoom", "url": "https://www.spareroom.co.uk", "description": "Room rental and flatshare platform"},
            {"name": "Peak District Property", "url": "https://www.peakdistrictproperty.co.uk", "description": "Local estate agents in Peak District"}
        ],
        "employment": [
            {"name": "Indeed UK", "url": "https://uk.indeed.com", "description": "Job search platform"},
            {"name": "Reed", "url": "https://www.reed.co.uk", "description": "UK recruitment website"},
            {"name": "LinkedIn UK", "url": "https://www.linkedin.com/jobs", "description": "Professional networking and jobs"},
            {"name": "Peak District Jobs", "url": "https://www.peakdistrictjobs.co.uk", "description": "Local job opportunities"}
        ],
        "financial": [
            {"name": "Monzo", "url": "https://monzo.com", "description": "Digital bank popular with expats"},
            {"name": "Wise", "url": "https://wise.com", "description": "International money transfers"},
            {"name": "HMRC", "url": "https://www.gov.uk/government/organisations/hm-revenue-customs", "description": "UK tax authority"},
            {"name": "NHS Registration", "url": "https://www.nhs.uk/using-the-nhs/nhs-services/gps/how-to-register-with-a-gp-practice/", "description": "Healthcare registration"}
        ],
        "local_services": [
            {"name": "Peak District National Park", "url": "https://www.peakdistrict.gov.uk", "description": "Official park information"},
            {"name": "Derbyshire County Council", "url": "https://www.derbyshire.gov.uk", "description": "Local government services"},
            {"name": "Peak District Chamber", "url": "https://www.peakdistrictchamber.co.uk", "description": "Business networking"},
            {"name": "Local Community Groups", "url": "https://www.facebook.com/groups/peakdistrictexpats", "description": "Expat community support"}
        ],
        "lifestyle": [
            {"name": "Visit Peak District", "url": "https://www.visitpeakdistrict.com", "description": "Tourism and attractions"},
            {"name": "Peak District Weather", "url": "https://www.metoffice.gov.uk", "description": "Weather forecasts"},
            {"name": "Public Transport", "url": "https://www.travelsouthyorkshire.com", "description": "Local transport information"},
            {"name": "Healthcare Finder", "url": "https://www.nhs.uk/service-search", "description": "Find local healthcare services"}
        ]
    }

# Original endpoints (keeping for compatibility)
@api_router.get("/locations/phoenix")
async def get_phoenix_data():
    return {
        "location_name": "Phoenix, Arizona",
        "cost_of_living_index": 98.2,
        "housing_cost_index": 89.5,
        "safety_index": 6.8,
        "weather_info": {
            "avg_temp_f": 75,
            "sunny_days": 299,
            "humidity": 38,
            "climate": "Desert"
        },
        "job_market_score": 7.2,
        "education_score": 6.5,
        "healthcare_score": 7.1,
        "population": 1608139,
        "median_income": 62055
    }

@api_router.get("/locations/peak-district")
async def get_peak_district_data():
    return {
        "location_name": "Peak District, UK",
        "cost_of_living_index": 112.8,
        "housing_cost_index": 125.3,
        "safety_index": 8.9,
        "weather_info": {
            "avg_temp_f": 48,
            "sunny_days": 120,
            "humidity": 78,
            "climate": "Temperate Oceanic"
        },
        "job_market_score": 6.8,
        "education_score": 8.9,
        "healthcare_score": 9.2,
        "population": 38000,
        "median_income": 35000
    }

@api_router.get("/comparison/phoenix-to-peak-district")
async def get_relocation_comparison(current_user: User = Depends(get_current_user)):
    phoenix_data = await get_phoenix_data()
    peak_district_data = await get_peak_district_data()
    
    comparison = {
        "from_location": phoenix_data,
        "to_location": peak_district_data,
        "comparison_metrics": {
            "cost_difference_percent": ((peak_district_data["cost_of_living_index"] - phoenix_data["cost_of_living_index"]) / phoenix_data["cost_of_living_index"]) * 100,
            "housing_difference_percent": ((peak_district_data["housing_cost_index"] - phoenix_data["housing_cost_index"]) / phoenix_data["housing_cost_index"]) * 100,
            "safety_improvement": peak_district_data["safety_index"] - phoenix_data["safety_index"],
            "climate_change": {
                "temperature_change": peak_district_data["weather_info"]["avg_temp_f"] - phoenix_data["weather_info"]["avg_temp_f"],
                "humidity_change": peak_district_data["weather_info"]["humidity"] - phoenix_data["weather_info"]["humidity"]
            }
        },
        "relocation_tips": [
            "Cost of living is approximately 15% higher in Peak District",
            "Housing costs are significantly higher (40% increase)",
            "Much safer environment with higher safety index",
            "Cooler, more humid climate - prepare for weather change",
            "Excellent healthcare and education systems",
            "Consider visa requirements for UK relocation"
        ]
    }
    
    return comparison

@api_router.get("/housing/phoenix")
async def get_phoenix_housing():
    return {
        "median_home_price": 450000,
        "median_rent": 1650,
        "price_per_sqft": 185,
        "market_trend": "stable",
        "popular_neighborhoods": [
            "Scottsdale", "Tempe", "Chandler", "Gilbert", "Glendale"
        ],
        "housing_types": {
            "single_family": 65,
            "condos": 20,
            "apartments": 15
        }
    }

@api_router.get("/housing/peak-district")
async def get_peak_district_housing():
    return {
        "median_home_price": 320000,
        "median_rent": 950,
        "price_per_sqft": 240,
        "market_trend": "rising",
        "popular_areas": [
            "Buxton", "Bakewell", "Matlock", "Hathersage", "Castleton"
        ],
        "housing_types": {
            "cottages": 45,
            "terraced": 30,
            "detached": 25
        }
    }

@api_router.get("/jobs/opportunities")
async def get_job_opportunities(current_user: User = Depends(get_current_user)):
    return {
        "phoenix_jobs": {
            "tech_sector": 85,
            "healthcare": 92,
            "finance": 78,
            "education": 65,
            "avg_salary_usd": 62000
        },
        "peak_district_jobs": {
            "tourism": 88,
            "agriculture": 75,
            "outdoor_recreation": 82,
            "local_services": 70,
            "avg_salary_gbp": 28000
        },
        "remote_work_opportunities": [
            "Tech consulting",
            "Digital marketing",
            "Content creation",
            "Online education",
            "E-commerce"
        ]
    }

@api_router.get("/chrome-extensions")
async def get_chrome_extensions():
    extensions = [
        {
            "id": str(uuid.uuid4()),
            "extension_name": "Relocate Me Helper",
            "download_url": "/api/download/relocate-helper.zip",
            "version": "1.0.0",
            "description": "Quick access to relocation data and bookmarking tools",
            "features": ["Bookmark locations", "Compare costs", "Save searches"]
        },
        {
            "id": str(uuid.uuid4()),
            "extension_name": "Property Finder",
            "download_url": "/api/download/property-finder.zip",
            "version": "1.2.1",
            "description": "Find and compare properties across different locations",
            "features": ["Property search", "Price comparison", "Market analysis"]
        }
    ]
    return extensions

@api_router.get("/download/relocate-helper.zip")
async def download_relocate_helper():
    from fastapi.responses import FileResponse
    import zipfile
    import tempfile
    import os
    from pathlib import Path
    
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "relocate-helper.zip")
    
    extension_path = Path("/app/frontend/public/extensions/relocate-helper")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in extension_path.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(extension_path)
                zipf.write(file_path, arcname)
    
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="relocate-helper.zip",
        headers={"Content-Disposition": "attachment; filename=relocate-helper.zip"}
    )

@api_router.get("/download/property-finder.zip")
async def download_property_finder():
    from fastapi.responses import JSONResponse
    return JSONResponse({
        "message": "Property Finder extension coming soon!",
        "status": "development"
    })

@api_router.get("/dashboard/overview")
async def get_dashboard_overview(current_user: User = Depends(get_current_user)):
    completed_count = len(current_user.completed_steps)
    total_steps = len(RELOCATION_TIMELINE)
    completion_percentage = (completed_count / total_steps) * 100
    
    return {
        "user": current_user.username,
        "relocation_progress": {
            "completion_percentage": round(completion_percentage, 1),
            "completed_steps_count": completed_count,
            "total_steps": total_steps,
            "current_phase": get_current_phase(current_user.completed_steps)
        },
        "quick_stats": {
            "days_until_move": 120,
            "budget_allocated": 45000,
            "properties_viewed": 8,
            "applications_sent": 3
        },
        "recent_activity": [
            "Completed visa research step",
            "Updated housing preferences",
            "Bookmarked local schools",
            "Researched hiking trails"
        ]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db():
    await create_default_user()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
