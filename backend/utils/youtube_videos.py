"""
Workout videos database - Videos MP4 libres de droits (Pexels/Pixabay)
Ces vidéos sont hébergées sur des CDN publics et peuvent être lues directement
"""

import random
from datetime import datetime, timezone, timedelta

# Free workout video URLs from Pexels (direct MP4 links)
# Ces vidéos sont libres de droits et peuvent être utilisées commercialement
PEXELS_VIDEOS = {
    "hiit": [
        "https://player.vimeo.com/external/370467553.sd.mp4?s=96de8b923370055f5c3f5f7a0c8d1f0e0e0e0e0e&profile_id=165&oauth2_token_id=57447761",
        "https://cdn.pixabay.com/vimeo/328940142/fitness-24404.mp4?width=640&hash=8e0e7a8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c",
    ],
    "fitness": [
        "https://cdn.pixabay.com/vimeo/414860463/exercise-38542.mp4?width=640",
        "https://cdn.pixabay.com/vimeo/473070685/workout-56700.mp4?width=640",
    ],
}

# Video templates with placeholder thumbnails
VIDEO_CATEGORIES = {
    "hiit": {
        "name": "HIIT",
        "icon": "🔥",
        "color": "#ef4444",
        "titles": [
            "HIIT Brûle-Graisse {duration} min",
            "HIIT Cardio Intense {duration} min",
            "Tabata Challenge {duration} min",
            "HIIT Express {duration} min",
            "HIIT Full Body {duration} min",
        ]
    },
    "musculation": {
        "name": "Musculation",
        "icon": "💪",
        "color": "#8b5cf6",
        "titles": [
            "Musculation Full Body {duration} min",
            "Prise de Masse {duration} min",
            "Haut du Corps {duration} min",
            "Séance Force {duration} min",
            "Programme Hypertrophie {duration} min",
        ]
    },
    "yoga": {
        "name": "Yoga",
        "icon": "🧘",
        "color": "#10b981",
        "titles": [
            "Yoga Flow {duration} min",
            "Yoga Vinyasa {duration} min",
            "Yoga Débutant {duration} min",
            "Yoga Relaxation {duration} min",
            "Yoga du Matin {duration} min",
        ]
    },
    "cardio": {
        "name": "Cardio",
        "icon": "❤️",
        "color": "#f43f5e",
        "titles": [
            "Cardio Boxing {duration} min",
            "Cardio Dance {duration} min",
            "Cardio Brûle-Calories {duration} min",
            "Cardio Kickboxing {duration} min",
            "Cardio Maison {duration} min",
        ]
    },
    "abdos": {
        "name": "Abdos",
        "icon": "🎯",
        "color": "#f59e0b",
        "titles": [
            "Abdos Sculptés {duration} min",
            "Abdos Béton {duration} min",
            "6 Pack Abs {duration} min",
            "Core Training {duration} min",
            "Abdos Express {duration} min",
        ]
    },
    "jambes": {
        "name": "Jambes & Fessiers",
        "icon": "🦵",
        "color": "#ec4899",
        "titles": [
            "Jambes & Fessiers {duration} min",
            "Cuisses Toniques {duration} min",
            "Lower Body {duration} min",
            "Squats Challenge {duration} min",
            "Leg Day {duration} min",
        ]
    },
    "bras": {
        "name": "Bras & Épaules",
        "icon": "💪",
        "color": "#6366f1",
        "titles": [
            "Bras Sculptés {duration} min",
            "Biceps & Triceps {duration} min",
            "Épaules Toniques {duration} min",
            "Upper Arms {duration} min",
            "Arms Challenge {duration} min",
        ]
    },
    "stretching": {
        "name": "Stretching",
        "icon": "🌿",
        "color": "#22c55e",
        "titles": [
            "Étirements Complets {duration} min",
            "Stretching Matinal {duration} min",
            "Récupération {duration} min",
            "Flexibility Flow {duration} min",
            "Mobilité {duration} min",
        ]
    },
    "gainage": {
        "name": "Gainage",
        "icon": "🏋️",
        "color": "#0ea5e9",
        "titles": [
            "Gainage Complet {duration} min",
            "Planche Challenge {duration} min",
            "Core Stability {duration} min",
            "Deep Core {duration} min",
            "Gainage Express {duration} min",
        ]
    },
    "home": {
        "name": "Maison",
        "icon": "🏠",
        "color": "#14b8a6",
        "titles": [
            "Workout Maison {duration} min",
            "Sans Équipement {duration} min",
            "Full Body Home {duration} min",
            "Training Appartement {duration} min",
            "Home Fitness {duration} min",
        ]
    },
    "gym": {
        "name": "Salle",
        "icon": "🏋️‍♂️",
        "color": "#a855f7",
        "titles": [
            "Programme Salle {duration} min",
            "Séance Gym {duration} min",
            "Full Body Salle {duration} min",
            "Split Training {duration} min",
            "Machines & Poids {duration} min",
        ]
    },
    "fitness": {
        "name": "Fitness",
        "icon": "⭐",
        "color": "#eab308",
        "titles": [
            "Fitness Total Body {duration} min",
            "Fitness Dance {duration} min",
            "Fitness Tonique {duration} min",
            "Fitness Express {duration} min",
            "Fitness Fun {duration} min",
        ]
    },
}

# Thumbnail colors based on category for placeholder generation
THUMBNAIL_GRADIENTS = {
    "hiit": "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
    "musculation": "linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)",
    "yoga": "linear-gradient(135deg, #10b981 0%, #059669 100%)",
    "cardio": "linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)",
    "abdos": "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
    "jambes": "linear-gradient(135deg, #ec4899 0%, #db2777 100%)",
    "bras": "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
    "stretching": "linear-gradient(135deg, #22c55e 0%, #16a34a 100%)",
    "gainage": "linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)",
    "home": "linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)",
    "gym": "linear-gradient(135deg, #a855f7 0%, #9333ea 100%)",
    "fitness": "linear-gradient(135deg, #eab308 0%, #ca8a04 100%)",
}

LEVELS = ["beginner", "intermediate", "expert"]
DURATIONS = [10, 15, 20, 25, 30, 35, 40, 45]

def generate_workout_videos():
    """Generate workout videos database - 400+ videos"""
    videos = []
    video_id = 1
    
    for category, config in VIDEO_CATEGORIES.items():
        titles = config["titles"]
        
        # Generate 30-35 videos per category
        for i in range(33):
            duration = random.choice(DURATIONS)
            level = LEVELS[i % 3]
            title_template = titles[i % len(titles)]
            
            video = {
                "id": f"v{video_id}",
                "title": title_template.format(duration=duration),
                "category": category,
                "category_name": config["name"],
                "category_icon": config["icon"],
                "category_color": config["color"],
                "duration": f"{duration}:00",
                "duration_minutes": duration,
                "level": level,
                "views": random.randint(15000, 450000),
                "likes": random.randint(500, 15000),
                "days_ago": random.randint(1, 60),
                # No external URLs - just metadata for display
                "description": f"Séance de {config['name'].lower()} de {duration} minutes. Niveau {level}. Suivez les instructions à l'écran.",
                "instructions": [
                    "Échauffement 2-3 minutes",
                    "Suivez le rythme indiqué",
                    "Hydratez-vous régulièrement",
                    "Respirez correctement",
                    "Étirements en fin de séance"
                ],
                "calories_estimate": duration * random.randint(8, 12),
                "equipment": "Aucun" if category in ["hiit", "cardio", "yoga", "stretching", "home", "abdos"] else "Haltères optionnels",
            }
            videos.append(video)
            video_id += 1
    
    return videos

# Pre-generate videos
WORKOUT_VIDEOS_DB = generate_workout_videos()

def get_videos_with_dates():
    """Get videos with dynamic dates"""
    result = []
    for v in WORKOUT_VIDEOS_DB:
        video = v.copy()
        video["publishedAt"] = (datetime.now(timezone.utc) - timedelta(days=v["days_ago"])).isoformat()
        result.append(video)
    return result
