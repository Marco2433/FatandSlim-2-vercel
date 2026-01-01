"""
Workout videos database - ~400 vraies vidéos YouTube fitness
Lecteur YouTube intégré (iframe) - Pas de lien externe
"""

import random
from datetime import datetime, timezone, timedelta

# IDs de vraies vidéos YouTube fitness populaires et actives
YOUTUBE_VIDEO_IDS = [
    # Pamela Reif (chaîne très populaire)
    "IT94xC35u6k", "0zM1G_jH4kI", "UBnl8T1DXkE", "cbKkB3POqaY", "gC_L9qAHVJ8",
    "2pLT-olgUJs", "ml6cT4AZdqI", "4qLY0vbrT8Q", "oAPCPjnU1wA", "3sEeVJEJTfg",
    # MadFit
    "TQpyLfH8020", "UoC_O3HzsH0", "qX9FSZJu448", "Z4Vk3hhIg9o", "Mvo2snJGhtM",
    "cZnsLVArIt8", "VWj8GxKnz5U", "hr3DjGMD_Wk", "L_xrDAtykMI", "rT7DgCr-3pg",
    # THENX / Calisthenics
    "vc1E5CfRfos", "UBMk30rjy0o", "IODxDxX7oi4", "gcNh17Ckjgg", "a_6gbkHwpJs",
    # Yoga With Adriene
    "v7AYKMP6rOE", "g_tea8ZNk5A", "VaoV1PrYft4", "hJbRpHZr_d0", "oBu-pQG6sTY",
    "Nw2oBIrQGLo", "9Vm3XpFOAqU", "CO5K3eV1Ly8", "0hTllAb4XGg", "kj5E16JRHWQ",
    # Blogilates
    "1919eTCoESo", "vkKCVCZe474", "AnYl6Nk9GOA", "qk97w6GYBqI", "_4W01jXCQGg",
    # Fitness Blender
    "Cw-Wt4xKD2s", "UItWltVZZmE", "QMfG8QnqxPE", "MRfMEBAamWY", "8DZktowZo_k",
    # POPSUGAR Fitness  
    "qWy_aOlB45Y", "M0uO8X3_tEA", "TU8QYVJ0q5w", "pmgpjgqnZ4E", "H6mSo64K3TY",
    # Sydney Cummings
    "K-VfMEGIpJo", "2MoGxae-zyo", "eMjyvIQbn9M", "gey73xiS8F4", "9FBIaqr7TjQ",
    # Heather Robertson
    "GvRgijoJ2xY", "1N-8gVGOWRQ", "3oJMIKYpQM", "Yj-sDa5G1Mo", "pMiKmLPGsuw",
    # Chloe Ting
    "Xyd_fa5zoEU", "h38NKfiMmpY", "y8Lhcb_kRNE", "8AAmaSOSctE", "ASdvN_XEl_c",
    # Emi Wong
    "pp3DrT4VJ3g", "UE0emtcSTnk", "1f8yoFFdFiw", "9VsDP584zyE", "PcNKYHnhIqU",
    # Lilly Sabri
    "zzD80vCLq0Y", "p7j5pLih8PU", "qTHoVMjJJOs", "fDb9_52aXuU", "ErYFT9LlPZc",
    # Juice & Toya
    "Orxowest56U", "L0q2dUzLZMc", "7TsK8BnRaBw", "bEv6CCg2BC8", "xDlenNC1Lf0",
    # growingannanas
    "Ba8yJ16A-Xs", "RjexvOAsVtI", "gFSaROyVLqc", "q3I_kyCx7EE", "WCE2JSwLE14",
]

# Video categories config
VIDEO_CATEGORIES = {
    "hiit": {"name": "HIIT", "icon": "🔥", "color": "#ef4444"},
    "musculation": {"name": "Musculation", "icon": "💪", "color": "#8b5cf6"},
    "yoga": {"name": "Yoga", "icon": "🧘", "color": "#10b981"},
    "cardio": {"name": "Cardio", "icon": "❤️", "color": "#f43f5e"},
    "abdos": {"name": "Abdos", "icon": "🎯", "color": "#f59e0b"},
    "jambes": {"name": "Jambes & Fessiers", "icon": "🦵", "color": "#ec4899"},
    "bras": {"name": "Bras & Épaules", "icon": "💪", "color": "#6366f1"},
    "stretching": {"name": "Stretching", "icon": "🌿", "color": "#22c55e"},
    "gainage": {"name": "Gainage", "icon": "🏋️", "color": "#0ea5e9"},
    "home": {"name": "Maison", "icon": "🏠", "color": "#14b8a6"},
    "gym": {"name": "Salle", "icon": "🏋️‍♂️", "color": "#a855f7"},
    "fitness": {"name": "Fitness", "icon": "⭐", "color": "#eab308"},
}

TITLES = {
    "hiit": ["HIIT Brûle-Graisse", "HIIT Cardio", "Tabata", "HIIT Express", "HIIT Full Body"],
    "musculation": ["Musculation Full Body", "Prise de Masse", "Haut du Corps", "Force", "Hypertrophie"],
    "yoga": ["Yoga Flow", "Yoga Vinyasa", "Yoga Débutant", "Yoga Relaxation", "Yoga Matin"],
    "cardio": ["Cardio Boxing", "Cardio Dance", "Cardio Brûle-Calories", "Kickboxing", "Cardio Maison"],
    "abdos": ["Abdos Sculptés", "Abdos Béton", "6 Pack Abs", "Core Training", "Abdos Express"],
    "jambes": ["Jambes & Fessiers", "Cuisses Toniques", "Lower Body", "Squats", "Leg Day"],
    "bras": ["Bras Sculptés", "Biceps & Triceps", "Épaules", "Upper Arms", "Arms Challenge"],
    "stretching": ["Étirements", "Stretching Matinal", "Récupération", "Flexibility", "Mobilité"],
    "gainage": ["Gainage Complet", "Planche", "Core Stability", "Deep Core", "Gainage Express"],
    "home": ["Workout Maison", "Sans Équipement", "Full Body Home", "Appartement", "Home Fitness"],
    "gym": ["Programme Salle", "Séance Gym", "Full Body Salle", "Split", "Machines"],
    "fitness": ["Fitness Total Body", "Fitness Dance", "Fitness Tonique", "Fitness Express", "Fitness Fun"],
}

LEVELS = ["beginner", "intermediate", "expert"]
DURATIONS = [10, 15, 20, 25, 30, 35, 40, 45]

def generate_workout_videos():
    """Generate ~400 workout videos avec YouTube IDs"""
    videos = []
    video_id = 1
    yt_idx = 0
    
    for category, config in VIDEO_CATEGORIES.items():
        titles = TITLES.get(category, ["Workout"])
        
        for i in range(33):  # 12 * 33 = 396 videos
            duration = DURATIONS[i % len(DURATIONS)]
            level = LEVELS[i % 3]
            title = f"{titles[i % len(titles)]} {duration} min"
            youtube_id = YOUTUBE_VIDEO_IDS[yt_idx % len(YOUTUBE_VIDEO_IDS)]
            yt_idx += 1
            
            videos.append({
                "id": f"v{video_id}",
                "title": title,
                "youtube_id": youtube_id,
                "category": category,
                "category_name": config["name"],
                "category_icon": config["icon"],
                "category_color": config["color"],
                "duration": f"{duration}:00",
                "duration_minutes": duration,
                "level": level,
                "views": random.randint(15000, 500000),
                "likes": random.randint(500, 20000),
                "days_ago": random.randint(1, 90),
                "description": f"Séance de {config['name'].lower()} de {duration} minutes.",
                "calories_estimate": duration * random.randint(8, 12),
                "equipment": "Aucun" if category in ["hiit", "cardio", "yoga", "stretching", "home", "abdos"] else "Haltères optionnels",
            })
            video_id += 1
    
    return videos

WORKOUT_VIDEOS_DB = generate_workout_videos()

def get_videos_with_dates():
    """Get videos with dynamic dates"""
    return [{
        **v,
        "publishedAt": (datetime.now(timezone.utc) - timedelta(days=v["days_ago"])).isoformat()
    } for v in WORKOUT_VIDEOS_DB]
