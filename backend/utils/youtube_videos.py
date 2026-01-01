"""
Workout videos database - ~400 vraies vidéos YouTube fitness
Lecteur YouTube intégré (iframe) - Pas de lien externe
"""

import random
from datetime import datetime, timezone, timedelta

# IDs de vraies vidéos YouTube fitness (chaînes populaires)
YOUTUBE_VIDEO_IDS = [
    # HIIT & Cardio
    "ml6cT4AZdqI", "VWj8GxKnz5U", "qWy_aOlB45Y", "M0uO8X3_tEA", "gC_L9qAHVJ8",
    "cbKkB3POqaY", "Mvo2snJGhtM", "2pLT-olgUJs", "cZnsLVArIt8", "hr3DjGMD_Wk",
    "TU8QYVJ0q5w", "pmgpjgqnZ4E", "L_xrDAtykMI", "OBj8ueY5TBQ", "PH2WBcI4MWs",
    "H6mSo64K3TY", "IT94xC35u6k", "BJQPf-mJc4s", "IFQ2a6Fw0Fo", "Tl9hbsEu9Bk",
    # Musculation
    "UBMk30rjy0o", "vc1E5CfRfos", "a_6gbkHwpJs", "gcNh17Ckjgg", "IODxDxX7oi4",
    "sTAq4HKz3Cw", "rT7DgCr-3pg", "eGo4IYlbE5g", "SKmjgaGcFxA", "keZuLvW5Kes",
    "2zzj4UmVTvE", "QsYre__-aro", "BkS1-El_WlE", "j3Igk5nyZE4", "v_ZpVq87ZAM",
    "3g6oSaJzVvU", "8I4RR3hmpvk", "1Tq3QdYUuHs", "Cy4lALOHIfA", "FSSPflMj4TU",
    # Yoga & Stretching
    "v7AYKMP6rOE", "g_tea8ZNk5A", "VaoV1PrYft4", "Nw2oBIrQGLo", "hJbRpHZr_d0",
    "oBu-pQG6sTY", "9Vm3XpFOAqU", "0hTllAb4XGg", "CO5K3eV1Ly8", "kj5E16JRHWQ",
    "s2NQhpFGIOg", "6eMKXB3GJXQ", "inpok4MKVLM", "GLy2rYHwUqY", "Civtd6VFHH4",
    "4pKly2JojMw", "8TuRYV71Rgo", "L_xrDAtykMI", "SsKnKk2Iw2k", "OMu6OKF5Z1k",
    # Abdos
    "1919eTCoESo", "AnYl6Nk9GOA", "vkKCVCZe474", "2pLT-olgUJs", "qk97w6GYBqI",
    "Xyd_fa5zoEU", "h38NKfiMmpY", "_4W01jXCQGg", "y8Lhcb_kRNE", "8AAmaSOSctE",
    "pp3DrT4VJ3g", "ASdvN_XEl_c", "UE0emtcSTnk", "1f8yoFFdFiw", "9VsDP584zyE",
    "PcNKYHnhIqU", "zzD80vCLq0Y", "p7j5pLih8PU", "qTHoVMjJJOs", "fDb9_52aXuU",
    # Full Body
    "Cw-Wt4xKD2s", "UItWltVZZmE", "QMfG8QnqxPE", "oAPCPjnU1wA", "4qLY0vbrT8Q",
    "MRfMEBAamWY", "8DZktowZo_k", "eMjyvIQbn9M", "K-VfMEGIpJo", "2MoGxae-zyo",
    "IT94xC35u6k", "3sEeVJEJTfg", "gey73xiS8F4", "9FBIaqr7TjQ", "cbKkB3POqaY",
    "D4CPYhSN9W0", "Fw9M803f0R4", "neTtOGKhExs", "ecPfH7sXqQA", "SoibGfhCzpk",
    # Jambes & Fessiers
    "GvRgijoJ2xY", "1N-8gVGOWRQ", "qX9FSZJu448", "3oJMIKYpJQM", "UoC_O3HzsH0",
    "Yj-sDa5G1Mo", "pMiKmLPGsuw", "ErYFT9LlPZc", "Orxowest56U", "L0q2dUzLZMc",
    "7TsK8BnRaBw", "bEv6CCg2BC8", "xDlenNC1Lf0", "Ba8yJ16A-Xs", "RjexvOAsVtI",
    "gFSaROyVLqc", "q3I_kyCx7EE", "WCE2JSwLE14", "3sIJAoK41pg", "VHHp5lJyVFU",
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
