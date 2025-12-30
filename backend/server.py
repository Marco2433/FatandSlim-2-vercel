from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Response, Request
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import base64
import jwt
import bcrypt
import httpx

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

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    goal: str
    activity_level: str
    dietary_preferences: List[str] = []
    allergies: List[str] = []
    fitness_level: str
    # New fields
    gender: Optional[str] = "male"
    health_conditions: List[str] = []
    food_likes: List[str] = []
    food_dislikes: List[str] = []
    time_constraint: Optional[str] = "moderate"
    budget: Optional[str] = "medium"
    cooking_skill: Optional[str] = "intermediate"
    meals_per_day: Optional[int] = 3

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

# ==================== FOOD & NUTRITION ENDPOINTS ====================

@api_router.post("/food/analyze")
async def analyze_food(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Analyze food image using AI vision with user profile context"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    import json
    
    # Get user profile for personalized analysis
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    contents = await file.read()
    image_base64 = base64.b64encode(contents).decode()
    
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
        else:
            raise ValueError("No JSON found in response")
            
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

@api_router.post("/food/recommend-alternatives")
async def recommend_alternatives(entry: dict, user: dict = Depends(get_current_user)):
    """Get AI recommendations for healthier alternatives - IN FRENCH"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
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
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    
    # Get plan type: daily or weekly
    plan_type = data.get("type", "weekly")
    
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
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    
    count = data.get("count", 10)
    category = data.get("category", "all")  # all, breakfast, lunch, dinner, snack
    
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
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
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
        
        return {"recipe": recipe, "query": query}
        
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
    """Get user's shopping list"""
    items = await db.shopping_list.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).to_list(200)
    return items

@api_router.post("/shopping-list")
async def add_shopping_item(data: dict, user: dict = Depends(get_current_user)):
    """Add item to shopping list"""
    item_name = data.get("item")
    quantity = data.get("quantity", "")
    category = data.get("category", "Autres")
    
    if not item_name:
        raise HTTPException(status_code=400, detail="Item name required")
    
    # Check if item already exists
    existing = await db.shopping_list.find_one({
        "user_id": user["user_id"],
        "item": item_name.lower()
    })
    
    if existing:
        # Update quantity
        await db.shopping_list.update_one(
            {"item_id": existing["item_id"]},
            {"$set": {"quantity": quantity, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        return {"message": "Item updated", "item_id": existing["item_id"]}
    
    item_doc = {
        "item_id": f"item_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "item": item_name.lower(),
        "display_name": item_name,
        "quantity": quantity,
        "category": category,
        "checked": False,
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.shopping_list.insert_one(item_doc)
    return {"message": "Item added", "item_id": item_doc["item_id"]}

@api_router.post("/shopping-list/bulk")
async def add_shopping_items_bulk(data: dict, user: dict = Depends(get_current_user)):
    """Add multiple items to shopping list"""
    items = data.get("items", [])
    added = 0
    
    for item in items:
        item_name = item.get("item") or item
        if isinstance(item_name, str) and item_name.strip():
            existing = await db.shopping_list.find_one({
                "user_id": user["user_id"],
                "item": item_name.lower()
            })
            
            if not existing:
                item_doc = {
                    "item_id": f"item_{uuid.uuid4().hex[:8]}",
                    "user_id": user["user_id"],
                    "item": item_name.lower(),
                    "display_name": item_name,
                    "quantity": item.get("quantity", "") if isinstance(item, dict) else "",
                    "category": "Ingrédients",
                    "checked": False,
                    "added_at": datetime.now(timezone.utc).isoformat()
                }
                await db.shopping_list.insert_one(item_doc)
                added += 1
    
    return {"message": f"{added} items added", "added_count": added}

@api_router.put("/shopping-list/{item_id}")
async def update_shopping_item(item_id: str, data: dict, user: dict = Depends(get_current_user)):
    """Update shopping list item (check/uncheck)"""
    update_data = {}
    if "checked" in data:
        update_data["checked"] = data["checked"]
    if "quantity" in data:
        update_data["quantity"] = data["quantity"]
    
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
    
    total = len(recipes)
    paginated = recipes[offset:offset + limit]
    
    return {
        "recipes": paginated, 
        "total": total,
        "limit": limit,
        "offset": offset,
        "stats": get_recipes_stats()
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
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    
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
    
    # If no BMI history, create from weight history
    if not history:
        weight_history = await db.weight_history.find(
            {"user_id": user["user_id"]},
            {"_id": 0}
        ).sort("date", 1).to_list(365)
        
        height_m = (profile.get("height", 170) if profile else 170) / 100
        history = [
            {
                "date": w.get("date"),
                "bmi": round(w.get("weight", 70) / (height_m ** 2), 1),
                "weight": w.get("weight")
            } for w in weight_history
        ]
    
    ideal_bmi = profile.get("ideal_bmi", 22.0) if profile else 22.0
    current_bmi = profile.get("bmi", 0) if profile else 0
    
    return {
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
    
    all_badges = [
        {"id": "first_meal", "name": "Premier repas", "description": "Enregistrez votre premier repas", "icon": "utensils"},
        {"id": "first_workout", "name": "Premier entraînement", "description": "Complétez votre premier workout", "icon": "dumbbell"},
        {"id": "week_streak", "name": "Semaine parfaite", "description": "7 jours consécutifs d'activité", "icon": "fire"},
        {"id": "weight_goal_10", "name": "10% accompli", "description": "10% de votre objectif poids atteint", "icon": "target"},
        {"id": "food_scanner", "name": "Détective nutrition", "description": "Scannez 10 aliments", "icon": "camera"},
        {"id": "meal_planner", "name": "Chef organisé", "description": "Générez votre premier plan repas", "icon": "calendar"},
    ]
    
    earned_ids = {b["badge_id"] for b in user_badges}
    
    return {
        "earned": user_badges,
        "available": [b for b in all_badges if b["id"] not in earned_ids],
        "total_earned": len(user_badges)
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
    
    # Check streak
    if "week_streak" not in existing:
        streak = await get_streak(user_id)
        if streak["current"] >= 7:
            await award_badge(user_id, "week_streak", "Semaine parfaite")

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
    
    daily_challenges = [
        {"id": "log_3_meals", "name": "3 repas logués", "description": "Enregistrez 3 repas aujourd'hui", "xp": 50, "type": "daily"},
        {"id": "drink_water", "name": "Hydratation", "description": "Buvez 8 verres d'eau", "xp": 30, "type": "daily"},
        {"id": "workout_30", "name": "30 min d'exercice", "description": "Faites 30 minutes d'exercice", "xp": 100, "type": "daily"},
        {"id": "under_calories", "name": "Objectif calories", "description": "Restez sous votre objectif calorique", "xp": 75, "type": "daily"},
    ]
    
    # Check completion status
    food_count = await db.food_logs.count_documents({"user_id": user["user_id"], "logged_at": {"$regex": f"^{today}"}})
    workout_today = await db.workout_logs.find_one({"user_id": user["user_id"], "logged_at": {"$regex": f"^{today}"}})
    
    for challenge in daily_challenges:
        if challenge["id"] == "log_3_meals":
            challenge["progress"] = min(food_count, 3)
            challenge["target"] = 3
            challenge["completed"] = food_count >= 3
        elif challenge["id"] == "workout_30":
            challenge["progress"] = workout_today.get("duration_minutes", 0) if workout_today else 0
            challenge["target"] = 30
            challenge["completed"] = (workout_today.get("duration_minutes", 0) if workout_today else 0) >= 30
        else:
            challenge["progress"] = 0
            challenge["target"] = 1
            challenge["completed"] = False
    
    return {"daily": daily_challenges, "weekly": []}

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

# Include router
app.include_router(api_router)

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
