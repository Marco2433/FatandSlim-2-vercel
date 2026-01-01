from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Response, Request
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import random
import hashlib
import json
import re
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import base64
import jwt
import bcrypt
import httpx
from difflib import SequenceMatcher

# Import recipes database
from recipes_database import (
    SAMPLE_RECIPES, 
    get_daily_recipes, 
    get_recipes_by_nutri_score,
    get_recipes_stats,
    generate_recipe,
    search_recipes
)

ROOT_DIR = Path(__file__).parent
FRONTEND_PUBLIC_DIR = ROOT_DIR.parent / 'frontend' / 'public'
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'fatandslim_secret')
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# AI Usage limits configuration
AI_DAILY_LIMIT = 2  # Maximum AI calls per user per day
AI_CACHE_SIMILARITY_THRESHOLD = 0.90  # 90% similarity for cache hits
AI_CACHE_EXPIRY_DAYS = 30  # Cache entries expire after 30 days

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== AI USAGE LIMITING & CACHING SYSTEM ====================

def normalize_prompt(prompt: str) -> str:
    """Normalize prompt for better similarity matching"""
    # Remove extra whitespace
    normalized = ' '.join(prompt.lower().split())
    # Remove punctuation that doesn't affect meaning
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return normalized

def calculate_prompt_hash(prompt: str) -> str:
    """Generate a hash for the normalized prompt"""
    normalized = normalize_prompt(prompt)
    return hashlib.sha256(normalized.encode()).hexdigest()

def calculate_similarity(prompt1: str, prompt2: str) -> float:
    """Calculate similarity between two prompts (0.0 to 1.0)"""
    norm1 = normalize_prompt(prompt1)
    norm2 = normalize_prompt(prompt2)
    return SequenceMatcher(None, norm1, norm2).ratio()

async def check_ai_usage_limit(user_id: str) -> dict:
    """
    Check if user has exceeded daily AI usage limit.
    Returns: {"allowed": bool, "remaining": int, "used": int}
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    usage = await db.ai_usage_logs.find_one({
        "user_id": user_id,
        "date": today
    })
    
    used = usage.get("count", 0) if usage else 0
    remaining = max(0, AI_DAILY_LIMIT - used)
    
    return {
        "allowed": used < AI_DAILY_LIMIT,
        "remaining": remaining,
        "used": used,
        "limit": AI_DAILY_LIMIT
    }

async def increment_ai_usage(user_id: str, endpoint: str) -> None:
    """Increment user's daily AI usage counter"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    await db.ai_usage_logs.update_one(
        {"user_id": user_id, "date": today},
        {
            "$inc": {"count": 1},
            "$push": {
                "calls": {
                    "endpoint": endpoint,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            },
            "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}
        },
        upsert=True
    )
    
    logger.info(f"AI usage incremented for user {user_id}: endpoint={endpoint}")

async def get_cached_ai_response(prompt: str, endpoint: str, user_context_hash: str = "") -> Optional[dict]:
    """
    Search for a cached AI response with similarity matching.
    Returns cached response if found with >= 90% similarity, else None.
    """
    prompt_hash = calculate_prompt_hash(prompt)
    cache_key = f"{endpoint}:{user_context_hash}"
    
    # First, try exact hash match
    exact_match = await db.ai_cache.find_one({
        "prompt_hash": prompt_hash,
        "cache_key": cache_key
    }, {"_id": 0})
    
    if exact_match:
        logger.info(f"AI Cache HIT (exact): endpoint={endpoint}")
        await db.ai_cache.update_one(
            {"prompt_hash": prompt_hash, "cache_key": cache_key},
            {"$inc": {"hit_count": 1}, "$set": {"last_hit": datetime.now(timezone.utc).isoformat()}}
        )
        return exact_match.get("response")
    
    # Try similarity matching - get recent cache entries for this endpoint
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=AI_CACHE_EXPIRY_DAYS)).isoformat()
    recent_entries = await db.ai_cache.find({
        "cache_key": cache_key,
        "created_at": {"$gte": cutoff_date}
    }, {"_id": 0}).sort("hit_count", -1).limit(50).to_list(50)
    
    for entry in recent_entries:
        stored_prompt = entry.get("original_prompt", "")
        similarity = calculate_similarity(prompt, stored_prompt)
        
        if similarity >= AI_CACHE_SIMILARITY_THRESHOLD:
            logger.info(f"AI Cache HIT (similarity={similarity:.2%}): endpoint={endpoint}")
            await db.ai_cache.update_one(
                {"prompt_hash": entry["prompt_hash"], "cache_key": cache_key},
                {"$inc": {"hit_count": 1}, "$set": {"last_hit": datetime.now(timezone.utc).isoformat()}}
            )
            return entry.get("response")
    
    logger.info(f"AI Cache MISS: endpoint={endpoint}")
    return None

async def store_cached_ai_response(prompt: str, response: dict, endpoint: str, user_context_hash: str = "") -> None:
    """Store AI response in cache"""
    prompt_hash = calculate_prompt_hash(prompt)
    cache_key = f"{endpoint}:{user_context_hash}"
    
    await db.ai_cache.update_one(
        {"prompt_hash": prompt_hash, "cache_key": cache_key},
        {
            "$set": {
                "response": response,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$setOnInsert": {
                "original_prompt": prompt[:500],  # Store first 500 chars for similarity matching
                "created_at": datetime.now(timezone.utc).isoformat(),
                "hit_count": 0
            }
        },
        upsert=True
    )
    
    logger.info(f"AI response cached: endpoint={endpoint}")

async def enforce_ai_limit(user_id: str, endpoint: str) -> None:
    """
    Enforce AI usage limit. Raises HTTPException if limit exceeded.
    Call this BEFORE making any AI request.
    """
    usage = await check_ai_usage_limit(user_id)
    
    if not usage["allowed"]:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Limite quotidienne IA atteinte",
                "message": f"Vous avez atteint votre limite de {AI_DAILY_LIMIT} appels IA par jour. Revenez demain !",
                "used": usage["used"],
                "limit": usage["limit"],
                "reset_at": "minuit UTC"
            }
        )

def get_user_context_hash(profile: dict) -> str:
    """Generate a hash for user's dietary context to scope cache"""
    if not profile:
        return "default"
    
    # Include relevant dietary context that affects AI responses
    context = {
        "goal": profile.get("goal", ""),
        "allergies": sorted(profile.get("allergies", [])),
        "dietary_preferences": sorted(profile.get("dietary_preferences", [])),
        "health_conditions": sorted(profile.get("health_conditions", [])),
        "fitness_level": profile.get("fitness_level", "")
    }
    
    return hashlib.md5(json.dumps(context, sort_keys=True).encode()).hexdigest()[:12]

# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    target_weight: Optional[float] = None
    goal: Optional[str] = None
    activity_level: Optional[str] = None
    dietary_preferences: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    fitness_level: Optional[str] = None
    onboarding_completed: bool = False
    is_premium: bool = False
    created_at: Optional[str] = None

class OnboardingData(BaseModel):
    age: int
    height: float
    weight: float
    target_weight: float
    goal: str = "health"
    activity_level: str = "moderate"
    dietary_preferences: List[str] = []
    allergies: List[str] = []
    fitness_level: str = "beginner"
    gender: Optional[str] = "male"
    health_conditions: List[str] = []
    food_likes: List[str] = []
    food_dislikes: List[str] = []
    time_constraint: Optional[str] = "moderate"
    budget: Optional[str] = "medium"
    cooking_skill: Optional[str] = "intermediate"
    meals_per_day: Optional[int] = 3
    # Bariatric fields
    bariatric_surgery: Optional[str] = None
    bariatric_surgery_date: Optional[str] = None
    bariatric_pre_op_weight: Optional[float] = None
    bariatric_pre_op_height: Optional[float] = None
    bariatric_parcours: Optional[str] = None
    bariatric_phase: Optional[int] = None
    bariatric_supplements: Optional[List[str]] = []
    bariatric_intolerances: Optional[List[str]] = []
    bariatric_clinic: Optional[str] = None
    bariatric_surgeon: Optional[str] = None
    bariatric_nutritionist: Optional[str] = None
    bariatric_psychologist: Optional[str] = None
    
    model_config = {"extra": "ignore"}
    
    @field_validator('goal', mode='before')
    @classmethod
    def default_goal(cls, v):
        return v if v and v != '' else 'health'
    
    @field_validator('activity_level', mode='before')
    @classmethod
    def default_activity(cls, v):
        return v if v and v != '' else 'moderate'
    
    @field_validator('fitness_level', mode='before')
    @classmethod
    def default_fitness(cls, v):
        return v if v and v != '' else 'beginner'
    
    @field_validator('bariatric_pre_op_weight', 'bariatric_pre_op_height', mode='before')
    @classmethod
    def empty_str_to_none_float(cls, v):
        if v == '' or v is None:
            return None
        return v
    
    @field_validator('bariatric_surgery_date', 'bariatric_parcours', 'bariatric_clinic', 'bariatric_surgeon', 'bariatric_nutritionist', 'bariatric_psychologist', mode='before')
    @classmethod
    def empty_str_to_none_str(cls, v):
        if v == '' or v is None:
            return None
        return v
    
    @field_validator('bariatric_phase', mode='before')
    @classmethod
    def empty_str_to_none_int(cls, v):
        if v == '' or v is None:
            return None
        return v

class FoodLogEntry(BaseModel):
    food_name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    quantity: float = 1.0
    unit: str = "portion"
    meal_type: str = "snack"
    image_url: Optional[str] = None
    nutri_score: Optional[str] = None
    note: Optional[str] = None
    sugar: Optional[float] = 0
    sodium: Optional[float] = 0
    fiber: Optional[float] = 0

class WorkoutLog(BaseModel):
    workout_name: str
    duration_minutes: int
    calories_burned: int
    exercises: List[dict] = []

class WeightEntry(BaseModel):
    weight: float
    date: Optional[str] = None

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

async def get_current_user(request: Request) -> dict:
    # Check cookie first, then Authorization header
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if it's a session token from Google OAuth
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if session:
        expires_at = session.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired")
        
        user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    
    # Try JWT token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/register")
async def register(user: UserCreate, response: Response):
    existing = await db.users.find_one({"email": user.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": user.email,
        "name": user.name,
        "password_hash": hash_password(user.password),
        "picture": None,
        "onboarding_completed": False,
        "is_premium": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7*24*60*60,
        path="/"
    )
    
    return {
        "user_id": user_id,
        "email": user.email,
        "name": user.name,
        "token": token,
        "onboarding_completed": False
    }

@api_router.post("/auth/login")
async def login(user: UserLogin, response: Response):
    user_doc = await db.users.find_one({"email": user.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if "password_hash" in user_doc and not verify_password(user.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user_doc["user_id"])
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7*24*60*60,
        path="/"
    )
    
    return {
        "user_id": user_doc["user_id"],
        "email": user_doc["email"],
        "name": user_doc.get("name", ""),
        "token": token,
        "onboarding_completed": user_doc.get("onboarding_completed", False)
    }

@api_router.post("/auth/session")
async def process_session(request: Request, response: Response):
    """Process Google OAuth session_id and create local session"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Fetch user data from Emergent Auth
    async with httpx.AsyncClient() as client_http:
        resp = await client_http.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        user_data = resp.json()
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": user_data["name"], "picture": user_data.get("picture")}}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id,
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data.get("picture"),
            "onboarding_completed": False,
            "is_premium": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Create session
    session_token = user_data.get("session_token", f"session_{uuid.uuid4().hex}")
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7*24*60*60,
        path="/"
    )
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return {
        "user_id": user_id,
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "onboarding_completed": user.get("onboarding_completed", False)
    }

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user.get("name", ""),
        "picture": user.get("picture"),
        "onboarding_completed": user.get("onboarding_completed", False),
        "is_premium": user.get("is_premium", False)
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"message": "Logged out"}

# ==================== AI USAGE STATUS ENDPOINT ====================

@api_router.get("/ai/usage")
async def get_ai_usage_status(user: dict = Depends(get_current_user)):
    """Get user's AI usage status for today"""
    usage = await check_ai_usage_limit(user["user_id"])
    
    # Get today's call history
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    usage_doc = await db.ai_usage_logs.find_one({
        "user_id": user["user_id"],
        "date": today
    }, {"_id": 0})
    
    calls = usage_doc.get("calls", []) if usage_doc else []
    
    return {
        "used": usage["used"],
        "remaining": usage["remaining"],
        "limit": usage["limit"],
        "date": today,
        "calls": calls,
        "message": f"Vous avez utilisé {usage['used']}/{usage['limit']} appels IA aujourd'hui" if usage['used'] > 0 else "Vous n'avez pas encore utilisé l'IA aujourd'hui"
    }

# ==================== PROFILE ENDPOINTS ====================

@api_router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not profile:
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user.get("name", ""),
            "picture": user.get("picture"),
            "onboarding_completed": user.get("onboarding_completed", False)
        }
    return {**profile, "email": user["email"], "name": user.get("name", "")}

@api_router.post("/profile/onboarding")
async def complete_onboarding(data: OnboardingData, user: dict = Depends(get_current_user)):
    # Calculate BMI correctly: weight (kg) / height (m)²
    height_m = data.height / 100  # Convert cm to meters
    bmi = round(data.weight / (height_m ** 2), 1)
    
    # Calculate ideal BMI range (18.5-24.9 is healthy)
    ideal_bmi_min = 18.5
    ideal_bmi_max = 24.9
    ideal_weight_min = round(ideal_bmi_min * (height_m ** 2), 1)
    ideal_weight_max = round(ideal_bmi_max * (height_m ** 2), 1)
    ideal_bmi_target = 22.0  # Middle of healthy range
    ideal_weight = round(ideal_bmi_target * (height_m ** 2), 1)
    
    # ==================== CALORIE CALCULATION (ROBUST ALGORITHM) ====================
    # Step 1: Calculate BMR using Mifflin-St Jeor equation
    if data.gender == "female":
        bmr = (10 * data.weight) + (6.25 * data.height) - (5 * data.age) - 161
    else:
        bmr = (10 * data.weight) + (6.25 * data.height) - (5 * data.age) + 5
    
    # Step 2: Activity factor - CAPPED at 1.55 for wellness apps
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.55,      # CAPPED - never exceed 1.55
        "very_active": 1.55  # CAPPED - never exceed 1.55
    }
    
    # Apply lower activity factor for high BMI or older users (safety guard)
    activity_factor = activity_multipliers.get(data.activity_level, 1.2)
    if bmi > 35 or data.age > 50:
        activity_factor = min(activity_factor, 1.375)  # Reduced for safety
    
    # Step 3: Calculate TDEE (Total Daily Energy Expenditure)
    tdee = bmr * activity_factor
    
    # Step 4: Apply deficit/surplus based on goal
    if data.goal == "lose_weight":
        # Default 20% deficit, softer 15% for high BMI/age
        if bmi > 35 or data.age > 50:
            deficit_multiplier = 0.85  # 15% deficit (safer)
        else:
            deficit_multiplier = 0.80  # 20% deficit (standard)
        calorie_target = tdee * deficit_multiplier
    elif data.goal == "gain_muscle":
        calorie_target = tdee * 1.10  # 10% surplus
    else:
        calorie_target = tdee  # Maintenance
    
    # Step 5: Apply safety caps (MANDATORY)
    if data.gender == "female":
        calorie_target = min(calorie_target, 3500)  # Max for women
        calorie_target = max(calorie_target, 1200)  # Min safe for women
    else:
        calorie_target = min(calorie_target, 4000)  # Max for men
        calorie_target = max(calorie_target, 1500)  # Min safe for men
    
    # Log debug info
    logger.info(f"Calorie Calculation Debug - User: {user['user_id']}")
    logger.info(f"  Gender: {data.gender}, Age: {data.age}, Height: {data.height}cm, Weight: {data.weight}kg")
    logger.info(f"  BMR: {round(bmr)} kcal")
    logger.info(f"  Activity Factor: {activity_factor} (Level: {data.activity_level})")
    logger.info(f"  TDEE: {round(tdee)} kcal")
    logger.info(f"  Goal: {data.goal}, Final Target: {round(calorie_target)} kcal")
    
    # Special adjustments for health conditions
    if "diabetes" in data.health_conditions:
        carbs_ratio = 0.35  # Lower carbs for diabetics
    else:
        carbs_ratio = 0.45
    
    # Protein calculation based on goal
    if data.goal == "gain_muscle":
        protein_per_kg = 2.0
    elif data.goal == "lose_weight":
        protein_per_kg = 1.8  # Higher protein for satiety
    else:
        protein_per_kg = 1.6
    
    profile_doc = {
        "user_id": user["user_id"],
        "gender": data.gender,
        "age": data.age,
        "height": data.height,
        "weight": data.weight,
        "target_weight": data.target_weight,
        "bmi": bmi,
        "ideal_bmi": ideal_bmi_target,
        "ideal_weight": ideal_weight,
        "ideal_weight_range": {"min": ideal_weight_min, "max": ideal_weight_max},
        "goal": data.goal,
        "activity_level": data.activity_level,
        "dietary_preferences": data.dietary_preferences,
        "allergies": data.allergies,
        "fitness_level": data.fitness_level,
        # New personalization fields
        "health_conditions": data.health_conditions,
        "food_likes": data.food_likes,
        "food_dislikes": data.food_dislikes,
        "time_constraint": data.time_constraint,
        "budget": data.budget,
        "cooking_skill": data.cooking_skill,
        "meals_per_day": data.meals_per_day,
        # Bariatric data
        "bariatric_surgery": data.bariatric_surgery,
        "bariatric_surgery_date": data.bariatric_surgery_date,
        "bariatric_pre_op_weight": data.bariatric_pre_op_weight,
        "bariatric_pre_op_height": data.bariatric_pre_op_height,
        "bariatric_parcours": data.bariatric_parcours,
        "bariatric_phase": data.bariatric_phase,
        "bariatric_supplements": data.bariatric_supplements or [],
        "bariatric_intolerances": data.bariatric_intolerances or [],
        "bariatric_clinic": data.bariatric_clinic,
        "bariatric_surgeon": data.bariatric_surgeon,
        "bariatric_nutritionist": data.bariatric_nutritionist,
        "bariatric_psychologist": data.bariatric_psychologist,
        # Calculated targets with debug info
        "daily_calorie_target": round(calorie_target),
        "daily_protein_target": round(data.weight * protein_per_kg),
        "daily_carbs_target": round(calorie_target * carbs_ratio / 4),
        "daily_fat_target": round(calorie_target * 0.25 / 9),
        "daily_fiber_target": 30 if data.gender == "male" else 25,
        "daily_water_target": round(data.weight * 35),  # ml per kg
        # Debug values for transparency
        "calorie_debug": {
            "bmr": round(bmr),
            "activity_factor": activity_factor,
            "tdee_maintenance": round(tdee),
            "goal_applied": data.goal,
            "final_target": round(calorie_target)
        },
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Initialize bariatric tracking if surgery selected
    if data.bariatric_surgery:
        await db.bariatric_logs.delete_many({"user_id": user["user_id"]})  # Reset
        
        # Add surgery to agenda if date is in the future
        if data.bariatric_surgery_date:
            try:
                surgery_date_str = data.bariatric_surgery_date
                # Handle both date-only and datetime formats
                if 'T' not in surgery_date_str:
                    surgery_date_str = surgery_date_str + 'T00:00:00+00:00'
                elif '+' not in surgery_date_str and 'Z' not in surgery_date_str:
                    surgery_date_str = surgery_date_str + '+00:00'
                surgery_date = datetime.fromisoformat(surgery_date_str.replace('Z', '+00:00'))
                
                if surgery_date > datetime.now(timezone.utc):
                    surgery_name = "By-pass gastrique" if data.bariatric_surgery == "bypass" else "Sleeve gastrectomie"
                    await db.agenda_events.insert_one({
                        "event_id": f"event_{uuid.uuid4().hex[:8]}",
                        "user_id": user["user_id"],
                        "title": f"🏥 {surgery_name}",
                        "description": f"Opération bariatrique - {data.bariatric_clinic or 'Hôpital'}",
                        "date": data.bariatric_surgery_date,
                        "type": "surgery",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
            except Exception as e:
                logger.warning(f"Could not parse surgery date: {e}")
    
    await db.user_profiles.update_one(
        {"user_id": user["user_id"]},
        {"$set": profile_doc},
        upsert=True
    )
    
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"onboarding_completed": True}}
    )
    
    # Add initial weight entry
    await db.weight_history.insert_one({
        "user_id": user["user_id"],
        "weight": data.weight,
        "bmi": bmi,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "entry_id": f"weight_{uuid.uuid4().hex[:8]}"
    })
    
    # Add initial BMI entry
    await db.bmi_history.insert_one({
        "user_id": user["user_id"],
        "bmi": bmi,
        "weight": data.weight,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "entry_id": f"bmi_{uuid.uuid4().hex[:8]}"
    })
    
    return {"message": "Onboarding completed", "profile": profile_doc}

@api_router.put("/profile")
async def update_profile(data: dict, user: dict = Depends(get_current_user)):
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.user_profiles.update_one(
        {"user_id": user["user_id"]},
        {"$set": data},
        upsert=True
    )
    return {"message": "Profile updated"}

# ==================== BARIATRIC ENDPOINTS ====================

def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Calculate Basal Metabolic Rate using Mifflin St Jeor formula"""
    if gender == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Calculate Total Daily Energy Expenditure"""
    factors = {"sedentary": 1.2, "moderate": 1.4, "active": 1.6}
    return bmr * factors.get(activity_level, 1.2)

def get_bariatric_nutrition_rules(phase: int, parcours: str, surgery_type: str, profile: dict) -> dict:
    """Get nutrition rules based on phase and profile - NO AI, pure algorithm"""
    weight = profile.get("weight", 70)
    height = profile.get("height", 170)
    age = profile.get("age", 40)
    gender = profile.get("gender", "female")
    activity = profile.get("activity_level", "sedentary")
    
    bmr = calculate_bmr(weight, height, age, gender)
    tdee = calculate_tdee(bmr, activity)
    
    # PRE-OP RULES
    if parcours == "pre_op" or phase == 0:
        deficit = 0.22  # 22% deficit
        calories_target = tdee * (1 - deficit)
        min_cal = 1500 if gender == "male" else 1200
        calories_target = max(calories_target, min_cal)
        
        return {
            "phase_name": "Pré-opératoire",
            "phase_description": "Réduction du foie et préparation à la chirurgie",
            "calories": {"target": round(calories_target), "min": min_cal, "max": round(tdee * 0.85)},
            "protein": {"target": round(weight * 1.3), "unit": "g", "ratio": "1.2-1.5g/kg"},
            "fat": {"percent": 27, "grams": round(calories_target * 0.27 / 9)},
            "carbs": {"percent": 43, "grams": round(calories_target * 0.43 / 4)},
            "hydration": {"target": max(30 * weight, 1500), "unit": "ml", "tips": "Boire entre les repas"},
            "meals_per_day": 4,
            "portion_size": {"min": 150, "max": 200, "unit": "g"},
            "texture": "normal",
            "restrictions": ["Éviter sucres rapides", "Limiter graisses saturées", "Réduire sel"],
            "priorities": ["Déficit calorique contrôlé", "Protéines suffisantes", "Hydratation optimale"],
            "surgery_specific": {
                "sleeve": ["Éviter boissons gazeuses", "Préparer l'estomac"],
                "bypass": ["Éviter sucres rapides", "Habituer aux petites portions"]
            }.get(surgery_type, [])
        }
    
    # PHASE 1 - LIQUID (J1-J7)
    if phase == 1:
        return {
            "phase_name": "Phase 1 - Liquide",
            "phase_description": "Cicatrisation et réhydratation",
            "calories": {"target": 500, "min": 400, "max": 600},
            "protein": {"target": 60, "unit": "g", "ratio": "≥60g/jour"},
            "fat": {"percent": 15, "grams": round(500 * 0.15 / 9)},
            "carbs": {"percent": 25, "grams": round(500 * 0.25 / 4)},
            "hydration": {"target": 1500, "unit": "ml", "tips": "Petites gorgées toutes les 10-15 min"},
            "meals_per_day": 7,
            "portion_size": {"min": 30, "max": 50, "unit": "ml"},
            "texture": "liquid",
            "restrictions": ["Aucun solide", "Pas de paille", "Pas de boissons gazeuses"],
            "priorities": ["Cicatrisation", "Hydratation", "Protéines liquides"],
            "allowed_foods": ["Bouillons clairs", "Eau", "Thé/infusions", "Protéines liquides", "Yaourt liquide"],
            "surgery_specific": {
                "sleeve": ["Attention au reflux", "Position semi-assise après repas"],
                "bypass": ["Éviter tout sucre", "Risque dumping"]
            }.get(surgery_type, [])
        }
    
    # PHASE 2 - MIXED (S2-S3)
    if phase == 2:
        return {
            "phase_name": "Phase 2 - Mixé",
            "phase_description": "Réintroduction progressive",
            "calories": {"target": 700, "min": 600, "max": 800},
            "protein": {"target": 65, "unit": "g", "ratio": "60-70g/jour"},
            "fat": {"percent": 25, "grams": round(700 * 0.25 / 9)},
            "carbs": {"percent": 35, "grams": round(700 * 0.35 / 4)},
            "hydration": {"target": 1650, "unit": "ml", "tips": "30 min avant/après repas"},
            "meals_per_day": 6,
            "portion_size": {"min": 60, "max": 100, "unit": "g"},
            "texture": "mixed",
            "restrictions": ["Texture lisse obligatoire", "Pas de morceaux", "Mâcher 20x"],
            "priorities": ["Protéines d'abord", "Textures lisses", "Tolérance progressive"],
            "allowed_foods": ["Purées légumes", "Compotes", "Œufs brouillés mous", "Fromage blanc", "Poisson mixé"],
            "surgery_specific": {
                "sleeve": ["Tester tolérance lentement", "Éviter acidité"],
                "bypass": ["Protéines prioritaires", "Attention dumping"]
            }.get(surgery_type, [])
        }
    
    # PHASE 3 - SOFT (S4-S6)
    if phase == 3:
        return {
            "phase_name": "Phase 3 - Mou",
            "phase_description": "Diversification alimentaire",
            "calories": {"target": 900, "min": 800, "max": 1000},
            "protein": {"target": 75, "unit": "g", "ratio": "70-80g/jour"},
            "fat": {"percent": 28, "grams": round(900 * 0.28 / 9)},
            "carbs": {"percent": 37, "grams": round(900 * 0.37 / 4)},
            "hydration": {"target": 1800, "unit": "ml", "tips": "Objectif 1.8L minimum"},
            "meals_per_day": 5,
            "portion_size": {"min": 80, "max": 120, "unit": "g"},
            "texture": "soft",
            "restrictions": ["Bien mâcher", "Éviter fibreux", "Pas de pain frais"],
            "priorities": ["Protéines 70-80g", "Textures tendres", "Mastication 20-30x"],
            "allowed_foods": ["Poisson tendre", "Poulet haché", "Légumes bien cuits", "Fruits mous", "Œufs"],
            "surgery_specific": {
                "sleeve": ["Éviter aliments coincés", "Manger lentement"],
                "bypass": ["Suppléments essentiels", "Éviter sucres"]
            }.get(surgery_type, [])
        }
    
    # PHASE 4 - SOLID ADAPTED (>S6)
    calories_target = max(tdee * 0.80, 1200)
    protein_target = round(weight * 1.35)
    
    return {
        "phase_name": "Phase 4 - Solide adapté",
        "phase_description": "Alimentation normale adaptée",
        "calories": {"target": round(calories_target), "min": 1200, "max": round(tdee * 0.9)},
        "protein": {"target": protein_target, "unit": "g", "ratio": "1.2-1.5g/kg"},
        "fat": {"percent": 30, "grams": round(calories_target * 0.30 / 9)},
        "carbs": {"percent": 40, "grams": round(calories_target * 0.40 / 4)},
        "hydration": {"target": round(30 * weight), "unit": "ml", "tips": "30ml/kg de poids"},
        "meals_per_day": 4,
        "portion_size": {"min": 100, "max": 150, "unit": "g"},
        "texture": "solid_adapted",
        "restrictions": ["Portions contrôlées", "Mâcher 20x min", "Pas de boissons pendant repas"],
        "priorities": ["Protéines d'abord", "Légumes ensuite", "Féculents en dernier"],
        "allowed_foods": ["Viandes tendres", "Poissons", "Légumes variés", "Fruits", "Féculents modérés"],
        "surgery_specific": {
            "sleeve": ["Éviter reflux", "Pas de boissons gazeuses", "Éviter alcool"],
            "bypass": ["Suppléments à vie", "Attention dumping", "Éviter sucres rapides"]
        }.get(surgery_type, [])
    }

def calculate_bariatric_phase(surgery_date_str: str) -> dict:
    """Calculate bariatric phase based on surgery date"""
    if not surgery_date_str:
        return {"phase": None, "phase_name": None, "days_since_surgery": 0}
    
    try:
        surgery_date = datetime.fromisoformat(surgery_date_str.replace('Z', '+00:00'))
        days_since = (datetime.now(timezone.utc) - surgery_date).days
        
        if days_since < 0:
            return {"phase": 0, "phase_name": "Pré-opératoire", "days_since_surgery": days_since, "texture": "normal"}
        elif days_since <= 7:
            return {"phase": 1, "phase_name": "Phase 1 - Liquide", "days_since_surgery": days_since, "texture": "liquid", "weeks": "J1-J7"}
        elif days_since <= 21:
            return {"phase": 2, "phase_name": "Phase 2 - Mixé", "days_since_surgery": days_since, "texture": "mixed", "weeks": "S2-S3"}
        elif days_since <= 42:
            return {"phase": 3, "phase_name": "Phase 3 - Mou", "days_since_surgery": days_since, "texture": "soft", "weeks": "S4-S6"}
        else:
            return {"phase": 4, "phase_name": "Phase 4 - Solide adapté", "days_since_surgery": days_since, "texture": "solid_adapted", "weeks": "> S6"}
    except:
        return {"phase": None, "phase_name": None, "days_since_surgery": 0}

@api_router.get("/bariatric/nutrition-rules")
async def get_nutrition_rules(user: dict = Depends(get_current_user)):
    """Get personalized nutrition rules based on phase - NO AI"""
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    if not profile or not profile.get("bariatric_surgery"):
        raise HTTPException(status_code=404, detail="No bariatric profile found")
    
    phase_info = calculate_bariatric_phase(profile.get("bariatric_surgery_date"))
    phase = phase_info.get("phase") or 4
    parcours = profile.get("bariatric_parcours", "post_op")
    surgery_type = profile.get("bariatric_surgery", "sleeve")
    
    rules = get_bariatric_nutrition_rules(phase, parcours, surgery_type, profile)
    
    return {
        "phase": phase_info,
        "rules": rules,
        "profile_summary": {
            "weight": profile.get("weight"),
            "height": profile.get("height"),
            "surgery_type": surgery_type,
            "parcours": parcours
        }
    }

@api_router.get("/bariatric/dashboard")
async def get_bariatric_dashboard(user: dict = Depends(get_current_user)):
    """Get bariatric patient dashboard data with nutrition rules"""
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    if not profile or not profile.get("bariatric_surgery"):
        raise HTTPException(status_code=404, detail="No bariatric profile found")
    
    # Calculate current phase
    phase_info = calculate_bariatric_phase(profile.get("bariatric_surgery_date"))
    phase = phase_info.get("phase") or 4
    
    # Get nutrition rules
    parcours = profile.get("bariatric_parcours", "post_op")
    surgery_type = profile.get("bariatric_surgery", "sleeve")
    nutrition_rules = get_bariatric_nutrition_rules(phase, parcours, surgery_type, profile)
    
    # Get recent logs
    logs = await db.bariatric_logs.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("date", -1).limit(30).to_list(30)
    
    # Get weight history
    weights = await db.weight_history.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("date", -1).limit(30).to_list(30)
    
    # Calculate weight loss since surgery
    pre_op_weight = profile.get("bariatric_pre_op_weight", profile.get("weight", 0))
    current_weight = weights[0]["weight"] if weights else profile.get("weight", 0)
    weight_lost = pre_op_weight - current_weight
    
    # Get today's log
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_log = await db.bariatric_logs.find_one(
        {"user_id": user["user_id"], "date": today},
        {"_id": 0}
    )
    
    # Check for reminders
    reminders = []
    if not today_log:
        reminders.append({"type": "log", "message": "📝 N'oubliez pas de renseigner votre suivi quotidien !", "priority": "high"})
    elif not today_log.get("weight"):
        reminders.append({"type": "weight", "message": "⚖️ Pensez à noter votre poids du jour", "priority": "medium"})
    elif not today_log.get("hydration"):
        reminders.append({"type": "hydration", "message": "💧 Avez-vous noté votre hydratation ?", "priority": "medium"})
    
    # Check supplements reminder
    supplements = profile.get("bariatric_supplements", [])
    if supplements and today_log:
        taken = today_log.get("supplements_taken", [])
        missing = [s for s in supplements if s not in taken]
        if missing:
            reminders.append({"type": "supplements", "message": f"💊 Suppléments à prendre : {', '.join(missing)}", "priority": "high"})
    
    return {
        "profile": {
            "surgery_type": surgery_type,
            "surgery_date": profile.get("bariatric_surgery_date"),
            "pre_op_weight": pre_op_weight,
            "pre_op_bmi": round(pre_op_weight / ((profile.get("bariatric_pre_op_height", profile.get("height", 170)) / 100) ** 2), 1) if profile.get("bariatric_pre_op_height") or profile.get("height") else None,
            "current_weight": current_weight,
            "weight_lost": round(weight_lost, 1),
            "parcours": parcours,
            "supplements": supplements,
            "intolerances": profile.get("bariatric_intolerances", []),
            "clinic": profile.get("bariatric_clinic"),
            "surgeon": profile.get("bariatric_surgeon"),
            "nutritionist": profile.get("bariatric_nutritionist"),
            "psychologist": profile.get("bariatric_psychologist"),
            "allergies": profile.get("allergies", [])
        },
        "phase": phase_info,
        "nutrition_rules": nutrition_rules,
        "today_log": today_log,
        "recent_logs": logs,
        "weight_history": weights,
        "reminders": reminders
    }

@api_router.post("/bariatric/log")
async def create_bariatric_log(data: dict, user: dict = Depends(get_current_user)):
    """Log daily bariatric tracking data"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    log_entry = {
        "log_id": f"bari_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "date": data.get("date", today),
        "weight": data.get("weight"),
        "food_tolerance": data.get("food_tolerance"),  # "ok", "nausea", "vomiting"
        "energy_level": data.get("energy_level"),  # 1-5
        "hydration": data.get("hydration"),  # ml
        "supplements_taken": data.get("supplements_taken", []),
        "notes": data.get("notes", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Update or insert
    await db.bariatric_logs.update_one(
        {"user_id": user["user_id"], "date": log_entry["date"]},
        {"$set": log_entry},
        upsert=True
    )
    
    # Update weight history if weight provided
    if data.get("weight"):
        height = (await db.user_profiles.find_one({"user_id": user["user_id"]}))
        h = height.get("height", 170) if height else 170
        bmi = data["weight"] / ((h / 100) ** 2)
        
        await db.weight_history.update_one(
            {"user_id": user["user_id"], "date": log_entry["date"]},
            {"$set": {
                "weight": data["weight"],
                "bmi": round(bmi, 1),
                "date": log_entry["date"],
                "entry_id": f"weight_{uuid.uuid4().hex[:8]}"
            }},
            upsert=True
        )
    
    # Check for alerts
    alerts = []
    if data.get("food_tolerance") == "vomiting":
        alerts.append("⚠️ Vomissements signalés - consultez votre équipe médicale si ça persiste")
    if data.get("energy_level") and data["energy_level"] <= 2:
        alerts.append("⚠️ Niveau d'énergie bas - vérifiez votre hydratation et apports protéiques")
    if data.get("hydration") and data["hydration"] < 1000:
        alerts.append("⚠️ Hydratation insuffisante - visez au moins 1.5L par jour")
    
    return {"message": "Log saved", "log": log_entry, "alerts": alerts}

@api_router.get("/bariatric/recipes")
async def get_bariatric_recipes(user: dict = Depends(get_current_user)):
    """Get recipes filtered by bariatric phase - NO AI, rules-based"""
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    if not profile or not profile.get("bariatric_surgery"):
        raise HTTPException(status_code=404, detail="No bariatric profile found")
    
    phase_info = calculate_bariatric_phase(profile.get("bariatric_surgery_date"))
    phase = phase_info.get("phase") or 4  # Default to phase 4 if None
    texture = phase_info.get("texture") or "solid_adapted"
    
    # Bariatric-specific recipes by phase (rules-based, no AI)
    recipes_by_phase = {
        1: [  # Liquid phase
            {"name": "Bouillon de légumes", "texture": "liquid", "protein": 2, "calories": 25, "portion": "150ml", "ingredients": ["légumes", "eau", "sel"], "instructions": "Faire mijoter les légumes 30 min, filtrer"},
            {"name": "Smoothie protéiné", "texture": "liquid", "protein": 20, "calories": 120, "portion": "150ml", "ingredients": ["protéine en poudre", "lait écrémé", "eau"], "instructions": "Mixer tous les ingrédients"},
            {"name": "Yaourt liquide", "texture": "liquid", "protein": 8, "calories": 80, "portion": "125ml", "ingredients": ["yaourt nature 0%"], "instructions": "Diluer légèrement si nécessaire"},
            {"name": "Soupe de potiron lisse", "texture": "liquid", "protein": 3, "calories": 45, "portion": "150ml", "ingredients": ["potiron", "bouillon", "sel"], "instructions": "Cuire et mixer très finement"},
            {"name": "Compote de pomme liquide", "texture": "liquid", "protein": 0, "calories": 50, "portion": "100ml", "ingredients": ["pommes", "eau"], "instructions": "Cuire et mixer jusqu'à consistance liquide"},
        ],
        2: [  # Mixed phase
            {"name": "Purée de légumes", "texture": "mixed", "protein": 4, "calories": 80, "portion": "100g", "ingredients": ["carottes", "courgettes", "pomme de terre"], "instructions": "Cuire et mixer en purée lisse"},
            {"name": "Œufs brouillés très mous", "texture": "mixed", "protein": 12, "calories": 140, "portion": "80g", "ingredients": ["2 œufs", "lait"], "instructions": "Cuire doucement en remuant"},
            {"name": "Fromage blanc mixé", "texture": "mixed", "protein": 15, "calories": 100, "portion": "100g", "ingredients": ["fromage blanc 0%", "compote"], "instructions": "Mixer jusqu'à consistance lisse"},
            {"name": "Purée de poisson", "texture": "mixed", "protein": 18, "calories": 100, "portion": "80g", "ingredients": ["cabillaud", "crème légère"], "instructions": "Cuire le poisson et mixer avec la crème"},
            {"name": "Velouté de poulet", "texture": "mixed", "protein": 15, "calories": 120, "portion": "150ml", "ingredients": ["poulet", "bouillon", "légumes"], "instructions": "Cuire et mixer finement"},
        ],
        3: [  # Soft phase
            {"name": "Omelette moelleuse", "texture": "soft", "protein": 12, "calories": 160, "portion": "100g", "ingredients": ["2 œufs", "fromage râpé"], "instructions": "Cuire doucement, bien baveuse"},
            {"name": "Poisson vapeur émietté", "texture": "soft", "protein": 20, "calories": 110, "portion": "100g", "ingredients": ["saumon", "citron"], "instructions": "Cuire vapeur et émietter à la fourchette"},
            {"name": "Purée de patate douce", "texture": "soft", "protein": 2, "calories": 90, "portion": "100g", "ingredients": ["patate douce", "beurre"], "instructions": "Cuire et écraser"},
            {"name": "Poulet haché tendre", "texture": "soft", "protein": 25, "calories": 150, "portion": "80g", "ingredients": ["poulet haché", "sauce tomate"], "instructions": "Cuire doucement dans la sauce"},
            {"name": "Cottage cheese aux fruits", "texture": "soft", "protein": 14, "calories": 120, "portion": "120g", "ingredients": ["cottage cheese", "fruits mous"], "instructions": "Mélanger délicatement"},
        ],
        4: [  # Solid adapted phase
            {"name": "Blanc de poulet grillé", "texture": "solid_adapted", "protein": 30, "calories": 165, "portion": "100g", "ingredients": ["poulet", "herbes"], "instructions": "Griller et couper en petits morceaux"},
            {"name": "Saumon au four", "texture": "solid_adapted", "protein": 25, "calories": 200, "portion": "100g", "ingredients": ["saumon", "citron", "aneth"], "instructions": "Cuire au four 15 min"},
            {"name": "Tofu sauté aux légumes", "texture": "solid_adapted", "protein": 15, "calories": 150, "portion": "120g", "ingredients": ["tofu", "légumes", "sauce soja"], "instructions": "Sauter à la poêle"},
            {"name": "Œufs pochés", "texture": "solid_adapted", "protein": 12, "calories": 140, "portion": "2 œufs", "ingredients": ["œufs", "vinaigre"], "instructions": "Pocher 3 min dans l'eau frémissante"},
            {"name": "Crevettes grillées", "texture": "solid_adapted", "protein": 24, "calories": 120, "portion": "100g", "ingredients": ["crevettes", "ail", "persil"], "instructions": "Griller rapidement à la poêle"},
        ]
    }
    
    # Get recipes for current phase and below
    available_recipes = []
    for p in range(1, phase + 1):
        available_recipes.extend(recipes_by_phase.get(p, []))
    
    # Filter by allergies and intolerances
    allergies = profile.get("allergies", [])
    intolerances = profile.get("bariatric_intolerances", [])
    excluded = set(allergies + intolerances)
    
    filtered_recipes = []
    for recipe in available_recipes:
        # Simple ingredient check
        recipe_ingredients = " ".join(recipe.get("ingredients", [])).lower()
        exclude = False
        for allergen in excluded:
            if allergen.lower() in recipe_ingredients:
                exclude = True
                break
        if not exclude:
            recipe["phase_allowed"] = phase
            filtered_recipes.append(recipe)
    
    return {
        "phase": phase_info,
        "recipes": filtered_recipes,
        "guidelines": {
            "portion_size": "60-120g max par repas",
            "protein_first": "Toujours commencer par les protéines",
            "chew_well": "Mâcher au moins 20 fois chaque bouchée",
            "no_drinking": "Ne pas boire pendant les repas (30 min avant/après)"
        }
    }

@api_router.get("/bariatric/articles")
async def get_bariatric_articles(user: dict = Depends(get_current_user)):
    """Get daily bariatric-specific articles - NO AI"""
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    if not profile or not profile.get("bariatric_surgery"):
        raise HTTPException(status_code=404, detail="No bariatric profile found")
    
    surgery_type = profile.get("bariatric_surgery", "bypass")
    phase_info = calculate_bariatric_phase(profile.get("bariatric_surgery_date"))
    
    # Pool of bariatric articles with full content
    all_articles = [
        {
            "title": "Les protéines après chirurgie bariatrique",
            "category": "nutrition",
            "surgery": "both",
            "summary": "Pourquoi viser 60-80g de protéines par jour est essentiel pour préserver votre masse musculaire.",
            "content": """Les protéines sont essentielles après une chirurgie bariatrique pour plusieurs raisons fondamentales :

🎯 Objectif quotidien : 60 à 80g de protéines par jour

📌 Pourquoi c'est crucial :
• Préserve la masse musculaire pendant la perte de poids rapide
• Favorise la cicatrisation post-opératoire
• Maintient la force et l'énergie
• Prévient la fonte musculaire (sarcopénie)

🍽️ Sources de protéines recommandées :
• Viandes maigres (poulet, dinde)
• Poissons et fruits de mer
• Œufs (excellente source)
• Produits laitiers (fromage blanc, yaourt grec)
• Légumineuses (lentilles, pois chiches)
• Compléments protéinés si nécessaire

⏰ Conseils pratiques :
1. Commencez chaque repas par les protéines
2. Répartissez l'apport sur 4-5 repas
3. Utilisez des poudres protéinées si besoin
4. Évitez les protéines grasses

⚠️ N'hésitez pas à consulter votre nutritionniste si vous n'atteignez pas vos objectifs protéiques.""",
            "source": "HAS",
            "read_time": "4 min",
            "image": "https://images.unsplash.com/photo-1532550907401-a500c9a57435?w=400"
        },
        {
            "title": "Gérer les carences en vitamines",
            "category": "santé",
            "surgery": "both",
            "summary": "B12, fer, calcium, vitamine D : les suppléments indispensables et leur importance.",
            "content": """Après une chirurgie bariatrique, votre corps absorbe moins bien certains nutriments. La supplémentation est donc INDISPENSABLE À VIE.

💊 Suppléments essentiels :

🔴 Vitamine B12
• Injection mensuelle ou comprimés sublinguaux quotidiens
• Carence = fatigue, troubles neurologiques, anémie

🟠 Fer
• Particulièrement important pour les femmes
• À prendre à jeun avec vitamine C
• Ne pas associer au calcium

🟡 Calcium
• 1200-1500 mg/jour en citrate
• Répartir en 2-3 prises
• Essentiel pour les os

🔵 Vitamine D
• 2000-4000 UI/jour
• Aide à l'absorption du calcium
• Bilans réguliers recommandés

⚠️ Après un bypass :
• Ajoutez : vitamines A, E, K, zinc
• Risque de carences plus élevé

📅 Contrôles sanguins :
• Tous les 3 mois la 1ère année
• Puis tous les 6 mois
• Ajustements selon résultats

Ne jamais arrêter les suppléments sans avis médical !""",
            "source": "SOFFCO",
            "read_time": "5 min",
            "image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400"
        },
        {
            "title": "Le dumping syndrome : comprendre et prévenir",
            "category": "bypass",
            "surgery": "bypass",
            "summary": "Symptômes, causes et conseils pour éviter ce phénomène fréquent après un bypass.",
            "content": """Le dumping syndrome est une réaction fréquente après un bypass gastrique. Apprenez à le reconnaître et à l'éviter.

🔍 Qu'est-ce que c'est ?
Le dumping se produit quand les aliments passent trop vite dans l'intestin grêle, provoquant une série de symptômes désagréables.

⚡ Dumping précoce (15-30 min après le repas) :
• Nausées, crampes abdominales
• Diarrhée, ballonnements
• Sueurs, palpitations
• Sensation de malaise

🕐 Dumping tardif (1-3h après le repas) :
• Hypoglycémie réactionnelle
• Fatigue intense
• Tremblements
• Confusion

🍬 Aliments déclencheurs :
❌ Sucres rapides (bonbons, gâteaux, sodas)
❌ Aliments très gras
❌ Alcool
❌ Repas trop copieux

✅ Prévention :
• Manger lentement (20-30 min par repas)
• Petites portions
• Éviter de boire pendant les repas
• Privilégier les sucres complexes
• S'allonger après manger si symptômes

Le dumping diminue avec le temps mais reste un "garde-fou" contre les écarts alimentaires.""",
            "source": "CHU",
            "read_time": "5 min",
            "image": "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=400"
        },
        {
            "title": "Reprise alimentaire post-sleeve",
            "category": "sleeve",
            "surgery": "sleeve",
            "summary": "Les étapes de la réalimentation après une sleeve gastrectomie.",
            "content": """La réalimentation après une sleeve suit un protocole précis en 4 phases pour permettre une bonne cicatrisation.

📅 PHASE 1 - Liquide (J1 à J7)
• Eau, bouillons clairs, thé
• Par petites gorgées (30ml)
• Objectif : hydratation

📅 PHASE 2 - Mixé/Lisse (S2 à S3)
• Soupes veloutées, compotes
• Yaourts, fromage blanc
• Texture lisse obligatoire
• Portions : 60-100g

📅 PHASE 3 - Mou (S4 à S6)
• Textures tendres
• Poisson émietté, œufs brouillés
• Légumes bien cuits
• Portions : 80-120g

📅 PHASE 4 - Solide adapté (>S6)
• Retour progressif au solide
• Bien mâcher (20 fois min)
• Portions : 100-150g max

⚠️ Règles d'or :
• Ne jamais sauter d'étape
• Écouter son corps
• Arrêter dès la première sensation de satiété
• Ne pas boire en mangeant

🚨 Signaux d'alerte :
• Douleurs persistantes
• Vomissements répétés
• Impossibilité de s'hydrater
→ Contactez votre chirurgien""",
            "source": "AFDN",
            "read_time": "4 min",
            "image": "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=400"
        },
        {
            "title": "L'hydratation après chirurgie bariatrique",
            "category": "hydratation",
            "surgery": "both",
            "summary": "Comment atteindre 1.5L par jour quand l'estomac est réduit.",
            "content": """L'hydratation est un défi majeur après la chirurgie bariatrique. Voici comment y arriver.

🎯 Objectif : 1.5 à 2 litres par jour

⏰ Stratégies efficaces :
• Boire par petites gorgées régulières
• Toutes les 10-15 minutes
• Garder une bouteille toujours à portée
• Utiliser des rappels sur téléphone

⚠️ Règle cruciale :
Ne PAS boire pendant les repas !
• 30 min avant le repas
• 30-45 min après le repas

💧 Boissons recommandées :
✅ Eau plate
✅ Eau aromatisée (citron, menthe)
✅ Thé, infusions (sans sucre)
✅ Bouillons

❌ À éviter :
• Boissons gazeuses
• Sodas
• Jus de fruits sucrés
• Alcool (surtout après bypass)

🌡️ Signes de déshydratation :
• Urines foncées
• Fatigue
• Maux de tête
• Vertiges
• Constipation

📱 Astuce : Des apps peuvent vous aider à suivre votre hydratation quotidienne !""",
            "source": "HAS",
            "read_time": "3 min",
            "image": "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=400"
        },
        {
            "title": "Activité physique et perte de poids",
            "category": "sport",
            "surgery": "both",
            "summary": "Reprendre le sport progressivement pour optimiser vos résultats.",
            "content": """L'activité physique est un pilier essentiel pour optimiser et maintenir votre perte de poids après chirurgie.

📅 Reprise progressive :

Semaines 1-4 :
• Marche légère (10-15 min/jour)
• Mouvements doux
• Pas d'efforts abdominaux

Mois 2-3 :
• Marche 30 min/jour
• Natation (si cicatrisation OK)
• Vélo doux

À partir du mois 4 :
• Renforcement musculaire léger
• Cardio modéré
• Sports variés

🎯 Objectif long terme :
• 150 min d'activité modérée/semaine
• 2 séances de renforcement

💪 Bénéfices prouvés :
• Préserve la masse musculaire
• Accélère le métabolisme
• Améliore la qualité de peau
• Booste le moral
• Évite la reprise de poids

⚠️ Précautions :
• Toujours s'hydrater
• Collation protéinée après l'effort
• Écouter son corps
• Éviter les sports à impact les premiers mois

Commencez doucement mais commencez !""",
            "source": "SOFFCO",
            "read_time": "4 min",
            "image": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400"
        },
        {
            "title": "Les signaux de faim et satiété",
            "category": "comportement",
            "surgery": "both",
            "summary": "Réapprendre à écouter son corps après une chirurgie bariatrique.",
            "content": """Après l'opération, vos signaux de faim et satiété sont modifiés. Réapprenez à les reconnaître.

🔍 Nouveaux signaux de satiété :
• Pression dans la poitrine/estomac
• Hoquet
• Nez qui coule
• Éternuement
• Respiration difficile

⚠️ STOP immédiat si :
• Douleur
• Nausée
• Sensation de "trop plein"
→ Vous avez trop mangé !

📝 Conseils pratiques :
1. Manger dans le calme
2. Sans écran, concentré sur le repas
3. Poser les couverts entre chaque bouchée
4. Mâcher 20-30 fois
5. Repas de 20-30 min minimum

🧠 Distinguer faim physique vs émotionnelle :

Faim physique :
• Progressive
• Plusieurs aliments conviennent
• Disparaît quand on mange

Faim émotionnelle :
• Soudaine
• Envie d'un aliment précis
• Ne disparaît pas vraiment

✅ Astuce : Avant de manger, demandez-vous "Ai-je vraiment faim ou est-ce autre chose ?"

La pleine conscience alimentaire est votre meilleure alliée.""",
            "source": "CHU",
            "read_time": "4 min",
            "image": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=400"
        },
        {
            "title": "Éviter le grignotage émotionnel",
            "category": "psychologie",
            "surgery": "both",
            "summary": "Stratégies pour gérer les envies de manger liées aux émotions.",
            "content": """Le grignotage émotionnel peut saboter vos résultats. Apprenez à le reconnaître et le gérer.

🎭 Déclencheurs fréquents :
• Stress, anxiété
• Ennui
• Tristesse, déprime
• Fatigue
• Solitude
• Célébration

🛑 Le cycle du grignotage :
Émotion → Envie → Grignotage → Culpabilité → Émotion négative...

✅ Stratégies efficaces :

1. Identifier le déclencheur
"Pourquoi ai-je envie de manger ?"

2. Attendre 10 minutes
L'envie passe souvent

3. Alternatives saines :
• Boire de l'eau/thé
• Marcher 10 min
• Appeler un ami
• Faire une activité plaisir
• Technique de respiration

4. Si vous mangez quand même :
• Pas de culpabilité
• Petite portion
• Savourez consciemment

🧠 Travail de fond :
• Suivi psychologique recommandé
• Journal alimentaire émotionnel
• Techniques de gestion du stress
• Groupe de parole

La chirurgie opère l'estomac, pas la tête. Le travail psychologique est essentiel.""",
            "source": "AFDN",
            "read_time": "5 min",
            "image": "https://images.unsplash.com/photo-1493836512294-502baa1986e2?w=400"
        },
        {
            "title": "La peau après une perte de poids importante",
            "category": "corps",
            "surgery": "both",
            "summary": "Comment prendre soin de sa peau et options de chirurgie réparatrice.",
            "content": """L'excès de peau est fréquent après une perte de poids massive. Voici ce qu'il faut savoir.

📉 Pourquoi la peau ne se rétracte pas toujours ?
• Perte de poids rapide
• Âge
• Exposition solaire passée
• Qualité de la peau
• Quantité de poids perdu

🧴 Soins préventifs :
• Hydratation (eau + crèmes)
• Exercice physique (muscle = meilleur aspect)
• Apports en protéines suffisants
• Pas de tabac
• Protection solaire

💪 Zones les plus touchées :
• Ventre (tablier abdominal)
• Bras
• Cuisses
• Poitrine
• Visage

🏥 Chirurgie réparatrice :

Quand l'envisager ?
• Poids stable depuis 12-18 mois
• Retentissement fonctionnel ou psychologique

Interventions possibles :
• Abdominoplastie
• Lifting des bras/cuisses
• Bodylift circulaire

💶 Prise en charge :
• Certaines interventions remboursées (tablier gênant)
• Dossier à constituer avec photos
• Délais variables selon régions

Le plus important : accepter ce nouveau corps qui vous a permis de reprendre votre santé en main.""",
            "source": "SOFFCO",
            "read_time": "5 min",
            "image": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400"
        },
        {
            "title": "Alcool et chirurgie bariatrique",
            "category": "santé",
            "surgery": "both",
            "summary": "Pourquoi l'alcool est plus dangereux après une chirurgie et les précautions à prendre.",
            "content": """L'alcool après chirurgie bariatrique présente des risques particuliers qu'il est crucial de comprendre.

⚠️ Pourquoi c'est différent ?

Après la chirurgie :
• L'alcool passe plus vite dans le sang
• Effet plus rapide et plus fort
• Élimination plus lente
• Même quantité = effet x2 ou x3

🚨 Risques spécifiques :

Pour tous :
• Ivresse rapide et imprévue
• Hypoglycémie
• Déshydratation
• Calories vides = reprise de poids
• Risque d'addiction transférée

Après bypass :
• Dumping syndrome
• Absorption encore plus rapide
• Carences aggravées

📋 Recommandations :

Période post-op immédiate :
❌ Aucun alcool les 6 premiers mois minimum

Après stabilisation :
• Jamais l'estomac vide
• Portions très réduites
• Tester chez soi d'abord
• Ne pas conduire
• Éviter les cocktails sucrés

🍷 Si vous buvez :
• 1 verre peut = 3 verres d'effet
• Préférer le vin rouge
• Beaucoup d'eau avant/après
• Manger quelque chose avec

Le plus sûr reste l'abstinence. Parlez-en à votre équipe si vous avez du mal à vous limiter.""",
            "source": "HAS",
            "read_time": "4 min",
            "image": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=400"
        },
        {
            "title": "Plateau de perte de poids : que faire ?",
            "category": "motivation",
            "surgery": "both",
            "summary": "Comprendre et surmonter les phases de stagnation.",
            "content": """Les plateaux sont normaux et font partie du processus. Voici comment les gérer.

📊 Qu'est-ce qu'un plateau ?
• Stagnation du poids pendant 2-4 semaines
• Malgré le respect des règles
• Partie normale du processus

🧬 Pourquoi ça arrive ?
• Le corps s'adapte au nouveau poids
• Le métabolisme ralentit
• Parfois : perte de gras + gain de muscle

✅ Ce qu'il faut faire :

1. Ne pas paniquer !
Le plateau finit toujours par passer

2. Vérifier les bases :
• Apport protéique suffisant ?
• Hydratation OK ?
• Activité physique régulière ?
• Pas de grignotage caché ?

3. Ajustements possibles :
• Varier l'activité physique
• Revoir les portions
• Tenir un journal alimentaire
• Peser/mesurer précisément

4. Ce qui ne fonctionne PAS :
❌ Sauter des repas
❌ Régimes restrictifs
❌ Compléments "miracle"

📏 Autres mesures que le poids :
• Tour de taille
• Vêtements qui changent
• Énergie
• Santé globale

⏳ Patience !
La perte de poids post-chirurgie dure 12-18 mois. Les plateaux sont des pauses, pas des échecs.""",
            "source": "CHU",
            "read_time": "4 min",
            "image": "https://images.unsplash.com/photo-1434494878577-86c23bcb06b9?w=400"
        },
        {
            "title": "RGO et bypass gastrique",
            "category": "bypass",
            "surgery": "bypass",
            "summary": "Le reflux gastro-œsophagien : amélioration fréquente après bypass.",
            "content": """Le bypass gastrique peut significativement améliorer le reflux gastro-œsophagien (RGO). Voici pourquoi.

🔬 Comment le bypass aide ?
• Réduction de la production d'acide
• Le petit estomac ne reflue plus
• Amélioration chez 70-90% des patients

📈 Bénéfices observés :
• Diminution/arrêt des IPP
• Moins de brûlures
• Meilleur sommeil
• Qualité de vie améliorée

⚠️ Cas particuliers :
Parfois le RGO persiste ou apparaît :
• Vérifier avec votre chirurgien
• Examens si nécessaire
• Ajustements possibles

vs SLEEVE :
• La sleeve peut AGGRAVER le RGO
• C'est une contre-indication relative
• Le bypass est préféré si RGO préexistant

🏥 Avant l'opération :
• Mentionnez tout RGO au chirurgien
• Fibroscopie souvent recommandée
• Choix de technique adapté

💊 Après l'opération :
• Les IPP sont souvent arrêtés progressivement
• Toujours sous supervision médicale
• Signaler tout retour des symptômes

Le bypass reste la technique de choix pour les patients souffrant de RGO sévère.""",
            "source": "SOFFCO",
            "read_time": "4 min",
            "image": "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=400"
        },
        {
            "title": "Chute de cheveux post-opératoire",
            "category": "santé",
            "surgery": "both",
            "summary": "Causes, durée et solutions pour limiter la perte de cheveux.",
            "content": """La chute de cheveux après chirurgie bariatrique est fréquente mais temporaire. Voici ce qu'il faut savoir.

📅 Quand ça arrive ?
• 2 à 4 mois après l'opération
• Pic vers le 4ème mois
• Repousse à partir du 6ème mois

🔍 Pourquoi ?
• Stress de la chirurgie
• Perte de poids rapide
• Carences nutritionnelles
• Déficit protéique

⏳ Combien de temps ?
• Phase aiguë : 3-6 mois
• Repousse : progressive
• Retour à la normale : 12-18 mois

✅ Prévention et traitement :

Nutrition :
• Protéines : 60-80g/jour minimum
• Zinc : supplément si carence
• Biotine (B8) : peut aider
• Fer : contrôler et supplémenter

Soins externes :
• Shampooing doux
• Éviter chaleur excessive
• Pas de coiffures tirées
• Massage du cuir chevelu

🚨 Consulter si :
• Chute massive
• Pas de repousse après 12 mois
• Autres symptômes associés

💡 Rappel :
Les cheveux repoussent presque toujours. Cette phase difficile est temporaire. Concentrez-vous sur votre nutrition !""",
            "source": "AFDN",
            "read_time": "4 min",
            "image": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400"
        },
        {
            "title": "Grossesse après chirurgie bariatrique",
            "category": "santé",
            "surgery": "both",
            "summary": "Délais recommandés et suivi particulier pour une grossesse en sécurité.",
            "content": """Une grossesse est tout à fait possible après chirurgie bariatrique, avec quelques précautions importantes.

⏰ Délai recommandé :
• Attendre 12 à 18 mois après l'opération
• Poids stable depuis plusieurs mois
• Pas de carences majeures

Pourquoi attendre ?
• Phase de perte de poids = stress métabolique
• Carences à corriger avant
• Meilleur pronostic pour bébé

📋 Avant la conception :
• Bilan nutritionnel complet
• Ajustement des suppléments
• Acide folique : commencer 3 mois avant
• Consultation pré-conceptionnelle

🤰 Pendant la grossesse :

Suivi renforcé :
• Gynécologue + équipe bariatrique
• Bilans sanguins fréquents
• Échographies classiques

Nutrition :
• Augmentation des besoins
• Protéines : 70-90g/jour
• Supplémentation adaptée
• Pas de restriction calorique

Surveillance :
• Prise de poids modérée
• Glycémie (diabète gestationnel)
• Croissance fœtale

⚠️ Particularités bypass :
• Risque de carences accru
• Attention au dumping
• Ajuster vitamines/fer

👶 Allaitement :
• Possible et recommandé
• Maintenir supplémentation
• Surveillance bébé

La chirurgie bariatrique améliore souvent la fertilité. Consultez avant de planifier !""",
            "source": "HAS",
            "read_time": "5 min",
            "image": "https://images.unsplash.com/photo-1493894473891-10fc1e5dbd22?w=400"
        },
        {
            "title": "Sleeve et reflux gastrique",
            "category": "sleeve",
            "surgery": "sleeve",
            "summary": "Comprendre pourquoi le reflux peut apparaître après une sleeve.",
            "content": """Le reflux gastro-œsophagien (RGO) peut apparaître ou s'aggraver après une sleeve. Voici les explications.

🔬 Pourquoi la sleeve peut causer du RGO ?
• Pression augmentée dans l'estomac réduit
• Sphincter œsophagien parfois affaibli
• Modification de l'anatomie

📊 Fréquence :
• RGO nouveau ou aggravé : 20-30% des cas
• Amélioration pour certains patients
• Variable selon les individus

🚨 Symptômes à surveiller :
• Brûlures d'estomac
• Remontées acides
• Toux nocturne
• Goût acide dans la bouche
• Difficulté à dormir

✅ Gestion du RGO post-sleeve :

Mode de vie :
• Ne pas se coucher juste après manger
• Surélever la tête du lit
• Éviter aliments déclencheurs
• Petites portions
• Pas de vêtements serrés

Aliments à éviter :
❌ Café, thé fort
❌ Alcool
❌ Épices
❌ Agrumes
❌ Tomates
❌ Chocolat

💊 Traitement médicamenteux :
• IPP (Oméprazole, etc.)
• Souvent nécessaires à long terme
• Surveillance régulière

🏥 Si RGO sévère et résistant :
• Fibroscopie de contrôle
• Discussion d'une conversion en bypass
• Décision au cas par cas

Prévenez votre chirurgien si les symptômes persistent ou s'aggravent.""",
            "source": "CHU",
            "read_time": "4 min",
            "image": "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=400"
        },
    ]
    
    # Filter by surgery type
    filtered = [a for a in all_articles if a["surgery"] in ["both", surgery_type]]
    
    # Use day of year to rotate articles (3 per day)
    day_of_year = datetime.now(timezone.utc).timetuple().tm_yday
    start_idx = (day_of_year * 3) % len(filtered)
    
    daily_articles = []
    for i in range(3):
        idx = (start_idx + i) % len(filtered)
        article = filtered[idx].copy()
        article["article_id"] = f"bari_art_{idx}"
        daily_articles.append(article)
    
    return {"articles": daily_articles, "surgery_type": surgery_type}

@api_router.post("/bariatric/coach")
async def bariatric_coach(data: dict, user: dict = Depends(get_current_user)):
    """Bariatric AI coach with strict medical guardrails - uses AI credits"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    if not profile or not profile.get("bariatric_surgery"):
        raise HTTPException(status_code=404, detail="No bariatric profile found")
    
    question = data.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question required")
    
    # Check AI usage limit
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    usage = await db.ai_usage_logs.find_one({"user_id": user["user_id"], "date": today})
    daily_count = usage.get("count", 0) if usage else 0
    
    if daily_count >= 2:
        raise HTTPException(status_code=429, detail={"message": "Limite quotidienne IA atteinte (2/jour). Revenez demain !", "used": daily_count, "limit": 2})
    
    # Calculate phase
    phase_info = calculate_bariatric_phase(profile.get("bariatric_surgery_date"))
    surgery_type = profile.get("bariatric_surgery")
    surgery_name = "bypass gastrique" if surgery_type == "bypass" else "sleeve gastrectomie"
    
    # Check cache first
    cache_key = f"bariatric_{surgery_type}_phase{phase_info.get('phase')}_{question[:50]}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
    
    cached = await db.ai_cache.find_one({"prompt_hash": cache_hash})
    if cached:
        await db.ai_cache.update_one({"prompt_hash": cache_hash}, {"$inc": {"hits": 1}})
        return {"response": cached["response"], "from_cache": True, "phase": phase_info}
    
    # Build strict system prompt
    system_prompt = f"""Tu es un coach de soutien pour patients ayant subi une {surgery_name}.

RÈGLES STRICTES À RESPECTER ABSOLUMENT :
1. Tu n'es PAS un professionnel de santé
2. Tu ne donnes JAMAIS d'avis médical
3. Tu ne modifies JAMAIS les traitements ou prescriptions
4. Tu ne fais JAMAIS de diagnostic
5. Pour toute question médicale, tu renvoies vers l'équipe soignante

CONTEXTE DU PATIENT :
- Type d'opération : {surgery_name}
- Phase actuelle : {phase_info.get('phase_name', 'Non définie')} ({phase_info.get('days_since_surgery', 0)} jours post-op)
- Texture autorisée : {phase_info.get('texture', 'solide adapté')}
- Suppléments prescrits : {', '.join(profile.get('bariatric_supplements', [])) or 'Non renseignés'}
- Intolérances : {', '.join(profile.get('bariatric_intolerances', [])) or 'Aucune'}
- Allergies : {', '.join(profile.get('allergies', [])) or 'Aucune'}

TU PEUX :
- Donner des conseils nutritionnels généraux adaptés à la phase
- Proposer des idées de repas adaptées à la texture autorisée
- Encourager et motiver
- Expliquer des phénomènes courants (dumping, plateau, etc.)
- Rappeler l'importance des suppléments

TU DOIS TOUJOURS :
- Commencer par ce disclaimer : "⚕️ Je ne suis pas un professionnel de santé. Mes conseils sont généraux et ne remplacent pas l'avis de votre équipe médicale."
- Rester bienveillant et encourageant
- Adapter tes conseils à la phase du patient
- Répondre en français

QUESTION DU PATIENT : {question}"""

    try:
        llm = LlmChat(api_key=os.environ.get('EMERGENT_API_KEY'))
        response = await llm.send_async(
            model="gpt-4o",
            messages=[UserMessage(text=system_prompt)]
        )
        
        # Log AI usage
        await db.ai_usage_logs.update_one(
            {"user_id": user["user_id"], "date": today},
            {"$inc": {"count": 1}, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        
        # Cache response
        await db.ai_cache.insert_one({
            "prompt_hash": cache_hash,
            "response": response.text,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "hits": 0
        })
        
        return {"response": response.text, "from_cache": False, "phase": phase_info}
        
    except Exception as e:
        logger.error(f"Bariatric coach error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la génération de la réponse")

@api_router.get("/bariatric/check-disclaimer")
async def check_bariatric_disclaimer(user: dict = Depends(get_current_user)):
    """Check if user has seen the bariatric disclaimer"""
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return {"seen_disclaimer": profile.get("bariatric_disclaimer_seen", False) if profile else False}

@api_router.post("/bariatric/accept-disclaimer")
async def accept_bariatric_disclaimer(user: dict = Depends(get_current_user)):
    """Mark bariatric disclaimer as seen"""
    await db.user_profiles.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"bariatric_disclaimer_seen": True}}
    )
    return {"message": "Disclaimer accepted"}

# ==================== FOOD & NUTRITION ENDPOINTS ====================

@api_router.post("/food/analyze")
async def analyze_food(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Analyze food image using AI vision with user profile context"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    import json
    
    # ===== AI LIMIT CHECK =====
    await enforce_ai_limit(user["user_id"], "/food/analyze")
    
    # Get user profile for personalized analysis
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    contents = await file.read()
    image_base64 = base64.b64encode(contents).decode()
    
    # For image analysis, we can't cache effectively (images are unique)
    # So we just count the usage but don't use cache
    
    # Build context from user profile
    health_context = ""
    if profile:
        conditions = profile.get("health_conditions", [])
        allergies = profile.get("allergies", [])
        dislikes = profile.get("food_dislikes", [])
        if conditions:
            health_context += f"\nUser health conditions: {', '.join(conditions)}"
        if allergies:
            health_context += f"\nUser allergies: {', '.join(allergies)}"
        if dislikes:
            health_context += f"\nUser dislikes: {', '.join(dislikes)}"
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"food_analysis_{uuid.uuid4().hex[:8]}",
            system_message=f"""You are an expert nutritionist AI that analyzes food images with high precision.

IMPORTANT INSTRUCTIONS:
1. Carefully examine the image to identify the EXACT food/dish shown
2. If you see multiple items, list them all
3. Provide ACCURATE nutritional estimates based on typical serving sizes
4. Be specific about the food name (e.g., "Grilled Salmon with Vegetables" not just "Food")
5. Consider cooking methods visible (fried, grilled, steamed, etc.)
6. Estimate portion size from the image context

{health_context}

You MUST respond with a valid JSON object containing these exact fields:
{{
    "food_name": "Specific name of the dish/food in French",
    "food_name_en": "English name",
    "calories": <number between 50-1500>,
    "protein": <number in grams>,
    "carbs": <number in grams>,
    "fat": <number in grams>,
    "fiber": <number in grams>,
    "sugar": <number in grams>,
    "sodium": <number in mg>,
    "nutri_score": "<A, B, C, D, or E>",
    "serving_size": "estimated portion size",
    "health_tips": ["tip1", "tip2"],
    "ingredients_detected": ["ingredient1", "ingredient2"],
    "is_healthy": <true or false>,
    "warnings": ["warning if applicable for user's health conditions"]
}}

Nutri-Score guidelines:
- A: Very healthy (vegetables, fruits, lean proteins)
- B: Good choice (whole grains, fish)
- C: Moderate (some processed foods)
- D: Less healthy (fried foods, sugary items)
- E: Unhealthy (fast food, high sugar/fat)"""
        ).with_model("openai", "gpt-4o")
        
        # ImageContent is a special FileContent with content_type='image'
        image_content = ImageContent(image_base64=image_base64)
        user_message = UserMessage(
            text="Analyze this food image carefully. Identify exactly what food/dish is shown and provide accurate nutritional information. Be specific and precise. Respond ONLY with valid JSON.",
            file_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        logger.info(f"AI Response: {response[:500]}")
        
        # Parse JSON from response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            result = json.loads(response[json_start:json_end])
            # Ensure all required fields exist
            result.setdefault("food_name", "Aliment détecté")
            result.setdefault("calories", 200)
            result.setdefault("protein", 10)
            result.setdefault("carbs", 25)
            result.setdefault("fat", 8)
            result.setdefault("fiber", 3)
            result.setdefault("sugar", 5)
            result.setdefault("sodium", 300)
            result.setdefault("nutri_score", "C")
            result.setdefault("serving_size", "1 portion")
            result.setdefault("health_tips", [])
            result.setdefault("ingredients_detected", [])
            result.setdefault("is_healthy", True)
            result.setdefault("warnings", [])
            
            # ===== INCREMENT AI USAGE AFTER SUCCESSFUL CALL =====
            await increment_ai_usage(user["user_id"], "/food/analyze")
            
            # ===== SAVE TO SCAN HISTORY =====
            # Determine category based on food name
            food_lower = result.get("food_name", "").lower()
            category = "Autre"
            if any(w in food_lower for w in ["salade", "légume", "carotte", "tomate", "courgette", "brocoli", "épinard"]):
                category = "Légumes"
            elif any(w in food_lower for w in ["fruit", "pomme", "banane", "orange", "fraise", "raisin", "kiwi"]):
                category = "Fruits"
            elif any(w in food_lower for w in ["viande", "poulet", "bœuf", "porc", "steak", "jambon"]):
                category = "Viandes"
            elif any(w in food_lower for w in ["poisson", "saumon", "thon", "crevette", "cabillaud"]):
                category = "Poissons"
            elif any(w in food_lower for w in ["pain", "pâtes", "riz", "céréale", "baguette", "sandwich"]):
                category = "Féculents"
            elif any(w in food_lower for w in ["yaourt", "fromage", "lait", "crème"]):
                category = "Produits laitiers"
            elif any(w in food_lower for w in ["gâteau", "chocolat", "bonbon", "biscuit", "glace", "dessert"]):
                category = "Desserts"
            elif any(w in food_lower for w in ["boisson", "jus", "eau", "café", "thé", "soda"]):
                category = "Boissons"
            elif any(w in food_lower for w in ["pizza", "burger", "frites", "kebab", "tacos"]):
                category = "Fast-food"
            elif any(w in food_lower for w in ["soupe", "potage", "bouillon"]):
                category = "Soupes"
            elif any(w in food_lower for w in ["œuf", "omelette"]):
                category = "Œufs"
            elif any(w in food_lower for w in ["plat", "repas"]):
                category = "Plats préparés"
            
            scan_entry = {
                "scan_id": f"scan_{uuid.uuid4().hex[:12]}",
                "user_id": user["user_id"],
                "food_name": result.get("food_name"),
                "category": category,
                "calories": result.get("calories"),
                "protein": result.get("protein"),
                "carbs": result.get("carbs"),
                "fat": result.get("fat"),
                "fiber": result.get("fiber"),
                "sugar": result.get("sugar"),
                "sodium": result.get("sodium"),
                "nutri_score": result.get("nutri_score"),
                "serving_size": result.get("serving_size"),
                "health_tips": result.get("health_tips", []),
                "warnings": result.get("warnings", []),
                "is_healthy": result.get("is_healthy", True),
                "image_data": image_base64 if image_base64 else None,  # Store full image
                "scanned_at": datetime.now(timezone.utc).isoformat()
            }
            await db.scan_history.insert_one(scan_entry)
            result["scan_id"] = scan_entry["scan_id"]
            result["category"] = category
        else:
            raise ValueError("No JSON found in response")
            
    except HTTPException:
        raise  # Re-raise HTTP exceptions (like 429 limit exceeded)
    except Exception as e:
        logger.error(f"AI food analysis error: {str(e)}")
        result = {
            "food_name": "Analyse en cours...",
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0,
            "sugar": 0,
            "sodium": 0,
            "nutri_score": "?",
            "serving_size": "Non déterminé",
            "health_tips": ["Veuillez réessayer avec une photo plus nette", "Assurez-vous que l'aliment est bien visible et éclairé"],
            "ingredients_detected": [],
            "is_healthy": True,
            "warnings": [],
            "error": str(e)
        }
    
    return result

# --- Scan History Endpoints ---
@api_router.get("/food/scan-history")
async def get_scan_history(user: dict = Depends(get_current_user)):
    """Get user's scan history grouped by category, ordered by date"""
    scans = await db.scan_history.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("scanned_at", -1).to_list(200)
    
    # Group by category
    categories = {}
    for scan in scans:
        cat = scan.get("category", "Autre")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(scan)
    
    return {
        "scans": scans,
        "by_category": categories,
        "total": len(scans)
    }

@api_router.get("/food/scan/{scan_id}")
async def get_scan_detail(scan_id: str, user: dict = Depends(get_current_user)):
    """Get details of a specific scan"""
    scan = await db.scan_history.find_one(
        {"scan_id": scan_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@api_router.delete("/food/scan/{scan_id}")
async def delete_scan(scan_id: str, user: dict = Depends(get_current_user)):
    """Delete a scan from history"""
    result = await db.scan_history.delete_one(
        {"scan_id": scan_id, "user_id": user["user_id"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"message": "Scan deleted"}

@api_router.post("/food/recommend-alternatives")
async def recommend_alternatives(entry: dict, user: dict = Depends(get_current_user)):
    """Get AI recommendations for healthier alternatives - IN FRENCH"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json
    
    # ===== AI LIMIT CHECK =====
    await enforce_ai_limit(user["user_id"], "/food/recommend-alternatives")
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    user_context_hash = get_user_context_hash(profile)
    
    # Build the prompt for cache lookup
    prompt_for_cache = f"alternatives for {entry.get('food_name')} {entry.get('nutri_score', '')}"
    
    # ===== CHECK CACHE FIRST =====
    cached = await get_cached_ai_response(prompt_for_cache, "recommend-alternatives", user_context_hash)
    if cached:
        return cached
    
    health_context = ""
    if profile:
        conditions = profile.get("health_conditions", [])
        preferences = profile.get("dietary_preferences", [])
        likes = profile.get("food_likes", [])
        dislikes = profile.get("food_dislikes", [])
        if conditions:
            health_context += f"Conditions de santé: {', '.join(conditions)}. "
        if preferences:
            health_context += f"Préférences alimentaires: {', '.join(preferences)}. "
        if likes:
            health_context += f"Aliments aimés: {', '.join(likes)}. "
        if dislikes:
            health_context += f"Aliments détestés (À ÉVITER): {', '.join(dislikes)}. "
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"food_recommend_{uuid.uuid4().hex[:8]}",
            system_message=f"""Tu es un expert en nutrition français. Suggère des alternatives plus saines.
IMPORTANT: Réponds UNIQUEMENT en français.
{health_context}

Réponds en JSON:
{{
    "analysis": "Analyse brève de pourquoi cet aliment n'est pas idéal",
    "alternatives": [
        {{"name": "Alternative 1", "calories": number, "benefit": "Pourquoi c'est mieux"}},
        {{"name": "Alternative 2", "calories": number, "benefit": "Pourquoi c'est mieux"}},
        {{"name": "Alternative 3", "calories": number, "benefit": "Pourquoi c'est mieux"}}
    ],
    "tips": ["Conseil pour manger plus sainement"]
}}"""
        ).with_model("openai", "gpt-4o")
        
        prompt = f"""L'utilisateur a mangé: {entry.get('food_name')}
Infos nutritionnelles: {entry.get('calories')} calories, {entry.get('protein')}g protéines, {entry.get('carbs')}g glucides, {entry.get('fat')}g lipides
Nutri-Score: {entry.get('nutri_score', 'Inconnu')}

Suggère 3 alternatives plus saines que l'utilisateur pourrait apprécier. RÉPONDS EN FRANÇAIS."""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        result = json.loads(response[json_start:json_end])
        
        # ===== CACHE THE RESULT & INCREMENT USAGE =====
        await store_cached_ai_response(prompt_for_cache, result, "recommend-alternatives", user_context_hash)
        await increment_ai_usage(user["user_id"], "/food/recommend-alternatives")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        result = {
            "analysis": "Analyse indisponible",
            "alternatives": [],
            "tips": ["Privilégiez les aliments frais et non transformés"]
        }
    
    return result

@api_router.post("/food/log")
async def log_food(entry: FoodLogEntry, user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    
    log_doc = {
        "entry_id": f"food_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        **entry.model_dump(),
        "date": date_str,
        "time": time_str,
        "logged_at": now.isoformat()
    }
    await db.food_logs.insert_one(log_doc)
    
    # Also add to agenda for tracking
    meal_type_labels = {
        "breakfast": "Petit-déjeuner",
        "lunch": "Déjeuner",
        "dinner": "Dîner",
        "snack": "Collation"
    }
    meal_label = meal_type_labels.get(entry.meal_type, "Repas")
    
    agenda_note = {
        "note_id": f"meal_{log_doc['entry_id']}",
        "user_id": user["user_id"],
        "date": date_str,
        "content": f"🍽️ {meal_label} à {time_str}: {entry.food_name} ({entry.calories} kcal)",
        "type": "meal_log",
        "food_entry_id": log_doc["entry_id"],
        "created_at": now.isoformat()
    }
    
    await db.agenda_notes.insert_one(agenda_note)
    
    return {
        "message": "Food logged", 
        "entry_id": log_doc["entry_id"],
        "date": date_str,
        "time": time_str
    }

@api_router.put("/food/log/{entry_id}/note")
async def update_food_note(entry_id: str, data: dict, user: dict = Depends(get_current_user)):
    """Add or update note for a food entry"""
    result = await db.food_logs.update_one(
        {"entry_id": entry_id, "user_id": user["user_id"]},
        {"$set": {"note": data.get("note", "")}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Note updated"}

@api_router.get("/food/diary")
async def get_food_diary(month: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get food diary grouped by date"""
    if not month:
        month = datetime.now(timezone.utc).strftime("%Y-%m")
    
    logs = await db.food_logs.find(
        {"user_id": user["user_id"], "date": {"$regex": f"^{month}"}},
        {"_id": 0}
    ).sort("logged_at", -1).to_list(500)
    
    # Group by date
    diary = {}
    for log in logs:
        date = log.get("date", log.get("logged_at", "")[:10])
        if date not in diary:
            diary[date] = {
                "date": date,
                "meals": [],
                "total_calories": 0,
                "total_protein": 0,
                "total_carbs": 0,
                "total_fat": 0
            }
        diary[date]["meals"].append(log)
        diary[date]["total_calories"] += log.get("calories", 0) * log.get("quantity", 1)
        diary[date]["total_protein"] += log.get("protein", 0) * log.get("quantity", 1)
        diary[date]["total_carbs"] += log.get("carbs", 0) * log.get("quantity", 1)
        diary[date]["total_fat"] += log.get("fat", 0) * log.get("quantity", 1)
    
    return sorted(diary.values(), key=lambda x: x["date"], reverse=True)

@api_router.get("/food/logs")
async def get_food_logs(date: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"user_id": user["user_id"]}
    if date:
        query["logged_at"] = {"$regex": f"^{date}"}
    
    logs = await db.food_logs.find(query, {"_id": 0}).sort("logged_at", -1).to_list(100)
    return logs

@api_router.get("/food/daily-summary")
async def get_daily_summary(date: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get daily nutrition summary - resets at midnight each day"""
    if not date:
        # Use UTC date for consistency
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Query by date field (more reliable than logged_at prefix)
    logs = await db.food_logs.find(
        {"user_id": user["user_id"], "date": date},
        {"_id": 0}
    ).to_list(100)
    
    # Fallback: also check logged_at for backward compatibility
    if not logs:
        logs = await db.food_logs.find(
            {"user_id": user["user_id"], "logged_at": {"$regex": f"^{date}"}},
            {"_id": 0}
        ).to_list(100)
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    total_calories = sum(log.get("calories", 0) * log.get("quantity", 1) for log in logs)
    total_protein = sum(log.get("protein", 0) * log.get("quantity", 1) for log in logs)
    total_carbs = sum(log.get("carbs", 0) * log.get("quantity", 1) for log in logs)
    total_fat = sum(log.get("fat", 0) * log.get("quantity", 1) for log in logs)
    
    targets = {
        "calories": profile.get("daily_calorie_target", 2000) if profile else 2000,
        "protein": profile.get("daily_protein_target", 100) if profile else 100,
        "carbs": profile.get("daily_carbs_target", 250) if profile else 250,
        "fat": profile.get("daily_fat_target", 65) if profile else 65
    }
    
    return {
        "date": date,
        "consumed": {
            "calories": round(total_calories),
            "protein": round(total_protein),
            "carbs": round(total_carbs),
            "fat": round(total_fat)
        },
        "targets": targets,
        "remaining": {
            "calories": max(0, targets["calories"] - total_calories),
            "protein": max(0, targets["protein"] - total_protein),
            "carbs": max(0, targets["carbs"] - total_carbs),
            "fat": max(0, targets["fat"] - total_fat)
        },
        "meals_logged": len(logs)
    }

@api_router.delete("/food/log/{entry_id}")
async def delete_food_log(entry_id: str, user: dict = Depends(get_current_user)):
    result = await db.food_logs.delete_one({"entry_id": entry_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry deleted"}

# ==================== AGENDA NOTES ENDPOINTS ====================

@api_router.post("/agenda/notes")
async def create_agenda_note(data: dict, user: dict = Depends(get_current_user)):
    """Create or update a note for a specific date"""
    note_doc = {
        "note_id": f"note_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "date": data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "content": data.get("content", ""),
        "type": data.get("type", "general"),  # general, meal_plan, reminder
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Upsert - update if exists for same date, else insert
    await db.agenda_notes.update_one(
        {"user_id": user["user_id"], "date": note_doc["date"], "type": note_doc["type"]},
        {"$set": note_doc},
        upsert=True
    )
    
    return {"message": "Note saved", "note": note_doc}

@api_router.get("/agenda/notes")
async def get_agenda_notes(month: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get all notes for a month"""
    if not month:
        month = datetime.now(timezone.utc).strftime("%Y-%m")
    
    notes = await db.agenda_notes.find(
        {"user_id": user["user_id"], "date": {"$regex": f"^{month}"}},
        {"_id": 0}
    ).to_list(100)
    
    return notes

@api_router.delete("/agenda/notes/{note_id}")
async def delete_agenda_note(note_id: str, user: dict = Depends(get_current_user)):
    result = await db.agenda_notes.delete_one({"note_id": note_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted"}

# ==================== MEAL PLANS ENDPOINTS ====================

@api_router.post("/meals/generate")
async def generate_meal_plan(data: dict = {}, user: dict = Depends(get_current_user)):
    """Generate AI-powered meal plan based on user profile"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json
    
    # ===== AI LIMIT CHECK =====
    await enforce_ai_limit(user["user_id"], "/meals/generate")
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    
    # Get plan type: daily or weekly
    plan_type = data.get("type", "weekly")
    user_context_hash = get_user_context_hash(profile)
    
    # ===== CHECK CACHE FIRST =====
    prompt_for_cache = f"meal plan {plan_type} goal:{profile.get('goal', '')}"
    cached = await get_cached_ai_response(prompt_for_cache, "meals-generate", user_context_hash)
    if cached:
        # Still save to user's plans
        plan_doc = {
            "plan_id": f"plan_{uuid.uuid4().hex[:8]}",
            "user_id": user["user_id"],
            "type": plan_type,
            "meal_plan": cached,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "from_cache": True
        }
        await db.meal_plans.insert_one(plan_doc)
        return {"plan_id": plan_doc["plan_id"], "type": plan_type, "meal_plan": cached, "from_cache": True}
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"meal_plan_{uuid.uuid4().hex[:8]}",
            system_message=f"""Tu es un nutritionniste professionnel français. Crée des plans repas personnalisés.
IMPORTANT: Réponds UNIQUEMENT en français et en JSON valide. Tous les noms de plats, jours et conseils doivent être en FRANÇAIS.

Contexte utilisateur:
- Objectif calorique: {profile.get('daily_calorie_target', 2000)} kcal/jour
- Objectif: {profile.get('goal', 'maintain')}
- Préférences alimentaires: {', '.join(profile.get('dietary_preferences', [])) or 'Aucune'}
- Allergies: {', '.join(profile.get('allergies', [])) or 'Aucune'}
- Aliments aimés: {', '.join(profile.get('food_likes', [])) or 'Variés'}
- Aliments détestés (À ÉVITER ABSOLUMENT): {', '.join(profile.get('food_dislikes', [])) or 'Aucun'}
- Conditions de santé: {', '.join(profile.get('health_conditions', [])) or 'Aucune'}
- Budget: {profile.get('budget', 'moyen')}
- Temps disponible: {profile.get('time_constraint', 'modéré')}
- Compétences cuisine: {profile.get('cooking_skill', 'intermédiaire')}

Règles:
1. Ne JAMAIS inclure les aliments détestés
2. Favoriser les aliments aimés
3. Respecter les allergies
4. Adapter aux conditions de santé (moins de sucre pour diabète, etc.)
5. Proposer des recettes simples et économiques
6. Le petit-déjeuner doit être énergisant
7. Le déjeuner doit être équilibré
8. Le dîner doit être plus léger
9. TOUS les textes en FRANÇAIS"""
        ).with_model("openai", "gpt-4o")
        
        if plan_type == "daily":
            prompt = """Crée un plan repas pour UNE journée avec 3 repas. TOUT EN FRANÇAIS.
Réponds UNIQUEMENT avec ce JSON (noms de plats en français):
{
    "date": "aujourd'hui",
    "meals": {
        "breakfast": {"name": "Nom du plat en français", "calories": number, "protein": number, "carbs": number, "fat": number, "recipe": "instructions courtes en français", "prep_time": "10 min", "ingredients": ["ingrédient 1", "ingrédient 2"]},
        "lunch": {"name": "Nom du plat en français", "calories": number, "protein": number, "carbs": number, "fat": number, "recipe": "instructions courtes en français", "prep_time": "20 min", "ingredients": ["ingrédient 1", "ingrédient 2"]},
        "dinner": {"name": "Nom du plat en français", "calories": number, "protein": number, "carbs": number, "fat": number, "recipe": "instructions courtes en français", "prep_time": "15 min", "ingredients": ["ingrédient 1", "ingrédient 2"]}
    },
    "total_calories": number,
    "shopping_list": ["ingrédient 1 en français", "ingrédient 2 en français"],
    "tips": ["conseil en français"]
}"""
        else:
            prompt = """Crée un plan repas pour 7 jours avec 3 repas par jour. TOUT EN FRANÇAIS.
Les jours doivent être: Lundi, Mardi, Mercredi, Jeudi, Vendredi, Samedi, Dimanche.
Réponds UNIQUEMENT avec ce JSON (tous les textes en français):
{
    "days": [
        {
            "day": "Lundi",
            "meals": {
                "breakfast": {"name": "Nom en français", "calories": number, "protein": number, "carbs": number, "fat": number, "recipe": "instructions en français", "prep_time": "10 min", "ingredients": ["ingrédient"]},
                "lunch": {"name": "Nom en français", "calories": number, "protein": number, "carbs": number, "fat": number, "recipe": "instructions en français", "prep_time": "20 min", "ingredients": ["ingrédient"]},
                "dinner": {"name": "Nom en français", "calories": number, "protein": number, "carbs": number, "fat": number, "recipe": "instructions en français", "prep_time": "15 min", "ingredients": ["ingrédient"]}
            },
            "total_calories": number
        }
    ],
    "shopping_list": ["ingrédient en français"],
    "tips": ["conseil en français"],
    "estimated_weekly_cost": "XX€"
}"""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        meal_plan = json.loads(response[json_start:json_end])
        
        # ===== CACHE THE RESULT & INCREMENT USAGE =====
        await store_cached_ai_response(prompt_for_cache, meal_plan, "meals-generate", user_context_hash)
        await increment_ai_usage(user["user_id"], "/meals/generate")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI meal plan error: {e}")
        # Return a fallback meal plan in French
        if plan_type == "daily":
            meal_plan = {
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "meals": {
                    "breakfast": {"name": "Porridge aux fruits rouges", "calories": 350, "protein": 12, "carbs": 55, "fat": 8, "recipe": "Cuire les flocons d'avoine avec du lait, ajouter les fruits frais", "prep_time": "10 min", "ingredients": ["Flocons d'avoine", "Lait", "Fruits rouges", "Miel"]},
                    "lunch": {"name": "Salade de quinoa au poulet", "calories": 500, "protein": 35, "carbs": 40, "fat": 18, "recipe": "Mélanger le quinoa cuit avec le poulet grillé et les légumes", "prep_time": "20 min", "ingredients": ["Quinoa", "Blanc de poulet", "Tomates", "Concombre", "Huile d'olive"]},
                    "dinner": {"name": "Soupe de légumes et pain complet", "calories": 400, "protein": 15, "carbs": 50, "fat": 12, "recipe": "Faire revenir les légumes et mixer avec du bouillon", "prep_time": "15 min", "ingredients": ["Carottes", "Poireaux", "Pommes de terre", "Bouillon", "Pain complet"]}
                },
                "total_calories": 1250,
                "shopping_list": ["Flocons d'avoine", "Fruits rouges", "Quinoa", "Poulet", "Légumes frais", "Pain complet"],
                "tips": ["Buvez 2L d'eau par jour"]
            }
        else:
            days_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
            meal_plan = {
                "days": [
                    {
                        "day": day,
                        "meals": {
                            "breakfast": {"name": "Petit-déjeuner équilibré", "calories": 400, "protein": 20, "carbs": 50, "fat": 15, "recipe": "Préparation simple et rapide", "prep_time": "10 min", "ingredients": ["Céréales", "Lait", "Fruits"]},
                            "lunch": {"name": "Déjeuner complet", "calories": 600, "protein": 35, "carbs": 60, "fat": 20, "recipe": "Repas équilibré avec protéines et légumes", "prep_time": "20 min", "ingredients": ["Protéine au choix", "Légumes", "Féculents"]},
                            "dinner": {"name": "Dîner léger", "calories": 500, "protein": 30, "carbs": 45, "fat": 18, "recipe": "Préparation facile et digeste", "prep_time": "15 min", "ingredients": ["Poisson ou volaille", "Légumes verts", "Riz"]}
                        },
                        "total_calories": 1500
                    } for day in days_fr
                ],
                "shopping_list": ["Fruits frais", "Légumes variés", "Protéines maigres", "Céréales complètes", "Produits laitiers"],
                "tips": ["Buvez 2L d'eau par jour", "Mangez lentement", "Préparez vos repas à l'avance"],
                "estimated_weekly_cost": "50-70€"
            }
    
    # Save meal plan
    plan_doc = {
        "plan_id": f"plan_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "type": data.get("type", "weekly"),
        "meal_plan": meal_plan,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.meal_plans.insert_one(plan_doc)
    
    # Add images to meals based on meal type and keywords
    meal_images = {
        "breakfast": [
            "https://images.unsplash.com/photo-1517673400267-0251440c45dc?w=400",  # porridge
            "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=400",  # eggs
            "https://images.unsplash.com/photo-1590301157890-4810ed352733?w=400",  # smoothie bowl
            "https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=400",  # avocado toast
            "https://images.unsplash.com/photo-1504754524776-8f4f37790ca0?w=400",  # breakfast
        ],
        "lunch": [
            "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",  # salad
            "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=400",  # wrap
            "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400",  # bowl
            "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400",  # burger
            "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400",  # healthy
        ],
        "dinner": [
            "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400",  # salmon
            "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400",  # soup
            "https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400",  # chicken
            "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=400",  # stir fry
            "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400",  # pizza
        ],
    }
    
    import random
    
    # Add images to the meal plan
    if "meals" in meal_plan:
        for meal_type, meal in meal_plan["meals"].items():
            if meal and meal_type in meal_images:
                meal["image"] = random.choice(meal_images[meal_type])
    elif "days" in meal_plan:
        for day in meal_plan["days"]:
            for meal_type, meal in day.get("meals", {}).items():
                if meal and meal_type in meal_images:
                    meal["image"] = random.choice(meal_images[meal_type])
    
    return {"plan_id": plan_doc["plan_id"], "type": plan_doc["type"], "meal_plan": meal_plan}

@api_router.get("/meals/plans")
async def get_meal_plans(user: dict = Depends(get_current_user)):
    plans = await db.meal_plans.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    return plans

# ==================== AI RECIPES GENERATION ====================

@api_router.post("/recipes/generate")
async def generate_recipes(data: dict = {}, user: dict = Depends(get_current_user)):
    """Generate AI-powered simple and affordable recipes"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json
    
    # ===== AI LIMIT CHECK =====
    await enforce_ai_limit(user["user_id"], "/recipes/generate")
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    
    count = data.get("count", 10)
    category = data.get("category", "all")  # all, breakfast, lunch, dinner, snack
    user_context_hash = get_user_context_hash(profile)
    
    # ===== CHECK CACHE FIRST =====
    prompt_for_cache = f"recipes {count} {category} goal:{profile.get('goal', '')}"
    cached = await get_cached_ai_response(prompt_for_cache, "recipes-generate", user_context_hash)
    if cached:
        return cached
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"recipes_{uuid.uuid4().hex[:8]}",
            system_message=f"""Tu es un chef cuisinier français spécialisé dans les recettes simples, économiques et saines.
IMPORTANT: Réponds UNIQUEMENT en français et en JSON valide.

Contexte utilisateur:
- Objectif calorique: {profile.get('daily_calorie_target', 2000)} kcal/jour
- Objectif: {profile.get('goal', 'maintain')}
- Préférences: {', '.join(profile.get('dietary_preferences', [])) or 'Aucune'}
- Allergies (À ÉVITER): {', '.join(profile.get('allergies', [])) or 'Aucune'}
- Aliments aimés: {', '.join(profile.get('food_likes', [])) or 'Variés'}
- Aliments détestés (À ÉVITER): {', '.join(profile.get('food_dislikes', [])) or 'Aucun'}
- Budget: {profile.get('budget', 'moyen')}
- Compétences: {profile.get('cooking_skill', 'intermédiaire')}

Règles:
1. Recettes SIMPLES (max 8 étapes)
2. Ingrédients ÉCONOMIQUES et faciles à trouver
3. Temps de préparation < 30 min
4. Ne jamais utiliser les aliments détestés ou allergènes
5. Favoriser les aliments aimés"""
        ).with_model("openai", "gpt-4o")
        
        category_filter = f"pour {category}" if category != "all" else "variées (petit-déjeuner, déjeuner, dîner, collation)"
        
        prompt = f"""Génère {count} recettes exclusives, simples et économiques {category_filter}.

Réponds UNIQUEMENT avec ce JSON:
{{
    "recipes": [
        {{
            "id": "recipe_1",
            "name": "Nom de la recette",
            "category": "breakfast|lunch|dinner|snack",
            "calories": 350,
            "protein": 20,
            "carbs": 40,
            "fat": 12,
            "prep_time": "15 min",
            "cook_time": "10 min",
            "servings": 2,
            "difficulty": "facile",
            "cost": "économique",
            "ingredients": [
                {{"item": "Ingrédient 1", "quantity": "200g"}},
                {{"item": "Ingrédient 2", "quantity": "1 pièce"}}
            ],
            "steps": [
                "Étape 1: ...",
                "Étape 2: ..."
            ],
            "tips": "Conseil pour cette recette",
            "nutri_score": "A"
        }}
    ]
}}"""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        result = json.loads(response[json_start:json_end])
        
        # ===== CACHE THE RESULT & INCREMENT USAGE =====
        await store_cached_ai_response(prompt_for_cache, result, "recipes-generate", user_context_hash)
        await increment_ai_usage(user["user_id"], "/recipes/generate")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI recipes error: {e}")
        result = {
            "recipes": [
                {
                    "id": f"recipe_{i+1}",
                    "name": f"Recette simple {i+1}",
                    "category": ["breakfast", "lunch", "dinner", "snack"][i % 4],
                    "calories": 350 + (i * 50),
                    "protein": 15 + (i * 2),
                    "carbs": 40,
                    "fat": 12,
                    "prep_time": "15 min",
                    "cook_time": "10 min",
                    "servings": 2,
                    "difficulty": "facile",
                    "cost": "économique",
                    "ingredients": [{"item": "Ingrédient", "quantity": "200g"}],
                    "steps": ["Préparer les ingrédients", "Cuisiner", "Servir"],
                    "tips": "Recette rapide et économique",
                    "nutri_score": "B"
                } for i in range(min(count, 5))
            ]
        }
    
    return result

# ==================== AI RECIPE SEARCH ====================

@api_router.post("/recipes/search")
async def search_recipe_by_ai(data: dict, user: dict = Depends(get_current_user)):
    """Search for a specific recipe using AI based on user query"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json
    
    query = data.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    # ===== AI LIMIT CHECK =====
    await enforce_ai_limit(user["user_id"], "/recipes/search")
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    user_context_hash = get_user_context_hash(profile)
    
    # ===== CHECK CACHE FIRST (using the query as prompt) =====
    cached = await get_cached_ai_response(query, "recipes-search", user_context_hash)
    if cached:
        return {"recipe": cached, "query": query, "from_cache": True}
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"recipe_search_{uuid.uuid4().hex[:8]}",
            system_message=f"""Tu es un chef cuisinier français expert qui crée des recettes personnalisées.
IMPORTANT: Réponds UNIQUEMENT en français et en JSON valide.

Contexte utilisateur:
- Objectif calorique: {profile.get('daily_calorie_target', 2000) if profile else 2000} kcal/jour
- Objectif: {profile.get('goal', 'maintain') if profile else 'maintain'}
- Préférences: {', '.join(profile.get('dietary_preferences', [])) if profile else 'Aucune'}
- Allergies (À ÉVITER ABSOLUMENT): {', '.join(profile.get('allergies', [])) if profile else 'Aucune'}
- Aliments aimés: {', '.join(profile.get('food_likes', [])) if profile else 'Variés'}
- Aliments détestés (À ÉVITER): {', '.join(profile.get('food_dislikes', [])) if profile else 'Aucun'}

Règles:
1. Crée une recette qui correspond EXACTEMENT à la demande de l'utilisateur
2. Respecte les contraintes mentionnées (temps, ingrédients, santé, etc.)
3. Ne jamais utiliser les allergènes ou aliments détestés
4. Recette détaillée avec étapes claires"""
        ).with_model("openai", "gpt-4o")
        
        prompt = f"""L'utilisateur recherche: "{query}"

Crée UNE recette qui correspond parfaitement à cette demande.

Réponds UNIQUEMENT avec ce JSON (pas de texte avant ou après):
{{
    "name": "Nom de la recette en français",
    "category": "breakfast|lunch|dinner|snack",
    "calories": 400,
    "protein": 25,
    "carbs": 35,
    "fat": 15,
    "prep_time": "20 min",
    "cook_time": "15 min",
    "servings": 2,
    "difficulty": "facile|moyen|difficile",
    "cost": "économique|moyen|élevé",
    "nutri_score": "A|B|C",
    "ingredients": [
        {{"item": "Ingrédient 1", "quantity": "200g"}},
        {{"item": "Ingrédient 2", "quantity": "1 pièce"}}
    ],
    "steps": [
        "Étape 1: Description claire de l'étape",
        "Étape 2: Description claire de l'étape"
    ],
    "tips": "Un conseil utile pour cette recette"
}}"""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        recipe = json.loads(response[json_start:json_end])
        
        # ===== CACHE THE RESULT & INCREMENT USAGE =====
        await store_cached_ai_response(query, recipe, "recipes-search", user_context_hash)
        await increment_ai_usage(user["user_id"], "/recipes/search")
        
        return {"recipe": recipe, "query": query}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI recipe search error: {e}")
        # Return a fallback recipe
        return {
            "recipe": {
                "name": "Recette personnalisée",
                "category": "lunch",
                "calories": 400,
                "protein": 25,
                "carbs": 40,
                "fat": 15,
                "prep_time": "25 min",
                "cook_time": "15 min",
                "servings": 2,
                "difficulty": "facile",
                "cost": "économique",
                "nutri_score": "B",
                "ingredients": [
                    {"item": "Ingrédient principal", "quantity": "200g"},
                    {"item": "Légumes", "quantity": "150g"},
                    {"item": "Assaisonnement", "quantity": "1 c.à.s"}
                ],
                "steps": [
                    "Étape 1: Préparer les ingrédients",
                    "Étape 2: Cuisiner selon les instructions",
                    "Étape 3: Servir chaud"
                ],
                "tips": "Adaptez les quantités selon vos goûts"
            },
            "query": query
        }

@api_router.post("/recipes/favorites")
async def add_favorite_recipe(data: dict, user: dict = Depends(get_current_user)):
    """Add a recipe to favorites"""
    recipe = data.get("recipe")
    if not recipe:
        raise HTTPException(status_code=400, detail="Recipe data required")
    
    fav_doc = {
        "favorite_id": f"fav_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "recipe": recipe,
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Check if already in favorites
    existing = await db.favorite_recipes.find_one({
        "user_id": user["user_id"], 
        "recipe.name": recipe.get("name")
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Recipe already in favorites")
    
    await db.favorite_recipes.insert_one(fav_doc)
    return {"message": "Recipe added to favorites", "favorite_id": fav_doc["favorite_id"]}

@api_router.get("/recipes/favorites")
async def get_favorite_recipes(user: dict = Depends(get_current_user)):
    """Get all favorite recipes"""
    favorites = await db.favorite_recipes.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("added_at", -1).to_list(100)
    return favorites

@api_router.delete("/recipes/favorites/{favorite_id}")
async def remove_favorite_recipe(favorite_id: str, user: dict = Depends(get_current_user)):
    result = await db.favorite_recipes.delete_one({"favorite_id": favorite_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"message": "Recipe removed from favorites"}

# ==================== SHOPPING LIST (LISTE DE COURSES) ====================

@api_router.get("/shopping-list")
async def get_shopping_list(user: dict = Depends(get_current_user)):
    """Get user's shopping list grouped by category"""
    items = await db.shopping_list.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).to_list(200)
    
    # Auto-categorize items that don't have a category
    for item in items:
        if not item.get("category") or item.get("category") == "Autres" or item.get("category") == "Ingrédients":
            item["category"] = categorize_food_item(item.get("display_name", item.get("item", "")))
    
    return items

def categorize_food_item(item_name: str) -> str:
    """Automatically categorize food items"""
    item_lower = item_name.lower()
    
    # Fruits
    fruits = ["pomme", "banane", "orange", "citron", "fraise", "framboise", "myrtille", "raisin", 
              "poire", "pêche", "abricot", "cerise", "mangue", "ananas", "kiwi", "melon", "pastèque",
              "fruit", "agrume", "baie", "clémentine", "mandarine", "prune", "figue"]
    if any(f in item_lower for f in fruits):
        return "🍎 Fruits"
    
    # Légumes
    legumes = ["carotte", "tomate", "salade", "laitue", "épinard", "courgette", "aubergine", 
               "poivron", "oignon", "ail", "échalote", "brocoli", "chou", "haricot vert",
               "petit pois", "asperge", "artichaut", "betterave", "navet", "radis", "céleri",
               "poireau", "fenouil", "légume", "concombre", "avocat", "champignon", "endive"]
    if any(l in item_lower for l in legumes):
        return "🥬 Légumes"
    
    # Viandes
    viandes = ["poulet", "boeuf", "porc", "veau", "agneau", "dinde", "canard", "lapin",
               "viande", "steak", "escalope", "filet", "côte", "rôti", "saucisse", "jambon",
               "bacon", "lard", "chorizo", "merguez"]
    if any(v in item_lower for v in viandes):
        return "🥩 Viandes"
    
    # Poissons et fruits de mer
    poissons = ["saumon", "thon", "cabillaud", "colin", "sole", "bar", "dorade", "truite",
                "sardine", "maquereau", "crevette", "moule", "huître", "crabe", "homard",
                "poisson", "fruit de mer", "anchois", "lieu"]
    if any(p in item_lower for p in poissons):
        return "🐟 Poissons"
    
    # Produits laitiers
    laitiers = ["lait", "fromage", "yaourt", "yogourt", "crème", "beurre", "œuf", "oeuf",
                "mozzarella", "parmesan", "gruyère", "comté", "camembert", "chèvre", "feta"]
    if any(l in item_lower for l in laitiers):
        return "🥛 Produits laitiers"
    
    # Féculents
    feculents = ["riz", "pâte", "spaghetti", "tagliatelle", "penne", "pain", "baguette",
                 "pomme de terre", "patate", "quinoa", "boulgour", "semoule", "couscous",
                 "lentille", "pois chiche", "haricot sec", "fève", "céréale", "flocon",
                 "avoine", "blé", "orge", "maïs", "farine", "féculent"]
    if any(f in item_lower for f in feculents):
        return "🍞 Féculents"
    
    # Épices et condiments
    epices = ["sel", "poivre", "épice", "herbe", "thym", "romarin", "basilic", "persil",
              "coriandre", "menthe", "cumin", "curry", "paprika", "cannelle", "muscade",
              "huile", "vinaigre", "moutarde", "ketchup", "mayonnaise", "sauce", "bouillon"]
    if any(e in item_lower for e in epices):
        return "🧂 Épices & Condiments"
    
    # Boissons
    boissons = ["eau", "jus", "café", "thé", "lait", "soda", "limonade", "sirop", "boisson"]
    if any(b in item_lower for b in boissons):
        return "🥤 Boissons"
    
    # Sucreries et desserts
    sucres = ["sucre", "chocolat", "bonbon", "gâteau", "biscuit", "cookie", "miel", 
              "confiture", "dessert", "glace", "crème glacée", "pâtisserie", "tarte"]
    if any(s in item_lower for s in sucres):
        return "🍫 Sucreries"
    
    # Surgelés
    surgeles = ["surgelé", "congelé", "glacé"]
    if any(s in item_lower for s in surgeles):
        return "❄️ Surgelés"
    
    return "📦 Autres"

@api_router.post("/shopping-list")
async def add_shopping_item(data: dict, user: dict = Depends(get_current_user)):
    """Add item to shopping list with auto-categorization"""
    item_name = data.get("item")
    quantity = data.get("quantity", "")
    portions = data.get("portions", 1)
    category = data.get("category")
    
    if not item_name:
        raise HTTPException(status_code=400, detail="Item name required")
    
    # Auto-categorize if no category provided
    if not category:
        category = categorize_food_item(item_name)
    
    # Check if item already exists
    existing = await db.shopping_list.find_one({
        "user_id": user["user_id"],
        "item": item_name.lower()
    })
    
    if existing:
        # Update quantity and portions
        await db.shopping_list.update_one(
            {"item_id": existing["item_id"]},
            {"$set": {
                "quantity": quantity, 
                "portions": portions,
                "category": category,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return {"message": "Item updated", "item_id": existing["item_id"]}
    
    item_doc = {
        "item_id": f"item_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "item": item_name.lower(),
        "display_name": item_name,
        "quantity": quantity,
        "portions": portions,
        "category": category,
        "checked": False,
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.shopping_list.insert_one(item_doc)
    return {"message": "Item added", "item_id": item_doc["item_id"], "category": category}

@api_router.post("/shopping-list/bulk")
async def add_shopping_items_bulk(data: dict, user: dict = Depends(get_current_user)):
    """Add multiple items to shopping list with auto-categorization"""
    items = data.get("items", [])
    added = 0
    
    for item in items:
        item_name = item.get("item") or item if isinstance(item, str) else item.get("item", "")
        if isinstance(item_name, str) and item_name.strip():
            existing = await db.shopping_list.find_one({
                "user_id": user["user_id"],
                "item": item_name.lower()
            })
            
            if not existing:
                quantity = item.get("quantity", "") if isinstance(item, dict) else ""
                item_doc = {
                    "item_id": f"item_{uuid.uuid4().hex[:8]}",
                    "user_id": user["user_id"],
                    "item": item_name.lower(),
                    "display_name": item_name,
                    "quantity": quantity,
                    "portions": 1,
                    "category": categorize_food_item(item_name),
                    "checked": False,
                    "added_at": datetime.now(timezone.utc).isoformat()
                }
                await db.shopping_list.insert_one(item_doc)
                added += 1
    
    return {"message": f"{added} items added", "added_count": added}

@api_router.put("/shopping-list/{item_id}")
async def update_shopping_item(item_id: str, data: dict, user: dict = Depends(get_current_user)):
    """Update shopping list item"""
    update_data = {}
    if "checked" in data:
        update_data["checked"] = data["checked"]
    if "quantity" in data:
        update_data["quantity"] = data["quantity"]
    if "portions" in data:
        update_data["portions"] = data["portions"]
    if "category" in data:
        update_data["category"] = data["category"]
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.shopping_list.update_one(
            {"item_id": item_id, "user_id": user["user_id"]},
            {"$set": update_data}
        )
    
    return {"message": "Item updated"}

@api_router.delete("/shopping-list/{item_id}")
async def delete_shopping_item(item_id: str, user: dict = Depends(get_current_user)):
    result = await db.shopping_list.delete_one({"item_id": item_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}

@api_router.delete("/shopping-list")
async def clear_shopping_list(user: dict = Depends(get_current_user)):
    """Clear all checked items or all items"""
    await db.shopping_list.delete_many({"user_id": user["user_id"], "checked": True})
    return {"message": "Checked items cleared"}

# ==================== HEALTH ARTICLES ====================

@api_router.get("/articles")
async def get_health_articles(user: dict = Depends(get_current_user)):
    """Get health and nutrition articles - cached daily"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Check cache first
    cached = await db.articles_cache.find_one({"date": today}, {"_id": 0})
    if cached and cached.get("articles"):
        return {"articles": cached["articles"]}
    
    # Generate articles (simulated - in production, would fetch from news APIs)
    articles = [
        {
            "id": f"art_{today}_1",
            "title": "10 aliments brûle-graisses à intégrer dans votre alimentation",
            "summary": "Découvrez les aliments qui accélèrent naturellement votre métabolisme et favorisent la perte de poids.",
            "category": "nutrition",
            "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",
            "source": "Santé Magazine",
            "date": today,
            "read_time": "4 min",
            "content": """Les aliments brûle-graisses sont vos alliés minceur ! Voici les 10 meilleurs :

1. **Le pamplemousse** - Riche en fibres et en vitamine C, il aide à réguler la glycémie.

2. **Le thé vert** - Ses catéchines stimulent le métabolisme et l'oxydation des graisses.

3. **Les épinards** - Très peu caloriques mais riches en nutriments essentiels.

4. **Le saumon** - Ses oméga-3 favorisent la combustion des graisses.

5. **Les œufs** - Riches en protéines, ils augmentent la satiété.

6. **Le poivron** - La capsaïcine qu'il contient booste le métabolisme.

7. **L'avocat** - Ses bonnes graisses aident à contrôler l'appétit.

8. **Les baies** - Faibles en calories et riches en antioxydants.

9. **Le brocoli** - Excellent ratio nutriments/calories.

10. **La cannelle** - Aide à réguler la glycémie et réduit les envies de sucre.

**Conseil** : Intégrez ces aliments progressivement dans vos repas quotidiens pour des résultats durables."""
        },
        {
            "id": f"art_{today}_2",
            "title": "Chirurgie bariatrique : ce qu'il faut savoir avant de se lancer",
            "summary": "Bypass, sleeve : comprendre les différentes options et leurs implications sur votre santé.",
            "category": "santé",
            "image": "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=400",
            "source": "Le Figaro Santé",
            "date": today,
            "read_time": "6 min",
            "content": """La chirurgie bariatrique est une solution pour l'obésité sévère quand les autres méthodes ont échoué.

**Les principales interventions :**

🔹 **La Sleeve gastrectomie**
- Réduction de l'estomac de 75%
- Perte de poids moyenne : 60% de l'excès de poids
- Intervention irréversible

🔹 **Le Bypass gastrique**
- Court-circuit de l'estomac et d'une partie de l'intestin
- Perte de poids moyenne : 70% de l'excès de poids
- Nécessite un suivi nutritionnel strict

**Critères d'éligibilité :**
- IMC supérieur à 40
- Ou IMC supérieur à 35 avec comorbidités (diabète, apnée du sommeil...)
- Échec des régimes sur plusieurs années

**Suivi post-opératoire essentiel :**
- Consultations régulières
- Supplémentation en vitamines
- Adaptation progressive de l'alimentation
- Activité physique régulière

Consultez toujours un spécialiste avant de prendre une décision."""
        },
        {
            "id": f"art_{today}_3",
            "title": "5 exercices pour perdre du ventre à faire chez soi",
            "summary": "Un programme simple et efficace pour tonifier votre ceinture abdominale sans équipement.",
            "category": "fitness",
            "image": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400",
            "source": "Doctissimo",
            "date": today,
            "read_time": "5 min",
            "content": """Perdre du ventre demande de la régularité. Voici 5 exercices efficaces :

**1. La planche (30 sec à 1 min)**
Position de pompe, corps aligné, gainé. Maintenez la position.

**2. Les crunchs (3x15 répétitions)**
Allongé sur le dos, jambes pliées, montez le buste en contractant les abdos.

**3. Le mountain climber (3x30 sec)**
En position de planche, ramenez alternativement les genoux vers la poitrine.

**4. Le gainage latéral (30 sec chaque côté)**
Sur le côté, corps aligné, soulevez les hanches.

**5. Le bicycle crunch (3x20 répétitions)**
Allongé, simulez le pédalage en touchant coude/genou opposé.

**Programme suggéré :**
- 3 à 4 séances par semaine
- Repos de 30 secondes entre chaque exercice
- Augmentez progressivement la durée

**Important** : Ces exercices tonifient mais ne font pas "fondre" la graisse localement. Associez-les à une alimentation équilibrée et du cardio pour des résultats optimaux."""
        }
    ]
    
    # Cache for today
    await db.articles_cache.update_one(
        {"date": today},
        {"$set": {"articles": articles, "created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"articles": articles}

# ==================== DAILY RECIPES (RECETTES DU JOUR) ====================

@api_router.get("/recipes/daily")
async def get_daily_recipes_endpoint(user: dict = Depends(get_current_user)):
    """Get 6 personalized recipes of the day based on user profile"""
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    # Use the imported function from recipes_database
    if profile:
        profile["user_id"] = user["user_id"]
    
    selected = get_daily_recipes(user_profile=profile, count=6)
    
    return {
        "recipes": selected, 
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "total_database": len(SAMPLE_RECIPES)
    }

@api_router.get("/recipes/all")
async def get_all_recipes_endpoint(
    nutri_score: Optional[str] = None,
    category: Optional[str] = None,
    dish_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get all available recipes with filtering"""
    recipes = SAMPLE_RECIPES.copy()
    
    # Filter by nutri_score
    if nutri_score:
        recipes = [r for r in recipes if r["nutri_score"] == nutri_score.upper()]
    
    # Filter by category
    if category:
        recipes = [r for r in recipes if r["category"] == category.lower()]
    
    # Filter by dish_type (entree, plat, dessert, accompagnement, viande, gouter)
    if dish_type:
        recipes = [r for r in recipes if r.get("dish_type", "") == dish_type.lower()]
    
    total = len(recipes)
    paginated = recipes[offset:offset + limit]
    
    # Get enhanced stats including dish_type
    stats = get_recipes_stats()
    
    # Add dish_type stats from sample
    dish_type_stats = {}
    for r in SAMPLE_RECIPES:
        dt = r.get("dish_type", "autre")
        dish_type_stats[dt] = dish_type_stats.get(dt, 0) + 1
    stats["by_dish_type"] = dish_type_stats
    
    return {
        "recipes": paginated, 
        "total": total,
        "limit": limit,
        "offset": offset,
        "stats": stats
    }

@api_router.get("/recipes/stats")
async def get_recipes_stats_endpoint():
    """Get statistics about the recipe database"""
    return get_recipes_stats()

# ==================== PROFILE PICTURE UPLOAD ====================

@api_router.post("/profile/picture")
async def upload_profile_picture(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload a profile picture"""
    # Check file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read and encode as base64
    contents = await file.read()
    
    # Limit size to 2MB
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 2MB)")
    
    image_base64 = base64.b64encode(contents).decode()
    picture_data = f"data:{file.content_type};base64,{image_base64}"
    
    # Update user profile
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"picture": picture_data}}
    )
    
    await db.user_profiles.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"picture": picture_data}},
        upsert=True
    )
    
    return {"message": "Profile picture updated", "picture": picture_data}

@api_router.delete("/profile/picture")
async def delete_profile_picture(user: dict = Depends(get_current_user)):
    """Delete profile picture"""
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"picture": None}}
    )
    
    await db.user_profiles.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"picture": None}}
    )
    
    return {"message": "Profile picture deleted"}

@api_router.delete("/profile/account")
async def delete_account(user: dict = Depends(get_current_user)):
    """Delete user account and all associated data"""
    user_id = user["user_id"]
    
    # Delete all user data from all collections
    collections_to_clean = [
        "users", "user_profiles", "user_points", "user_badges",
        "food_logs", "workout_logs", "weight_history", "bmi_history",
        "agenda_events", "bariatric_logs", "scan_history",
        "social_posts", "friendships", "conversations", "messages",
        "group_members", "favorite_recipes", "shopping_list",
        "ai_usage", "ai_cache", "recipe_generation_cache"
    ]
    
    for collection in collections_to_clean:
        try:
            await db[collection].delete_many({"user_id": user_id})
        except Exception:
            pass
    
    # Also delete where user might be friend_id
    try:
        await db.friendships.delete_many({"friend_id": user_id})
    except Exception:
        pass
    
    return {"message": "Account deleted successfully"}

@api_router.post("/profile/reset-onboarding")
async def reset_onboarding(user: dict = Depends(get_current_user)):
    """Reset onboarding to allow user to redo the questionnaire"""
    user_id = user["user_id"]
    
    # Delete old profile data
    await db.user_profiles.delete_many({"user_id": user_id})
    
    # Reset onboarding flag
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"onboarding_completed": False}}
    )
    
    # Clear old weight/bmi history to start fresh
    await db.weight_history.delete_many({"user_id": user_id})
    await db.bmi_history.delete_many({"user_id": user_id})
    
    # Clear bariatric logs if any
    await db.bariatric_logs.delete_many({"user_id": user_id})
    
    return {"message": "Onboarding reset successfully", "onboarding_completed": False}

# ==================== ADD MEAL FROM AI PLAN TO DIARY ====================

@api_router.post("/meals/add-to-diary")
async def add_meal_to_diary(data: dict, user: dict = Depends(get_current_user)):
    """Add a meal from AI plan to food diary"""
    meal = data.get("meal")
    meal_type = data.get("meal_type", "snack")
    date = data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    
    if not meal:
        raise HTTPException(status_code=400, detail="Meal data required")
    
    log_doc = {
        "entry_id": f"food_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "food_name": meal.get("name", "Repas"),
        "calories": meal.get("calories", 0),
        "protein": meal.get("protein", 0),
        "carbs": meal.get("carbs", 0),
        "fat": meal.get("fat", 0),
        "quantity": 1,
        "meal_type": meal_type,
        "source": "ai_plan",
        "date": date,
        "logged_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.food_logs.insert_one(log_doc)
    
    # Also save to agenda notes
    await db.agenda_notes.update_one(
        {"user_id": user["user_id"], "date": date, "type": "meal_plan"},
        {"$set": {
            "user_id": user["user_id"],
            "date": date,
            "type": "meal_plan",
            "content": f"Repas IA: {meal.get('name')}",
            "meal_data": meal,
            "created_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"message": "Meal added to diary", "entry_id": log_doc["entry_id"]}

# ==================== WORKOUTS ENDPOINTS ====================

@api_router.post("/workouts/generate")
async def generate_workout(user: dict = Depends(get_current_user)):
    """Generate AI-powered workout plan"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json
    
    # ===== AI LIMIT CHECK =====
    await enforce_ai_limit(user["user_id"], "/workouts/generate")
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    
    user_context_hash = get_user_context_hash(profile)
    
    # ===== CHECK CACHE FIRST =====
    prompt_for_cache = f"workout plan goal:{profile.get('goal', '')} fitness:{profile.get('fitness_level', '')}"
    cached = await get_cached_ai_response(prompt_for_cache, "workouts-generate", user_context_hash)
    if cached:
        plan_doc = {
            "program_id": f"workout_{uuid.uuid4().hex[:8]}",
            "user_id": user["user_id"],
            "workout_plan": cached,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "from_cache": True
        }
        await db.workout_programs.insert_one(plan_doc)
        return {"program_id": plan_doc["program_id"], "workout_plan": cached, "from_cache": True}
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"workout_{uuid.uuid4().hex[:8]}",
            system_message="""You are a professional fitness coach. Create personalized workout plans.
Respond ONLY in JSON format:
{
    "program_name": "string",
    "duration_weeks": number,
    "days_per_week": number,
    "workouts": [
        {
            "day": "string",
            "focus": "string",
            "duration_minutes": number,
            "calories_burn_estimate": number,
            "exercises": [
                {
                    "name": "string",
                    "sets": number,
                    "reps": "string",
                    "rest_seconds": number,
                    "instructions": "string"
                }
            ],
            "warmup": "string",
            "cooldown": "string"
        }
    ],
    "tips": ["string"],
    "equipment_needed": ["string"]
}"""
        ).with_model("openai", "gpt-4o")
        
        prompt = f"""Create a weekly workout program for:
- Fitness level: {profile.get('fitness_level', 'beginner')}
- Goal: {profile.get('goal', 'general_fitness')}
- Activity level: {profile.get('activity_level', 'moderate')}
- Weight: {profile.get('weight', 70)} kg

Create effective, progressive workouts that can be done at home or gym. Return JSON only."""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        workout_plan = json.loads(response[json_start:json_end])
        
        # ===== CACHE THE RESULT & INCREMENT USAGE =====
        await store_cached_ai_response(prompt_for_cache, workout_plan, "workouts-generate", user_context_hash)
        await increment_ai_usage(user["user_id"], "/workouts/generate")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI workout generation error: {e}")
        # Return fallback workout plan
        workout_plan = {
            "program_name": "Programme Débutant",
            "duration_weeks": 4,
            "days_per_week": 3,
            "workouts": [
                {
                    "day": "Jour 1",
                    "focus": "Full Body",
                    "duration_minutes": 30,
                    "calories_burn_estimate": 200,
                    "exercises": [
                        {"name": "Squats", "sets": 3, "reps": "12", "rest_seconds": 60, "instructions": "Descendre jusqu'aux cuisses parallèles"},
                        {"name": "Pompes", "sets": 3, "reps": "10", "rest_seconds": 60, "instructions": "Gardez le dos droit"},
                        {"name": "Planche", "sets": 3, "reps": "30 sec", "rest_seconds": 45, "instructions": "Maintenez la position"}
                    ],
                    "warmup": "5 min de marche sur place",
                    "cooldown": "5 min d'étirements"
                }
            ],
            "tips": ["Échauffez-vous toujours", "Hydratez-vous bien", "Progressez à votre rythme"],
            "equipment_needed": ["Aucun équipement requis"]
        }
    
    plan_doc = {
        "program_id": f"workout_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "workout_plan": workout_plan,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.workout_programs.insert_one(plan_doc)
    
    return {"program_id": plan_doc["program_id"], "workout_plan": workout_plan}

@api_router.get("/workouts/programs")
async def get_workout_programs(user: dict = Depends(get_current_user)):
    programs = await db.workout_programs.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    return programs

@api_router.post("/workouts/log")
async def log_workout(workout: WorkoutLog, user: dict = Depends(get_current_user)):
    log_doc = {
        "log_id": f"wlog_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        **workout.model_dump(),
        "logged_at": datetime.now(timezone.utc).isoformat()
    }
    await db.workout_logs.insert_one(log_doc)
    
    # Update streak
    await update_streak(user["user_id"])
    
    return {"message": "Workout logged", "log_id": log_doc["log_id"]}

@api_router.get("/workouts/logs")
async def get_workout_logs(user: dict = Depends(get_current_user)):
    logs = await db.workout_logs.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("logged_at", -1).to_list(50)
    return logs

# ==================== WORKOUT VIDEOS ENDPOINTS ====================

# Mock workout videos data (in production, would use YouTube API)
WORKOUT_VIDEOS = [
    {
        "id": "v1",
        "title": "HIIT Brûle-Graisse 20 min - Sans équipement",
        "thumbnail": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400",
        "duration": "20:00",
        "category": "hiit",
        "level": "intermediate",
        "views": 125000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
    },
    {
        "id": "v2",
        "title": "Gainage Complet - 15 min pour des abdos en béton",
        "thumbnail": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400",
        "duration": "15:00",
        "category": "gainage",
        "level": "beginner",
        "views": 89000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
    },
    {
        "id": "v3",
        "title": "Musculation à la maison - Full Body",
        "thumbnail": "https://images.unsplash.com/photo-1581009146145-b5ef050c149a?w=400",
        "duration": "35:00",
        "category": "home",
        "level": "intermediate",
        "views": 156000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
    },
    {
        "id": "v4",
        "title": "Entraînement Jambes & Fessiers - Salle",
        "thumbnail": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=400",
        "duration": "45:00",
        "category": "jambes",
        "level": "expert",
        "views": 78000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
    },
    {
        "id": "v5",
        "title": "Fitness Dance - Cardio Fun 30 min",
        "thumbnail": "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400",
        "duration": "30:00",
        "category": "fitness",
        "level": "beginner",
        "views": 234000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
    },
    {
        "id": "v6",
        "title": "Musculation Haut du Corps - Prise de masse",
        "thumbnail": "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=400",
        "duration": "40:00",
        "category": "musculation",
        "level": "expert",
        "views": 145000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
    },
    {
        "id": "v7",
        "title": "Yoga Flow Matinal - 20 min détente",
        "thumbnail": "https://images.unsplash.com/photo-1575052814086-f385e2e2ad1b?w=400",
        "duration": "20:00",
        "category": "yoga",
        "level": "beginner",
        "views": 98000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
    },
    {
        "id": "v8",
        "title": "Cardio Boxing - Séance Intense",
        "thumbnail": "https://images.unsplash.com/photo-1549719386-74dfcbf7dbed?w=400",
        "duration": "25:00",
        "category": "cardio",
        "level": "expert",
        "views": 167000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=6)).isoformat(),
    },
    {
        "id": "v9",
        "title": "Abdos Sculptés - 10 min chrono",
        "thumbnail": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400",
        "duration": "10:00",
        "category": "abdos",
        "level": "intermediate",
        "views": 312000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
    },
    {
        "id": "v10",
        "title": "Étirements Post-Entraînement - 15 min récupération",
        "thumbnail": "https://images.unsplash.com/photo-1552196563-55cd4e45efb3?w=400",
        "duration": "15:00",
        "category": "stretching",
        "level": "beginner",
        "views": 87000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
    },
    {
        "id": "v11",
        "title": "HIIT Tabata - 4 min intense",
        "thumbnail": "https://images.unsplash.com/photo-1434682881908-b43d0467b798?w=400",
        "duration": "04:00",
        "category": "hiit",
        "level": "expert",
        "views": 445000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
    },
    {
        "id": "v12",
        "title": "Bras & Épaules - Sculpture musculaire",
        "thumbnail": "https://images.unsplash.com/photo-1581009137042-c552e485697a?w=400",
        "duration": "30:00",
        "category": "bras",
        "level": "intermediate",
        "views": 123000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=8)).isoformat(),
    },
    {
        "id": "v13",
        "title": "Yoga Vinyasa - Flow dynamique",
        "thumbnail": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=400",
        "duration": "45:00",
        "category": "yoga",
        "level": "intermediate",
        "views": 156000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
    },
    {
        "id": "v14",
        "title": "Cardio à la maison - Brûlez 500 calories",
        "thumbnail": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=400",
        "duration": "40:00",
        "category": "home",
        "level": "intermediate",
        "views": 289000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
    },
    {
        "id": "v15",
        "title": "Musculation Dos & Biceps - Programme salle",
        "thumbnail": "https://images.unsplash.com/photo-1534368420009-621bfab424a8?w=400",
        "duration": "50:00",
        "category": "gym",
        "level": "expert",
        "views": 98000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=9)).isoformat(),
    },
    {
        "id": "v16",
        "title": "Planche Challenge - 30 jours",
        "thumbnail": "https://images.unsplash.com/photo-1566241142559-40e1dab266c6?w=400",
        "duration": "12:00",
        "category": "gainage",
        "level": "beginner",
        "views": 567000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=6)).isoformat(),
    },
    {
        "id": "v17",
        "title": "Jambes & Cardio - Circuit training",
        "thumbnail": "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?w=400",
        "duration": "35:00",
        "category": "jambes",
        "level": "intermediate",
        "views": 178000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
    },
    {
        "id": "v18",
        "title": "Fitness Total Body - 25 min efficace",
        "thumbnail": "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=400",
        "duration": "25:00",
        "category": "fitness",
        "level": "beginner",
        "views": 234000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
    },
    {
        "id": "v19",
        "title": "Abdos V-Shape - Programme avancé",
        "thumbnail": "https://images.unsplash.com/photo-1571019613914-85f342c6a11e?w=400",
        "duration": "20:00",
        "category": "abdos",
        "level": "expert",
        "views": 198000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=11)).isoformat(),
    },
    {
        "id": "v20",
        "title": "Étirements matinaux - Réveil en douceur",
        "thumbnail": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400",
        "duration": "10:00",
        "category": "stretching",
        "level": "beginner",
        "views": 145000,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
    },
]

@api_router.get("/workouts/videos")
async def get_workout_videos(category: Optional[str] = None):
    """Get workout videos, optionally filtered by category"""
    videos = WORKOUT_VIDEOS.copy()
    
    # Filter by category if provided
    if category:
        videos = [v for v in videos if v["category"] == category]
    
    # Sort by publishedAt (most recent first)
    videos.sort(key=lambda x: x["publishedAt"], reverse=True)
    
    return videos

@api_router.post("/badges/award")
async def award_video_badge(data: dict, user: dict = Depends(get_current_user)):
    """Award a badge for completing a workout video"""
    badge_type = data.get("type", "video_complete")
    video_id = data.get("video_id")
    video_title = data.get("video_title", "Vidéo")
    
    # Check if badge already earned for this video
    existing = await db.badges.find_one({
        "user_id": user["user_id"],
        "video_id": video_id
    })
    
    if existing:
        return {"message": "Badge already earned", "badge": None}
    
    # Create badge
    badge_icons = ["🏋️", "💪", "🔥", "⭐", "🎯", "🏆", "🥇", "💎"]
    badge = {
        "badge_id": f"badge_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "type": badge_type,
        "video_id": video_id,
        "name": f"Séance {video_title[:20]}...",
        "icon": random.choice(badge_icons),
        "earned_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.badges.insert_one({**badge, "_id": None})
    badge.pop("_id", None)
    
    return {"message": "Badge awarded!", "badge": badge}

# ==================== COACH IA ENDPOINTS ====================

@api_router.post("/workouts/coach/generate")
async def generate_coach_program(config: dict, user: dict = Depends(get_current_user)):
    """Generate personalized workout program using AI"""
    
    # ===== AI LIMIT CHECK =====
    await enforce_ai_limit(user["user_id"], "/workouts/coach/generate")
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    user_context_hash = get_user_context_hash(profile)
    
    duration = config.get("duration", "month")
    time_of_day = config.get("timeOfDay", "morning")
    daily_duration = int(config.get("dailyDuration", "30"))
    body_parts = config.get("bodyParts", ["full_body"])
    equipment = config.get("equipment", "none")
    goals = config.get("goals", "")
    injuries = config.get("injuries", "")
    
    # Duration mapping
    duration_weeks = {
        "week": 1,
        "15days": 2,
        "month": 4,
        "3months": 12,
        "6months": 24,
        "year": 52
    }
    
    weeks = duration_weeks.get(duration, 4)
    
    # ===== CHECK CACHE FIRST =====
    prompt_for_cache = f"coach program {duration} {' '.join(body_parts)} {equipment} {daily_duration}min"
    cached = await get_cached_ai_response(prompt_for_cache, "coach-generate", user_context_hash)
    if cached:
        program_doc = {
            "program_id": f"prog_{uuid.uuid4().hex[:8]}",
            "user_id": user["user_id"],
            "config": config,
            "workout_plan": cached,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "from_cache": True
        }
        await db.workout_programs.insert_one(program_doc)
        return cached
    
    # Build AI prompt
    prompt = f"""Génère un programme d'entraînement personnalisé en français.

Profil utilisateur:
- Âge: {profile.get('age', 30) if profile else 30} ans
- Sexe: {profile.get('gender', 'non spécifié') if profile else 'non spécifié'}
- Poids actuel: {profile.get('weight', 70) if profile else 70} kg
- Objectif: {profile.get('goal', 'maintien') if profile else 'maintien'}
- Niveau fitness: {profile.get('fitness_level', 'intermediate') if profile else 'intermediate'}

Configuration du programme:
- Durée: {weeks} semaines
- Moment de la journée: {time_of_day}
- Durée par séance: {daily_duration} minutes
- Parties du corps: {', '.join(body_parts)}
- Équipement: {equipment}
- Objectifs spécifiques: {goals or 'Aucun'}
- Blessures/Limitations: {injuries or 'Aucune'}

Génère un programme structuré avec:
1. Un nom accrocheur pour le programme
2. Une description courte
3. Pour chaque semaine (minimum 2 semaines à détailler):
   - 3-5 jours d'entraînement
   - Pour chaque jour: liste d'exercices avec séries, répétitions et repos

Format JSON attendu:
{{
  "name": "Nom du programme",
  "description": "Description courte",
  "weeks": [
    {{
      "week_number": 1,
      "days": [
        {{
          "day_number": 1,
          "name": "Jour 1 - Focus",
          "exercises": [
            {{"name": "Exercice", "sets": 3, "reps": "12", "rest": "60s"}}
          ]
        }}
      ]
    }}
  ]
}}"""

    try:
        from emergentintegrations.llm.chat import chat, Message
        
        response = await chat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            messages=[Message(role="user", content=prompt)],
            model="gpt-4o",
            temperature=0.7
        )
        
        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response.message)
        if json_match:
            program = json.loads(json_match.group())
        else:
            raise ValueError("Could not parse program JSON")
        
        # ===== CACHE THE RESULT & INCREMENT USAGE =====
        await store_cached_ai_response(prompt_for_cache, program, "coach-generate", user_context_hash)
        await increment_ai_usage(user["user_id"], "/workouts/coach/generate")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"AI generation error: {e}")
        # Fallback to basic program
        program = {
            "name": f"Programme {', '.join([p.replace('_', ' ').title() for p in body_parts[:2]])}",
            "description": f"Programme personnalisé de {weeks} semaines pour atteindre vos objectifs",
            "weeks": [
                {
                    "week_number": w + 1,
                    "days": [
                        {
                            "day_number": d + 1,
                            "name": f"Jour {d + 1} - {'Cardio' if d % 2 == 0 else 'Renforcement'}",
                            "exercises": [
                                {"name": "Échauffement", "sets": 1, "reps": "5 min", "rest": "0"},
                                {"name": "Squats", "sets": 3, "reps": "15", "rest": "45s"},
                                {"name": "Pompes", "sets": 3, "reps": "12", "rest": "45s"},
                                {"name": "Planche", "sets": 3, "reps": "30s", "rest": "30s"},
                                {"name": "Burpees", "sets": 3, "reps": "10", "rest": "60s"},
                                {"name": "Étirements", "sets": 1, "reps": "5 min", "rest": "0"},
                            ]
                        }
                        for d in range(min(3 + (w % 2), 5))
                    ]
                }
                for w in range(min(weeks, 4))
            ]
        }
    
    # Save program
    program_doc = {
        "program_id": f"prog_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "config": config,
        "workout_plan": program,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.workout_programs.insert_one(program_doc)
    
    return program

@api_router.post("/workouts/coach/add-to-agenda")
async def add_program_to_agenda(data: dict, user: dict = Depends(get_current_user)):
    """Add generated program to user's agenda with reminders"""
    program = data.get("program")
    config = data.get("config", {})
    
    if not program:
        raise HTTPException(status_code=400, detail="Program data required")
    
    time_of_day_hours = {
        "morning": "08:00",
        "noon": "12:00",
        "afternoon": "15:00",
        "evening": "19:00"
    }
    
    default_time = time_of_day_hours.get(config.get("timeOfDay", "morning"), "08:00")
    
    appointments_added = 0
    today = datetime.now(timezone.utc)
    
    for week in program.get("weeks", []):
        week_num = week.get("week_number", 1)
        
        for day in week.get("days", []):
            day_num = day.get("day_number", 1)
            
            # Calculate date
            days_offset = (week_num - 1) * 7 + day_num - 1
            workout_date = (today + timedelta(days=days_offset)).strftime("%Y-%m-%d")
            
            # Create appointment
            appointment = {
                "appointment_id": f"apt_{uuid.uuid4().hex[:8]}",
                "user_id": user["user_id"],
                "title": day.get("name", f"Entraînement Jour {day_num}"),
                "type": "sport",
                "date": workout_date,
                "time": default_time,
                "notes": f"Programme: {program.get('name', 'Coach IA')}\n{len(day.get('exercises', []))} exercices",
                "pinned": day_num == 1 and week_num == 1,  # Pin first workout
                "reminder": True,
                "program_id": program.get("program_id"),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.appointments.insert_one(appointment)
            appointments_added += 1
    
    return {
        "message": f"{appointments_added} séances ajoutées à l'agenda",
        "appointments_added": appointments_added
    }

# ==================== PROGRESS & STATS ENDPOINTS ====================

@api_router.post("/progress/weight")
async def log_weight(entry: WeightEntry, user: dict = Depends(get_current_user)):
    # Get profile for BMI calculation
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    height_m = (profile.get("height", 170) if profile else 170) / 100
    bmi = round(entry.weight / (height_m ** 2), 1)
    
    date_str = entry.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    weight_doc = {
        "entry_id": f"weight_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "weight": entry.weight,
        "bmi": bmi,
        "date": date_str,
        "logged_at": datetime.now(timezone.utc).isoformat()
    }
    await db.weight_history.insert_one(weight_doc)
    
    # Also log BMI history
    await db.bmi_history.insert_one({
        "entry_id": f"bmi_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "bmi": bmi,
        "weight": entry.weight,
        "date": date_str,
        "logged_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Update profile current weight and BMI
    await db.user_profiles.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "weight": entry.weight, 
            "bmi": bmi,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Weight logged", "entry_id": weight_doc["entry_id"], "bmi": bmi}

@api_router.get("/progress/weight")
async def get_weight_history(user: dict = Depends(get_current_user)):
    history = await db.weight_history.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("date", 1).to_list(365)
    return history

@api_router.get("/progress/bmi")
async def get_bmi_history(user: dict = Depends(get_current_user)):
    """Get BMI history with ideal BMI target"""
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    history = await db.bmi_history.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("date", 1).to_list(365)
    
    height = profile.get("height", 170) if profile else 170
    weight = profile.get("weight", 70) if profile else 70
    height_m = height / 100
    
    # If no BMI history, create from weight history
    if not history:
        weight_history = await db.weight_history.find(
            {"user_id": user["user_id"]},
            {"_id": 0}
        ).sort("date", 1).to_list(365)
        
        history = [
            {
                "date": w.get("date"),
                "bmi": round(w.get("weight", 70) / (height_m ** 2), 1),
                "weight": w.get("weight")
            } for w in weight_history
        ]
    
    ideal_bmi = profile.get("ideal_bmi", 22.0) if profile else 22.0
    current_bmi = profile.get("bmi", round(weight / (height_m ** 2), 1)) if profile else round(weight / (height_m ** 2), 1)
    
    return {
        # Frontend expected format
        "bmi": current_bmi,
        "height": height,
        "weight": weight,
        # Additional data
        "history": history,
        "current_bmi": current_bmi,
        "ideal_bmi": ideal_bmi,
        "ideal_weight": profile.get("ideal_weight") if profile else None,
        "ideal_weight_range": profile.get("ideal_weight_range") if profile else None,
        "bmi_categories": {
            "underweight": {"max": 18.4, "label": "Insuffisance pondérale"},
            "normal": {"min": 18.5, "max": 24.9, "label": "Poids normal"},
            "overweight": {"min": 25, "max": 29.9, "label": "Surpoids"},
            "obese": {"min": 30, "label": "Obésité"}
        }
    }

@api_router.get("/progress/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    # Get this week's data
    today = datetime.now(timezone.utc)
    week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")
    
    food_logs = await db.food_logs.find(
        {"user_id": user["user_id"], "logged_at": {"$gte": week_start}},
        {"_id": 0}
    ).to_list(500)
    
    # Today's food logs only
    today_food_logs = await db.food_logs.find(
        {"user_id": user["user_id"], "date": today_str},
        {"_id": 0}
    ).to_list(100)
    
    workout_logs = await db.workout_logs.find(
        {"user_id": user["user_id"], "logged_at": {"$gte": week_start}},
        {"_id": 0}
    ).to_list(100)
    
    weight_history = await db.weight_history.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("date", -1).to_list(30)
    
    # Calculate stats
    total_calories_week = sum(log.get("calories", 0) * log.get("quantity", 1) for log in food_logs)
    total_workouts_week = len(workout_logs)
    total_workout_minutes = sum(log.get("duration_minutes", 0) for log in workout_logs)
    
    # Today's calories consumed
    calories_consumed_today = sum(log.get("calories", 0) * log.get("quantity", 1) for log in today_food_logs)
    
    current_weight = profile.get("weight", 0) if profile else 0
    target_weight = profile.get("target_weight", 0) if profile else 0
    start_weight = weight_history[-1]["weight"] if weight_history else current_weight
    
    # Get calorie targets from profile
    calorie_target = profile.get("daily_calorie_target", 2000) if profile else 2000
    calorie_debug = profile.get("calorie_debug", {}) if profile else {}
    tdee_maintenance = calorie_debug.get("tdee_maintenance", calorie_target)
    
    # Calculate remaining calories
    calories_remaining = max(0, calorie_target - calories_consumed_today)
    
    # Get streak
    streak = await get_streak(user["user_id"])
    
    # Health disclaimer for high BMI or age
    bmi = profile.get("bmi", 0) if profile else 0
    age = profile.get("age", 0) if profile else 0
    health_disclaimer = None
    if bmi > 35 or age > 50:
        health_disclaimer = "Les recommandations sont des estimations basées sur des formules reconnues. En cas d'obésité ou de pathologie, un avis médical est recommandé."
    
    return {
        "current_weight": current_weight,
        "target_weight": target_weight,
        "weight_change": round(current_weight - start_weight, 1),
        "bmi": profile.get("bmi", 0) if profile else 0,
        "weekly_stats": {
            "calories_consumed": round(total_calories_week),
            "workouts_completed": total_workouts_week,
            "workout_minutes": total_workout_minutes,
            "avg_daily_calories": round(total_calories_week / 7)
        },
        # Clear separation of calorie concepts (MANDATORY FOR UX)
        "calories": {
            "maintenance": round(tdee_maintenance),  # TDEE - calories to maintain weight
            "target": round(calorie_target),         # Recommended based on goal
            "consumed_today": round(calories_consumed_today),
            "remaining_today": round(calories_remaining)
        },
        "calorie_debug": calorie_debug,  # BMR, activity factor, TDEE for transparency
        "streak": streak,
        "daily_targets": {
            "calories": calorie_target,
            "protein": profile.get("daily_protein_target", 100) if profile else 100,
            "carbs": profile.get("daily_carbs_target", 250) if profile else 250,
            "fat": profile.get("daily_fat_target", 65) if profile else 65
        },
        "ideal_bmi": profile.get("ideal_bmi", 22.0) if profile else 22.0,
        "ideal_weight": profile.get("ideal_weight") if profile else None,
        "ideal_weight_range": profile.get("ideal_weight_range") if profile else None,
        "health_conditions": profile.get("health_conditions", []) if profile else [],
        "health_disclaimer": health_disclaimer
    }

async def update_streak(user_id: str):
    """Update user's activity streak"""
    streak_doc = await db.streaks.find_one({"user_id": user_id}, {"_id": 0})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    if not streak_doc:
        await db.streaks.insert_one({
            "user_id": user_id,
            "current_streak": 1,
            "longest_streak": 1,
            "last_activity_date": today
        })
    else:
        last_date = streak_doc.get("last_activity_date", "")
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        
        if last_date == today:
            return  # Already logged today
        elif last_date == yesterday:
            new_streak = streak_doc.get("current_streak", 0) + 1
        else:
            new_streak = 1
        
        longest = max(new_streak, streak_doc.get("longest_streak", 0))
        
        await db.streaks.update_one(
            {"user_id": user_id},
            {"$set": {
                "current_streak": new_streak,
                "longest_streak": longest,
                "last_activity_date": today
            }}
        )

async def get_streak(user_id: str) -> dict:
    streak_doc = await db.streaks.find_one({"user_id": user_id}, {"_id": 0})
    if not streak_doc:
        return {"current": 0, "longest": 0}
    return {
        "current": streak_doc.get("current_streak", 0),
        "longest": streak_doc.get("longest_streak", 0)
    }

# ==================== BADGES & GAMIFICATION ====================

@api_router.get("/badges")
async def get_badges(user: dict = Depends(get_current_user)):
    user_badges = await db.user_badges.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).to_list(100)
    
    # Check for new badges
    await check_and_award_badges(user["user_id"])
    
    # Get user stats for progress calculation
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    food_count = await db.food_logs.count_documents({"user_id": user["user_id"]})
    workout_count = await db.workout_logs.count_documents({"user_id": user["user_id"]})
    streak_data = await get_streak(user["user_id"])
    scan_count = await db.food_logs.count_documents({"user_id": user["user_id"], "image_url": {"$exists": True}})
    meal_plan_count = await db.meal_plans.count_documents({"user_id": user["user_id"]})
    user_points = await db.user_points.find_one({"user_id": user["user_id"]}, {"_id": 0})
    total_points = user_points.get("total_points", 0) if user_points else 0
    friend_count = await db.friendships.count_documents({
        "$or": [{"user_id": user["user_id"]}, {"friend_id": user["user_id"]}],
        "status": "accepted"
    })
    
    all_badges = [
        # Beginner badges
        {"id": "first_meal", "name": "Premier repas", "description": "Enregistrez votre premier repas", "icon": "🍽️", "category": "nutrition", "progress": min(food_count, 1), "target": 1},
        {"id": "first_workout", "name": "Premier entraînement", "description": "Complétez votre premier workout", "icon": "💪", "category": "fitness", "progress": min(workout_count, 1), "target": 1},
        {"id": "week_streak", "name": "Semaine parfaite", "description": "7 jours consécutifs d'activité", "icon": "🔥", "category": "streak", "progress": streak_data.get("current", 0), "target": 7},
        
        # Progress badges
        {"id": "food_scanner", "name": "Détective nutrition", "description": "Scannez 10 aliments", "icon": "📸", "category": "nutrition", "progress": min(scan_count, 10), "target": 10},
        {"id": "meal_planner", "name": "Chef organisé", "description": "Générez votre premier plan repas", "icon": "📅", "category": "nutrition", "progress": min(meal_plan_count, 1), "target": 1},
        {"id": "nutrition_master", "name": "Maître nutrition", "description": "100 repas enregistrés", "icon": "🥗", "category": "nutrition", "progress": min(food_count, 100), "target": 100},
        
        # Fitness badges
        {"id": "workout_warrior", "name": "Guerrier fitness", "description": "50 entraînements complétés", "icon": "🏋️", "category": "fitness", "progress": min(workout_count, 50), "target": 50},
        {"id": "month_streak", "name": "Mois incroyable", "description": "30 jours consécutifs", "icon": "⭐", "category": "streak", "progress": streak_data.get("current", 0), "target": 30},
        
        # Points badges
        {"id": "points_100", "name": "Challenger", "description": "Gagnez 100 points de défis", "icon": "🎯", "category": "challenges", "progress": min(total_points, 100), "target": 100},
        {"id": "points_500", "name": "Champion", "description": "Gagnez 500 points de défis", "icon": "🏆", "category": "challenges", "progress": min(total_points, 500), "target": 500},
        {"id": "points_1000", "name": "Légende", "description": "Gagnez 1000 points de défis", "icon": "👑", "category": "challenges", "progress": min(total_points, 1000), "target": 1000},
        
        # Social badges
        {"id": "first_friend", "name": "Social", "description": "Ajoutez votre premier ami", "icon": "👋", "category": "social", "progress": min(friend_count, 1), "target": 1},
        {"id": "social_butterfly", "name": "Papillon social", "description": "10 amis dans votre réseau", "icon": "🦋", "category": "social", "progress": min(friend_count, 10), "target": 10},
    ]
    
    earned_ids = {b["badge_id"] for b in user_badges}
    
    # Calculate next badges to earn (closest to completion)
    available_badges = []
    for badge in all_badges:
        if badge["id"] not in earned_ids:
            progress_percent = (badge["progress"] / badge["target"]) * 100 if badge["target"] > 0 else 0
            badge["progress_percent"] = round(progress_percent, 1)
            badge["earned"] = False
            available_badges.append(badge)
    
    # Sort by progress percentage (closest to completion first)
    available_badges.sort(key=lambda x: x["progress_percent"], reverse=True)
    next_badges = available_badges[:4]  # Show top 4 closest badges
    
    # Add earned status to all badges
    earned_badges = []
    for badge in all_badges:
        if badge["id"] in earned_ids:
            earned_badge = next((b for b in user_badges if b["badge_id"] == badge["id"]), None)
            badge["earned"] = True
            badge["progress_percent"] = 100
            badge["earned_at"] = earned_badge.get("earned_at") if earned_badge else None
            earned_badges.append(badge)
    
    return {
        "earned": earned_badges,
        "available": available_badges,
        "next_badges": next_badges,
        "total_earned": len(earned_badges),
        "total_available": len(all_badges)
    }

async def check_and_award_badges(user_id: str):
    existing = {b["badge_id"] for b in await db.user_badges.find({"user_id": user_id}, {"_id": 0}).to_list(100)}
    
    # Check first meal
    if "first_meal" not in existing:
        count = await db.food_logs.count_documents({"user_id": user_id})
        if count > 0:
            await award_badge(user_id, "first_meal", "Premier repas")
    
    # Check first workout
    if "first_workout" not in existing:
        count = await db.workout_logs.count_documents({"user_id": user_id})
        if count > 0:
            await award_badge(user_id, "first_workout", "Premier entraînement")
    
    # Check streak badges
    streak = await get_streak(user_id)
    if "week_streak" not in existing and streak["current"] >= 7:
        await award_badge(user_id, "week_streak", "Semaine parfaite")
    if "month_streak" not in existing and streak["current"] >= 30:
        await award_badge(user_id, "month_streak", "Mois incroyable")
    
    # Check nutrition master
    if "nutrition_master" not in existing:
        food_count = await db.food_logs.count_documents({"user_id": user_id})
        if food_count >= 100:
            await award_badge(user_id, "nutrition_master", "Maître nutrition")
    
    # Check food scanner
    if "food_scanner" not in existing:
        scan_count = await db.food_logs.count_documents({"user_id": user_id, "image_url": {"$exists": True}})
        if scan_count >= 10:
            await award_badge(user_id, "food_scanner", "Détective nutrition")
    
    # Check meal planner
    if "meal_planner" not in existing:
        meal_plan_count = await db.meal_plans.count_documents({"user_id": user_id})
        if meal_plan_count >= 1:
            await award_badge(user_id, "meal_planner", "Chef organisé")
    
    # Check workout warrior
    if "workout_warrior" not in existing:
        workout_count = await db.workout_logs.count_documents({"user_id": user_id})
        if workout_count >= 50:
            await award_badge(user_id, "workout_warrior", "Guerrier fitness")
    
    # Check points badges
    user_points = await db.user_points.find_one({"user_id": user_id}, {"_id": 0})
    total_points = user_points.get("total_points", 0) if user_points else 0
    
    if "points_100" not in existing and total_points >= 100:
        await award_badge(user_id, "points_100", "Challenger")
    if "points_500" not in existing and total_points >= 500:
        await award_badge(user_id, "points_500", "Champion")
    if "points_1000" not in existing and total_points >= 1000:
        await award_badge(user_id, "points_1000", "Légende")
    
    # Check social badges
    friend_count = await db.friendships.count_documents({
        "$or": [{"user_id": user_id}, {"friend_id": user_id}],
        "status": "accepted"
    })
    if "first_friend" not in existing and friend_count >= 1:
        await award_badge(user_id, "first_friend", "Social")
    if "social_butterfly" not in existing and friend_count >= 10:
        await award_badge(user_id, "social_butterfly", "Papillon social")

async def award_badge(user_id: str, badge_id: str, badge_name: str):
    await db.user_badges.insert_one({
        "user_id": user_id,
        "badge_id": badge_id,
        "badge_name": badge_name,
        "earned_at": datetime.now(timezone.utc).isoformat()
    })

# ==================== CHALLENGES ====================

@api_router.get("/challenges")
async def get_challenges(user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    # Get current data
    food_count = await db.food_logs.count_documents({"user_id": user["user_id"], "logged_at": {"$regex": f"^{today}"}})
    workout_today = await db.workout_logs.find_one({"user_id": user["user_id"], "logged_at": {"$regex": f"^{today}"}})
    steps_today = await db.step_logs.find_one({"user_id": user["user_id"], "date": today})
    
    # Daily summary for calories
    daily_summary_docs = await db.food_logs.find(
        {"user_id": user["user_id"], "logged_at": {"$regex": f"^{today}"}}
    ).to_list(100)
    total_calories_today = sum([d.get("calories", 0) for d in daily_summary_docs])
    target_calories = profile.get("daily_calorie_target", 2000) if profile else 2000
    
    # Dynamic daily challenges
    daily_challenges = [
        {
            "id": "log_breakfast",
            "title": "Petit-déjeuner enregistré",
            "description": "Commencez bien la journée",
            "icon": "🍳",
            "reward": 25,
            "progress": min(food_count, 1),
            "target": 1,
            "completed": food_count >= 1
        },
        {
            "id": "log_3_meals",
            "title": "3 repas équilibrés",
            "description": "Enregistrez 3 repas aujourd'hui",
            "icon": "🥗",
            "reward": 50,
            "progress": min(food_count, 3),
            "target": 3,
            "completed": food_count >= 3
        },
        {
            "id": "walk_5000_steps",
            "title": "5 000 pas",
            "description": "Objectif mi-journée",
            "icon": "👟",
            "reward": 40,
            "progress": steps_today.get("steps", 0) if steps_today else 0,
            "target": 5000,
            "completed": (steps_today.get("steps", 0) if steps_today else 0) >= 5000
        },
        {
            "id": "walk_10000_steps",
            "title": "10 000 pas",
            "description": "Objectif quotidien",
            "icon": "🏃",
            "reward": 100,
            "progress": steps_today.get("steps", 0) if steps_today else 0,
            "target": 10000,
            "completed": (steps_today.get("steps", 0) if steps_today else 0) >= 10000
        },
        {
            "id": "workout_20",
            "title": "20 min d'exercice",
            "description": "Bougez votre corps",
            "icon": "💪",
            "reward": 60,
            "progress": workout_today.get("duration_minutes", 0) if workout_today else 0,
            "target": 20,
            "completed": (workout_today.get("duration_minutes", 0) if workout_today else 0) >= 20
        },
        {
            "id": "under_calories",
            "title": "Objectif calories",
            "description": f"Restez sous {target_calories} kcal",
            "icon": "🎯",
            "reward": 75,
            "progress": total_calories_today,
            "target": target_calories,
            "completed": total_calories_today <= target_calories and total_calories_today > 0
        },
    ]
    
    # Use day of year as seed for consistent selection
    day_of_year = datetime.now(timezone.utc).timetuple().tm_yday
    random.seed(day_of_year + hash(user["user_id"]))
    
    # Select 4 challenges for today (random but consistent for the day)
    selected_challenges = random.sample(daily_challenges, min(4, len(daily_challenges)))
    
    # Get user's total challenge points (never resets)
    user_points = await db.user_points.find_one({"user_id": user["user_id"]}, {"_id": 0})
    total_points = user_points.get("total_points", 0) if user_points else 0
    
    # Check if any challenges were completed and award points
    completed_today = await db.challenge_completions.find(
        {"user_id": user["user_id"], "date": today},
        {"_id": 0}
    ).to_list(100)
    completed_ids = {c["challenge_id"] for c in completed_today}
    
    points_earned_today = 0
    for challenge in selected_challenges:
        if challenge["completed"] and challenge["id"] not in completed_ids:
            # Award points for newly completed challenge
            points_earned_today += challenge["reward"]
            await db.challenge_completions.insert_one({
                "user_id": user["user_id"],
                "challenge_id": challenge["id"],
                "date": today,
                "points": challenge["reward"],
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Update total points if any earned
    if points_earned_today > 0:
        await db.user_points.update_one(
            {"user_id": user["user_id"]},
            {
                "$inc": {"total_points": points_earned_today},
                "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
            },
            upsert=True
        )
        total_points += points_earned_today
    
    # Mark already completed challenges
    for challenge in selected_challenges:
        challenge["already_claimed"] = challenge["id"] in completed_ids
    
    return {
        "daily": selected_challenges, 
        "weekly": [],
        "total_points": total_points,
        "points_earned_today": points_earned_today
    }

@api_router.get("/challenges/points")
async def get_challenge_points(user: dict = Depends(get_current_user)):
    """Get user's total challenge points"""
    user_points = await db.user_points.find_one({"user_id": user["user_id"]}, {"_id": 0})
    total_points = user_points.get("total_points", 0) if user_points else 0
    
    # Get points history
    history = await db.challenge_completions.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("completed_at", -1).to_list(50)
    
    return {
        "total_points": total_points,
        "history": history
    }

# ==================== MOTIVATION MESSAGES ====================

@api_router.get("/motivation")
async def get_motivation_message(user: dict = Depends(get_current_user)):
    """Get personalized daily motivation message based on user profile"""
    import random
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    # Get current stats
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    food_count = await db.food_logs.count_documents({"user_id": user["user_id"], "date": today})
    
    # Get streak
    streak_data = await get_streak(user["user_id"])
    streak = streak_data.get("current", 0)
    
    # Get weight progress
    weight_history = await db.weight_history.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("date", -1).to_list(2)
    
    weight_lost = 0
    if weight_history and len(weight_history) > 1:
        weight_lost = weight_history[-1].get("weight", 0) - weight_history[0].get("weight", 0)
    
    # Personalization based on profile
    goal = profile.get("goal", "lose_weight") if profile else "lose_weight"
    name = user.get("name", "").split()[0] if user.get("name") else "Champion"
    
    # Use day of year as seed for consistent daily message
    day_of_year = datetime.now(timezone.utc).timetuple().tm_yday
    random.seed(day_of_year + hash(user["user_id"]))
    
    # Messages based on goal and context
    messages_lose_weight = [
        f"💪 {name}, chaque petit pas compte ! Continue comme ça !",
        f"🌟 Tu es sur la bonne voie, {name} ! Ta discipline paie !",
        f"🔥 {name}, rappelle-toi pourquoi tu as commencé. Tu peux le faire !",
        f"✨ Aujourd'hui est un nouveau jour pour progresser, {name} !",
        f"🏆 {name}, ton corps te remerciera pour tes efforts d'aujourd'hui !",
        f"💎 La persévérance est ta meilleure alliée, {name} !",
        f"🚀 {name}, tu es plus fort(e) que tes excuses !",
        f"🌈 Chaque repas sain est une victoire, {name} !",
        f"⭐ {name}, tu mérites d'être fier(e) de toi !",
        f"🎯 Reste concentré(e) sur ton objectif, {name} !",
    ]
    
    messages_gain_muscle = [
        f"💪 {name}, les muscles se construisent jour après jour !",
        f"🏋️ Force et détermination, {name} ! Tu progresses !",
        f"🔥 {name}, chaque entraînement te rapproche de ton objectif !",
        f"⚡ {name}, ton corps se transforme, continue !",
        f"🦁 {name}, libère ta puissance intérieure aujourd'hui !",
    ]
    
    messages_maintain = [
        f"😊 {name}, tu maintiens un excellent équilibre !",
        f"🌟 Continue comme ça, {name} ! La constance est la clé !",
        f"✨ {name}, ton mode de vie sain t'inspire !",
        f"🎉 Bravo {name} pour ton engagement au quotidien !",
    ]
    
    # Select messages based on goal
    if goal == "gain_muscle":
        base_messages = messages_gain_muscle
    elif goal == "maintain":
        base_messages = messages_maintain
    else:
        base_messages = messages_lose_weight
    
    message = random.choice(base_messages)
    
    # Add contextual bonus messages
    bonus = None
    if streak >= 7:
        bonus = f"🔥 Incroyable ! {streak} jours de suite !"
    elif streak >= 3:
        bonus = f"⚡ Belle série de {streak} jours !"
    elif weight_lost < 0:  # Lost weight (negative change)
        bonus = f"📉 Tu as perdu {abs(round(weight_lost, 1))} kg ! Continue !"
    elif food_count >= 3:
        bonus = "✅ Tu as bien suivi tes repas aujourd'hui !"
    
    return {
        "message": message,
        "bonus": bonus,
        "streak": streak,
        "day_of_year": day_of_year
    }

# ==================== STATIC FILES FOR PWA (ICONS, MANIFEST) ====================
# Serve PWA static files directly to bypass React Router redirect
# These are served via /api/pwa/* to ensure they are accessible

@app.get("/api/pwa/icon-48x48.png")
async def get_pwa_icon_48():
    icon_path = FRONTEND_PUBLIC_DIR / "icon-48x48.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/api/pwa/icon-72x72.png")
async def get_pwa_icon_72():
    icon_path = FRONTEND_PUBLIC_DIR / "icon-72x72.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/api/pwa/icon-96x96.png")
async def get_pwa_icon_96():
    icon_path = FRONTEND_PUBLIC_DIR / "icon-96x96.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/api/pwa/icon-128x128.png")
async def get_pwa_icon_128():
    icon_path = FRONTEND_PUBLIC_DIR / "icon-128x128.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/api/pwa/icon-144x144.png")
async def get_pwa_icon_144():
    icon_path = FRONTEND_PUBLIC_DIR / "icon-144x144.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/api/pwa/icon-192x192.png")
async def get_pwa_icon_192():
    icon_path = FRONTEND_PUBLIC_DIR / "icon-192x192.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/api/pwa/icon-256x256.png")
async def get_pwa_icon_256():
    icon_path = FRONTEND_PUBLIC_DIR / "icon-256x256.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/api/pwa/icon-384x384.png")
async def get_pwa_icon_384():
    icon_path = FRONTEND_PUBLIC_DIR / "icon-384x384.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/api/pwa/icon-152x152.png")
async def get_pwa_icon_152():
    icon_path = FRONTEND_PUBLIC_DIR / "icon-152x152.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/api/pwa/icon-512x512.png")
async def get_pwa_icon_512():
    icon_path = FRONTEND_PUBLIC_DIR / "icon-512x512.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/api/pwa/icon-192x192-maskable.png")
async def get_pwa_maskable_192():
    icon_path = FRONTEND_PUBLIC_DIR / "icon-192x192-maskable.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/api/pwa/icon-512x512-maskable.png")
async def get_pwa_maskable_512():
    icon_path = FRONTEND_PUBLIC_DIR / "icon-512x512-maskable.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/api/pwa/screenshot-wide.png")
async def get_pwa_screenshot_wide():
    path = FRONTEND_PUBLIC_DIR / "screenshot-wide.png"
    if path.exists():
        return FileResponse(path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Screenshot not found")

@app.get("/api/pwa/screenshot-narrow.png")
async def get_pwa_screenshot_narrow():
    path = FRONTEND_PUBLIC_DIR / "screenshot-narrow.png"
    if path.exists():
        return FileResponse(path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Screenshot not found")

# ==================== ASSETLINKS FOR TWA (Android App Links) ====================

@app.get("/.well-known/assetlinks.json")
async def get_assetlinks():
    """Serve assetlinks.json for Android TWA verification"""
    assetlinks_path = FRONTEND_PUBLIC_DIR / ".well-known" / "assetlinks.json"
    if assetlinks_path.exists():
        return FileResponse(
            assetlinks_path, 
            media_type="application/json",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    # Fallback if file doesn't exist
    return JSONResponse(
        content=[{
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": "com.fatandslim.app",
                "sha256_cert_fingerprints": ["REMPLACER_PAR_VOTRE_SHA256_GOOGLE_PLAY"]
            }
        }],
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )

# ==================== USER STATS & BADGES ====================

@api_router.get("/user/stats")
async def get_user_stats(user: dict = Depends(get_current_user)):
    """Get user stats including days active, badges and profile picture"""
    user_doc = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get profile for picture
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    created_at = user_doc.get("created_at")
    if isinstance(created_at, str):
        from dateutil import parser
        created_at = parser.parse(created_at)
    elif not created_at:
        created_at = datetime.now(timezone.utc)
    
    days_active = (datetime.now(timezone.utc) - created_at.replace(tzinfo=timezone.utc)).days + 1
    
    # Calculate consecutive days (streak)
    streak = await calculate_streak(user["user_id"])
    
    # Get badges
    badges = await get_user_badges(user["user_id"], days_active, streak)
    
    # Get earned badges sorted by most recent
    earned_badges = [b for b in badges if b["earned"]]
    
    # Get recently earned badges from user_badges collection
    recent_badges_docs = await db.user_badges.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("earned_at", -1).limit(3).to_list(3)
    
    # Map recent badges with full info
    recent_badges = []
    for rb in recent_badges_docs:
        badge_info = next((b for b in badges if b["id"] == rb["badge_id"]), None)
        if badge_info:
            recent_badges.append({
                **badge_info,
                "earned_at": rb.get("earned_at")
            })
    
    # If no recent badges from DB, use earned badges
    if not recent_badges:
        recent_badges = earned_badges[:3]
    
    # Get profile picture from profile or user doc
    picture = profile.get("picture") if profile else None
    if not picture:
        picture = user_doc.get("picture")
    
    return {
        "days_active": days_active,
        "streak": streak,
        "badges": badges,
        "badges_count": len(earned_badges),
        "recent_badges": recent_badges,
        "created_at": created_at.isoformat(),
        "picture": picture,
        "name": user_doc.get("name", "Utilisateur")
    }

async def calculate_streak(user_id: str) -> int:
    """Calculate consecutive days of activity"""
    today = datetime.now(timezone.utc).date()
    streak = 0
    current_date = today
    
    for _ in range(365):  # Check up to 1 year
        date_str = current_date.strftime("%Y-%m-%d")
        # Check if user logged food or weight on this day
        food_log = await db.food_logs.find_one({"user_id": user_id, "date": date_str})
        weight_log = await db.weight_entries.find_one({"user_id": user_id, "date": date_str})
        
        if food_log or weight_log:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    return streak

async def get_user_badges(user_id: str, days_active: int, streak: int) -> list:
    """Get user badges based on activity"""
    badge_definitions = [
        {"id": "first_day", "name": "Premier Pas", "description": "Premier jour sur l'app", "icon": "🌟", "requirement": 1, "type": "days"},
        {"id": "3_days", "name": "Débutant", "description": "3 jours d'utilisation", "icon": "🥉", "requirement": 3, "type": "days"},
        {"id": "5_days", "name": "Motivé", "description": "5 jours d'utilisation", "icon": "💪", "requirement": 5, "type": "days"},
        {"id": "7_days", "name": "Semaine Complète", "description": "7 jours d'utilisation", "icon": "🏅", "requirement": 7, "type": "days"},
        {"id": "10_days", "name": "Persévérant", "description": "10 jours d'utilisation", "icon": "🎯", "requirement": 10, "type": "days"},
        {"id": "15_days", "name": "Discipliné", "description": "15 jours d'utilisation", "icon": "🥈", "requirement": 15, "type": "days"},
        {"id": "30_days", "name": "Champion", "description": "30 jours d'utilisation", "icon": "🥇", "requirement": 30, "type": "days"},
        {"id": "60_days", "name": "Expert", "description": "60 jours d'utilisation", "icon": "🏆", "requirement": 60, "type": "days"},
        {"id": "100_days", "name": "Légende", "description": "100 jours d'utilisation", "icon": "👑", "requirement": 100, "type": "days"},
        {"id": "streak_3", "name": "Série de 3", "description": "3 jours de suite", "icon": "🔥", "requirement": 3, "type": "streak"},
        {"id": "streak_7", "name": "Série de 7", "description": "7 jours de suite", "icon": "🔥🔥", "requirement": 7, "type": "streak"},
        {"id": "streak_14", "name": "Série de 14", "description": "14 jours de suite", "icon": "🔥🔥🔥", "requirement": 14, "type": "streak"},
    ]
    
    badges = []
    for badge in badge_definitions:
        if badge["type"] == "days":
            earned = days_active >= badge["requirement"]
        elif badge["type"] == "streak":
            earned = streak >= badge["requirement"]
        else:
            earned = False
        
        badges.append({**badge, "earned": earned})
    
    return badges

# ==================== APPOINTMENTS / RDV AGENDA ====================

@api_router.get("/appointments")
async def get_appointments(user: dict = Depends(get_current_user)):
    """Get all user appointments"""
    appointments = await db.appointments.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("date", 1).to_list(100)
    return appointments

@api_router.post("/appointments")
async def create_appointment(data: dict, user: dict = Depends(get_current_user)):
    """Create a new appointment"""
    apt = {
        "appointment_id": f"apt_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "title": data.get("title", "Rendez-vous"),
        "type": data.get("type", "medical"),  # medical, sport, wellness
        "date": data.get("date"),
        "time": data.get("time"),
        "location": data.get("location", ""),
        "notes": data.get("notes", ""),
        "pinned": data.get("pinned", False),
        "reminder": data.get("reminder", True),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.appointments.insert_one(apt)
    return {"message": "Appointment created", "appointment_id": apt["appointment_id"]}

@api_router.put("/appointments/{appointment_id}")
async def update_appointment(appointment_id: str, data: dict, user: dict = Depends(get_current_user)):
    """Update an appointment"""
    result = await db.appointments.update_one(
        {"appointment_id": appointment_id, "user_id": user["user_id"]},
        {"$set": {k: v for k, v in data.items() if k not in ["appointment_id", "user_id"]}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment updated"}

@api_router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, user: dict = Depends(get_current_user)):
    """Delete an appointment"""
    result = await db.appointments.delete_one(
        {"appointment_id": appointment_id, "user_id": user["user_id"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment deleted"}

@api_router.get("/appointments/today")
async def get_today_appointments(user: dict = Depends(get_current_user)):
    """Get today's appointments for alert"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    appointments = await db.appointments.find(
        {"user_id": user["user_id"], "date": today},
        {"_id": 0}
    ).sort("time", 1).to_list(50)
    return appointments

# ==================== STEP COUNTER & CALORIES BURNED ====================

@api_router.post("/steps/log")
async def log_steps(data: dict, user: dict = Depends(get_current_user)):
    """Log steps from device"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    steps = data.get("steps", 0)
    source = data.get("source", "manual")  # manual, google_fit, health_connect
    
    # Get user profile for calorie calculation
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    # Calculate calories burned (simple formula)
    # Calories = steps * weight_factor * 0.04
    weight = profile.get("weight", 70) if profile else 70
    weight_factor = weight / 70  # Normalize to 70kg
    calories_burned = round(steps * weight_factor * 0.04)
    
    step_doc = {
        "user_id": user["user_id"],
        "date": today,
        "steps": steps,
        "calories_burned": calories_burned,
        "source": source,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.step_logs.update_one(
        {"user_id": user["user_id"], "date": today},
        {"$set": step_doc},
        upsert=True
    )
    
    return {
        "message": "Steps logged",
        "steps": steps,
        "calories_burned": calories_burned,
        "date": today
    }

@api_router.get("/steps/today")
async def get_today_steps(user: dict = Depends(get_current_user)):
    """Get today's step count and goals"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    step_log = await db.step_logs.find_one(
        {"user_id": user["user_id"], "date": today},
        {"_id": 0}
    )
    
    # Default step goal based on activity level
    activity_goals = {
        "sedentary": 5000,
        "light": 7500,
        "moderate": 10000,
        "active": 12500,
        "very_active": 15000
    }
    activity_level = profile.get("activity_level", "moderate") if profile else "moderate"
    step_goal = activity_goals.get(activity_level, 10000)
    
    return {
        "date": today,
        "steps": step_log.get("steps", 0) if step_log else 0,
        "calories_burned": step_log.get("calories_burned", 0) if step_log else 0,
        "goal": step_goal,
        "progress": round((step_log.get("steps", 0) / step_goal * 100) if step_log else 0, 1),
        "source": step_log.get("source", "none") if step_log else "none"
    }

@api_router.get("/steps/history")
async def get_steps_history(days: int = 7, user: dict = Depends(get_current_user)):
    """Get step history for the past N days"""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    logs = await db.step_logs.find(
        {
            "user_id": user["user_id"],
            "date": {
                "$gte": start_date.strftime("%Y-%m-%d"),
                "$lte": end_date.strftime("%Y-%m-%d")
            }
        },
        {"_id": 0}
    ).sort("date", 1).to_list(days)
    
    return logs

# ==================== SMART RECOMMENDATIONS ====================

@api_router.get("/recommendations/smart")
async def get_smart_recommendation(user: dict = Depends(get_current_user)):
    """Get a personalized smart recommendation based on user profile and activity"""
    import random
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get today's data
    food_logs = await db.food_logs.find({"user_id": user["user_id"], "date": today}, {"_id": 0}).to_list(100)
    step_log = await db.step_logs.find_one({"user_id": user["user_id"], "date": today}, {"_id": 0})
    
    total_calories = sum(log.get("calories", 0) for log in food_logs)
    total_steps = step_log.get("steps", 0) if step_log else 0
    goal = profile.get("goal", "maintain") if profile else "maintain"
    activity_level = profile.get("activity_level", "moderate") if profile else "moderate"
    
    # Categories of recommendations
    recommendations = {
        "activity": [
            "🚶 Nous vous recommandons de marcher un minimum de 15 minutes aujourd'hui pour rester actif !",
            "🏃 Une petite marche digestive après le repas aide à mieux assimiler les nutriments.",
            "💃 Dansez 10 minutes sur votre musique préférée, c'est bon pour le moral et la forme !",
            "🧘 Quelques étirements pendant 5 minutes peuvent faire une grande différence dans votre journée.",
            "🚴 Si possible, privilégiez le vélo ou la marche pour vos petits trajets.",
            "⬆️ Prenez les escaliers plutôt que l'ascenseur, vos jambes vous remercieront !",
        ],
        "nutrition_general": [
            "🥗 En choisissant les légumes à volonté plutôt qu'un plat trop calorique, je me fais plaisir en qualité et en quantité !",
            "🍎 Si vous n'avez pas consommé de fruits aujourd'hui, il est grand temps de se fendre la poire !",
            "💧 Pensez à boire au moins 1,5L d'eau aujourd'hui pour rester bien hydraté.",
            "🥦 Les légumes verts sont vos meilleurs alliés pour un repas rassasiant et peu calorique.",
            "🥚 Les protéines au petit-déjeuner aident à tenir jusqu'au déjeuner sans fringale.",
            "🍵 Une tisane en fin de journée aide à la digestion et prépare un bon sommeil.",
        ],
        "motivation": [
            "💪 Les efforts commencent à payer, ne pas abandonner c'est se dépasser !",
            "🌟 Chaque petit pas compte, vous êtes sur la bonne voie !",
            "🎯 Votre constance est admirable, continuez ainsi !",
            "🔥 La motivation vous a amené ici, la discipline vous fera continuer !",
            "⭐ Vous êtes plus fort(e) que vous ne le pensez, croyez en vous !",
            "🏆 Le succès est la somme de petits efforts répétés jour après jour.",
            "✨ Chaque jour est une nouvelle opportunité de devenir meilleur(e) !",
        ],
        "tracking": [
            "📊 Pensez à bien renseigner votre poids dans votre profil afin d'actualiser vos progrès.",
            "📝 N'oubliez pas de noter vos repas pour un suivi optimal de votre alimentation.",
            "📈 Consultez régulièrement vos statistiques pour mesurer vos progrès !",
            "🎯 Définir des objectifs clairs vous aide à rester motivé(e) sur le long terme.",
        ],
        "sleep_wellness": [
            "😴 Un bon sommeil est essentiel pour la récupération et la gestion du poids.",
            "🧘‍♀️ La méditation de 5 minutes par jour réduit le stress et les envies de grignotage.",
            "☀️ Exposez-vous à la lumière naturelle le matin pour réguler votre rythme circadien.",
            "📵 Évitez les écrans 1h avant le coucher pour un sommeil réparateur.",
        ]
    }
    
    # Choose category based on context
    if total_steps < 3000 and activity_level in ["sedentary", "light"]:
        category = "activity"
    elif len(food_logs) == 0:
        category = "tracking"
    elif total_calories < 500 and datetime.now(timezone.utc).hour > 12:
        category = "nutrition_general"
    else:
        category = random.choice(["motivation", "nutrition_general", "activity", "sleep_wellness"])
    
    # Get a random recommendation from the chosen category
    message = random.choice(recommendations[category])
    
    # Make sure we don't repeat the same message (store in session/cache)
    last_recommendations = await db.user_recommendations.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(5)
    
    last_messages = [r.get("message") for r in last_recommendations]
    attempts = 0
    while message in last_messages and attempts < 10:
        message = random.choice(recommendations[random.choice(list(recommendations.keys()))])
        attempts += 1
    
    # Store this recommendation
    await db.user_recommendations.insert_one({
        "user_id": user["user_id"],
        "message": message,
        "category": category,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": message,
        "category": category,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ==================== PDF REPORT GENERATION ====================

@api_router.get("/reports/progress-pdf")
async def generate_progress_pdf(user: dict = Depends(get_current_user)):
    """Generate a comprehensive PDF report of user progress"""
    from io import BytesIO
    import base64
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    user_doc = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not found")
    
    # Get all data
    weight_entries = await db.weight_entries.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("date", 1).to_list(1000)
    
    food_logs = await db.food_logs.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).to_list(1000)
    
    step_logs = await db.step_logs.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).to_list(365)
    
    # Calculate statistics
    created_at = user_doc.get("created_at", datetime.now(timezone.utc).isoformat())
    if isinstance(created_at, str):
        from dateutil import parser
        created_at = parser.parse(created_at)
    
    days_active = (datetime.now(timezone.utc) - created_at.replace(tzinfo=timezone.utc)).days + 1
    
    # Weight stats
    if weight_entries:
        weights = [e["weight"] for e in weight_entries]
        weight_start = weights[0]
        weight_current = weights[-1]
        weight_change = weight_current - weight_start
        weight_min = min(weights)
        weight_max = max(weights)
    else:
        weight_start = weight_current = profile.get("weight", 0)
        weight_change = 0
        weight_min = weight_max = profile.get("weight", 0)
    
    # Food stats
    total_meals_logged = len(food_logs)
    total_calories_logged = sum(log.get("calories", 0) for log in food_logs)
    avg_daily_calories = round(total_calories_logged / max(days_active, 1))
    
    # Steps stats
    total_steps = sum(log.get("steps", 0) for log in step_logs)
    total_calories_burned = sum(log.get("calories_burned", 0) for log in step_logs)
    avg_daily_steps = round(total_steps / max(len(step_logs), 1))
    
    # BMI calculation
    height_m = profile.get("height", 170) / 100
    bmi_start = round(weight_start / (height_m ** 2), 1) if weight_start else 0
    bmi_current = round(weight_current / (height_m ** 2), 1) if weight_current else 0
    
    # Prepare report data
    report_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user": {
            "name": user_doc.get("name", "Utilisateur"),
            "email": user_doc.get("email", ""),
            "created_at": created_at.isoformat(),
            "days_active": days_active
        },
        "profile": {
            "age": profile.get("age"),
            "gender": profile.get("gender"),
            "height": profile.get("height"),
            "goal": profile.get("goal"),
            "activity_level": profile.get("activity_level"),
            "daily_calorie_target": profile.get("daily_calorie_target"),
            "target_weight": profile.get("target_weight")
        },
        "weight_progress": {
            "start_weight": weight_start,
            "current_weight": weight_current,
            "target_weight": profile.get("target_weight"),
            "weight_change": round(weight_change, 1),
            "weight_min": weight_min,
            "weight_max": weight_max,
            "bmi_start": bmi_start,
            "bmi_current": bmi_current,
            "entries_count": len(weight_entries),
            "entries": weight_entries[-30:]  # Last 30 entries
        },
        "nutrition_stats": {
            "total_meals_logged": total_meals_logged,
            "total_calories_logged": total_calories_logged,
            "avg_daily_calories": avg_daily_calories,
            "target_calories": profile.get("daily_calorie_target", 2000)
        },
        "activity_stats": {
            "total_steps": total_steps,
            "total_calories_burned": total_calories_burned,
            "avg_daily_steps": avg_daily_steps,
            "days_tracked": len(step_logs)
        }
    }
    
    return report_data

# ==================== GOOGLE CALENDAR INTEGRATION ====================

# Google Calendar OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', '')
GOOGLE_CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

@api_router.get("/calendar/auth-url")
async def get_calendar_auth_url(user: dict = Depends(get_current_user)):
    """Get Google Calendar OAuth URL"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google Calendar not configured")
    
    from google_auth_oauthlib.flow import Flow
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=GOOGLE_CALENDAR_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    
    auth_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true',
        state=user["user_id"]  # Pass user_id in state
    )
    
    # Store state for verification
    await db.oauth_states.insert_one({
        "state": state,
        "user_id": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"auth_url": auth_url}

@api_router.get("/calendar/callback")
async def calendar_oauth_callback(code: str, state: str):
    """Handle Google Calendar OAuth callback"""
    from google.oauth2.credentials import Credentials
    
    # Verify state
    state_doc = await db.oauth_states.find_one({"state": state})
    if not state_doc:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    user_id = state_doc["user_id"]
    
    # Exchange code for tokens
    async with httpx.AsyncClient() as client_http:
        token_resp = await client_http.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'redirect_uri': GOOGLE_REDIRECT_URI,
                'grant_type': 'authorization_code'
            }
        )
        
        if token_resp.status_code != 200:
            logger.error(f"Token exchange failed: {token_resp.text}")
            raise HTTPException(status_code=400, detail="Token exchange failed")
        
        tokens = token_resp.json()
    
    # Store tokens
    await db.google_calendar_tokens.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "access_token": tokens.get("access_token"),
                "refresh_token": tokens.get("refresh_token"),
                "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    # Clean up state
    await db.oauth_states.delete_one({"state": state})
    
    # Redirect to app
    frontend_url = os.environ.get('FRONTEND_URL', 'https://bariatric-algo.preview.emergentagent.com')
    return RedirectResponse(f"{frontend_url}/dashboard?calendar_connected=true")

@api_router.get("/calendar/status")
async def get_calendar_status(user: dict = Depends(get_current_user)):
    """Check if Google Calendar is connected"""
    tokens = await db.google_calendar_tokens.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    return {
        "connected": bool(tokens and tokens.get("access_token")),
        "configured": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
    }

@api_router.delete("/calendar/disconnect")
async def disconnect_calendar(user: dict = Depends(get_current_user)):
    """Disconnect Google Calendar"""
    await db.google_calendar_tokens.delete_one({"user_id": user["user_id"]})
    return {"message": "Calendar disconnected"}

async def get_valid_calendar_credentials(user_id: str):
    """Get valid Google Calendar credentials, refreshing if needed"""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request as GoogleRequest
    
    tokens = await db.google_calendar_tokens.find_one({"user_id": user_id}, {"_id": 0})
    
    if not tokens or not tokens.get("access_token"):
        return None
    
    creds = Credentials(
        token=tokens.get("access_token"),
        refresh_token=tokens.get("refresh_token"),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET
    )
    
    # Check if expired and refresh
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleRequest())
            # Update stored tokens
            await db.google_calendar_tokens.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "access_token": creds.token,
                        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return None
    
    return creds

@api_router.get("/calendar/events")
async def get_calendar_events(
    user: dict = Depends(get_current_user),
    time_min: str = None,
    time_max: str = None,
    max_results: int = 50
):
    """Get Google Calendar events"""
    from googleapiclient.discovery import build
    
    creds = await get_valid_calendar_credentials(user["user_id"])
    
    if not creds:
        raise HTTPException(status_code=401, detail="Google Calendar not connected")
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        # Default to next 30 days
        if not time_min:
            time_min = datetime.now(timezone.utc).isoformat()
        if not time_max:
            time_max = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Format events for the app
        formatted_events = []
        for event in events:
            start = event.get('start', {})
            end = event.get('end', {})
            
            formatted_events.append({
                "id": event.get('id'),
                "title": event.get('summary', 'Sans titre'),
                "description": event.get('description', ''),
                "start": start.get('dateTime') or start.get('date'),
                "end": end.get('dateTime') or end.get('date'),
                "all_day": 'date' in start,
                "location": event.get('location', ''),
                "source": "google_calendar",
                "color": "#4285F4"  # Google blue
            })
        
        return {"events": formatted_events, "count": len(formatted_events)}
        
    except Exception as e:
        logger.error(f"Calendar fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch calendar: {str(e)}")

@api_router.get("/calendar/sync")
async def sync_calendar_to_agenda(user: dict = Depends(get_current_user)):
    """Sync Google Calendar events to app agenda"""
    from googleapiclient.discovery import build
    
    creds = await get_valid_calendar_credentials(user["user_id"])
    
    if not creds:
        raise HTTPException(status_code=401, detail="Google Calendar not connected")
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        # Get events for next 30 days
        time_min = datetime.now(timezone.utc).isoformat()
        time_max = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        synced_count = 0
        
        for event in events:
            start = event.get('start', {})
            start_time = start.get('dateTime') or start.get('date')
            
            # Check if already synced
            existing = await db.appointments.find_one({
                "user_id": user["user_id"],
                "google_event_id": event.get('id')
            })
            
            if not existing:
                # Create appointment from Google event
                appointment = {
                    "appointment_id": f"gcal_{event.get('id')}",
                    "user_id": user["user_id"],
                    "google_event_id": event.get('id'),
                    "title": event.get('summary', 'Sans titre'),
                    "description": event.get('description', ''),
                    "datetime": start_time,
                    "type": "event",
                    "source": "google_calendar",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.appointments.insert_one(appointment)
                synced_count += 1
        
        return {
            "message": f"Synchronisation terminée",
            "synced": synced_count,
            "total_events": len(events)
        }
        
    except Exception as e:
        logger.error(f"Calendar sync error: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

# ==================== SOCIAL NETWORK ENDPOINTS ====================

# --- Public Profiles ---
@api_router.get("/social/profile/{user_id}")
async def get_public_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get a user's public profile with badges, points and objective"""
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = await db.user_profiles.find_one({"user_id": user_id}, {"_id": 0})
    
    # Get badges
    user_badges = await db.user_badges.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Get points (total + challenge)
    user_points = await db.user_points.find_one({"user_id": user_id}, {"_id": 0})
    total_points = user_points.get("total_points", 0) if user_points else 0
    challenge_points = user_points.get("challenge_points", 0) if user_points else 0
    
    # Get favorite recipes count
    favorite_count = await db.favorite_recipes.count_documents({"user_id": user_id})
    
    # Get posts count
    posts_count = await db.social_posts.count_documents({"user_id": user_id})
    
    # Get friends count
    friends_count = await db.friendships.count_documents({
        "$or": [{"user_id": user_id}, {"friend_id": user_id}],
        "status": "accepted"
    })
    
    # Check friendship status
    friendship = await db.friendships.find_one({
        "$or": [
            {"user_id": current_user["user_id"], "friend_id": user_id},
            {"user_id": user_id, "friend_id": current_user["user_id"]}
        ]
    }, {"_id": 0})
    
    is_friend = friendship and friendship.get("status") == "accepted"
    is_pending = friendship and friendship.get("status") == "pending"
    is_self = current_user["user_id"] == user_id
    
    # Get objective from onboarding
    objective = user_doc.get("objective") or (profile.get("goal") if profile else None)
    
    return {
        "user_id": user_id,
        "name": user_doc.get("name", "Utilisateur"),
        "picture": user_doc.get("picture") or (profile.get("picture") if profile else None),
        "objective": objective,
        "goal": profile.get("goal") if profile else None,
        "fitness_level": profile.get("fitness_level") if profile else None,
        "badges": user_badges,
        "badges_count": len(user_badges) or user_doc.get("badges_count", 0),
        "total_points": total_points,
        "challenge_points": challenge_points,
        "favorite_recipes_count": favorite_count,
        "posts_count": posts_count,
        "friends_count": friends_count,
        "is_friend": is_friend,
        "is_pending": is_pending,
        "is_self": is_self,
        "is_premium": user_doc.get("is_premium", False),
        "created_at": user_doc.get("created_at")
    }

@api_router.get("/social/search")
async def search_users(q: str, user: dict = Depends(get_current_user)):
    """Search for users by name or email"""
    if len(q) < 2:
        return {"users": []}
    
    users = await db.users.find({
        "$and": [
            {"user_id": {"$ne": user["user_id"]}},
            {"$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}}
            ]}
        ]
    }, {"_id": 0, "password_hash": 0}).limit(20).to_list(20)
    
    # Add friendship status
    result = []
    for u in users:
        friendship = await db.friendships.find_one({
            "$or": [
                {"user_id": user["user_id"], "friend_id": u["user_id"]},
                {"user_id": u["user_id"], "friend_id": user["user_id"]}
            ]
        }, {"_id": 0})
        
        result.append({
            "user_id": u["user_id"],
            "name": u.get("name", "Utilisateur"),
            "email": u.get("email", ""),
            "picture": u.get("picture"),
            "friendship_status": friendship.get("status") if friendship else None
        })
    
    return {"users": result}

# --- Friendships ---
@api_router.post("/social/friends/request")
async def send_friend_request(data: dict, user: dict = Depends(get_current_user)):
    """Send a friend request"""
    friend_id = data.get("friend_id")
    if not friend_id:
        raise HTTPException(status_code=400, detail="friend_id required")
    
    if friend_id == user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot add yourself")
    
    # Check if friendship already exists
    existing = await db.friendships.find_one({
        "$or": [
            {"user_id": user["user_id"], "friend_id": friend_id},
            {"user_id": friend_id, "friend_id": user["user_id"]}
        ]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Friendship already exists or pending")
    
    friendship = {
        "friendship_id": f"friend_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "friend_id": friend_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.friendships.insert_one(friendship)
    
    # Create notification
    await create_notification(friend_id, "friend_request", f"{user.get('name') or 'Quelquun'} veut être votre ami !", user["user_id"])
    
    return {"message": "Friend request sent", "friendship_id": friendship["friendship_id"]}

@api_router.post("/social/friends/accept")
async def accept_friend_request(data: dict, user: dict = Depends(get_current_user)):
    """Accept a friend request"""
    friendship_id = data.get("friendship_id")
    
    result = await db.friendships.update_one(
        {"friendship_id": friendship_id, "friend_id": user["user_id"], "status": "pending"},
        {"$set": {"status": "accepted", "accepted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    # Get the friendship to notify the other user
    friendship = await db.friendships.find_one({"friendship_id": friendship_id}, {"_id": 0})
    if friendship:
        await create_notification(friendship["user_id"], "friend_accepted", f"{user.get('name') or 'Quelquun'} a accepté votre demande d'ami !", user["user_id"])
    
    return {"message": "Friend request accepted"}

@api_router.post("/social/friends/reject")
async def reject_friend_request(data: dict, user: dict = Depends(get_current_user)):
    """Reject or cancel a friend request"""
    friendship_id = data.get("friendship_id")
    
    result = await db.friendships.delete_one({
        "friendship_id": friendship_id,
        "$or": [
            {"friend_id": user["user_id"]},
            {"user_id": user["user_id"]}
        ]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    return {"message": "Friend request rejected/cancelled"}

@api_router.delete("/social/friends/{friend_id}")
async def remove_friend(friend_id: str, user: dict = Depends(get_current_user)):
    """Remove a friend"""
    result = await db.friendships.delete_one({
        "status": "accepted",
        "$or": [
            {"user_id": user["user_id"], "friend_id": friend_id},
            {"user_id": friend_id, "friend_id": user["user_id"]}
        ]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Friendship not found")
    
    return {"message": "Friend removed"}

@api_router.get("/social/friends")
async def get_friends(user: dict = Depends(get_current_user)):
    """Get user's friends list"""
    friendships = await db.friendships.find({
        "$or": [{"user_id": user["user_id"]}, {"friend_id": user["user_id"]}],
        "status": "accepted"
    }, {"_id": 0}).to_list(100)
    
    friends = []
    for f in friendships:
        friend_user_id = f["friend_id"] if f["user_id"] == user["user_id"] else f["user_id"]
        friend_user = await db.users.find_one({"user_id": friend_user_id}, {"_id": 0, "password_hash": 0})
        
        if friend_user:
            user_points = await db.user_points.find_one({"user_id": friend_user_id}, {"_id": 0})
            friends.append({
                "user_id": friend_user_id,
                "name": friend_user.get("name", "Utilisateur"),
                "picture": friend_user.get("picture"),
                "total_points": user_points.get("total_points", 0) if user_points else 0,
                "friendship_id": f["friendship_id"],
                "since": f.get("accepted_at", f.get("created_at"))
            })
    
    return {"friends": friends, "count": len(friends)}

@api_router.get("/social/friends/requests")
async def get_friend_requests(user: dict = Depends(get_current_user)):
    """Get pending friend requests"""
    # Requests received
    received = await db.friendships.find({
        "friend_id": user["user_id"],
        "status": "pending"
    }, {"_id": 0}).to_list(50)
    
    received_list = []
    for r in received:
        sender = await db.users.find_one({"user_id": r["user_id"]}, {"_id": 0, "password_hash": 0})
        if sender:
            received_list.append({
                "friendship_id": r["friendship_id"],
                "user_id": r["user_id"],
                "name": sender.get("name", "Utilisateur"),
                "picture": sender.get("picture"),
                "sent_at": r["created_at"]
            })
    
    # Requests sent
    sent = await db.friendships.find({
        "user_id": user["user_id"],
        "status": "pending"
    }, {"_id": 0}).to_list(50)
    
    sent_list = []
    for s in sent:
        recipient = await db.users.find_one({"user_id": s["friend_id"]}, {"_id": 0, "password_hash": 0})
        if recipient:
            sent_list.append({
                "friendship_id": s["friendship_id"],
                "user_id": s["friend_id"],
                "name": recipient.get("name", "Utilisateur"),
                "picture": recipient.get("picture"),
                "sent_at": s["created_at"]
            })
    
    return {"received": received_list, "sent": sent_list}

# --- Activity Feed ---
@api_router.get("/social/feed")
async def get_activity_feed(user: dict = Depends(get_current_user), limit: int = 30, feed_type: str = "friends"):
    """Get activity feed - friends only or public"""
    
    if feed_type == "public":
        # Get ALL public activities
        activities = await db.social_activities.find(
            {"visibility": {"$ne": "private"}},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
    else:
        # Get friend activities only
        friendships = await db.friendships.find({
            "$or": [{"user_id": user["user_id"]}, {"friend_id": user["user_id"]}],
            "status": "accepted"
        }, {"_id": 0}).to_list(100)
        
        friend_ids = [user["user_id"]]
        for f in friendships:
            friend_ids.append(f["friend_id"] if f["user_id"] == user["user_id"] else f["user_id"])
        
        activities = await db.social_activities.find(
            {"user_id": {"$in": friend_ids}},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Enrich with user info and comments
    result = []
    for activity in activities:
        activity_user = await db.users.find_one({"user_id": activity["user_id"]}, {"_id": 0, "password_hash": 0})
        profile = await db.user_profiles.find_one({"user_id": activity["user_id"]}, {"_id": 0})
        likes_count = await db.activity_likes.count_documents({"activity_id": activity["activity_id"]})
        user_liked = await db.activity_likes.find_one({
            "activity_id": activity["activity_id"],
            "user_id": user["user_id"]
        })
        
        # Get comments
        comments = await db.activity_comments.find(
            {"activity_id": activity["activity_id"]},
            {"_id": 0}
        ).sort("created_at", 1).limit(10).to_list(10)
        
        # Enrich comments with user info
        enriched_comments = []
        for comment in comments:
            comment_user = await db.users.find_one({"user_id": comment["user_id"]}, {"_id": 0, "password_hash": 0})
            enriched_comments.append({
                **comment,
                "user_name": comment_user.get("name") if comment_user else "Utilisateur",
                "user_picture": comment_user.get("picture") if comment_user else None
            })
        
        user_picture = profile.get("picture") if profile else None
        if not user_picture:
            user_picture = activity_user.get("picture") if activity_user else None
        
        result.append({
            **activity,
            "user_name": activity_user.get("name", "Utilisateur") if activity_user else "Utilisateur",
            "user_picture": user_picture,
            "likes_count": likes_count,
            "user_liked": bool(user_liked),
            "comments": enriched_comments,
            "comments_count": len(enriched_comments)
        })
    
    return {"activities": result}

# Old post endpoint - redirecting to new system
# (Keeping comment endpoint for backward compatibility)

@api_router.post("/social/comment")
async def add_comment(data: dict, user: dict = Depends(get_current_user)):
    """Add a comment to a post"""
    activity_id = data.get("activity_id")
    content = data.get("content", "").strip()
    
    if not activity_id or not content:
        raise HTTPException(status_code=400, detail="activity_id and content required")
    
    comment = {
        "comment_id": f"cmt_{uuid.uuid4().hex[:8]}",
        "activity_id": activity_id,
        "user_id": user["user_id"],
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.activity_comments.insert_one(comment)
    
    # Notify post owner
    activity = await db.social_activities.find_one({"activity_id": activity_id}, {"_id": 0})
    if activity and activity["user_id"] != user["user_id"]:
        await create_notification(activity["user_id"], "comment", f"{user.get('name') or 'Quelquun'} a commenté votre publication", user["user_id"])
    
    return {"message": "Comment added", "comment": comment}

@api_router.post("/social/like/{activity_id}")
async def like_activity(activity_id: str, user: dict = Depends(get_current_user)):
    """Like or unlike an activity"""
    existing = await db.activity_likes.find_one({
        "activity_id": activity_id,
        "user_id": user["user_id"]
    })
    
    if existing:
        await db.activity_likes.delete_one({"activity_id": activity_id, "user_id": user["user_id"]})
        return {"message": "Unliked", "liked": False}
    else:
        await db.activity_likes.insert_one({
            "activity_id": activity_id,
            "user_id": user["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Create notification for post owner
        activity = await db.social_activities.find_one({"activity_id": activity_id}, {"_id": 0})
        if activity and activity["user_id"] != user["user_id"]:
            await create_notification(activity["user_id"], "like", f"{user.get('name') or 'Quelquun'} a aimé votre publication", user["user_id"])
        
        return {"message": "Liked", "liked": True}

# --- Messaging ---
@api_router.get("/social/messages")
async def get_conversations(user: dict = Depends(get_current_user)):
    """Get list of conversations"""
    # Get all messages where user is sender or recipient
    messages = await db.messages.find({
        "$or": [{"sender_id": user["user_id"]}, {"recipient_id": user["user_id"]}]
    }, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Group by conversation partner
    conversations = {}
    for msg in messages:
        partner_id = msg["recipient_id"] if msg["sender_id"] == user["user_id"] else msg["sender_id"]
        
        if partner_id not in conversations:
            partner = await db.users.find_one({"user_id": partner_id}, {"_id": 0, "password_hash": 0})
            unread_count = await db.messages.count_documents({
                "sender_id": partner_id,
                "recipient_id": user["user_id"],
                "read": False
            })
            
            conversations[partner_id] = {
                "partner_id": partner_id,
                "partner_name": partner.get("name", "Utilisateur") if partner else "Utilisateur",
                "partner_picture": partner.get("picture") if partner else None,
                "last_message": msg,
                "unread_count": unread_count
            }
    
    return {"conversations": list(conversations.values())}

@api_router.get("/social/messages/{partner_id}")
async def get_messages(partner_id: str, user: dict = Depends(get_current_user)):
    """Get messages with a specific user"""
    messages = await db.messages.find({
        "$or": [
            {"sender_id": user["user_id"], "recipient_id": partner_id},
            {"sender_id": partner_id, "recipient_id": user["user_id"]}
        ]
    }, {"_id": 0}).sort("created_at", 1).to_list(100)
    
    # Mark as read
    await db.messages.update_many(
        {"sender_id": partner_id, "recipient_id": user["user_id"], "read": False},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"messages": messages}

@api_router.post("/social/messages")
async def send_message(data: dict, user: dict = Depends(get_current_user)):
    """Send a message"""
    recipient_id = data.get("recipient_id")
    content = data.get("content", "").strip()
    
    if not recipient_id or not content:
        raise HTTPException(status_code=400, detail="recipient_id and content required")
    
    # Check if they are friends
    friendship = await db.friendships.find_one({
        "status": "accepted",
        "$or": [
            {"user_id": user["user_id"], "friend_id": recipient_id},
            {"user_id": recipient_id, "friend_id": user["user_id"]}
        ]
    })
    
    if not friendship:
        raise HTTPException(status_code=403, detail="You can only message friends")
    
    message = {
        "message_id": f"msg_{uuid.uuid4().hex[:8]}",
        "sender_id": user["user_id"],
        "recipient_id": recipient_id,
        "content": content,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.messages.insert_one(message)
    
    # Create notification
    await create_notification(recipient_id, "message", f"Nouveau message de {user.get('name') or 'Quelquun'}", user["user_id"])
    
    return {"message": "Message sent", "data": message}

# --- Notifications ---
async def create_notification(user_id: str, notif_type: str, content: str, from_user_id: str = None):
    """Helper to create notifications"""
    notification = {
        "notification_id": f"notif_{uuid.uuid4().hex[:8]}",
        "user_id": user_id,
        "type": notif_type,
        "content": content,
        "from_user_id": from_user_id,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)

@api_router.get("/social/notifications")
async def get_notifications(user: dict = Depends(get_current_user)):
    """Get user notifications"""
    notifications = await db.notifications.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    # Enrich with from_user info
    result = []
    for n in notifications:
        if n.get("from_user_id"):
            from_user = await db.users.find_one({"user_id": n["from_user_id"]}, {"_id": 0, "password_hash": 0})
            n["from_user_name"] = from_user.get("name") if from_user else None
            n["from_user_picture"] = from_user.get("picture") if from_user else None
        result.append(n)
    
    unread_count = sum(1 for n in notifications if not n.get("read"))
    
    return {"notifications": result, "unread_count": unread_count}

@api_router.post("/social/notifications/read")
async def mark_notifications_read(data: dict, user: dict = Depends(get_current_user)):
    """Mark notifications as read"""
    notification_ids = data.get("notification_ids", [])
    
    if notification_ids:
        await db.notifications.update_many(
            {"notification_id": {"$in": notification_ids}, "user_id": user["user_id"]},
            {"$set": {"read": True}}
        )
    else:
        # Mark all as read
        await db.notifications.update_many(
            {"user_id": user["user_id"], "read": False},
            {"$set": {"read": True}}
        )
    
    return {"message": "Notifications marked as read"}

# --- Friend Challenges ---
@api_router.post("/social/challenges/create")
async def create_friend_challenge(data: dict, user: dict = Depends(get_current_user)):
    """Create a challenge between friends"""
    friend_id = data.get("friend_id")
    challenge_type = data.get("type", "steps")  # steps, meals, workouts
    target = data.get("target", 10000)
    duration_days = data.get("duration_days", 7)
    
    if not friend_id:
        raise HTTPException(status_code=400, detail="friend_id required")
    
    # Verify friendship
    friendship = await db.friendships.find_one({
        "status": "accepted",
        "$or": [
            {"user_id": user["user_id"], "friend_id": friend_id},
            {"user_id": friend_id, "friend_id": user["user_id"]}
        ]
    })
    
    if not friendship:
        raise HTTPException(status_code=403, detail="Not friends")
    
    end_date = (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()
    
    challenge = {
        "challenge_id": f"fc_{uuid.uuid4().hex[:8]}",
        "creator_id": user["user_id"],
        "opponent_id": friend_id,
        "type": challenge_type,
        "target": target,
        "duration_days": duration_days,
        "status": "pending",
        "creator_progress": 0,
        "opponent_progress": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "end_date": end_date
    }
    
    await db.friend_challenges.insert_one(challenge)
    await create_notification(friend_id, "challenge", f"{user.get('name') or 'Quelquun'} vous lance un défi !", user["user_id"])
    
    return {"message": "Challenge created", "challenge": challenge}

@api_router.get("/social/challenges")
async def get_friend_challenges(user: dict = Depends(get_current_user)):
    """Get friend challenges"""
    challenges = await db.friend_challenges.find({
        "$or": [{"creator_id": user["user_id"]}, {"opponent_id": user["user_id"]}]
    }, {"_id": 0}).sort("created_at", -1).to_list(50)
    
    result = []
    for c in challenges:
        opponent_id = c["opponent_id"] if c["creator_id"] == user["user_id"] else c["creator_id"]
        opponent = await db.users.find_one({"user_id": opponent_id}, {"_id": 0, "password_hash": 0})
        
        result.append({
            **c,
            "opponent_name": opponent.get("name") if opponent else "Utilisateur",
            "opponent_picture": opponent.get("picture") if opponent else None,
            "is_creator": c["creator_id"] == user["user_id"]
        })
    
    return {"challenges": result}

@api_router.post("/social/challenges/{challenge_id}/accept")
async def accept_friend_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
    """Accept a friend challenge"""
    result = await db.friend_challenges.update_one(
        {"challenge_id": challenge_id, "opponent_id": user["user_id"], "status": "pending"},
        {"$set": {"status": "active", "started_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    challenge = await db.friend_challenges.find_one({"challenge_id": challenge_id}, {"_id": 0})
    if challenge:
        await create_notification(challenge["creator_id"], "challenge_accepted", f"{user.get('name')} a accepté votre défi !", user["user_id"])
    
    return {"message": "Challenge accepted"}

# --- Leaderboard ---
@api_router.get("/social/leaderboard")
async def get_leaderboard(user: dict = Depends(get_current_user)):
    """Get friends leaderboard"""
    # Get friend ids
    friendships = await db.friendships.find({
        "$or": [{"user_id": user["user_id"]}, {"friend_id": user["user_id"]}],
        "status": "accepted"
    }, {"_id": 0}).to_list(100)
    
    user_ids = [user["user_id"]]
    for f in friendships:
        user_ids.append(f["friend_id"] if f["user_id"] == user["user_id"] else f["user_id"])
    
    # Get points for all
    leaderboard = []
    for uid in user_ids:
        u = await db.users.find_one({"user_id": uid}, {"_id": 0, "password_hash": 0})
        points_doc = await db.user_points.find_one({"user_id": uid}, {"_id": 0})
        badges_count = await db.user_badges.count_documents({"user_id": uid})
        
        if u:
            leaderboard.append({
                "user_id": uid,
                "name": u.get("name", "Utilisateur"),
                "picture": u.get("picture"),
                "total_points": points_doc.get("total_points", 0) if points_doc else 0,
                "badges_count": badges_count,
                "is_self": uid == user["user_id"]
            })
    
    # Sort by points
    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    
    # Add rank
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
    
    return {"leaderboard": leaderboard}

# --- Enhanced Leaderboards (Friends, Global, Group) ---
@api_router.get("/social/leaderboard/{leaderboard_type}")
async def get_enhanced_leaderboard(leaderboard_type: str, group_id: str = None, user: dict = Depends(get_current_user)):
    """
    Get leaderboard: 'friends', 'global', or 'group'
    For 'group' type, pass group_id as query param
    """
    leaderboard = []
    
    if leaderboard_type == "friends":
        # Friends leaderboard (existing logic)
        friendships = await db.friendships.find({
            "$or": [{"user_id": user["user_id"]}, {"friend_id": user["user_id"]}],
            "status": "accepted"
        }, {"_id": 0}).to_list(100)
        
        user_ids = [user["user_id"]]
        for f in friendships:
            user_ids.append(f["friend_id"] if f["user_id"] == user["user_id"] else f["user_id"])
            
    elif leaderboard_type == "global":
        # Get all users with points
        all_points = await db.user_points.find({}, {"_id": 0}).sort("total_points", -1).limit(100).to_list(100)
        user_ids = [p["user_id"] for p in all_points]
        # Add current user if not in list
        if user["user_id"] not in user_ids:
            user_ids.append(user["user_id"])
            
    elif leaderboard_type == "group" and group_id:
        # Get group members
        members = await db.group_members.find({"group_id": group_id}, {"_id": 0}).to_list(500)
        user_ids = [m["user_id"] for m in members]
    else:
        raise HTTPException(status_code=400, detail="Invalid leaderboard type")
    
    # Get points for all users
    for uid in user_ids:
        u = await db.users.find_one({"user_id": uid}, {"_id": 0, "password_hash": 0})
        points_doc = await db.user_points.find_one({"user_id": uid}, {"_id": 0})
        badges_count = await db.user_badges.count_documents({"user_id": uid})
        
        if u:
            leaderboard.append({
                "user_id": uid,
                "name": u.get("name", "Utilisateur"),
                "picture": u.get("picture"),
                "total_points": points_doc.get("total_points", 0) if points_doc else 0,
                "badges_count": badges_count,
                "is_self": uid == user["user_id"]
            })
    
    # Sort by points
    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    
    # Add rank
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
    
    return {"leaderboard": leaderboard, "type": leaderboard_type}

# --- Public Feed (All Users) ---
@api_router.get("/social/feed/public")
async def get_public_feed(limit: int = 50, user: dict = Depends(get_current_user)):
    """Get public feed with all users' posts"""
    posts = await db.social_posts.find(
        {"is_public": {"$ne": False}},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    result = []
    for post in posts:
        poster = await db.users.find_one({"user_id": post["user_id"]}, {"_id": 0, "password_hash": 0})
        likes_count = await db.post_likes.count_documents({"post_id": post["post_id"]})
        user_liked = await db.post_likes.find_one({"post_id": post["post_id"], "user_id": user["user_id"]}) is not None
        comments_count = await db.post_comments.count_documents({"post_id": post["post_id"]})
        
        result.append({
            **post,
            "user_name": poster.get("name") if poster else "Utilisateur",
            "user_picture": poster.get("picture") if poster else None,
            "likes_count": likes_count,
            "user_liked": user_liked,
            "comments_count": comments_count
        })
    
    return {"posts": result}

# --- Group Feed ---
@api_router.get("/social/groups/{group_id}/feed")
async def get_group_feed(group_id: str, limit: int = 50, user: dict = Depends(get_current_user)):
    """Get feed for a specific group"""
    # Check if user is member
    is_member = await db.group_members.find_one({"group_id": group_id, "user_id": user["user_id"]})
    if not is_member:
        raise HTTPException(status_code=403, detail="You must be a member to see this feed")
    
    posts = await db.social_posts.find(
        {"group_id": group_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    result = []
    for post in posts:
        poster = await db.users.find_one({"user_id": post["user_id"]}, {"_id": 0, "password_hash": 0})
        likes_count = await db.post_likes.count_documents({"post_id": post["post_id"]})
        user_liked = await db.post_likes.find_one({"post_id": post["post_id"], "user_id": user["user_id"]}) is not None
        comments_count = await db.post_comments.count_documents({"post_id": post["post_id"]})
        
        result.append({
            **post,
            "user_name": poster.get("name") if poster else "Utilisateur",
            "user_picture": poster.get("picture") if poster else None,
            "likes_count": likes_count,
            "user_liked": user_liked,
            "comments_count": comments_count
        })
    
    return {"posts": result, "group_id": group_id}

# --- Enhanced Post Creation with Image Support ---
@api_router.post("/social/post")
async def create_post(data: dict, user: dict = Depends(get_current_user)):
    """Create a new post with optional image and group_id"""
    content = data.get("content", "").strip()
    image_url = data.get("image_url")  # Base64 or URL
    image_base64 = data.get("image_base64")  # Direct base64 data
    post_type = data.get("type", "text")  # text, image, share_program, share_recipe
    group_id = data.get("group_id")  # If posting to a group
    shared_item = data.get("shared_item")  # For sharing programs/recipes
    is_public = data.get("is_public", True)
    
    if not content and not image_url and not image_base64 and not shared_item:
        raise HTTPException(status_code=400, detail="Content, image or shared item required")
    
    # If posting to a group, verify membership
    if group_id:
        is_member = await db.group_members.find_one({"group_id": group_id, "user_id": user["user_id"]})
        if not is_member:
            raise HTTPException(status_code=403, detail="You must be a member to post in this group")
    
    post = {
        "post_id": f"post_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "content": content,
        "type": post_type,
        "image_url": image_url,
        "image_base64": image_base64,
        "group_id": group_id,
        "shared_item": shared_item,
        "is_public": is_public if not group_id else False,  # Group posts are private
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.social_posts.insert_one(post)
    
    # Award points for posting
    await db.user_points.update_one(
        {"user_id": user["user_id"]},
        {"$inc": {"total_points": 5}, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"message": "Post created", "post": {k: v for k, v in post.items() if k != "_id"}}

# --- Upload Image for Post ---
@api_router.post("/social/upload-image")
async def upload_post_image(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload an image for a post, returns base64 data"""
    contents = await file.read()
    
    # Check file size (max 5MB)
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
    
    # Convert to base64
    image_base64 = base64.b64encode(contents).decode()
    content_type = file.content_type or "image/jpeg"
    
    # Return data URL
    data_url = f"data:{content_type};base64,{image_base64}"
    
    return {"image_url": data_url}

# --- Post Comments ---
@api_router.get("/social/post/{post_id}/comments")
async def get_post_comments(post_id: str, user: dict = Depends(get_current_user)):
    """Get comments for a post"""
    comments = await db.post_comments.find(
        {"post_id": post_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    result = []
    for comment in comments:
        commenter = await db.users.find_one({"user_id": comment["user_id"]}, {"_id": 0, "password_hash": 0})
        result.append({
            **comment,
            "user_name": commenter.get("name") if commenter else "Utilisateur",
            "user_picture": commenter.get("picture") if commenter else None
        })
    
    return {"comments": result}

@api_router.post("/social/post/{post_id}/comment")
async def add_comment(post_id: str, data: dict, user: dict = Depends(get_current_user)):
    """Add a comment to a post"""
    content = data.get("content", "").strip()
    
    if not content:
        raise HTTPException(status_code=400, detail="Content required")
    
    # Verify post exists
    post = await db.social_posts.find_one({"post_id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comment = {
        "comment_id": f"cmt_{uuid.uuid4().hex[:8]}",
        "post_id": post_id,
        "user_id": user["user_id"],
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.post_comments.insert_one(comment)
    
    # Notify post owner
    if post["user_id"] != user["user_id"]:
        await create_notification(post["user_id"], "comment", f"{user.get('name', 'Quelquun')} a commenté votre publication", user["user_id"])
    
    return {"message": "Comment added", "comment": {k: v for k, v in comment.items() if k != "_id"}}

# --- Like Posts ---
@api_router.post("/social/post/{post_id}/like")
async def like_post(post_id: str, user: dict = Depends(get_current_user)):
    """Like or unlike a post"""
    existing = await db.post_likes.find_one({"post_id": post_id, "user_id": user["user_id"]})
    
    if existing:
        # Unlike
        await db.post_likes.delete_one({"post_id": post_id, "user_id": user["user_id"]})
        return {"message": "Post unliked", "liked": False}
    else:
        # Like
        await db.post_likes.insert_one({
            "post_id": post_id,
            "user_id": user["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Notify post owner
        post = await db.social_posts.find_one({"post_id": post_id})
        if post and post["user_id"] != user["user_id"]:
            await create_notification(post["user_id"], "like", f"{user.get('name', 'Quelquun')} aime votre publication", user["user_id"])
        
        return {"message": "Post liked", "liked": True}

# --- Share Program to Community ---
@api_router.post("/social/share/program")
async def share_program(data: dict, user: dict = Depends(get_current_user)):
    """Share a workout program to community feed"""
    program = data.get("program")
    group_id = data.get("group_id")  # Optional - share to group
    message = data.get("message", "")
    
    if not program:
        raise HTTPException(status_code=400, detail="Program required")
    
    content = f"💪 Je partage mon programme d'entraînement: {program.get('name', 'Programme personnalisé')}"
    if message:
        content = f"{message}\n\n{content}"
    
    post = {
        "post_id": f"post_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "content": content,
        "type": "share_program",
        "shared_item": program,
        "group_id": group_id,
        "is_public": not group_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.social_posts.insert_one(post)
    
    return {"message": "Program shared", "post_id": post["post_id"]}

# --- Share Recipe to Community ---
@api_router.post("/social/share/recipe")
async def share_recipe(data: dict, user: dict = Depends(get_current_user)):
    """Share a recipe to community feed"""
    recipe = data.get("recipe")
    group_id = data.get("group_id")  # Optional - share to group
    message = data.get("message", "")
    
    if not recipe:
        raise HTTPException(status_code=400, detail="Recipe required")
    
    content = f"🍳 Je partage ma recette: {recipe.get('name', 'Recette')}"
    if message:
        content = f"{message}\n\n{content}"
    
    post = {
        "post_id": f"post_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "content": content,
        "type": "share_recipe",
        "shared_item": recipe,
        "group_id": group_id,
        "is_public": not group_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.social_posts.insert_one(post)
    
    return {"message": "Recipe shared", "post_id": post["post_id"]}

# --- Group Daily Challenges ---
@api_router.get("/social/groups/{group_id}/challenge")
async def get_group_daily_challenge(group_id: str, user: dict = Depends(get_current_user)):
    """Get today's challenge for a group"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Check if user is member
    is_member = await db.group_members.find_one({"group_id": group_id, "user_id": user["user_id"]})
    if not is_member:
        raise HTTPException(status_code=403, detail="You must be a member")
    
    # Get or create today's challenge
    challenge = await db.group_challenges.find_one({"group_id": group_id, "date": today}, {"_id": 0})
    
    if not challenge:
        # Generate a random challenge
        challenges_pool = [
            {"type": "steps", "target": 10000, "description": "🚶 Marcher 10 000 pas", "points": 50},
            {"type": "workout", "target": 1, "description": "💪 Faire 1 séance d'entraînement", "points": 30},
            {"type": "water", "target": 8, "description": "💧 Boire 8 verres d'eau", "points": 20},
            {"type": "healthy_meal", "target": 3, "description": "🥗 Manger 3 repas sains", "points": 40},
            {"type": "stretching", "target": 1, "description": "🧘 Faire 10 min d'étirements", "points": 15},
            {"type": "meditation", "target": 1, "description": "🧠 Méditer 5 minutes", "points": 15},
            {"type": "sleep", "target": 8, "description": "😴 Dormir au moins 8h", "points": 25},
            {"type": "no_sugar", "target": 1, "description": "🍬 Journée sans sucre ajouté", "points": 35},
            {"type": "protein", "target": 100, "description": "🥩 Consommer 100g de protéines", "points": 30},
            {"type": "cardio", "target": 30, "description": "❤️ 30 min de cardio", "points": 40},
        ]
        
        random_challenge = random.choice(challenges_pool)
        challenge = {
            "challenge_id": f"gc_{uuid.uuid4().hex[:8]}",
            "group_id": group_id,
            "date": today,
            **random_challenge,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.group_challenges.insert_one(challenge)
    
    # Check if user has accepted/completed
    participation = await db.challenge_participations.find_one({
        "challenge_id": challenge["challenge_id"],
        "user_id": user["user_id"]
    }, {"_id": 0})
    
    # Count participants
    participants_count = await db.challenge_participations.count_documents({"challenge_id": challenge["challenge_id"]})
    completions_count = await db.challenge_participations.count_documents({"challenge_id": challenge["challenge_id"], "completed": True})
    
    return {
        "challenge": {k: v for k, v in challenge.items() if k != "_id"},
        "participation": participation,
        "participants_count": participants_count,
        "completions_count": completions_count
    }

@api_router.post("/social/groups/{group_id}/challenge/accept")
async def accept_group_challenge(group_id: str, user: dict = Depends(get_current_user)):
    """Accept today's group challenge"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    challenge = await db.group_challenges.find_one({"group_id": group_id, "date": today})
    if not challenge:
        raise HTTPException(status_code=404, detail="No challenge today")
    
    existing = await db.challenge_participations.find_one({
        "challenge_id": challenge["challenge_id"],
        "user_id": user["user_id"]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Already participating")
    
    await db.challenge_participations.insert_one({
        "participation_id": f"cp_{uuid.uuid4().hex[:8]}",
        "challenge_id": challenge["challenge_id"],
        "group_id": group_id,
        "user_id": user["user_id"],
        "accepted": True,
        "completed": False,
        "accepted_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Challenge accepted"}

@api_router.post("/social/groups/{group_id}/challenge/complete")
async def complete_group_challenge(group_id: str, user: dict = Depends(get_current_user)):
    """Mark group challenge as completed"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    challenge = await db.group_challenges.find_one({"group_id": group_id, "date": today})
    if not challenge:
        raise HTTPException(status_code=404, detail="No challenge today")
    
    participation = await db.challenge_participations.find_one({
        "challenge_id": challenge["challenge_id"],
        "user_id": user["user_id"]
    })
    
    if not participation:
        raise HTTPException(status_code=400, detail="You haven't accepted this challenge")
    
    if participation.get("completed"):
        raise HTTPException(status_code=400, detail="Already completed")
    
    # Mark as completed
    await db.challenge_participations.update_one(
        {"challenge_id": challenge["challenge_id"], "user_id": user["user_id"]},
        {"$set": {"completed": True, "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Award points
    points = challenge.get("points", 20)
    await db.user_points.update_one(
        {"user_id": user["user_id"]},
        {"$inc": {"total_points": points}, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"message": f"Challenge completed! +{points} points", "points_earned": points}

# --- Seed Fake Users ---
@api_router.post("/social/seed-fake-users")
async def seed_fake_users(data: dict = None, user: dict = Depends(get_current_user)):
    """Create 3798 fake users for community simulation with smart interactions"""
    target_count = data.get("count", 3798) if data else 3798
    
    # Check existing
    existing_fake = await db.users.count_documents({"is_fake": True})
    if existing_fake >= target_count:
        return {"message": f"Already have {existing_fake} fake users", "created": 0}
    
    # Extended French names for variety
    female_names = ["Marie", "Camille", "Léa", "Manon", "Emma", "Chloé", "Louise", "Jade", "Alice", "Sarah", 
                   "Julie", "Laura", "Marion", "Pauline", "Clara", "Charlotte", "Anaïs", "Océane", "Margot", "Valentine",
                   "Sophie", "Lucie", "Audrey", "Justine", "Mathilde", "Caroline", "Amélie", "Élodie", "Mélanie", "Aurélie",
                   "Céline", "Marine", "Nathalie", "Sandrine", "Virginie", "Stéphanie", "Delphine", "Isabelle", "Valérie", "Laetitia",
                   "Alexandra", "Christelle", "Séverine", "Morgane", "Floriane", "Élise", "Gaëlle", "Noémie", "Agathe", "Inès",
                   "Zoé", "Lola", "Romane", "Nina", "Eva", "Maëva", "Alicia", "Mélissa", "Coralie", "Cindy"]
    male_names = ["Thomas", "Lucas", "Hugo", "Maxime", "Alexandre", "Antoine", "Julien", "Nicolas", "Pierre", "Louis",
                 "Clément", "Vincent", "François", "Guillaume", "Romain", "Mathieu", "Adrien", "Quentin", "Xavier", "Florian",
                 "Sébastien", "Laurent", "Christophe", "Olivier", "Frédéric", "David", "Philippe", "Jérôme", "Benoît", "Damien",
                 "Kevin", "Jonathan", "Benjamin", "Raphaël", "Théo", "Nathan", "Léo", "Noah", "Enzo", "Mathis",
                 "Dylan", "Jordan", "Alexis", "Valentin", "Victor", "Baptiste", "Gabriel", "Arthur", "Ethan", "Paul"]
    
    last_names = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau",
                 "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier",
                 "Morel", "Girard", "André", "Mercier", "Dupont", "Lambert", "Bonnet", "François", "Martinez", "Legrand",
                 "Garnier", "Faure", "Rousseau", "Blanc", "Guerin", "Muller", "Henry", "Roussel", "Nicolas", "Perrin",
                 "Morin", "Mathieu", "Clement", "Gauthier", "Dumont", "Lopez", "Fontaine", "Chevalier", "Robin", "Masson"]
    
    avatar_base = "https://ui-avatars.com/api/?background=random&name="
    groups = ["fitness", "cardio", "nutrition", "weight_loss", "muscle_gain", "yoga"]
    objectives = ["Perdre du poids", "Gagner en muscle", "Améliorer mon endurance", "Manger plus sainement", "Être en meilleure forme"]
    
    post_contents = [
        "Super séance aujourd'hui ! 💪", "Je me sens en forme ! 🏋️", "Objectif du jour atteint ✅",
        "Petit déjeuner healthy 🥗", "Merci pour vos encouragements ! ❤️", "Nouvelle semaine, nouveaux objectifs 🎯",
        "Le sport, c'est la vie ! 🏃", "Progrès du mois, fier(e) de moi 📈", "Recette du jour : smoothie protéiné 🍓",
        "Motivation au top ! 🔥", "Jour de repos bien mérité 😴", "30 min de cardio ce matin 🚴",
        "Mes muscles me disent merci 💪", "Premier jour sans grignotage ! 🎉", "Meal prep du dimanche 🍱",
        "1kg de perdu cette semaine ! ⬇️", "Nouvelle PR au squat 🏆", "Hydratation on point 💧",
        "Je ne lâche rien ! 💯", "Semaine 4 de mon programme 📅", "Mon coach serait fier de moi 🌟",
        "Les résultats commencent à se voir 👀", "Alimentation équilibrée = énergie décuplée ⚡",
        "Marche quotidienne ✅ 10 000 pas atteints", "Stretching du soir 🧘", "Sleep is the best recovery 😴",
        "Protéines ✓ Légumes ✓ Hydratation ✓", "Batch cooking pour la semaine 🍳", "Objectif 5km en moins de 30min 🏃‍♂️",
        "Mental fort, corps fort 🧠💪", "Yoga flow du matin terminé 🙏", "Félicitations à tous pour vos efforts ! 🎊"
    ]
    
    comment_templates = [
        "Bravo ! Continue comme ça 💪", "Super motivation ! 🔥", "Tu gères ! 👏", "Félicitations ! 🎉",
        "Ça donne envie ! 😍", "Respect ! 💯", "Top ! On lâche rien 🙌", "Inspirant ! ⭐",
        "Belle performance ! 🏆", "Continue comme ça ! 👍", "Waouh impressionnant ! 😮", "Tu m'inspires ! 🌟",
        "Quel courage ! 💪", "Bravo pour ta régularité ! 📈", "On est tous avec toi ! ❤️", "Force à toi ! 💥"
    ]
    
    created = 0
    to_create = target_count - existing_fake
    female_count = int(to_create * 0.6)
    
    # Create users in batch
    batch_size = 100
    fake_user_ids = []
    
    for batch_start in range(0, to_create, batch_size):
        batch_end = min(batch_start + batch_size, to_create)
        users_batch = []
        points_batch = []
        memberships_batch = []
        
        for i in range(batch_start, batch_end):
            is_female = i < female_count
            first_name = random.choice(female_names if is_female else male_names)
            last_name = random.choice(last_names)
            name = f"{first_name} {last_name}"
            
            user_id = f"fake_{uuid.uuid4().hex[:10]}"
            fake_user_ids.append(user_id)
            
            points = random.randint(50, 8000)
            badges_count = random.randint(0, 20)
            
            fake_user = {
                "user_id": user_id,
                "email": f"{first_name.lower()}.{last_name.lower()}{random.randint(1,999)}@example.com",
                "name": name,
                "picture": f"{avatar_base}{first_name}+{last_name}",
                "onboarding_completed": True,
                "is_premium": random.random() < 0.15,
                "is_fake": True,
                "gender": "female" if is_female else "male",
                "objective": random.choice(objectives),
                "badges_count": badges_count,
                "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 365))).isoformat()
            }
            users_batch.append(fake_user)
            
            points_batch.append({
                "user_id": user_id,
                "total_points": points,
                "challenge_points": random.randint(0, points // 3),
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            
            user_groups = random.sample(groups, random.randint(1, 4))
            for group_id in user_groups:
                memberships_batch.append({
                    "group_id": group_id,
                    "user_id": user_id,
                    "joined_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180))).isoformat()
                })
        
        if users_batch:
            await db.users.insert_many(users_batch)
        if points_batch:
            await db.user_points.insert_many(points_batch)
        if memberships_batch:
            await db.group_members.insert_many(memberships_batch)
        
        created += len(users_batch)
        
        # Create posts for this batch
        posts_batch = []
        for user in users_batch:
            num_posts = random.randint(0, 5)
            for _ in range(num_posts):
                posts_batch.append({
                    "post_id": f"post_{uuid.uuid4().hex[:12]}",
                    "user_id": user["user_id"],
                    "content": random.choice(post_contents),
                    "type": "text",
                    "is_public": True,
                    "group_id": random.choice(groups) if random.random() < 0.6 else None,
                    "likes": [],
                    "comments": [],
                    "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 60), hours=random.randint(0, 23))).isoformat()
                })
        if posts_batch:
            await db.social_posts.insert_many(posts_batch)
    
    # Create friendships between fake users
    friendships_batch = []
    for i in range(min(len(fake_user_ids), 500)):
        user_id = random.choice(fake_user_ids)
        friend_id = random.choice([uid for uid in fake_user_ids if uid != user_id])
        friendships_batch.append({
            "friendship_id": f"friend_{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "friend_id": friend_id,
            "status": "accepted",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90))).isoformat()
        })
    if friendships_batch:
        await db.friendships.insert_many(friendships_batch)
    
    return {"message": f"Created {created} fake users with interactions", "created": created, "target": target_count}

@api_router.post("/social/simulate-interactions")
async def simulate_fake_interactions(user: dict = Depends(get_current_user)):
    """Simulate autonomous interactions between fake users - likes, comments, friendships"""
    # Get fake users
    fake_users = await db.users.find({"is_fake": True}, {"user_id": 1, "name": 1}).limit(500).to_list(500)
    if len(fake_users) < 10:
        return {"message": "Not enough fake users to simulate", "interactions": 0}
    
    fake_user_ids = [u["user_id"] for u in fake_users]
    
    # Get recent posts
    recent_posts = await db.social_posts.find({}, {"post_id": 1, "user_id": 1, "likes": 1}).sort("created_at", -1).limit(200).to_list(200)
    
    comment_templates = [
        "Bravo ! Continue comme ça 💪", "Super motivation ! 🔥", "Tu gères ! 👏", "Félicitations ! 🎉",
        "Ça donne envie ! 😍", "Respect ! 💯", "Top ! 🙌", "Inspirant ! ⭐", "Belle perf ! 🏆", "Continue ! 👍"
    ]
    
    interactions = 0
    
    # Add likes to posts
    for post in random.sample(recent_posts, min(50, len(recent_posts))):
        likers = random.sample(fake_user_ids, random.randint(1, min(15, len(fake_user_ids))))
        existing_likes = post.get("likes", []) or []
        new_likes = [uid for uid in likers if uid not in existing_likes]
        if new_likes:
            await db.social_posts.update_one(
                {"post_id": post["post_id"]},
                {"$addToSet": {"likes": {"$each": new_likes}}}
            )
            interactions += len(new_likes)
    
    # Add comments
    for post in random.sample(recent_posts, min(30, len(recent_posts))):
        commenter = random.choice(fake_users)
        comment = {
            "comment_id": f"cmt_{uuid.uuid4().hex[:8]}",
            "user_id": commenter["user_id"],
            "user_name": commenter["name"],
            "content": random.choice(comment_templates),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.social_posts.update_one(
            {"post_id": post["post_id"]},
            {"$push": {"comments": comment}}
        )
        interactions += 1
    
    # Create new posts from fake users
    post_contents = [
        "Super séance ! 💪", "Objectif atteint ✅", "Motivation au top ! 🔥", "On lâche rien ! 💯",
        "Nouvelle semaine, nouveaux défis 🎯", "Fier(e) de mes progrès 📈", "Le sport c'est la vie 🏃"
    ]
    
    for _ in range(random.randint(5, 15)):
        poster = random.choice(fake_users)
        post = {
            "post_id": f"post_{uuid.uuid4().hex[:12]}",
            "user_id": poster["user_id"],
            "content": random.choice(post_contents),
            "type": "text",
            "is_public": True,
            "group_id": random.choice(["fitness", "cardio", "nutrition", "weight_loss", "muscle_gain", "yoga"]) if random.random() < 0.5 else None,
            "likes": random.sample(fake_user_ids, random.randint(0, 10)),
            "comments": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.social_posts.insert_one(post)
        interactions += 1
    
    # Create new friendships
    for _ in range(random.randint(10, 30)):
        user1, user2 = random.sample(fake_user_ids, 2)
        existing = await db.friendships.find_one({"$or": [
            {"user_id": user1, "friend_id": user2},
            {"user_id": user2, "friend_id": user1}
        ]})
        if not existing:
            await db.friendships.insert_one({
                "friendship_id": f"friend_{uuid.uuid4().hex[:8]}",
                "user_id": user1,
                "friend_id": user2,
                "status": "accepted",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            interactions += 1
    
    return {"message": f"Simulated {interactions} interactions", "interactions": interactions}

@api_router.get("/social/groups")
async def get_groups(user: dict = Depends(get_current_user)):
    """Get available groups/communities"""
    # Get user's groups
    user_groups = await db.group_members.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(50)
    user_group_ids = [g["group_id"] for g in user_groups]
    
    # Get all groups
    all_groups = await db.groups.find({}, {"_id": 0}).to_list(100)
    
    result = []
    for group in all_groups:
        member_count = await db.group_members.count_documents({"group_id": group["group_id"]})
        result.append({
            **group,
            "member_count": member_count,
            "is_member": group["group_id"] in user_group_ids
        })
    
    return {"groups": result}

@api_router.get("/social/groups/{group_id}")
async def get_group_details(group_id: str, user: dict = Depends(get_current_user)):
    """Get detailed info for a specific group"""
    group = await db.groups.find_one({"group_id": group_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    is_member = await db.group_members.find_one({"group_id": group_id, "user_id": user["user_id"]}) is not None
    member_count = await db.group_members.count_documents({"group_id": group_id})
    posts_count = await db.social_posts.count_documents({"group_id": group_id})
    
    # Get recent members
    recent_members_docs = await db.group_members.find({"group_id": group_id}, {"_id": 0}).sort("joined_at", -1).limit(5).to_list(5)
    recent_members = []
    for m in recent_members_docs:
        u = await db.users.find_one({"user_id": m["user_id"]}, {"_id": 0, "password_hash": 0})
        if u:
            recent_members.append({"user_id": u["user_id"], "name": u.get("name"), "picture": u.get("picture")})
    
    return {
        "group": group,
        "is_member": is_member,
        "member_count": member_count,
        "posts_count": posts_count,
        "recent_members": recent_members
    }

@api_router.post("/social/groups/join")
async def join_group(data: dict, user: dict = Depends(get_current_user)):
    """Join a group"""
    group_id = data.get("group_id")
    
    existing = await db.group_members.find_one({"group_id": group_id, "user_id": user["user_id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Already a member")
    
    await db.group_members.insert_one({
        "group_id": group_id,
        "user_id": user["user_id"],
        "joined_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Joined group"}

@api_router.post("/social/groups/leave")
async def leave_group(data: dict, user: dict = Depends(get_current_user)):
    """Leave a group"""
    group_id = data.get("group_id")
    
    await db.group_members.delete_one({"group_id": group_id, "user_id": user["user_id"]})
    
    return {"message": "Left group"}

# Initialize default groups on startup
async def init_default_groups():
    """Create default community groups if they don't exist"""
    default_groups = [
        {"group_id": "fitness", "name": "🏋️ Fitness", "description": "Passionnés de fitness et musculation", "category": "fitness"},
        {"group_id": "cardio", "name": "🏃 Cardio", "description": "Coureurs, cyclistes et amateurs de cardio", "category": "cardio"},
        {"group_id": "nutrition", "name": "🥗 Nutrition", "description": "Conseils et astuces nutrition", "category": "nutrition"},
        {"group_id": "weight_loss", "name": "⚖️ Perte de poids", "description": "Soutien pour la perte de poids", "category": "weight"},
        {"group_id": "muscle_gain", "name": "💪 Prise de muscle", "description": "Objectif prise de masse", "category": "muscle"},
        {"group_id": "yoga", "name": "🧘 Yoga & Bien-être", "description": "Yoga, méditation et bien-être", "category": "wellness"},
    ]
    
    for group in default_groups:
        existing = await db.groups.find_one({"group_id": group["group_id"]})
        if not existing:
            group["created_at"] = datetime.now(timezone.utc).isoformat()
            await db.groups.insert_one(group)

# Call init on startup
@app.on_event("startup")
async def startup_event():
    await init_default_groups()

# Include router - MUST be after all endpoint definitions
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
