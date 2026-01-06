// Version and cache management for PWA updates
// This file handles automatic cache clearing and data migration after app updates

const APP_VERSION = '3.9.0';
const DATA_SCHEMA_VERSION = 12;

// Keys to ALWAYS preserve during cache clear (auth-critical)
const PRESERVED_KEYS = [
  'token',
  'user',
  'auth_token',
  'session_token',
  'user_preferences',
  'theme',
  'language',
  'onboarding_completed',
  'user_id',
  'profile_id'
];

// Keys to clear on update (cached data that needs refresh)
const CACHE_KEYS_TO_CLEAR = [
  'cached_recipes',
  'cached_articles',
  'cached_workouts',
  'cached_videos',
  'daily_summary',
  'challenges',
  'appointments',
  'notifications_read',
  'last_fetch_',
  'api_cache_'
];

/**
 * Check if app was updated and perform cleanup if needed
 * Returns true if an update was detected and cleanup was performed
 */
export const checkAppUpdate = () => {
  const storedVersion = localStorage.getItem('app_version');
  const storedSchemaVersion = parseInt(localStorage.getItem('data_schema_version') || '1');
  
  const isNewVersion = storedVersion !== APP_VERSION;
  const needsMigration = storedSchemaVersion < DATA_SCHEMA_VERSION;
  
  if (isNewVersion || needsMigration) {
    console.log(`[PWA Update] Detected: ${storedVersion || 'new'} → ${APP_VERSION}`);
    console.log(`[PWA Update] Schema: ${storedSchemaVersion} → ${DATA_SCHEMA_VERSION}`);
    performPostUpdateCleanup();
    return true;
  }
  
  return false;
};

/**
 * Perform targeted cleanup after update
 * Preserves auth and user prefs, clears cached data
 */
const performPostUpdateCleanup = () => {
  console.log('[PWA Update] Starting post-update cleanup...');
  
  // 1. Preserve critical data
  const preservedData = {};
  PRESERVED_KEYS.forEach(key => {
    const value = localStorage.getItem(key);
    if (value) {
      preservedData[key] = value;
    }
  });
  
  // 2. Clear specific cache keys (targeted cleanup)
  const keysToRemove = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && !PRESERVED_KEYS.includes(key) && 
        key !== 'app_version' && 
        key !== 'data_schema_version' &&
        key !== 'last_update') {
      // Check if key matches any cache pattern
      const shouldClear = CACHE_KEYS_TO_CLEAR.some(pattern => key.includes(pattern)) ||
                         key.startsWith('cache_') ||
                         key.startsWith('temp_') ||
                         key.includes('_cache');
      if (shouldClear) {
        keysToRemove.push(key);
      }
    }
  }
  
  console.log(`[PWA Update] Clearing ${keysToRemove.length} cached items`);
  keysToRemove.forEach(key => localStorage.removeItem(key));
  
  // 3. Clear sessionStorage (except auth-related)
  const sessionKeysToRemove = [];
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    if (key && !key.includes('auth') && !key.includes('token') && !key.includes('user')) {
      sessionKeysToRemove.push(key);
    }
  }
  sessionKeysToRemove.forEach(key => sessionStorage.removeItem(key));
  
  // 4. Restore preserved data (just in case)
  Object.entries(preservedData).forEach(([key, value]) => {
    localStorage.setItem(key, value);
  });
  
  // 5. Update version markers
  localStorage.setItem('app_version', APP_VERSION);
  localStorage.setItem('data_schema_version', String(DATA_SCHEMA_VERSION));
  localStorage.setItem('last_update', new Date().toISOString());
  
  // 6. Clear service worker caches
  clearServiceWorkerCaches();
  
  // 7. Set flag to force refresh data from API
  sessionStorage.setItem('force_refresh', 'true');
  sessionStorage.setItem('update_timestamp', Date.now().toString());
  
  console.log('[PWA Update] Post-update cleanup completed ✓');
};

/**
 * Clear service worker caches (API and dynamic content)
 */
const clearServiceWorkerCaches = async () => {
  if ('caches' in window) {
    try {
      const cacheNames = await caches.keys();
      for (const name of cacheNames) {
        // Clear API caches and dynamic content
        if (name.includes('api') || 
            name.includes('dynamic') || 
            name.includes('runtime') ||
            name.includes('workbox')) {
          await caches.delete(name);
          console.log(`[PWA Update] Cleared cache: ${name}`);
        }
      }
    } catch (error) {
      console.warn('[PWA Update] Error clearing caches:', error);
    }
  }
  
  // Unregister and re-register service worker for clean slate
  if ('serviceWorker' in navigator) {
    try {
      const registrations = await navigator.serviceWorker.getRegistrations();
      for (const registration of registrations) {
        await registration.update();
      }
    } catch (error) {
      console.warn('[PWA Update] Error updating service worker:', error);
    }
  }
};

/**
 * Check if we need to force refresh data from API
 */
export const shouldForceRefresh = () => {
  const forceRefresh = sessionStorage.getItem('force_refresh');
  if (forceRefresh === 'true') {
    sessionStorage.removeItem('force_refresh');
    return true;
  }
  return false;
};

/**
 * Get headers to bypass cache for API calls after update
 */
export const getNoCacheHeaders = () => {
  const updateTimestamp = sessionStorage.getItem('update_timestamp');
  if (updateTimestamp) {
    return {
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'X-App-Version': APP_VERSION
    };
  }
  return { 'X-App-Version': APP_VERSION };
};

/**
 * Get current app version
 */
export const getAppVersion = () => APP_VERSION;

/**
 * Get data schema version
 */
export const getDataSchemaVersion = () => DATA_SCHEMA_VERSION;

/**
 * Initialize version check on app load
 * This should be called once at app startup
 */
export const initVersionCheck = () => {
  const wasUpdated = checkAppUpdate();
  
  // Store version if first time
  if (!localStorage.getItem('app_version')) {
    localStorage.setItem('app_version', APP_VERSION);
    localStorage.setItem('data_schema_version', String(DATA_SCHEMA_VERSION));
    localStorage.setItem('first_install', new Date().toISOString());
  }
  
  return wasUpdated;
};

/**
 * Manual cache clear (for debugging or user-triggered refresh)
 */
export const manualCacheClear = async () => {
  console.log('[PWA] Manual cache clear requested');
  performPostUpdateCleanup();
  await clearServiceWorkerCaches();
  return true;
};

export default {
  checkAppUpdate,
  shouldForceRefresh,
  getNoCacheHeaders,
  getAppVersion,
  getDataSchemaVersion,
  initVersionCheck,
  manualCacheClear
};
