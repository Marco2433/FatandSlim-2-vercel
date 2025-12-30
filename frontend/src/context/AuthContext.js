import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Configure axios defaults for cookie handling
axios.defaults.withCredentials = true;

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isProcessingAuth, setIsProcessingAuth] = useState(false);
  const logoutInProgress = useRef(false);

  // Force logout function - clears everything locally
  const forceLogout = useCallback(() => {
    if (logoutInProgress.current) return;
    logoutInProgress.current = true;
    
    console.log('Force logout triggered');
    
    // Clear all storage
    localStorage.clear();
    sessionStorage.clear();
    
    // Clear cookies manually
    document.cookie.split(";").forEach((c) => {
      document.cookie = c
        .replace(/^ +/, "")
        .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
    });
    
    // Clear user state
    setUser(null);
    
    // Redirect to home
    window.location.href = '/';
  }, []);

  // Setup axios interceptor for 401/403 errors
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        // Handle 401 (Unauthorized) and 403 (Forbidden) errors
        if (error.response?.status === 401 || error.response?.status === 403) {
          console.warn('Auth error detected:', error.response.status);
          
          // Don't logout if we're on public pages or already logging out
          const currentPath = window.location.pathname;
          const isPublicPage = currentPath === '/login' || 
                               currentPath === '/register' || 
                               currentPath === '/' ||
                               currentPath === '/privacy' ||
                               currentPath === '/privacy-policy';
          
          if (!isPublicPage && !logoutInProgress.current) {
            console.log('Session expired or invalid, forcing logout');
            forceLogout();
          }
        }
        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, [forceLogout]);

  useEffect(() => {
    // Check if there's a session_id in URL - if so, don't check auth yet
    // The AuthCallback will handle it
    if (window.location.hash?.includes('session_id=')) {
      setLoading(false);
      setIsProcessingAuth(true);
      return;
    }
    checkAuth();
  }, []);

  const checkAuth = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        withCredentials: true,
        timeout: 10000 // 10 second timeout
      });
      setUser(response.data);
    } catch (error) {
      console.log('Auth check failed:', error.message);
      setUser(null);
      
      // Clear any stale data if auth fails
      if (error.response?.status === 401 || error.response?.status === 403) {
        localStorage.clear();
        sessionStorage.clear();
      }
    } finally {
      setLoading(false);
      setIsProcessingAuth(false);
    }
  }, []);

  const login = async (email, password) => {
    logoutInProgress.current = false;
    const response = await axios.post(`${API}/auth/login`, 
      { email, password },
      { withCredentials: true, timeout: 15000 }
    );
    setUser(response.data);
    return response.data;
  };

  const register = async (email, password, name) => {
    logoutInProgress.current = false;
    const response = await axios.post(`${API}/auth/register`,
      { email, password, name },
      { withCredentials: true, timeout: 15000 }
    );
    setUser(response.data);
    return response.data;
  };

  const loginWithGoogle = () => {
    logoutInProgress.current = false;
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const processSession = async (sessionId) => {
    logoutInProgress.current = false;
    setIsProcessingAuth(true);
    try {
      const response = await axios.post(`${API}/auth/session`,
        { session_id: sessionId },
        { withCredentials: true, timeout: 15000 }
      );
      setUser(response.data);
      setIsProcessingAuth(false);
      return response.data;
    } catch (error) {
      setIsProcessingAuth(false);
      throw error;
    }
  };

  const logout = async () => {
    if (logoutInProgress.current) return;
    logoutInProgress.current = true;
    
    // Try to call backend logout, but don't wait for it
    try {
      await Promise.race([
        axios.post(`${API}/auth/logout`, {}, { withCredentials: true }),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 3000))
      ]);
    } catch (error) {
      console.log('Backend logout failed or timed out, proceeding with local cleanup');
    }
    
    // Always clear local state regardless of backend response
    localStorage.clear();
    sessionStorage.clear();
    
    // Clear cookies manually
    document.cookie.split(";").forEach((c) => {
      document.cookie = c
        .replace(/^ +/, "")
        .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
    });
    
    // Clear user state
    setUser(null);
    
    // Force reload to clear any cached data
    window.location.href = '/';
  };

  const updateUser = (updates) => {
    setUser(prev => prev ? { ...prev, ...updates } : null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      isProcessingAuth,
      login,
      register,
      loginWithGoogle,
      processSession,
      logout,
      updateUser,
      checkAuth,
      forceLogout
    }}>
      {children}
    </AuthContext.Provider>
  );
};
