// Version and cache management for PWA updates
// This file handles automatic cache clearing and data migration after app updates

const APP_VERSION = '3.2';
const DATA_SCHEMA_VERSION = 3;

// Keys to preserve during cache clear
const PRESERVED_KEYS = [
  'token',
  'user',
  'auth_token',
  'session_token',
  'user_preferences',
  'theme',
  'language',
  'onboarding_completed'
];

// Check if app was updated
export const checkAppUpdate = () => {
  const storedVersion = localStorage.getItem('app_version');
  const storedSchemaVersion = localStorage.getItem('data_schema_version');
  
  const isNewVersion = storedVersion !== APP_VERSION;
  const needsMigration = parseInt(storedSchemaVersion || '1') < DATA_SCHEMA_VERSION;
  
  if (isNewVersion || needsMigration) {
    console.log(`[Update] App updated from ${storedVersion} to ${APP_VERSION}`);
    performPostUpdateCleanup();
    return true;
  }
  
  return false;
};

// Perform cleanup after update
const performPostUpdateCleanup = () => {
  console.log('[Update] Performing post-update cleanup...');
  
  // 1. Preserve important data
  const preservedData = {};
  PRESERVED_KEYS.forEach(key => {
    const value = localStorage.getItem(key);
    if (value) {
      preservedData[key] = value;
    }
  });
  
  // 2. Clear application cache (localStorage items that aren't preserved)
  const keysToRemove = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (!PRESERVED_KEYS.includes(key) && 
        key !== 'app_version' && 
        key !== 'data_schema_version') {
      keysToRemove.push(key);
    }
  }
  keysToRemove.forEach(key => localStorage.removeItem(key));
  
  // 3. Clear sessionStorage (except auth-related)
  const sessionKeysToRemove = [];
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    if (!key.includes('auth') && !key.includes('token')) {
      sessionKeysToRemove.push(key);
    }
  }
  sessionKeysToRemove.forEach(key => sessionStorage.removeItem(key));
  
  // 4. Restore preserved data
  Object.entries(preservedData).forEach(([key, value]) => {
    localStorage.setItem(key, value);
  });
  
  // 5. Update version markers
  localStorage.setItem('app_version', APP_VERSION);
  localStorage.setItem('data_schema_version', String(DATA_SCHEMA_VERSION));
  localStorage.setItem('last_update', new Date().toISOString());
  
  // 6. Clear service worker cache if available
  if ('caches' in window) {
    caches.keys().then(names => {
      names.forEach(name => {
        // Clear API and asset caches, keep static
        if (name.includes('api') || name.includes('dynamic')) {
          caches.delete(name);
        }
      });
    });
  }
  
  // 7. Force refresh critical data flag
  sessionStorage.setItem('force_refresh', 'true');
  
  console.log('[Update] Post-update cleanup completed');
};

// Check if we need to force refresh data
export const shouldForceRefresh = () => {
  const forceRefresh = sessionStorage.getItem('force_refresh');
  if (forceRefresh === 'true') {
    sessionStorage.removeItem('force_refresh');
    return true;
  }
  return false;
};

// Get current app version
export const getAppVersion = () => APP_VERSION;

// Get data schema version
export const getDataSchemaVersion = () => DATA_SCHEMA_VERSION;

// Initialize version check on app load
export const initVersionCheck = () => {
  const wasUpdated = checkAppUpdate();
  
  // Store version if first time
  if (!localStorage.getItem('app_version')) {
    localStorage.setItem('app_version', APP_VERSION);
    localStorage.setItem('data_schema_version', String(DATA_SCHEMA_VERSION));
  }
  
  return wasUpdated;
};

export default {
  checkAppUpdate,
  shouldForceRefresh,
  getAppVersion,
  getDataSchemaVersion,
  initVersionCheck
};
