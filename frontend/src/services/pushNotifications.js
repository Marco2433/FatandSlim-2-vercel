// Firebase Cloud Messaging - Push Notifications Service
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

const API = process.env.REACT_APP_BACKEND_URL;

// Firebase configuration
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY || "AIzaSyCDLwpNEGx-Z7k3kWv_rgD_27Gud8y0ABo",
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN || "fatslim-8d2c9.firebaseapp.com",
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID || "fatslim-8d2c9",
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET || "fatslim-8d2c9.firebasestorage.app",
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID || "188523032690",
  appId: process.env.REACT_APP_FIREBASE_APP_ID || "1:188523032690:web:86f958696abb2a9d9dd2eb"
};

let app = null;
let messaging = null;

/**
 * Initialize Firebase
 */
export const initializeFirebase = () => {
  try {
    if (!app) {
      app = initializeApp(firebaseConfig);
      console.log('[Push] Firebase initialized');
    }
    
    if (!messaging && 'Notification' in window) {
      messaging = getMessaging(app);
      console.log('[Push] Messaging initialized');
    }
    
    return true;
  } catch (error) {
    console.error('[Push] Firebase initialization error:', error);
    return false;
  }
};

/**
 * Check if push notifications are supported
 */
export const isPushSupported = () => {
  return 'Notification' in window && 
         'serviceWorker' in navigator && 
         'PushManager' in window;
};

/**
 * Get current permission status
 */
export const getPermissionStatus = () => {
  if (!('Notification' in window)) return 'unsupported';
  return Notification.permission; // 'granted', 'denied', 'default'
};

/**
 * Request notification permission and get FCM token
 */
export const requestPushPermission = async () => {
  if (!isPushSupported()) {
    console.log('[Push] Push notifications not supported');
    return { success: false, error: 'Push notifications not supported' };
  }
  
  try {
    // Request permission
    const permission = await Notification.requestPermission();
    console.log('[Push] Permission:', permission);
    
    if (permission !== 'granted') {
      return { success: false, error: 'Permission denied' };
    }
    
    // Initialize Firebase if not done
    if (!messaging) {
      initializeFirebase();
    }
    
    if (!messaging) {
      return { success: false, error: 'Messaging not initialized' };
    }
    
    // Get registration token
    // VAPID key from Firebase Console > Project Settings > Cloud Messaging
    const vapidKey = process.env.REACT_APP_FIREBASE_VAPID_KEY || 'wM82C8AiRfk7nL9e09KaBtmVZCa5plbtpHYvSmrOjWU';
    
    const token = await getToken(messaging, {
      vapidKey: vapidKey,
      serviceWorkerRegistration: await navigator.serviceWorker.ready
    });
    
    console.log('[Push] FCM Token:', token);
    
    // Save token to backend
    await saveTokenToServer(token);
    
    return { success: true, token };
    
  } catch (error) {
    console.error('[Push] Error requesting permission:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Save FCM token to backend
 */
export const saveTokenToServer = async (token) => {
  try {
    const response = await fetch(`${API}/api/notifications/register-token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ token })
    });
    
    if (!response.ok) {
      throw new Error('Failed to save token');
    }
    
    console.log('[Push] Token saved to server');
    return true;
  } catch (error) {
    console.error('[Push] Error saving token:', error);
    return false;
  }
};

/**
 * Listen for foreground messages
 */
export const onForegroundMessage = (callback) => {
  if (!messaging) {
    initializeFirebase();
  }
  
  if (messaging) {
    return onMessage(messaging, (payload) => {
      console.log('[Push] Foreground message:', payload);
      callback(payload);
    });
  }
  
  return null;
};

/**
 * Unsubscribe from notifications
 */
export const unsubscribeFromPush = async () => {
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    
    if (subscription) {
      await subscription.unsubscribe();
      console.log('[Push] Unsubscribed');
    }
    
    // Remove token from server
    await fetch(`${API}/api/notifications/unregister-token`, {
      method: 'POST',
      credentials: 'include'
    });
    
    return true;
  } catch (error) {
    console.error('[Push] Error unsubscribing:', error);
    return false;
  }
};

export default {
  initializeFirebase,
  isPushSupported,
  getPermissionStatus,
  requestPushPermission,
  saveTokenToServer,
  onForegroundMessage,
  unsubscribeFromPush
};
