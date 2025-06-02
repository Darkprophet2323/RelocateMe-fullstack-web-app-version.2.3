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
app = FastAPI(title="Relocate Me API", version="1.0.0")

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

class LocationData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    location_name: str
    cost_of_living_index: float
    housing_cost_index: float
    safety_index: float
    weather_info: Dict[str, Any]
    job_market_score: float
    education_score: float
    healthcare_score: float
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RelocationComparison(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    from_location: str
    to_location: str
    comparison_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChromeExtensionDownload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    extension_name: str
    download_url: str
    version: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

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
            hashed_password=hashed_password
        )
        await db.users.insert_one(default_user.dict())
        print("Default user created successfully")

# API Routes
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
    
    # Save comparison to database
    comparison_record = RelocationComparison(
        user_id=current_user.id,
        from_location="Phoenix, Arizona",
        to_location="Peak District, UK",
        comparison_data=comparison
    )
    await db.relocation_comparisons.insert_one(comparison_record.dict())
    
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
            "download_url": "/api/download/relocate-helper.crx",
            "version": "1.0.0",
            "description": "Quick access to relocation data and bookmarking tools",
            "features": ["Bookmark locations", "Compare costs", "Save searches"]
        },
        {
            "id": str(uuid.uuid4()),
            "extension_name": "Property Finder",
            "download_url": "/api/download/property-finder.crx",
            "version": "1.2.1",
            "description": "Find and compare properties across different locations",
            "features": ["Property search", "Price comparison", "Market analysis"]
        }
    ]
    return extensions

@api_router.get("/dashboard/overview")
async def get_dashboard_overview(current_user: User = Depends(get_current_user)):
    return {
        "user": current_user.username,
        "relocation_progress": {
            "completion_percentage": 35,
            "completed_steps": [
                "Location research",
                "Cost analysis",
                "Housing search initiated"
            ],
            "pending_steps": [
                "Visa application",
                "Job applications",
                "Moving logistics",
                "Healthcare setup"
            ]
        },
        "quick_stats": {
            "days_until_move": 120,
            "budget_allocated": 45000,
            "properties_viewed": 8,
            "applications_sent": 3
        },
        "recent_activity": [
            "Viewed property in Bakewell",
            "Updated cost comparison",
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
