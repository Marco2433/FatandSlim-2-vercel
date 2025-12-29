import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { 
  User, 
  ArrowLeft,
  Moon,
  Sun,
  LogOut,
  Crown,
  Settings,
  Bell,
  Shield,
  HelpCircle,
  ChevronRight,
  Camera,
  Loader2,
  Trash2
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, logout, updateUser } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploadingPicture, setUploadingPicture] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/profile`, { withCredentials: true });
      setProfile(response.data);
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    toast.success('Déconnexion réussie');
    navigate('/');
  };

  const handlePictureUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Le fichier doit être une image');
      return;
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast.error('L\'image est trop grande (max 2MB)');
      return;
    }

    setUploadingPicture(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/profile/picture`, formData, {
        withCredentials: true,
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Update local state
      setProfile(prev => ({ ...prev, picture: response.data.picture }));
      updateUser({ picture: response.data.picture });
      toast.success('Photo de profil mise à jour');
    } catch (error) {
      console.error('Error uploading picture:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors du téléchargement');
    } finally {
      setUploadingPicture(false);
    }
  };

  const handleDeletePicture = async () => {
    try {
      await axios.delete(`${API}/profile/picture`, { withCredentials: true });
      setProfile(prev => ({ ...prev, picture: null }));
      updateUser({ picture: null });
      toast.success('Photo de profil supprimée');
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const menuItems = [
    { icon: Bell, label: 'Notifications', action: () => {} },
    { icon: Shield, label: 'Confidentialité', action: () => {} },
    { icon: HelpCircle, label: 'Aide & Support', action: () => {} },
  ];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full gradient-primary" />
        </div>
      </div>
    );
  }

  const goalLabels = {
    lose_weight: 'Perdre du poids',
    gain_muscle: 'Prendre du muscle',
    maintain: 'Maintenir ma forme',
    improve_health: 'Améliorer ma santé'
  };

  return (
    <div className="min-h-screen bg-background pb-safe" data-testid="profile-page">
      {/* Header */}
      <header className="sticky top-0 z-10 px-4 py-4 bg-background/80 backdrop-blur-lg border-b border-border">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => navigate('/dashboard')}
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <h1 className="font-heading text-xl font-bold">Profil</h1>
        </div>
      </header>

      <main className="p-4 space-y-6 pb-24">
        {/* User Info */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-2xl font-bold">
                {user?.name?.charAt(0) || 'U'}
              </div>
              <div className="flex-1">
                <h2 className="font-heading text-xl font-bold">{user?.name}</h2>
                <p className="text-sm text-muted-foreground">{user?.email}</p>
              </div>
              <Button variant="outline" size="sm" className="rounded-full">
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Premium Banner */}
        {!user?.is_premium && (
          <Card className="border-secondary/30 bg-gradient-to-r from-secondary/10 to-secondary/5 overflow-hidden">
            <CardContent className="p-6 relative">
              <div className="absolute top-0 right-0 w-32 h-32 bg-secondary/20 rounded-full blur-3xl" />
              <div className="relative">
                <div className="flex items-center gap-2 mb-2">
                  <Crown className="w-5 h-5 text-secondary" />
                  <span className="font-heading font-bold text-secondary">Premium</span>
                </div>
                <p className="text-sm text-muted-foreground mb-4">
                  Débloquez toutes les fonctionnalités avancées
                </p>
                <Button className="rounded-full shadow-glow-purple bg-secondary hover:bg-secondary/90">
                  Passer à Premium - 19,99€/mois
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats */}
        {profile && profile.goal && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="font-heading text-lg">Mes informations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-xl bg-muted/50">
                  <p className="text-xs text-muted-foreground">Âge</p>
                  <p className="font-semibold">{profile.age} ans</p>
                </div>
                <div className="p-3 rounded-xl bg-muted/50">
                  <p className="text-xs text-muted-foreground">Taille</p>
                  <p className="font-semibold">{profile.height} cm</p>
                </div>
                <div className="p-3 rounded-xl bg-muted/50">
                  <p className="text-xs text-muted-foreground">Poids</p>
                  <p className="font-semibold">{profile.weight} kg</p>
                </div>
                <div className="p-3 rounded-xl bg-muted/50">
                  <p className="text-xs text-muted-foreground">Objectif</p>
                  <p className="font-semibold">{profile.target_weight} kg</p>
                </div>
              </div>
              <div className="p-3 rounded-xl bg-primary/5 border border-primary/20">
                <p className="text-xs text-muted-foreground">Mon objectif</p>
                <p className="font-semibold text-primary">{goalLabels[profile.goal] || profile.goal}</p>
              </div>
              <div className="p-3 rounded-xl bg-muted/50">
                <p className="text-xs text-muted-foreground">Objectif calories/jour</p>
                <p className="font-semibold">{profile.daily_calorie_target} kcal</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Theme Toggle */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {theme === 'dark' ? (
                  <Moon className="w-5 h-5 text-muted-foreground" />
                ) : (
                  <Sun className="w-5 h-5 text-muted-foreground" />
                )}
                <div>
                  <Label className="font-medium">Mode sombre</Label>
                  <p className="text-xs text-muted-foreground">Activer le thème sombre</p>
                </div>
              </div>
              <Switch 
                checked={theme === 'dark'} 
                onCheckedChange={toggleTheme}
                data-testid="theme-toggle"
              />
            </div>
          </CardContent>
        </Card>

        {/* Menu Items */}
        <Card>
          <CardContent className="p-0">
            {menuItems.map((item, index) => (
              <div key={index}>
                <button
                  onClick={item.action}
                  className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <item.icon className="w-5 h-5 text-muted-foreground" />
                    <span className="font-medium">{item.label}</span>
                  </div>
                  <ChevronRight className="w-5 h-5 text-muted-foreground" />
                </button>
                {index < menuItems.length - 1 && <Separator />}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Logout */}
        <Button 
          variant="outline" 
          className="w-full rounded-full text-destructive border-destructive/50 hover:bg-destructive/10"
          onClick={handleLogout}
          data-testid="logout-btn"
        >
          <LogOut className="w-4 h-4 mr-2" />
          Déconnexion
        </Button>

        {/* App Version */}
        <p className="text-center text-xs text-muted-foreground">
          Fat & Slim v1.0.0
        </p>
      </main>
    </div>
  );
}
