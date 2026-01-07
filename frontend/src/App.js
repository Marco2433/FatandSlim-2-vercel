import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import "@/App.css";

// Version management
import { initVersionCheck, shouldForceRefresh, getAppVersion } from "@/utils/versionManager";

// Pages
import LandingPage from "@/pages/LandingPage";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import OnboardingPage from "@/pages/OnboardingPage";
import DashboardPage from "@/pages/DashboardPage";
import FoodScannerPage from "@/pages/FoodScannerPage";
import NutritionPage from "@/pages/NutritionPage";
import MealPlansPage from "@/pages/MealPlansPage";
import WorkoutsPage from "@/pages/WorkoutsPage";
import ProgressPage from "@/pages/ProgressPage";
import ProfilePage from "@/pages/ProfilePage";
import SocialPage from "@/pages/SocialPage";
import BariatricPage from "@/pages/BariatricPage";
import AuthCallback from "@/pages/AuthCallback";
import PrivacyPolicyPage from "@/pages/PrivacyPolicyPage";
import PremiumPage from "@/pages/PremiumPage";

// Context
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";
import { LanguageProvider } from "@/context/LanguageContext";
import { PremiumProvider } from "@/context/PremiumContext";

// Components
import { Toaster } from "@/components/ui/sonner";
import BottomNav from "@/components/BottomNav";

// Initialize version check on app load
const wasUpdated = initVersionCheck();
if (wasUpdated) {
  console.log(`[App] Application updated to v${getAppVersion()}, cache cleared`);
  // Force page reload after update to ensure fresh content
  if (shouldForceRefresh()) {
    console.log('[App] Force refreshing data from API');
  }
}

const ProtectedRoute = ({ children }) => {
  const { user, loading, isProcessingAuth } = useAuth();
  const location = useLocation();

  // Show loading while checking auth or processing OAuth
  if (loading || isProcessingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full gradient-primary" />
          <p className="text-muted-foreground">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Redirect to onboarding if not completed
  if (!user.onboarding_completed && location.pathname !== "/onboarding") {
    return <Navigate to="/onboarding" replace />;
  }

  return children;
};

const PublicRoute = ({ children }) => {
  const { user, loading, isProcessingAuth } = useAuth();

  // Show loading while checking auth or processing OAuth
  if (loading || isProcessingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full gradient-primary" />
          <p className="text-muted-foreground">Chargement...</p>
        </div>
      </div>
    );
  }

  if (user) {
    if (!user.onboarding_completed) {
      return <Navigate to="/onboarding" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

function AppRouter() {
  const location = useLocation();

  // Scroll to top on page change
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  // Check URL fragment for session_id (Google OAuth callback)
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  const showBottomNav = ['/dashboard', '/scanner', '/nutrition', '/meals', '/workouts', '/progress', '/profile'].some(
    path => location.pathname.startsWith(path)
  );

  return (
    <>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<PublicRoute><LandingPage /></PublicRoute>} />
        <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
        <Route path="/privacy" element={<PrivacyPolicyPage />} />
        <Route path="/privacy-policy" element={<PrivacyPolicyPage />} />
        
        {/* Protected routes */}
        <Route path="/onboarding" element={<ProtectedRoute><OnboardingPage /></ProtectedRoute>} />
        <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/scanner" element={<ProtectedRoute><FoodScannerPage /></ProtectedRoute>} />
        <Route path="/nutrition" element={<ProtectedRoute><NutritionPage /></ProtectedRoute>} />
        <Route path="/meals" element={<ProtectedRoute><MealPlansPage /></ProtectedRoute>} />
        <Route path="/workouts" element={<ProtectedRoute><WorkoutsPage /></ProtectedRoute>} />
        <Route path="/progress" element={<ProtectedRoute><ProgressPage /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
        <Route path="/social" element={<ProtectedRoute><SocialPage /></ProtectedRoute>} />
        <Route path="/bariatric" element={<ProtectedRoute><BariatricPage /></ProtectedRoute>} />
        
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      
      {showBottomNav && <BottomNav />}
      <Toaster position="top-center" richColors />
    </>
  );
}

function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <AuthProvider>
          <BrowserRouter>
            <AppRouter />
          </BrowserRouter>
        </AuthProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
}

export default App;
