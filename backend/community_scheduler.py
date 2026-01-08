"""
Automated Community Scheduler
Handles automatic interactions between fake users at different times
"""
import asyncio
import random
from datetime import datetime, timezone, timedelta
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging

logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'fatslim')

# Post content templates
POST_CONTENTS_FR = [
    "Super séance aujourd'hui ! 💪", "Objectif atteint ! ✅", "Motivation au top ce matin ! 🔥",
    "On lâche rien, on continue ! 💯", "Nouvelle semaine, nouveaux défis 🎯",
    "Fier(e) de mes progrès 📈", "Le sport c'est la vie 🏃‍♀️", "Encore un pas vers mon objectif 🎯",
    "Qui est motivé(e) aujourd'hui ? 💪", "Belle journée pour bouger ! ☀️",
    "Défi du jour relevé ! 🏆", "Merci pour vos encouragements ! ❤️",
    "Petit à petit, l'oiseau fait son nid 🐦", "Chaque effort compte ! 💫",
    "Bonne ambiance au sport aujourd'hui ! 😊", "Je me sens de mieux en mieux 🌟",
    "Nouveau record personnel ! 🎉", "Ensemble on est plus forts ! 🤝",
    "Week-end actif = week-end réussi 💪", "Qui m'accompagne demain ? 🏋️",
]

COMMENT_TEMPLATES_FR = [
    "Bravo ! Continue comme ça 💪", "Super motivation ! 🔥", "Tu gères ! 👏", 
    "Félicitations ! 🎉", "Ça donne envie ! 😍", "Respect ! 💯", "Top ! 🙌", 
    "Inspirant ! ⭐", "Belle perf ! 🏆", "Continue ! 👍", "Génial ! 🌟",
    "Tu assures ! 💪", "Quelle motivation ! 🔥", "Super fier(e) de toi ! ❤️",
    "Objectif en vue ! 🎯", "Ça c'est du courage ! 💯", "Bien joué ! 👏",
    "Tu m'inspires ! ✨", "On lâche rien ! 💪", "C'est ça l'esprit ! 🙌",
]

# Groups
COMMUNITY_GROUPS = ["fitness", "cardio", "nutrition", "weight_loss", "muscle_gain", "yoga", "running", "wellness"]


async def get_db():
    """Get database connection"""
    client = AsyncIOMotorClient(MONGO_URL)
    return client[DB_NAME]


async def get_fake_users(db, limit=500):
    """Get list of fake users"""
    return await db.users.find({"is_fake": True}, {"user_id": 1, "name": 1, "avatar": 1}).limit(limit).to_list(limit)


async def create_automated_post(db, fake_users):
    """Create a new post from a random fake user"""
    if not fake_users:
        return None
    
    poster = random.choice(fake_users)
    fake_user_ids = [u["user_id"] for u in fake_users]
    
    post = {
        "post_id": f"auto_{uuid.uuid4().hex[:12]}",
        "user_id": poster["user_id"],
        "content": random.choice(POST_CONTENTS_FR),
        "type": "text",
        "is_public": True,
        "group_id": random.choice(COMMUNITY_GROUPS) if random.random() < 0.6 else None,
        "likes": random.sample(fake_user_ids, min(random.randint(3, 25), len(fake_user_ids))),
        "comments": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_automated": True
    }
    
    await db.social_posts.insert_one(post)
    logger.info(f"[AutoScheduler] Created post by {poster['name']}")
    return post


async def add_automated_comments(db, fake_users):
    """Add comments to recent posts"""
    if len(fake_users) < 5:
        return 0
    
    # Get recent posts (last 24h)
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    recent_posts = await db.social_posts.find(
        {"created_at": {"$gte": since}},
        {"post_id": 1, "comments": 1}
    ).limit(50).to_list(50)
    
    comments_added = 0
    for post in random.sample(recent_posts, min(10, len(recent_posts))):
        # Check if we should add a comment (not too many)
        existing_comments = len(post.get("comments", []) or [])
        if existing_comments > 15:
            continue
            
        commenter = random.choice(fake_users)
        comment = {
            "comment_id": f"auto_cmt_{uuid.uuid4().hex[:8]}",
            "user_id": commenter["user_id"],
            "user_name": commenter["name"],
            "content": random.choice(COMMENT_TEMPLATES_FR),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.social_posts.update_one(
            {"post_id": post["post_id"]},
            {"$push": {"comments": comment}}
        )
        comments_added += 1
    
    logger.info(f"[AutoScheduler] Added {comments_added} comments")
    return comments_added


async def add_automated_likes(db, fake_users):
    """Add likes to recent posts"""
    if len(fake_users) < 5:
        return 0
    
    fake_user_ids = [u["user_id"] for u in fake_users]
    
    # Get recent posts
    recent_posts = await db.social_posts.find(
        {},
        {"post_id": 1, "likes": 1}
    ).sort("created_at", -1).limit(100).to_list(100)
    
    likes_added = 0
    for post in random.sample(recent_posts, min(30, len(recent_posts))):
        existing_likes = post.get("likes", []) or []
        
        # Add 1-10 new likes
        potential_likers = [uid for uid in fake_user_ids if uid not in existing_likes]
        if not potential_likers:
            continue
            
        new_likers = random.sample(potential_likers, min(random.randint(1, 10), len(potential_likers)))
        
        await db.social_posts.update_one(
            {"post_id": post["post_id"]},
            {"$addToSet": {"likes": {"$each": new_likers}}}
        )
        likes_added += len(new_likers)
    
    logger.info(f"[AutoScheduler] Added {likes_added} likes")
    return likes_added


async def create_automated_friendships(db, fake_users):
    """Create friendships between fake users"""
    if len(fake_users) < 10:
        return 0
    
    fake_user_ids = [u["user_id"] for u in fake_users]
    friendships_created = 0
    
    for _ in range(random.randint(5, 20)):
        user1, user2 = random.sample(fake_user_ids, 2)
        
        existing = await db.friendships.find_one({
            "$or": [
                {"user_id": user1, "friend_id": user2},
                {"user_id": user2, "friend_id": user1}
            ]
        })
        
        if not existing:
            await db.friendships.insert_one({
                "friendship_id": f"auto_friend_{uuid.uuid4().hex[:8]}",
                "user_id": user1,
                "friend_id": user2,
                "status": "accepted",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            friendships_created += 1
    
    logger.info(f"[AutoScheduler] Created {friendships_created} friendships")
    return friendships_created


async def run_automated_interactions():
    """Main function to run all automated interactions"""
    try:
        db = await get_db()
        fake_users = await get_fake_users(db)
        
        if len(fake_users) < 10:
            logger.warning("[AutoScheduler] Not enough fake users")
            return {"status": "skipped", "reason": "not enough fake users"}
        
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "posts_created": 0,
            "comments_added": 0,
            "likes_added": 0,
            "friendships_created": 0
        }
        
        # Create 2-5 new posts
        for _ in range(random.randint(2, 5)):
            post = await create_automated_post(db, fake_users)
            if post:
                results["posts_created"] += 1
        
        # Add comments
        results["comments_added"] = await add_automated_comments(db, fake_users)
        
        # Add likes
        results["likes_added"] = await add_automated_likes(db, fake_users)
        
        # Create friendships
        results["friendships_created"] = await create_automated_friendships(db, fake_users)
        
        # Log the run
        await db.scheduler_logs.insert_one({
            "type": "community_automation",
            "results": results,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"[AutoScheduler] Completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"[AutoScheduler] Error: {e}")
        return {"status": "error", "error": str(e)}


# Function to be called by APScheduler
def run_community_automation():
    """Synchronous wrapper for the async automation"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(run_automated_interactions())
    finally:
        loop.close()
