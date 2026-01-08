# Firebase Cloud Messaging - Notifications Push
import os
import logging
from typing import Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("Firebase Admin SDK not installed")

# Initialize Firebase
firebase_app = None

def init_firebase():
    """Initialize Firebase Admin SDK"""
    global firebase_app
    
    if not FIREBASE_AVAILABLE:
        logger.error("Firebase Admin SDK not available")
        return False
    
    if firebase_app:
        return True
    
    # Check for service account file
    service_account_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT', '/app/backend/firebase-service-account.json')
    
    if os.path.exists(service_account_path):
        try:
            cred = credentials.Certificate(service_account_path)
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Firebase initialization error: {e}")
            return False
    else:
        logger.warning(f"Firebase service account not found at {service_account_path}")
        return False

async def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
    image: Optional[str] = None
) -> bool:
    """Send push notification to a single device"""
    if not firebase_app:
        if not init_firebase():
            logger.error("Cannot send notification - Firebase not initialized")
            return False
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
                image=image
            ),
            data=data or {},
            token=token,
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon='/icon-192x192.png',
                    badge='/icon-96x96.png',
                    vibrate=[100, 50, 100],
                    require_interaction=True,
                    actions=[
                        messaging.WebpushNotificationAction(
                            action='open',
                            title='Ouvrir'
                        ),
                        messaging.WebpushNotificationAction(
                            action='close', 
                            title='Fermer'
                        )
                    ]
                ),
                fcm_options=messaging.WebpushFCMOptions(
                    link='/dashboard'
                )
            )
        )
        
        response = messaging.send(message)
        logger.info(f"Notification sent successfully: {response}")
        return True
        
    except messaging.UnregisteredError:
        logger.warning(f"Token unregistered: {token[:20]}...")
        return False
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False

async def send_push_to_multiple(
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[dict] = None
) -> dict:
    """Send push notification to multiple devices"""
    if not firebase_app:
        if not init_firebase():
            return {"success": 0, "failure": len(tokens)}
    
    if not tokens:
        return {"success": 0, "failure": 0}
    
    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            tokens=tokens,
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon='/icon-192x192.png',
                    badge='/icon-96x96.png'
                )
            )
        )
        
        response = messaging.send_multicast(message)
        logger.info(f"Multicast sent: {response.success_count} success, {response.failure_count} failures")
        
        return {
            "success": response.success_count,
            "failure": response.failure_count
        }
        
    except Exception as e:
        logger.error(f"Error sending multicast: {e}")
        return {"success": 0, "failure": len(tokens)}

# Notification types for the app
NOTIFICATION_TYPES = {
    "welcome": {
        "title": "Bienvenue sur Fat & Slim ! 🎉",
        "body": "Commencez votre transformation dès maintenant."
    },
    "daily_reminder": {
        "title": "N'oubliez pas de vous peser ! ⚖️",
        "body": "Enregistrez votre poids pour suivre vos progrès."
    },
    "meal_reminder": {
        "title": "C'est l'heure du repas ! 🍽️",
        "body": "N'oubliez pas d'enregistrer ce que vous mangez."
    },
    "workout_reminder": {
        "title": "Prêt pour votre entraînement ? 💪",
        "body": "Une nouvelle vidéo vous attend !"
    },
    "achievement": {
        "title": "Félicitations ! 🏆",
        "body": "Vous avez débloqué un nouveau badge !"
    },
    "community": {
        "title": "Nouvelle activité 👥",
        "body": "Quelqu'un a interagi avec votre publication."
    },
    "weekly_summary": {
        "title": "Votre résumé hebdomadaire 📊",
        "body": "Découvrez vos progrès de la semaine !"
    }
}

async def send_typed_notification(
    token: str,
    notification_type: str,
    custom_data: Optional[dict] = None
) -> bool:
    """Send a predefined notification type"""
    if notification_type not in NOTIFICATION_TYPES:
        logger.error(f"Unknown notification type: {notification_type}")
        return False
    
    notif = NOTIFICATION_TYPES[notification_type]
    data = {"type": notification_type, "timestamp": datetime.now(timezone.utc).isoformat()}
    if custom_data:
        data.update(custom_data)
    
    return await send_push_notification(
        token=token,
        title=notif["title"],
        body=notif["body"],
        data=data
    )
