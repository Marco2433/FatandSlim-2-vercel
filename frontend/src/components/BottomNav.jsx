import { useLocation, useNavigate } from 'react-router-dom';
import { Home, Camera, Utensils, Dumbbell, TrendingUp, User } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';

export default function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { t } = useLanguage();

  const navItems = [
    { path: '/dashboard', icon: Home, label: t('home') },
    { path: '/scanner', icon: Camera, label: t('scanner') },
    { path: '/nutrition', icon: Utensils, label: t('nutrition') },
    { path: '/workouts', icon: Dumbbell, label: t('sport') },
    { path: '/progress', icon: TrendingUp, label: t('progress') },
  ];

  return (
    <nav 
      className="fixed bottom-0 left-0 right-0 h-16 bg-background/80 backdrop-blur-lg border-t border-border flex justify-around items-center z-50 md:hidden"
      data-testid="bottom-nav"
    >
      {navItems.map(({ path, icon: Icon, label }) => {
        const isActive = location.pathname === path;
        return (
          <button
            key={path}
            onClick={() => navigate(path)}
            data-testid={`nav-${label.toLowerCase()}`}
            className={`flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-xl transition-colors ${
              isActive 
                ? 'text-primary' 
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Icon className={`w-5 h-5 ${isActive ? 'stroke-[2.5px]' : ''}`} />
            <span className="text-xs font-medium">{label}</span>
          </button>
        );
      })}
    </nav>
  );
}
