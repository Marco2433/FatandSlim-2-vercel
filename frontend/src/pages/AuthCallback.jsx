import { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';

export default function AuthCallback() {
  const navigate = useNavigate();
  const location = useLocation();
  const { processSession } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Prevent double processing in StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      try {
        // Extract session_id from URL fragment
        const hash = location.hash;
        const sessionId = new URLSearchParams(hash.replace('#', '?')).get('session_id');

        if (!sessionId) {
          toast.error('Session invalide');
          navigate('/login');
          return;
        }

        const user = await processSession(sessionId);
        toast.success('Connexion réussie !');
        
        // Clear the hash from URL
        window.history.replaceState(null, '', window.location.pathname);
        
        if (!user.onboarding_completed) {
          navigate('/onboarding', { state: { user } });
        } else {
          navigate('/dashboard', { state: { user } });
        }
      } catch (error) {
        console.error('Auth callback error:', error);
        toast.error('Erreur d\'authentification');
        navigate('/login');
      }
    };

    processAuth();
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="animate-pulse flex flex-col items-center gap-4">
        <div className="w-16 h-16 rounded-full gradient-primary" />
        <p className="text-muted-foreground">Authentification en cours...</p>
      </div>
    </div>
  );
}
