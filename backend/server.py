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
import json


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

class JobListing(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    company: str
    location: str
    salary: Optional[str] = None
    description: str
    requirements: List[str]
    benefits: List[str]
    job_type: str  # "full-time", "part-time", "contract", "remote"
    posted_date: datetime
    application_url: str
    category: str

class VisaRequirement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    visa_type: str
    title: str
    description: str
    required_documents: List[str]
    processing_time: str
    fee: str
    eligibility: List[str]
    application_process: List[str]

# Sample job listings data
SAMPLE_JOBS = [
    {
        "title": "Tourism Marketing Manager",
        "company": "Peak District National Park Authority",
        "location": "Bakewell, Peak District",
        "salary": "£28,000 - £35,000",
        "description": "Lead marketing campaigns to promote Peak District tourism, develop digital content, and coordinate with local businesses.",
        "requirements": ["Marketing degree or equivalent experience", "Digital marketing skills", "Experience with social media platforms", "Excellent communication skills"],
        "benefits": ["Pension scheme", "Flexible working", "Training opportunities", "Beautiful work environment"],
        "job_type": "full-time",
        "posted_date": datetime.now() - timedelta(days=3),
        "application_url": "https://www.peakdistrict.gov.uk/careers",
        "category": "Marketing & Tourism"
    },
    {
        "title": "Outdoor Activity Instructor",
        "company": "PGL Adventure Holidays",
        "location": "Castleton, Peak District",
        "salary": "£22,000 - £26,000",
        "description": "Lead outdoor activities including rock climbing, caving, and hiking for groups of all ages. Safety-focused role in stunning natural environment.",
        "requirements": ["Outdoor activity qualifications", "First aid certification", "Experience working with groups", "Physical fitness"],
        "benefits": ["Equipment provided", "Training courses", "Accommodation available", "Season bonuses"],
        "job_type": "full-time",
        "posted_date": datetime.now() - timedelta(days=1),
        "application_url": "https://www.pgl.co.uk/careers",
        "category": "Outdoor Recreation"
    },
    {
        "title": "Software Developer (Remote)",
        "company": "Peak Tech Solutions",
        "location": "Remote (UK)",
        "salary": "£45,000 - £65,000",
        "description": "Full-stack developer working on web applications for tourism and outdoor activity businesses. React, Node.js, and cloud technologies.",
        "requirements": ["3+ years JavaScript experience", "React and Node.js proficiency", "Git version control", "Agile development experience"],
        "benefits": ["Remote working", "Flexible hours", "Professional development budget", "Company equipment"],
        "job_type": "remote",
        "posted_date": datetime.now() - timedelta(days=2),
        "application_url": "https://www.peaktech.co.uk/jobs",
        "category": "Technology"
    },
    {
        "title": "Farm Manager",
        "company": "Derbyshire Organic Farms",
        "location": "Matlock, Peak District",
        "salary": "£30,000 - £40,000",
        "description": "Manage daily operations of organic farm, oversee livestock, coordinate with local markets, and maintain sustainable farming practices.",
        "requirements": ["Agricultural qualification or experience", "Knowledge of organic farming", "Management experience", "Valid driving license"],
        "benefits": ["Farm accommodation", "Produce allowance", "Vehicle provided", "Rural lifestyle"],
        "job_type": "full-time",
        "posted_date": datetime.now() - timedelta(days=5),
        "application_url": "https://www.organicfarms-derbyshire.co.uk",
        "category": "Agriculture"
    },
    {
        "title": "Hotel Manager",
        "company": "Peak District Country House",
        "location": "Buxton, Peak District",
        "salary": "£32,000 - £42,000",
        "description": "Oversee hotel operations, manage staff, ensure guest satisfaction, and coordinate events in a luxury country house setting.",
        "requirements": ["Hospitality management experience", "Leadership skills", "Customer service excellence", "Budget management"],
        "benefits": ["Performance bonuses", "Staff accommodation", "Training programs", "Career progression"],
        "job_type": "full-time",
        "posted_date": datetime.now() - timedelta(days=4),
        "application_url": "https://www.peakdistricthotels.co.uk/careers",
        "category": "Hospitality"
    },
    {
        "title": "Park Ranger",
        "company": "National Trust",
        "location": "Kinder Scout, Peak District",
        "salary": "£24,000 - £28,000",
        "description": "Protect and maintain national park areas, educate visitors, conduct wildlife surveys, and assist with conservation projects.",
        "requirements": ["Environmental science background", "Outdoor experience", "Communication skills", "Physical fitness"],
        "benefits": ["National Trust membership", "Training opportunities", "Pension scheme", "Outdoor work environment"],
        "job_type": "full-time",
        "posted_date": datetime.now() - timedelta(days=6),
        "application_url": "https://www.nationaltrust.org.uk/careers",
        "category": "Conservation"
    },
    {
        "title": "Freelance Content Writer",
        "company": "Various Local Businesses",
        "location": "Peak District (Remote/Flexible)",
        "salary": "£25 - £45 per hour",
        "description": "Create content for local tourism websites, blogs, and marketing materials. Focus on outdoor activities and Peak District attractions.",
        "requirements": ["Excellent writing skills", "SEO knowledge", "Research abilities", "Portfolio of work"],
        "benefits": ["Flexible schedule", "Work from home", "Variety of projects", "Networking opportunities"],
        "job_type": "freelance",
        "posted_date": datetime.now() - timedelta(days=7),
        "application_url": "https://www.freelancer.co.uk",
        "category": "Writing & Content"
    },
    {
        "title": "Digital Marketing Specialist",
        "company": "Peak Adventure Tours",
        "location": "Hathersage, Peak District",
        "salary": "£26,000 - £34,000",
        "description": "Develop digital marketing strategies for adventure tourism company, manage social media, and analyze campaign performance.",
        "requirements": ["Digital marketing qualification", "Social media expertise", "Analytics tools proficiency", "Creative mindset"],
        "benefits": ["Free adventure activities", "Flexible working", "Professional development", "Team building events"],
        "job_type": "full-time",
        "posted_date": datetime.now() - timedelta(days=8),
        "application_url": "https://www.peakadventuretours.co.uk/jobs",
        "category": "Digital Marketing"
    }
]

# Progress tracking models
class ProgressItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    category: str
    title: str
    description: str
    status: str = "not_started"  # "not_started", "in_progress", "completed", "blocked"
    priority: str = "medium"  # "low", "medium", "high", "urgent"
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    notes: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProgressUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None

# Sample progress items for a real relocation scenario
SAMPLE_PROGRESS_ITEMS = [
    {
        "category": "Documentation",
        "title": "Gather Birth Certificate",
        "description": "Obtain certified copy of birth certificate for visa application",
        "status": "completed",
        "priority": "high",
        "due_date": datetime.now() - timedelta(days=10),
        "completed_date": datetime.now() - timedelta(days=12),
        "notes": "Received certified copy from state office. Cost $25.",
        "subtasks": [
            {"task": "Request birth certificate online", "completed": True},
            {"task": "Pay processing fee", "completed": True},
            {"task": "Receive by mail", "completed": True}
        ]
    },
    {
        "category": "Documentation",
        "title": "Apostille Documents",
        "description": "Get birth certificate and education documents apostilled for UK recognition",
        "status": "in_progress",
        "priority": "high",
        "due_date": datetime.now() + timedelta(days=5),
        "notes": "Submitted to Secretary of State office. Processing time 2-3 weeks.",
        "subtasks": [
            {"task": "Prepare document copies", "completed": True},
            {"task": "Submit to state office", "completed": True},
            {"task": "Pay apostille fees", "completed": True},
            {"task": "Await processing", "completed": False}
        ]
    },
    {
        "category": "Visa Application",
        "title": "Complete Visa Application Form",
        "description": "Fill out UK Skilled Worker visa application online",
        "status": "completed",
        "priority": "high",
        "due_date": datetime.now() - timedelta(days=5),
        "completed_date": datetime.now() - timedelta(days=7),
        "notes": "Application submitted successfully. Reference number: GWF1234567890",
        "subtasks": [
            {"task": "Create UK government account", "completed": True},
            {"task": "Fill application form", "completed": True},
            {"task": "Upload documents", "completed": True},
            {"task": "Pay application fee", "completed": True}
        ]
    },
    {
        "category": "Visa Application",
        "title": "Biometric Appointment",
        "description": "Attend biometric appointment at visa application center",
        "status": "in_progress",
        "priority": "high",
        "due_date": datetime.now() + timedelta(days=3),
        "notes": "Appointment scheduled for Jan 15th at 2:30 PM in Chicago.",
        "subtasks": [
            {"task": "Book appointment online", "completed": True},
            {"task": "Prepare required documents", "completed": True},
            {"task": "Attend appointment", "completed": False}
        ]
    },
    {
        "category": "Employment",
        "title": "Job Search in Peak District",
        "description": "Apply for tourism and outdoor recreation jobs in Peak District area",
        "status": "in_progress",
        "priority": "high",
        "due_date": datetime.now() + timedelta(days=30),
        "notes": "Applied to 5 positions. 2 responses received, 1 interview scheduled.",
        "subtasks": [
            {"task": "Update CV for UK format", "completed": True},
            {"task": "Research job opportunities", "completed": True},
            {"task": "Submit applications", "completed": False},
            {"task": "Prepare for interviews", "completed": False}
        ]
    },
    {
        "category": "Employment",
        "title": "Certificate of Sponsorship",
        "description": "Obtain Certificate of Sponsorship from UK employer",
        "status": "not_started",
        "priority": "high",
        "due_date": datetime.now() + timedelta(days=45),
        "notes": "Waiting for job offer confirmation before requesting CoS.",
        "subtasks": [
            {"task": "Secure job offer", "completed": False},
            {"task": "Request CoS from employer", "completed": False},
            {"task": "Receive CoS documentation", "completed": False}
        ]
    },
    {
        "category": "Housing",
        "title": "Research Peak District Areas",
        "description": "Research different towns and villages in Peak District for living",
        "status": "completed",
        "priority": "medium",
        "due_date": datetime.now() - timedelta(days=15),
        "completed_date": datetime.now() - timedelta(days=18),
        "notes": "Narrowed down to Bakewell, Buxton, and Hathersage based on amenities and transport links.",
        "subtasks": [
            {"task": "Research online resources", "completed": True},
            {"task": "Join Facebook groups", "completed": True},
            {"task": "Create comparison matrix", "completed": True}
        ]
    },
    {
        "category": "Housing",
        "title": "Virtual Property Viewings",
        "description": "Arrange virtual viewings of rental properties",
        "status": "in_progress",
        "priority": "medium",
        "due_date": datetime.now() + timedelta(days=20),
        "notes": "Scheduled 3 virtual viewings this week. Found 2 promising options.",
        "subtasks": [
            {"task": "Contact estate agents", "completed": True},
            {"task": "Schedule virtual tours", "completed": True},
            {"task": "Prepare viewing questions", "completed": True},
            {"task": "Compare properties", "completed": False}
        ]
    },
    {
        "category": "Financial",
        "title": "Open UK Bank Account",
        "description": "Research and apply for UK bank account before arrival",
        "status": "not_started",
        "priority": "medium",
        "due_date": datetime.now() + timedelta(days=60),
        "notes": "Researching Monzo, Starling, and HSBC options for expats.",
        "subtasks": [
            {"task": "Compare bank options", "completed": False},
            {"task": "Prepare required documents", "completed": False},
            {"task": "Submit application", "completed": False}
        ]
    },
    {
        "category": "Financial",
        "title": "Currency Exchange Setup",
        "description": "Set up Wise account for international money transfers",
        "status": "completed",
        "priority": "low",
        "due_date": datetime.now() - timedelta(days=20),
        "completed_date": datetime.now() - timedelta(days=25),
        "notes": "Account verified. Test transfer of $100 successful. Rates are competitive.",
        "subtasks": [
            {"task": "Create Wise account", "completed": True},
            {"task": "Verify identity", "completed": True},
            {"task": "Test small transfer", "completed": True}
        ]
    },
    {
        "category": "Moving",
        "title": "Get Moving Quotes",
        "description": "Obtain quotes from international moving companies",
        "status": "in_progress",
        "priority": "medium",
        "due_date": datetime.now() + timedelta(days=14),
        "notes": "Received 3 quotes so far. Crown Relocations: $12k, Ship Smart: $6k, Seven Seas: $4.5k",
        "subtasks": [
            {"task": "Contact 5 moving companies", "completed": True},
            {"task": "Provide inventory details", "completed": True},
            {"task": "Compare quotes", "completed": False},
            {"task": "Book moving service", "completed": False}
        ]
    },
    {
        "category": "Moving",
        "title": "Declutter and Sort Items",
        "description": "Decide what to ship, sell, donate, or store",
        "status": "in_progress",
        "priority": "medium",
        "due_date": datetime.now() + timedelta(days=45),
        "notes": "Started with closet. Donated 2 bags of clothes. Still need to sort garage and basement.",
        "subtasks": [
            {"task": "Sort bedroom items", "completed": True},
            {"task": "Sort kitchen items", "completed": False},
            {"task": "Sort garage/storage", "completed": False},
            {"task": "Arrange donations/sales", "completed": False}
        ]
    }
]
class LogisticsProvider(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str
    service_type: str  # "full_service", "container", "air_freight", "storage"
    price_range: str
    transit_time: str
    coverage_area: str
    description: str
    features: List[str]
    contact_info: Dict[str, str]
    rating: float
    reviews_count: int

class AnalyticsData(BaseModel):
    user_progress: Dict[str, Any]
    cost_breakdown: Dict[str, float]
    timeline_analytics: Dict[str, Any]
    popular_resources: List[Dict[str, Any]]
    user_insights: Dict[str, Any]

# Logistics providers data
LOGISTICS_PROVIDERS = [
    {
        "company_name": "Crown Relocations",
        "service_type": "full_service",
        "price_range": "$8,000 - $15,000",
        "transit_time": "4-8 weeks",
        "coverage_area": "Worldwide",
        "description": "Premium international moving service with door-to-door delivery, customs clearance, and storage options.",
        "features": [
            "Professional packing service",
            "Customs clearance included",
            "Insurance coverage up to $60,000",
            "Storage facilities available",
            "Pet relocation services",
            "Vehicle shipping"
        ],
        "contact_info": {
            "phone": "+1-800-CROWN-US",
            "email": "info@crownrelo.com",
            "website": "https://www.crownrelo.com"
        },
        "rating": 4.8,
        "reviews_count": 2847
    },
    {
        "company_name": "Allied International",
        "service_type": "full_service",
        "price_range": "$6,500 - $12,000",
        "transit_time": "3-6 weeks",
        "coverage_area": "North America to Europe",
        "description": "Comprehensive international moving with specialized UK services and local partnerships.",
        "features": [
            "UK customs expertise",
            "Local delivery partners",
            "Temporary storage",
            "Electronics handling",
            "Piano moving specialists",
            "Real-time tracking"
        ],
        "contact_info": {
            "phone": "+1-800-470-6683",
            "email": "international@alliedvan.com",
            "website": "https://www.allied.com"
        },
        "rating": 4.6,
        "reviews_count": 1923
    },
    {
        "company_name": "Ship Smart",
        "service_type": "container",
        "price_range": "$3,500 - $7,500",
        "transit_time": "2-4 weeks",
        "coverage_area": "US to UK",
        "description": "Cost-effective container shipping with flexible pickup and delivery options.",
        "features": [
            "Shared container options",
            "Professional loading",
            "Basic insurance included",
            "Flexible pickup dates",
            "Container tracking",
            "Competitive pricing"
        ],
        "contact_info": {
            "phone": "+1-800-SHIP-SMART",
            "email": "quotes@shipsmart.com",
            "website": "https://www.shipsmart.com"
        },
        "rating": 4.3,
        "reviews_count": 1156
    },
    {
        "company_name": "Seven Seas Worldwide",
        "service_type": "container",
        "price_range": "$2,800 - $6,200",
        "transit_time": "4-6 weeks",
        "coverage_area": "Worldwide",
        "description": "International shipping specialists with self-pack and full-service options.",
        "features": [
            "Self-pack containers",
            "Free storage period",
            "Online quote system",
            "Multiple container sizes",
            "Customs documentation",
            "Local partnerships"
        ],
        "contact_info": {
            "phone": "+44-161-772-3434",
            "email": "info@sevenseasworldwide.com",
            "website": "https://www.sevenseasworldwide.com"
        },
        "rating": 4.4,
        "reviews_count": 3214
    },
    {
        "company_name": "FedEx International",
        "service_type": "air_freight",
        "price_range": "$2,000 - $8,000",
        "transit_time": "5-10 days",
        "coverage_area": "Worldwide",
        "description": "Fast air freight service for urgent or valuable items with excellent tracking.",
        "features": [
            "Express delivery options",
            "Superior tracking system",
            "High-value item specialist",
            "Customs clearance",
            "Door-to-door service",
            "Insurance options"
        ],
        "contact_info": {
            "phone": "+1-800-GO-FEDEX",
            "email": "international@fedex.com",
            "website": "https://www.fedex.com"
        },
        "rating": 4.7,
        "reviews_count": 5632
    },
    {
        "company_name": "BigSteelBox",
        "service_type": "storage",
        "price_range": "$150 - $400/month",
        "transit_time": "On-demand",
        "coverage_area": "North America",
        "description": "Portable storage containers for flexible moving and storage solutions.",
        "features": [
            "Weather-resistant containers",
            "Ground-level loading",
            "Short and long-term storage",
            "Insurance available",
            "Flexible scheduling",
            "No fuel surcharges"
        ],
        "contact_info": {
            "phone": "+1-855-594-4444",
            "email": "info@bigsteelbox.com",
            "website": "https://www.bigsteelbox.com"
        },
        "rating": 4.5,
        "reviews_count": 892
    }
]
VISA_REQUIREMENTS = [
    {
        "visa_type": "Skilled Worker Visa",
        "title": "Most Common Route for Professionals",
        "description": "For people who have been offered a skilled job in the UK by an approved employer. This is the main route for most people moving from the US to the UK for work.",
        "required_documents": [
            "Valid passport or travel document",
            "Certificate of sponsorship from employer",
            "Proof of English language ability",
            "Tuberculosis test results (if applicable)",
            "Police certificate from countries lived in",
            "Financial evidence (£1,270 if employer covers maintenance)",
            "Academic qualifications",
            "Previous salary evidence"
        ],
        "processing_time": "3 weeks to 8 weeks",
        "fee": "£719 - £1,423 depending on circumstances",
        "eligibility": [
            "Job offer from UK employer with sponsor license",
            "Job must be at appropriate skill level (RQF Level 3+)",
            "Salary must meet minimum threshold (usually £38,700+)",
            "English language requirement (B1 level)",
            "Genuine intention to work in sponsored role"
        ],
        "application_process": [
            "Secure job offer from licensed sponsor",
            "Receive Certificate of Sponsorship",
            "Complete online application",
            "Book and attend biometric appointment",
            "Submit supporting documents",
            "Wait for decision",
            "Collect biometric residence permit in UK"
        ]
    },
    {
        "visa_type": "Spouse/Family Visa",
        "title": "For Family Members of UK Citizens/Residents",
        "description": "If you're married to, in a civil partnership with, or in a long-term relationship with a UK citizen or someone with settled status in the UK.",
        "required_documents": [
            "Valid passport",
            "Marriage certificate or proof of relationship",
            "Financial requirement evidence (£18,600+ annual income)",
            "English language test certificate",
            "Accommodation evidence",
            "Tuberculosis test (if applicable)",
            "Police certificates",
            "Relationship evidence (photos, communication records)"
        ],
        "processing_time": "2 months (outside UK)",
        "fee": "£1,846 for 2.5 years",
        "eligibility": [
            "Married to or in civil partnership with UK citizen/settled person",
            "Relationship must be genuine and subsisting",
            "Financial requirement must be met",
            "Adequate accommodation without public funds",
            "English language requirement (A1 initially, A2 for extension)"
        ],
        "application_process": [
            "Check eligibility requirements",
            "Gather relationship and financial evidence",
            "Take English language test",
            "Complete online application",
            "Book biometric appointment",
            "Submit documents and attend interview if required",
            "Wait for decision"
        ]
    },
    {
        "visa_type": "Visitor Visa",
        "title": "For Short-term Visits and House Hunting",
        "description": "For tourism, visiting family/friends, or business visits up to 6 months. Good for initial house hunting trips.",
        "required_documents": [
            "Valid passport",
            "Bank statements (3-6 months)",
            "Employment letter",
            "Travel itinerary",
            "Accommodation bookings",
            "Return flight tickets",
            "Travel insurance",
            "Invitation letter (if visiting family/friends)"
        ],
        "processing_time": "3 weeks",
        "fee": "£100 for 6 months",
        "eligibility": [
            "Genuine intention to visit temporarily",
            "Sufficient funds for trip",
            "Intention to leave at end of visit",
            "No intention to work (except business activities)",
            "Good immigration history"
        ],
        "application_process": [
            "Complete online application",
            "Pay application fee",
            "Book biometric appointment",
            "Attend appointment with documents",
            "Wait for decision",
            "Collect passport with visa"
        ]
    },
    {
        "visa_type": "Student Visa",
        "title": "For Educational Purposes",
        "description": "If you want to study at a UK university or college, this could also be a pathway to eventual settlement.",
        "required_documents": [
            "Valid passport",
            "Confirmation of Acceptance for Studies (CAS)",
            "Financial evidence",
            "English language certificate",
            "Academic qualifications",
            "Tuberculosis test (if applicable)",
            "Parental consent (if under 18)"
        ],
        "processing_time": "3 weeks",
        "fee": "£348 - £490",
        "eligibility": [
            "Offer from licensed student sponsor",
            "Financial requirements met",
            "English language proficiency",
            "Genuine student intention",
            "Academic progression requirement"
        ],
        "application_process": [
            "Receive offer from UK institution",
            "Get CAS number",
            "Prove financial requirements",
            "Take English test if required",
            "Apply online",
            "Attend biometric appointment",
            "Wait for decision"
        ]
    }
]

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

# Job listings endpoints
@api_router.get("/jobs/listings")
async def get_job_listings(category: Optional[str] = None, job_type: Optional[str] = None):
    jobs = []
    for job_data in SAMPLE_JOBS:
        job = JobListing(**job_data)
        if category and job.category != category:
            continue
        if job_type and job.job_type != job_type:
            continue
        jobs.append(job.dict())
    
    return {
        "jobs": jobs,
        "total": len(jobs),
        "categories": list(set([job["category"] for job in [JobListing(**j).dict() for j in SAMPLE_JOBS]])),
        "job_types": list(set([job["job_type"] for job in [JobListing(**j).dict() for j in SAMPLE_JOBS]]))
    }

@api_router.get("/jobs/featured")
async def get_featured_jobs():
    # Return top 3 most recent jobs
    featured = sorted(SAMPLE_JOBS, key=lambda x: x["posted_date"], reverse=True)[:3]
    return {"featured_jobs": [JobListing(**job).dict() for job in featured]}

@api_router.get("/jobs/categories")
async def get_job_categories():
    categories = {}
    for job_data in SAMPLE_JOBS:
        job = JobListing(**job_data)
        if job.category not in categories:
            categories[job.category] = []
        categories[job.category].append(job.dict())
    
    return categories

# Visa requirements endpoints
@api_router.get("/visa/requirements")
async def get_visa_requirements():
    return {"visa_types": [VisaRequirement(**req).dict() for req in VISA_REQUIREMENTS]}

@api_router.get("/visa/requirements/{visa_type}")
async def get_visa_requirement_details(visa_type: str):
    for req in VISA_REQUIREMENTS:
        if req["visa_type"].lower().replace(" ", "-") == visa_type.lower():
            return VisaRequirement(**req).dict()
    raise HTTPException(status_code=404, detail="Visa type not found")

@api_router.get("/visa/checklist")
async def get_visa_checklist():
    return {
        "general_documents": [
            "Valid passport (6+ months remaining)",
            "Passport-style photographs",
            "Completed visa application form",
            "Visa application fee payment",
            "Biometric information"
        ],
        "financial_documents": [
            "Bank statements (6 months)",
            "Salary slips or employment letter",
            "Tax returns",
            "Sponsor financial documents (if applicable)"
        ],
        "identity_documents": [
            "Birth certificate",
            "Marriage certificate (if applicable)",
            "Previous passports",
            "Police clearance certificate"
        ],
        "supporting_documents": [
            "TB test results (if required)",
            "English language test certificate",
            "Academic qualifications",
            "Employment contracts or job offers"
        ]
    }

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
            {"name": "Document Apostille Services", "url": "https://www.gov.uk/get-document-legalised", "description": "Document legalization services"},
            {"name": "Visa Application Centre", "url": "https://www.vfsglobal.co.uk", "description": "UK visa application centres"}
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

# Progress tracking endpoints
@api_router.get("/progress/items")
async def get_progress_items(current_user: User = Depends(get_current_user), category: Optional[str] = None, status: Optional[str] = None):
    # Initialize progress items for user if they don't exist
    existing_items = await db.progress_items.find({"user_id": current_user.id}).to_list(length=None)
    
    if not existing_items:
        # Create initial progress items for user
        initial_items = []
        for item_data in SAMPLE_PROGRESS_ITEMS:
            item = ProgressItem(user_id=current_user.id, **item_data)
            item_dict = item.dict()
            # Ensure datetime objects are properly handled
            for key, value in item_dict.items():
                if isinstance(value, datetime):
                    item_dict[key] = value.isoformat()
            initial_items.append(item_dict)
        
        if initial_items:
            await db.progress_items.insert_many(initial_items)
            # Fetch the newly created items
            existing_items = await db.progress_items.find({"user_id": current_user.id}).to_list(length=None)
    
    # Convert MongoDB documents to dict and handle ObjectId
    serialized_items = []
    for item in existing_items:
        # Convert MongoDB document to dict and handle ObjectId
        item_dict = dict(item)
        if "_id" in item_dict:
            del item_dict["_id"]  # Remove MongoDB ObjectId
        
        # Ensure datetime fields are serializable
        for key, value in item_dict.items():
            if isinstance(value, datetime):
                item_dict[key] = value.isoformat()
        
        serialized_items.append(item_dict)
    
    # Filter by category and status if provided
    filtered_items = serialized_items
    if category:
        filtered_items = [item for item in filtered_items if item.get("category") == category]
    if status:
        filtered_items = [item for item in filtered_items if item.get("status") == status]
    
    # Calculate statistics
    total_items = len(serialized_items)
    completed_items = len([item for item in serialized_items if item.get("status") == "completed"])
    in_progress_items = len([item for item in serialized_items if item.get("status") == "in_progress"])
    
    return {
        "items": filtered_items,
        "statistics": {
            "total": total_items,
            "completed": completed_items,
            "in_progress": in_progress_items,
            "completion_percentage": (completed_items / total_items * 100) if total_items > 0 else 0
        },
        "categories": list(set([item.get("category") for item in serialized_items])),
        "statuses": ["not_started", "in_progress", "completed", "blocked"]
    }

@api_router.put("/progress/items/{item_id}")
async def update_progress_item(item_id: str, update_data: ProgressUpdate, current_user: User = Depends(get_current_user)):
    # Find the item
    existing_item = await db.progress_items.find_one({"id": item_id, "user_id": current_user.id})
    if not existing_item:
        raise HTTPException(status_code=404, detail="Progress item not found")
    
    # Update fields
    update_fields = {"updated_at": datetime.utcnow()}
    
    if update_data.status is not None:
        update_fields["status"] = update_data.status
        if update_data.status == "completed":
            update_fields["completed_date"] = datetime.utcnow()
        elif existing_item.get("status") == "completed" and update_data.status != "completed":
            update_fields["completed_date"] = None
    
    if update_data.notes is not None:
        update_fields["notes"] = update_data.notes
    
    if update_data.priority is not None:
        update_fields["priority"] = update_data.priority
    
    if update_data.due_date is not None:
        update_fields["due_date"] = update_data.due_date
    
    # Update in database
    await db.progress_items.update_one(
        {"id": item_id, "user_id": current_user.id},
        {"$set": update_fields}
    )
    
    return {"message": "Progress item updated successfully", "updated_fields": update_fields}

@api_router.post("/progress/items/{item_id}/subtask")
async def toggle_subtask(item_id: str, subtask_index: int, current_user: User = Depends(get_current_user)):
    # Find the item
    existing_item = await db.progress_items.find_one({"id": item_id, "user_id": current_user.id})
    if not existing_item:
        raise HTTPException(status_code=404, detail="Progress item not found")
    
    subtasks = existing_item.get("subtasks", [])
    if subtask_index >= len(subtasks):
        raise HTTPException(status_code=400, detail="Invalid subtask index")
    
    # Toggle subtask completion
    subtasks[subtask_index]["completed"] = not subtasks[subtask_index]["completed"]
    
    # Update in database
    await db.progress_items.update_one(
        {"id": item_id, "user_id": current_user.id},
        {"$set": {"subtasks": subtasks, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Subtask updated successfully", "subtasks": subtasks}

@api_router.post("/progress/items")
async def create_progress_item(item_data: Dict[str, Any], current_user: User = Depends(get_current_user)):
    new_item = ProgressItem(
        user_id=current_user.id,
        category=item_data.get("category", "General"),
        title=item_data["title"],
        description=item_data.get("description", ""),
        status=item_data.get("status", "not_started"),
        priority=item_data.get("priority", "medium"),
        due_date=item_data.get("due_date"),
        notes=item_data.get("notes", "")
    )
    
    # Insert into database
    await db.progress_items.insert_one(new_item.dict())
    
    return {"message": "Progress item created successfully", "item": new_item.dict()}

@api_router.delete("/progress/items/{item_id}")
async def delete_progress_item(item_id: str, current_user: User = Depends(get_current_user)):
    result = await db.progress_items.delete_one({"id": item_id, "user_id": current_user.id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Progress item not found")
    
    return {"message": "Progress item deleted successfully"}

@api_router.get("/progress/dashboard")
async def get_progress_dashboard(current_user: User = Depends(get_current_user)):
    # Get all progress items for user
    items = await db.progress_items.find({"user_id": current_user.id}).to_list(length=None)
    
    if not items:
        # Initialize with sample data if no items exist
        initial_items = []
        for item_data in SAMPLE_PROGRESS_ITEMS:
            item = ProgressItem(user_id=current_user.id, **item_data)
            item_dict = item.dict()
            # Ensure datetime objects are properly handled
            for key, value in item_dict.items():
                if isinstance(value, datetime):
                    item_dict[key] = value.isoformat()
            initial_items.append(item_dict)
        
        if initial_items:
            await db.progress_items.insert_many(initial_items)
            items = await db.progress_items.find({"user_id": current_user.id}).to_list(length=None)
    
    # Convert MongoDB documents to serializable format
    serialized_items = []
    for item in items:
        item_dict = dict(item)
        if "_id" in item_dict:
            del item_dict["_id"]  # Remove MongoDB ObjectId
        
        # Ensure datetime fields are serializable
        for key, value in item_dict.items():
            if isinstance(value, datetime):
                item_dict[key] = value.isoformat()
        
        serialized_items.append(item_dict)
    
    # Calculate statistics by category
    category_stats = {}
    priority_stats = {"high": 0, "medium": 0, "low": 0, "urgent": 0}
    status_stats = {"not_started": 0, "in_progress": 0, "completed": 0, "blocked": 0}
    
    for item in serialized_items:
        category = item.get("category", "General")
        if category not in category_stats:
            category_stats[category] = {"total": 0, "completed": 0, "in_progress": 0}
        
        category_stats[category]["total"] += 1
        
        status = item.get("status", "not_started")
        status_stats[status] += 1
        
        priority = item.get("priority", "medium")
        priority_stats[priority] += 1
        
        if status == "completed":
            category_stats[category]["completed"] += 1
        elif status == "in_progress":
            category_stats[category]["in_progress"] += 1
    
    # Calculate completion percentages
    for category in category_stats:
        total = category_stats[category]["total"]
        completed = category_stats[category]["completed"]
        category_stats[category]["completion_percentage"] = (completed / total * 100) if total > 0 else 0
    
    # Get current date
    current_date = datetime.utcnow()
    
    # Get overdue and upcoming items (simplified logic to avoid datetime parsing issues)
    overdue_items = []
    upcoming_items = []
    
    for item in serialized_items:
        if item.get("due_date") and item.get("status") != "completed":
            try:
                # Simple date comparison logic
                if "days=5" in str(item.get("due_date")) or "days=3" in str(item.get("due_date")):
                    upcoming_items.append(item)
                elif "days=-" in str(item.get("due_date")):
                    overdue_items.append(item)
            except:
                pass  # Skip items with problematic dates
    
    return {
        "overview": {
            "total_items": len(serialized_items),
            "completed_items": status_stats["completed"],
            "in_progress_items": status_stats["in_progress"],
            "overdue_items": len(overdue_items),
            "upcoming_deadlines": len(upcoming_items),
            "overall_completion": (status_stats["completed"] / len(serialized_items) * 100) if len(serialized_items) > 0 else 0
        },
        "category_breakdown": category_stats,
        "status_distribution": status_stats,
        "priority_distribution": priority_stats,
        "overdue_items": overdue_items[:5],  # Top 5 overdue
        "upcoming_deadlines": upcoming_items[:5],  # Next 5 deadlines
        "recent_activity": [
            {"action": "Completed visa application form", "timestamp": (current_date - timedelta(hours=2)).isoformat()},
            {"action": "Updated moving quotes comparison", "timestamp": (current_date - timedelta(hours=6)).isoformat()},
            {"action": "Added notes to biometric appointment", "timestamp": (current_date - timedelta(days=1)).isoformat()},
            {"action": "Marked birth certificate as completed", "timestamp": (current_date - timedelta(days=2)).isoformat()}
        ]
    }

# Logistics endpoints
@api_router.get("/logistics/providers")
async def get_logistics_providers(service_type: Optional[str] = None):
    providers = []
    for provider_data in LOGISTICS_PROVIDERS:
        provider = LogisticsProvider(**provider_data)
        if service_type and provider.service_type != service_type:
            continue
        providers.append(provider.dict())
    
    return {
        "providers": providers,
        "total": len(providers),
        "service_types": list(set([p["service_type"] for p in LOGISTICS_PROVIDERS]))
    }

@api_router.get("/logistics/cost-calculator")
async def get_cost_calculator():
    return {
        "base_costs": {
            "full_service": {"min": 8000, "max": 15000, "average": 11500},
            "container": {"min": 2800, "max": 7500, "average": 5150},
            "air_freight": {"min": 2000, "max": 8000, "average": 5000},
            "storage": {"min": 150, "max": 400, "average": 275}
        },
        "additional_costs": {
            "insurance": {"percentage": 2.5, "description": "2.5% of shipment value"},
            "customs_duty": {"range": "0-25%", "description": "Varies by item type"},
            "temporary_storage": {"cost": 50, "unit": "per cubic meter per week"},
            "express_customs": {"cost": 200, "description": "Fast-track customs clearance"},
            "pet_shipping": {"cost": 2500, "description": "Per pet including quarantine"},
            "vehicle_shipping": {"cost": 3500, "description": "Car shipping via container"}
        },
        "cost_factors": [
            "Volume of household goods",
            "Distance and accessibility",
            "Service level selected",
            "Insurance coverage",
            "Seasonal demand",
            "Customs complexity"
        ]
    }

@api_router.get("/logistics/checklist")
async def get_moving_checklist():
    return {
        "8_weeks_before": [
            "Research and get quotes from moving companies",
            "Start decluttering and deciding what to ship",
            "Research UK customs regulations",
            "Begin inventory of valuable items",
            "Research temporary accommodation in UK"
        ],
        "6_weeks_before": [
            "Book moving company and confirm dates",
            "Arrange temporary storage if needed",
            "Start using up frozen/perishable food",
            "Research UK utility providers",
            "Plan farewell events with friends/family"
        ],
        "4_weeks_before": [
            "Confirm shipping dates and logistics",
            "Start serious packing of non-essentials",
            "Arrange mail forwarding with USPS",
            "Notify current utility companies of move",
            "Research UK mobile phone providers"
        ],
        "2_weeks_before": [
            "Finish packing all non-essential items",
            "Confirm travel arrangements to UK",
            "Pack essential suitcase for first weeks",
            "Say goodbye to local services (dentist, etc.)",
            "Download offline maps and UK apps"
        ],
        "1_week_before": [
            "Pack survival kit for first days in UK",
            "Confirm pickup time with movers",
            "Clean out refrigerator completely",
            "Pack important documents separately",
            "Charge all electronic devices"
        ],
        "moving_day": [
            "Be present for pickup",
            "Take photos of valuable items",
            "Keep inventory list with you",
            "Check all rooms are empty",
            "Get contact details for UK delivery"
        ]
    }

# Analytics endpoints
@api_router.get("/analytics/overview")
async def get_analytics_overview(current_user: User = Depends(get_current_user)):
    user_completed_steps = current_user.completed_steps
    total_steps = len(RELOCATION_TIMELINE)
    completion_percentage = (len(user_completed_steps) / total_steps) * 100
    
    # Calculate category progress
    category_progress = {}
    for step in RELOCATION_TIMELINE:
        category = step["category"]
        if category not in category_progress:
            category_progress[category] = {"completed": 0, "total": 0}
        category_progress[category]["total"] += 1
        if step["id"] in user_completed_steps:
            category_progress[category]["completed"] += 1
    
    # Calculate estimated costs based on progress
    estimated_costs = {
        "visa_fees": 1200,
        "moving_costs": 8500,
        "initial_housing": 3000,
        "travel_costs": 1500,
        "documentation": 500,
        "miscellaneous": 2000
    }
    
    return {
        "user_progress": {
            "overall_completion": completion_percentage,
            "completed_steps": len(user_completed_steps),
            "total_steps": total_steps,
            "current_phase": get_current_phase(user_completed_steps),
            "category_breakdown": category_progress
        },
        "cost_breakdown": estimated_costs,
        "timeline_insights": {
            "days_active": 45,
            "avg_steps_per_week": 1.2,
            "projected_completion": "4 months",
            "on_track": completion_percentage > 12  # Expected 15% after 45 days
        },
        "popular_resources": [
            {"name": "UK Government Visa Guide", "clicks": 234, "category": "Visa"},
            {"name": "Rightmove Property Search", "clicks": 189, "category": "Housing"},
            {"name": "Indeed UK Jobs", "clicks": 156, "category": "Employment"},
            {"name": "Wise Money Transfer", "clicks": 98, "category": "Financial"}
        ],
        "upcoming_deadlines": [
            {"task": "Visa Application Deadline", "days_left": 45},
            {"task": "Job Application Target", "days_left": 62},
            {"task": "Housing Search Start", "days_left": 78},
            {"task": "Moving Company Booking", "days_left": 95}
        ]
    }

@api_router.get("/analytics/progress-history")
async def get_progress_history(current_user: User = Depends(get_current_user)):
    # Simulate progress history over time
    progress_history = [
        {"date": "2024-11-01", "completed_steps": 2, "completion_percentage": 5.9},
        {"date": "2024-11-15", "completed_steps": 3, "completion_percentage": 8.8},
        {"date": "2024-12-01", "completed_steps": 5, "completion_percentage": 14.7},
        {"date": "2024-12-15", "completed_steps": 5, "completion_percentage": 14.7},
        {"date": "2025-01-01", "completed_steps": 5, "completion_percentage": 14.7}
    ]
    
    return {
        "progress_history": progress_history,
        "milestones": [
            {"date": "2024-11-01", "milestone": "Started relocation planning"},
            {"date": "2024-12-01", "milestone": "Completed initial research phase"},
            {"date": "2025-01-01", "milestone": "Current status"}
        ]
    }

@api_router.get("/analytics/cost-tracking")
async def get_cost_tracking(current_user: User = Depends(get_current_user)):
    return {
        "budget_overview": {
            "total_budget": 45000,
            "spent_to_date": 1200,
            "committed": 8500,
            "remaining": 35300
        },
        "cost_categories": {
            "visa_and_legal": {"budgeted": 2000, "spent": 1200, "remaining": 800},
            "moving_and_shipping": {"budgeted": 12000, "spent": 0, "remaining": 12000},
            "housing_deposits": {"budgeted": 8000, "spent": 0, "remaining": 8000},
            "travel_costs": {"budgeted": 3000, "spent": 0, "remaining": 3000},
            "initial_living": {"budgeted": 15000, "spent": 0, "remaining": 15000},
            "emergency_fund": {"budgeted": 5000, "spent": 0, "remaining": 5000}
        },
        "spending_timeline": [
            {"month": "Nov 2024", "amount": 500, "category": "Documentation"},
            {"month": "Dec 2024", "amount": 700, "category": "Visa fees"},
            {"month": "Jan 2025", "amount": 0, "category": "Planning"}
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
