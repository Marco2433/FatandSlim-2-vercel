import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { useLanguage } from '@/context/LanguageContext';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
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
  Trash2,
  RefreshCw,
  Edit3,
  AlertTriangle,
  Save
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, logout, updateUser } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploadingPicture, setUploadingPicture] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [editingProfile, setEditingProfile] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/profile`, { withCredentials: true });
      setProfile(response.data);
      setEditingProfile(response.data);
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    toast.success(language === 'fr' ? 'Déconnexion réussie' : 'Successfully logged out');
    navigate('/');
  };

  const handlePictureUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Le fichier doit être une image');
      return;
    }

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
      
      setProfile(prev => ({ ...prev, picture: response.data.picture }));
      updateUser({ picture: response.data.picture });
      toast.success('Photo de profil mise à jour');
    } catch (error) {
      toast.error('Erreur lors du téléchargement');
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

  const handleSaveProfile = async () => {
    if (!editingProfile) return;
    
    setSavingProfile(true);
    try {
      // Update display name first if changed
      if (editingProfile.display_name) {
        await axios.put(`${API}/profile/name`, {
          name: editingProfile.display_name
        }, { withCredentials: true });
        updateUser({ name: editingProfile.display_name });
      }
      
      // Recalculate calories and targets based on updated profile
      const response = await axios.post(`${API}/profile/onboarding`, {
        gender: editingProfile.gender,
        age: parseInt(editingProfile.age),
        height: parseFloat(editingProfile.height),
        weight: parseFloat(editingProfile.weight),
        target_weight: parseFloat(editingProfile.target_weight),
        goal: editingProfile.goal,
        activity_level: editingProfile.activity_level,
        dietary_preferences: editingProfile.dietary_preferences || [],
        allergies: editingProfile.allergies || [],
        fitness_level: editingProfile.fitness_level || 'beginner',
        health_conditions: editingProfile.health_conditions || [],
        food_likes: editingProfile.food_likes || [],
        food_dislikes: editingProfile.food_dislikes || [],
        time_constraint: editingProfile.time_constraint || '30_minutes',
        budget: editingProfile.budget || 'moderate',
        cooking_skill: editingProfile.cooking_skill || 'intermediate',
        meals_per_day: editingProfile.meals_per_day || 3
      }, { withCredentials: true });
      
      setProfile(response.data.profile);
      setEditingProfile(response.data.profile);
      setShowSettingsDialog(false);
      toast.success('Profil mis à jour ! Vos objectifs ont été recalculés.');
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error('Erreur lors de la mise à jour: ' + (error.response?.data?.detail || 'Veuillez réessayer'));
    } finally {
      setSavingProfile(false);
    }
  };

  const handleResetQuestionnaire = async () => {
    try {
      // Use the dedicated reset endpoint
      await axios.post(`${API}/profile/reset-onboarding`, {}, { withCredentials: true });
      
      // Update user state
      updateUser({ onboarding_completed: false });
      
      setShowResetDialog(false);
      toast.success('Questionnaire réinitialisé');
      
      // Navigate to onboarding
      navigate('/onboarding');
    } catch (error) {
      toast.error('Erreur lors de la réinitialisation');
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await axios.delete(`${API}/profile/account`, { withCredentials: true });
      toast.success('Compte supprimé');
      await logout();
      navigate('/');
    } catch (error) {
      toast.error('Erreur lors de la suppression du compte');
    }
  };

  const goalLabels = {
    lose_weight: 'Perdre du poids',
    gain_muscle: 'Prendre du muscle',
    maintain: 'Maintenir ma forme',
    improve_health: 'Améliorer ma santé'
  };

  const activityLabels = {
    sedentary: 'Sédentaire',
    light: 'Légèrement actif',
    moderate: 'Modérément actif',
    active: 'Actif',
    very_active: 'Très actif'
  };

  const menuItems = [
    { icon: Bell, label: 'Notifications', action: () => toast.info('Bientôt disponible') },
    { icon: Shield, label: 'Confidentialité', action: () => toast.info('Bientôt disponible') },
    { icon: HelpCircle, label: 'Aide & Support', action: () => toast.info('Contactez-nous à support@fatandslim.app') },
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
          <h1 className="font-heading text-xl font-bold">Mon Profil</h1>
        </div>
      </header>

      <main className="p-4 space-y-4 max-w-lg mx-auto">
        {/* Profile Card */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center overflow-hidden">
                  {profile?.picture || user?.picture ? (
                    <img 
                      src={profile?.picture || user?.picture} 
                      alt="Profile" 
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <User className="w-10 h-10 text-white" />
                  )}
                </div>
                <button 
                  onClick={() => fileInputRef.current?.click()}
                  className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full bg-primary flex items-center justify-center shadow-lg"
                  disabled={uploadingPicture}
                >
                  {uploadingPicture ? (
                    <Loader2 className="w-4 h-4 text-white animate-spin" />
                  ) : (
                    <Camera className="w-4 h-4 text-white" />
                  )}
                </button>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handlePictureUpload}
                />
              </div>
              
              <div className="flex-1">
                <h2 className="font-heading text-xl font-bold">{user?.name}</h2>
                <p className="text-sm text-muted-foreground">{user?.email}</p>
              </div>
              
              <div className="flex flex-col gap-1">
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="rounded-full"
                  onClick={() => setShowSettingsDialog(true)}
                >
                  <Settings className="w-4 h-4" />
                </Button>
                {(profile?.picture || user?.picture) && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="rounded-full text-destructive hover:text-destructive"
                    onClick={handleDeletePicture}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Premium Banner */}
        <Card 
          className="border-yellow-500/30 bg-gradient-to-r from-yellow-500/10 to-orange-500/10 overflow-hidden cursor-pointer hover:border-yellow-500/50 transition-all"
          onClick={() => navigate('/premium')}
        >
          <CardContent className="p-4 relative">
            <div className="absolute top-0 right-0 w-32 h-32 bg-yellow-500/20 rounded-full blur-3xl" />
            <div className="relative flex items-center gap-4">
              <img 
                src="/premium-badge.png" 
                alt="Premium" 
                className="w-16 h-16 object-contain"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-heading font-bold text-yellow-500">
                    {user?.is_premium ? 'Vous êtes Premium !' : 'Passer Premium'}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  {user?.is_premium 
                    ? 'Gérer mon abonnement' 
                    : 'IA illimitée, recettes exclusives, programmes premium'}
                </p>
              </div>
              <ChevronRight className="w-5 h-5 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

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
                <Label htmlFor="theme-toggle">Mode sombre</Label>
              </div>
              <Switch
                id="theme-toggle"
                checked={theme === 'dark'}
                onCheckedChange={toggleTheme}
              />
            </div>
          </CardContent>
        </Card>

        {/* Language Selector */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-lg">🌐</span>
                <Label>Langue / Language</Label>
              </div>
              <div className="flex gap-2">
                <Button
                  variant={language === 'fr' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setLanguage('fr');
                    toast.success('Langue changée en Français');
                  }}
                >
                  🇫🇷 FR
                </Button>
                <Button
                  variant={language === 'en' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setLanguage('en');
                    toast.success('Language changed to English');
                  }}
                >
                  🇬🇧 EN
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Menu Items */}
        <Card>
          <CardContent className="p-0">
            {menuItems.map((item, index) => (
              <div key={item.label}>
                <button
                  onClick={item.action}
                  className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <item.icon className="w-5 h-5 text-muted-foreground" />
                    <span>{item.label}</span>
                  </div>
                  <ChevronRight className="w-5 h-5 text-muted-foreground" />
                </button>
                {index < menuItems.length - 1 && <Separator />}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Logout Button */}
        <Button 
          variant="destructive" 
          className="w-full rounded-full"
          onClick={handleLogout}
        >
          <LogOut className="w-4 h-4 mr-2" />
          Se déconnecter
        </Button>
      </main>

      {/* Settings Dialog */}
      <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Paramètres du profil
            </DialogTitle>
            <DialogDescription>
              Modifiez vos informations pour ajuster vos objectifs personnalisés
            </DialogDescription>
          </DialogHeader>

          {editingProfile && (
            <div className="space-y-4 py-4">
              {/* Name / Pseudo */}
              <div>
                <Label htmlFor="display_name">Nom / Pseudo</Label>
                <Input
                  id="display_name"
                  type="text"
                  placeholder="Votre nom ou pseudo"
                  value={editingProfile.display_name || user?.name || ''}
                  onChange={(e) => setEditingProfile(prev => ({ ...prev, display_name: e.target.value }))}
                />
                <p className="text-xs text-muted-foreground mt-1">Ce nom sera affiché dans la communauté</p>
              </div>

              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="age">Âge</Label>
                  <Input
                    id="age"
                    type="number"
                    value={editingProfile.age || ''}
                    onChange={(e) => setEditingProfile(prev => ({ ...prev, age: e.target.value }))}
                  />
                </div>
                <div>
                  <Label htmlFor="gender">Sexe</Label>
                  <Select 
                    value={editingProfile.gender || 'male'}
                    onValueChange={(value) => setEditingProfile(prev => ({ ...prev, gender: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="male">Homme</SelectItem>
                      <SelectItem value="female">Femme</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="height">Taille (cm)</Label>
                  <Input
                    id="height"
                    type="number"
                    value={editingProfile.height || ''}
                    onChange={(e) => setEditingProfile(prev => ({ ...prev, height: e.target.value }))}
                  />
                </div>
                <div>
                  <Label htmlFor="weight">Poids (kg)</Label>
                  <Input
                    id="weight"
                    type="number"
                    value={editingProfile.weight || ''}
                    onChange={(e) => setEditingProfile(prev => ({ ...prev, weight: e.target.value }))}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="target_weight">Poids objectif (kg)</Label>
                <Input
                  id="target_weight"
                  type="number"
                  value={editingProfile.target_weight || ''}
                  onChange={(e) => setEditingProfile(prev => ({ ...prev, target_weight: e.target.value }))}
                />
              </div>

              <div>
                <Label htmlFor="goal">Objectif</Label>
                <Select 
                  value={editingProfile.goal || 'maintain'}
                  onValueChange={(value) => setEditingProfile(prev => ({ ...prev, goal: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="lose_weight">Perdre du poids</SelectItem>
                    <SelectItem value="gain_muscle">Prendre du muscle</SelectItem>
                    <SelectItem value="maintain">Maintenir ma forme</SelectItem>
                    <SelectItem value="improve_health">Améliorer ma santé</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="activity">Niveau d'activité</Label>
                <Select 
                  value={editingProfile.activity_level || 'moderate'}
                  onValueChange={(value) => setEditingProfile(prev => ({ ...prev, activity_level: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sedentary">Sédentaire (peu ou pas d'exercice)</SelectItem>
                    <SelectItem value="light">Légèrement actif (1-3 jours/semaine)</SelectItem>
                    <SelectItem value="moderate">Modérément actif (3-5 jours/semaine)</SelectItem>
                    <SelectItem value="active">Actif (6-7 jours/semaine)</SelectItem>
                    <SelectItem value="very_active">Très actif (2x par jour)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              {/* Reset Questionnaire Button */}
              <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20">
                <div className="flex items-start gap-3">
                  <RefreshCw className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium text-sm">Recommencer le questionnaire</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Répondez à nouveau à toutes les questions pour recalculer vos objectifs depuis zéro
                    </p>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="mt-3 text-destructive border-destructive/50"
                      onClick={() => {
                        setShowSettingsDialog(false);
                        setShowResetDialog(true);
                      }}
                    >
                      <RefreshCw className="w-3 h-3 mr-2" />
                      Réinitialiser
                    </Button>
                  </div>
                </div>
              </div>

              {/* Delete Account Button - discret */}
              <div className="pt-4 border-t border-border/30">
                <button 
                  className="text-xs text-muted-foreground/50 hover:text-destructive transition-colors"
                  onClick={() => {
                    setShowSettingsDialog(false);
                    setShowDeleteDialog(true);
                  }}
                >
                  Supprimer mon compte
                </button>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSettingsDialog(false)}>
              Annuler
            </Button>
            <Button onClick={handleSaveProfile} disabled={savingProfile}>
              {savingProfile ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Enregistrement...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Enregistrer
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reset Confirmation Dialog */}
      <Dialog open={showResetDialog} onOpenChange={setShowResetDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="w-5 h-5" />
              Réinitialiser le questionnaire ?
            </DialogTitle>
            <DialogDescription>
              Cette action va effacer vos réponses actuelles et vous rediriger vers le questionnaire intelligent. 
              Vos données (repas, poids, favoris) seront conservées.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowResetDialog(false)}>
              Annuler
            </Button>
            <Button variant="destructive" onClick={handleResetQuestionnaire}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Réinitialiser
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Account Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <Trash2 className="w-5 h-5" />
              Supprimer définitivement le compte ?
            </DialogTitle>
            <DialogDescription>
              Cette action est IRRÉVERSIBLE. Toutes vos données seront supprimées définitivement : 
              profil, historique alimentaire, entraînements, favoris, messages, etc.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Annuler
            </Button>
            <Button variant="destructive" onClick={handleDeleteAccount}>
              <Trash2 className="w-4 h-4 mr-2" />
              Supprimer mon compte
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
