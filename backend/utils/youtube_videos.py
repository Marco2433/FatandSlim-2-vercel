"""
Workout videos database - Vidéos MP4 avec CORS activé
Lecteur HTML5 natif - Pas de liens externes
"""

import random
from datetime import datetime, timezone, timedelta

# Vidéos MP4 avec CORS activé - Sources fiables
# Ces URLs proviennent de CDN qui autorisent les requêtes cross-origin
WORKOUT_VIDEO_URLS = [
    # W3Schools sample videos - toujours disponibles
    "https://www.w3schools.com/html/mov_bbb.mp4",
    "https://www.w3schools.com/html/movie.mp4",
    # MDN sample video
    "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
]

# Video categories config
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
            "HIIT Débutant {duration} min",
            "HIIT Avancé {duration} min",
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
            "Musculation Débutant {duration} min",
            "Musculation Avancé {duration} min",
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
            "Yoga du Soir {duration} min",
            "Yoga Dynamique {duration} min",
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
            "Cardio Débutant {duration} min",
            "Cardio Intensif {duration} min",
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
            "Abdos Débutant {duration} min",
            "Abdos Challenge {duration} min",
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
            "Jambes Débutant {duration} min",
            "Fessiers Bombés {duration} min",
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
            "Bras Débutant {duration} min",
            "Bras Sans Matériel {duration} min",
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
            "Stretching Débutant {duration} min",
            "Stretching du Soir {duration} min",
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
            "Gainage Débutant {duration} min",
            "Gainage Avancé {duration} min",
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
            "Maison Débutant {duration} min",
            "Maison Intensif {duration} min",
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
            "Salle Débutant {duration} min",
            "Salle Avancé {duration} min",
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
            "Fitness Débutant {duration} min",
            "Fitness Avancé {duration} min",
        ]
    },
}

LEVELS = ["beginner", "intermediate", "expert"]
DURATIONS = [10, 15, 20, 25, 30, 35, 40, 45]

def generate_workout_videos():
    """Generate workout videos database - ~400 videos avec URLs MP4"""
    videos = []
    video_id = 1
    
    for category, config in VIDEO_CATEGORIES.items():
        titles = config["titles"]
        
        # Generate ~33 videos per category (12 categories * 33 = 396)
        for i in range(33):
            duration = DURATIONS[i % len(DURATIONS)]
            level = LEVELS[i % 3]
            title_template = titles[i % len(titles)]
            
            # Assign MP4 URL - cycle through available videos
            video_url = WORKOUT_VIDEO_URLS[i % len(WORKOUT_VIDEO_URLS)]
            
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
                "video_url": video_url,
                "description": f"Séance de {config['name'].lower()} de {duration} minutes. Niveau {level}.",
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
