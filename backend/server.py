from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Response, Request
from fastapi.responses import JSONResponse
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

ROOT_DIR = Path(__file__).parent
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
    # Calculate BMI
    height_m = data.height / 100
    bmi = round(data.weight / (height_m ** 2), 1)
    
    # Calculate daily calorie target based on goal
    bmr = 10 * data.weight + 6.25 * data.height - 5 * data.age
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    tdee = bmr * activity_multipliers.get(data.activity_level, 1.55)
    
    calorie_target = tdee
    if data.goal == "lose_weight":
        calorie_target = tdee - 500
    elif data.goal == "gain_muscle":
        calorie_target = tdee + 300
    
    profile_doc = {
        "user_id": user["user_id"],
        "age": data.age,
        "height": data.height,
        "weight": data.weight,
        "target_weight": data.target_weight,
        "bmi": bmi,
        "goal": data.goal,
        "activity_level": data.activity_level,
        "dietary_preferences": data.dietary_preferences,
        "allergies": data.allergies,
        "fitness_level": data.fitness_level,
        "daily_calorie_target": round(calorie_target),
        "daily_protein_target": round(data.weight * 1.6),
        "daily_carbs_target": round(calorie_target * 0.45 / 4),
        "daily_fat_target": round(calorie_target * 0.25 / 9),
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
        "date": datetime.now(timezone.utc).isoformat(),
        "entry_id": f"weight_{uuid.uuid4().hex[:8]}"
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
    """Analyze food image using AI vision"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    import json
    
    contents = await file.read()
    image_base64 = base64.b64encode(contents).decode()
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"food_analysis_{uuid.uuid4().hex[:8]}",
            system_message="""You are a nutrition expert AI. Analyze the food image and provide:
1. Food name/description
2. Estimated calories (per serving)
3. Estimated protein (g)
4. Estimated carbs (g)
5. Estimated fat (g)
6. Nutri-Score (A-E based on nutritional quality)
7. Health tips

Respond ONLY in JSON format:
{
    "food_name": "string",
    "calories": number,
    "protein": number,
    "carbs": number,
    "fat": number,
    "nutri_score": "A-E",
    "serving_size": "string",
    "health_tips": ["string"],
    "ingredients_detected": ["string"]
}"""
        ).with_model("openai", "gpt-5.2")
        
        image_content = ImageContent(image_base64=image_base64)
        user_message = UserMessage(
            text="Analyze this food image and provide nutritional information in JSON format.",
            image_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        
        # Parse JSON from response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            result = json.loads(response[json_start:json_end])
        else:
            raise ValueError("No JSON in response")
    except Exception as e:
        logger.error(f"AI food analysis error: {e}")
        # Return default values if AI fails
        result = {
            "food_name": "Aliment non reconnu",
            "calories": 250,
            "protein": 10,
            "carbs": 30,
            "fat": 10,
            "nutri_score": "C",
            "serving_size": "1 portion",
            "health_tips": ["Essayez avec une photo plus claire", "Assurez-vous que l'aliment est bien visible"],
            "ingredients_detected": []
        }
    
    return result

@api_router.post("/food/log")
async def log_food(entry: FoodLogEntry, user: dict = Depends(get_current_user)):
    log_doc = {
        "entry_id": f"food_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        **entry.model_dump(),
        "logged_at": datetime.now(timezone.utc).isoformat()
    }
    await db.food_logs.insert_one(log_doc)
    return {"message": "Food logged", "entry_id": log_doc["entry_id"]}

@api_router.get("/food/logs")
async def get_food_logs(date: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"user_id": user["user_id"]}
    if date:
        query["logged_at"] = {"$regex": f"^{date}"}
    
    logs = await db.food_logs.find(query, {"_id": 0}).sort("logged_at", -1).to_list(100)
    return logs

@api_router.get("/food/daily-summary")
async def get_daily_summary(date: Optional[str] = None, user: dict = Depends(get_current_user)):
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
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

# ==================== MEAL PLANS ENDPOINTS ====================

@api_router.post("/meals/generate")
async def generate_meal_plan(user: dict = Depends(get_current_user)):
    """Generate AI-powered meal plan based on user profile"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"meal_plan_{uuid.uuid4().hex[:8]}",
            system_message="""You are a professional nutritionist. Create personalized meal plans.
Respond ONLY in JSON format with a 7-day meal plan:
{
    "days": [
        {
            "day": "Monday",
            "meals": {
                "breakfast": {"name": "string", "calories": number, "protein": number, "carbs": number, "fat": number, "recipe": "string"},
                "lunch": {"name": "string", "calories": number, "protein": number, "carbs": number, "fat": number, "recipe": "string"},
                "dinner": {"name": "string", "calories": number, "protein": number, "carbs": number, "fat": number, "recipe": "string"},
                "snacks": [{"name": "string", "calories": number}]
            },
            "total_calories": number
        }
    ],
    "shopping_list": ["string"],
    "tips": ["string"]
}"""
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""Create a weekly meal plan for:
- Daily calorie target: {profile.get('daily_calorie_target', 2000)} kcal
- Goal: {profile.get('goal', 'maintain')}
- Dietary preferences: {', '.join(profile.get('dietary_preferences', [])) or 'None'}
- Allergies/restrictions: {', '.join(profile.get('allergies', [])) or 'None'}
- Activity level: {profile.get('activity_level', 'moderate')}

Create balanced, delicious meals that are easy to prepare. Return JSON only."""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        meal_plan = json.loads(response[json_start:json_end])
    except Exception as e:
        logger.error(f"AI meal plan error: {e}")
        # Return a fallback meal plan
        meal_plan = {
            "days": [
                {
                    "day": day,
                    "meals": {
                        "breakfast": {"name": "Petit-déjeuner équilibré", "calories": 400, "protein": 20, "carbs": 50, "fat": 15, "recipe": "Préparation simple et rapide"},
                        "lunch": {"name": "Déjeuner complet", "calories": 600, "protein": 35, "carbs": 60, "fat": 20, "recipe": "Repas équilibré"},
                        "dinner": {"name": "Dîner léger", "calories": 500, "protein": 30, "carbs": 45, "fat": 18, "recipe": "Préparation facile"},
                        "snacks": [{"name": "Collation saine", "calories": 150}]
                    },
                    "total_calories": 1650
                } for day in ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
            ],
            "shopping_list": ["Fruits frais", "Légumes variés", "Protéines maigres", "Céréales complètes"],
            "tips": ["Buvez 2L d'eau par jour", "Mangez lentement", "Préparez vos repas à l'avance"]
        }
    
    # Save meal plan
    plan_doc = {
        "plan_id": f"plan_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "meal_plan": meal_plan,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.meal_plans.insert_one(plan_doc)
    
    return {"plan_id": plan_doc["plan_id"], "meal_plan": meal_plan}

@api_router.get("/meals/plans")
async def get_meal_plans(user: dict = Depends(get_current_user)):
    plans = await db.meal_plans.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    return plans

# ==================== WORKOUTS ENDPOINTS ====================

@api_router.post("/workouts/generate")
async def generate_workout(user: dict = Depends(get_current_user)):
    """Generate AI-powered workout plan"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"workout_{uuid.uuid4().hex[:8]}",
        system_message="""You are a professional fitness coach. Create personalized workout plans.
Respond in JSON format:
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
    ).with_model("openai", "gpt-5.2")
    
    prompt = f"""Create a weekly workout program for:
- Fitness level: {profile.get('fitness_level', 'beginner')}
- Goal: {profile.get('goal', 'general_fitness')}
- Activity level: {profile.get('activity_level', 'moderate')}
- Weight: {profile.get('weight', 70)} kg

Create effective, progressive workouts that can be done at home or gym."""
    
    response = await chat.send_message(UserMessage(text=prompt))
    
    import json
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        workout_plan = json.loads(response[json_start:json_end])
    except:
        workout_plan = {"error": "Failed to generate workout", "raw": response[:500]}
    
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
    weight_doc = {
        "entry_id": f"weight_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "weight": entry.weight,
        "date": entry.date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "logged_at": datetime.now(timezone.utc).isoformat()
    }
    await db.weight_history.insert_one(weight_doc)
    
    # Update profile current weight
    await db.user_profiles.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"weight": entry.weight, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Weight logged", "entry_id": weight_doc["entry_id"]}

@api_router.get("/progress/weight")
async def get_weight_history(user: dict = Depends(get_current_user)):
    history = await db.weight_history.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("date", 1).to_list(365)
    return history

@api_router.get("/progress/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    profile = await db.user_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    # Get this week's data
    today = datetime.now(timezone.utc)
    week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    
    food_logs = await db.food_logs.find(
        {"user_id": user["user_id"], "logged_at": {"$gte": week_start}},
        {"_id": 0}
    ).to_list(500)
    
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
    
    current_weight = profile.get("weight", 0) if profile else 0
    target_weight = profile.get("target_weight", 0) if profile else 0
    start_weight = weight_history[-1]["weight"] if weight_history else current_weight
    
    # Get streak
    streak = await get_streak(user["user_id"])
    
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
        "streak": streak,
        "daily_targets": {
            "calories": profile.get("daily_calorie_target", 2000) if profile else 2000,
            "protein": profile.get("daily_protein_target", 100) if profile else 100,
            "carbs": profile.get("daily_carbs_target", 250) if profile else 250,
            "fat": profile.get("daily_fat_target", 65) if profile else 65
        }
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

# Include router
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
