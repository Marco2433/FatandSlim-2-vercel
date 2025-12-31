import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { 
  Flame, 
  Droplets, 
  Dumbbell, 
  Camera,
  TrendingUp,
  Trophy,
  ChevronRight,
  Zap,
  Apple,
  Target,
  Sparkles,
  Heart,
  ShoppingCart,
  Clock,
  Search,
  Loader2,
  ListPlus,
  BookOpen,
  Calendar,
  CalendarPlus,
  Pin,
  Bell,
  Award,
  X,
  MapPin,
  Edit,
  Trash2,
  AlertCircle,
  Stethoscope
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [dailySummary, setDailySummary] = useState(null);
  const [challenges, setChallenges] = useState(null);
  const [motivation, setMotivation] = useState(null);
  const [dailyRecipes, setDailyRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date().toISOString().split('T')[0]);
  
  // User stats & badges
  const [userStats, setUserStats] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  
  // Appointments
  const [appointments, setAppointments] = useState([]);
  const [todayAppointments, setTodayAppointments] = useState([]);
  const [showAppointmentDialog, setShowAppointmentDialog] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState(null);
  const [newAppointment, setNewAppointment] = useState({
    title: '',
    type: 'medical',
    date: new Date().toISOString().split('T')[0],
    time: '09:00',
    location: '',
    notes: '',
    pinned: false
  });
  
  // Smart recommendation popup
  const [showRecommendation, setShowRecommendation] = useState(false);
  const [recommendation, setRecommendation] = useState(null);
  const lastRecommendationTime = useRef(Date.now());
  const RECOMMENDATION_INTERVAL = 45 * 60 * 1000; // 45 minutes
  
  // AI Recipe Search state
  const [recipeSearchQuery, setRecipeSearchQuery] = useState('');
  const [searchedRecipe, setSearchedRecipe] = useState(null);
  const [loadingSearch, setLoadingSearch] = useState(false);

  // Check for midnight reset
  useEffect(() => {
    const checkDateChange = () => {
      const today = new Date().toISOString().split('T')[0];
      if (today !== currentDate) {
        console.log('New day detected, refreshing data...');
        setCurrentDate(today);
        setDailySummary(null);
        fetchDashboardData();
      }
    };

    const interval = setInterval(checkDateChange, 60000);
    
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        checkDateChange();
        checkRecommendationTimer();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [currentDate]);

  // Smart recommendation timer
  const checkRecommendationTimer = useCallback(async () => {
    const now = Date.now();
    if (now - lastRecommendationTime.current >= RECOMMENDATION_INTERVAL) {
      lastRecommendationTime.current = now;
      await fetchSmartRecommendation();
    }
  }, []);

  useEffect(() => {
    const interval = setInterval(checkRecommendationTimer, 60000); // Check every minute
    return () => clearInterval(interval);
  }, [checkRecommendationTimer]);

  useEffect(() => {
    fetchDashboardData();
    fetchUserStats();
    fetchAppointments();
    
    // Show recommendation after 45 minutes of first load
    const initialTimeout = setTimeout(() => {
      fetchSmartRecommendation();
    }, RECOMMENDATION_INTERVAL);
    
    return () => clearTimeout(initialTimeout);
  }, []);

  // Show today's appointments alert on load
  useEffect(() => {
    if (todayAppointments.length > 0 && !sessionStorage.getItem('todayAppointmentsShown')) {
      sessionStorage.setItem('todayAppointmentsShown', 'true');
      toast.info(`📅 Vous avez ${todayAppointments.length} rendez-vous aujourd'hui !`, {
        duration: 5000,
        action: {
          label: 'Voir',
          onClick: () => document.getElementById('appointments-section')?.scrollIntoView({ behavior: 'smooth' })
        }
      });
    }
  }, [todayAppointments]);

  const fetchDashboardData = async () => {
    const today = new Date().toISOString().split('T')[0];
    
    try {
      const [statsRes, summaryRes, challengesRes, motivationRes, recipesRes] = await Promise.allSettled([
        axios.get(`${API}/progress/stats`, { withCredentials: true }),
        axios.get(`${API}/food/daily-summary?date=${today}`, { withCredentials: true }),
        axios.get(`${API}/challenges`, { withCredentials: true }),
        axios.get(`${API}/motivation`, { withCredentials: true }),
        axios.get(`${API}/recipes/daily`, { withCredentials: true }),
      ]);
      
      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
      if (summaryRes.status === 'fulfilled') {
        const summaryData = summaryRes.value.data;
        if (summaryData.date === today) {
          setDailySummary(summaryData);
        } else {
          setDailySummary({
            date: today,
            consumed: { calories: 0, protein: 0, carbs: 0, fat: 0 },
            targets: summaryData.targets || { calories: 2000, protein: 100, carbs: 250, fat: 65 },
            remaining: summaryData.targets || { calories: 2000, protein: 100, carbs: 250, fat: 65 },
            meals_logged: 0
          });
        }
      }
      if (challengesRes.status === 'fulfilled') setChallenges(challengesRes.value.data);
      if (motivationRes.status === 'fulfilled') setMotivation(motivationRes.value.data);
      if (recipesRes.status === 'fulfilled') setDailyRecipes(recipesRes.value.data?.recipes || []);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserStats = async () => {
    try {
      const response = await axios.get(`${API}/user/stats`, { withCredentials: true });
      setUserStats(response.data);
    } catch (error) {
      console.error('Error fetching user stats:', error);
    }
  };

  const fetchAppointments = async () => {
    try {
      const [allRes, todayRes] = await Promise.allSettled([
        axios.get(`${API}/appointments`, { withCredentials: true }),
        axios.get(`${API}/appointments/today`, { withCredentials: true }),
      ]);
      
      if (allRes.status === 'fulfilled') setAppointments(allRes.value.data || []);
      if (todayRes.status === 'fulfilled') setTodayAppointments(todayRes.value.data || []);
    } catch (error) {
      console.error('Error fetching appointments:', error);
    }
  };

  const fetchSmartRecommendation = async () => {
    try {
      const response = await axios.get(`${API}/recommendations/smart`, { withCredentials: true });
      setRecommendation(response.data);
      setShowRecommendation(true);
    } catch (error) {
      console.error('Error fetching recommendation:', error);
    }
  };

  const addRecipeToFavorites = async (recipe) => {
    try {
      await axios.post(`${API}/recipes/favorites`, { recipe }, { withCredentials: true });
      toast.success('Recette ajoutée aux favoris !');
    } catch (error) {
      if (error.response?.status === 400) {
        toast.error('Recette déjà dans les favoris');
      } else {
        console.error('Error adding to favorites:', error);
        toast.error('Erreur lors de l\'ajout');
      }
    }
  };

  const addIngredientsToShoppingList = async (ingredients) => {
    if (!ingredients || ingredients.length === 0) {
      toast.error('Aucun ingrédient à ajouter');
      return;
    }
    try {
      const items = ingredients.map(i => ({ 
        item: i.item || i.name || String(i), 
        quantity: i.quantity || '' 
      })).filter(i => i.item && i.item.trim());
      
      if (items.length === 0) {
        toast.error('Aucun ingrédient valide');
        return;
      }
      
      const response = await axios.post(`${API}/shopping-list/bulk`, { items }, { withCredentials: true });
      toast.success(`${response.data.added_count || items.length} ingrédients ajoutés !`);
    } catch (error) {
      console.error('Error adding ingredients:', error);
      toast.error('Erreur lors de l\'ajout');
    }
  };

  const getNutriScoreColor = (score) => {
    const colors = {
      'A': 'bg-green-500',
      'B': 'bg-lime-500',
      'C': 'bg-yellow-500',
      'D': 'bg-orange-500',
      'E': 'bg-red-500',
    };
    return colors[score] || 'bg-gray-400';
  };

  const searchRecipeByAI = async () => {
    if (!recipeSearchQuery.trim()) {
      toast.error('Veuillez entrer une description de recette');
      return;
    }
    
    setLoadingSearch(true);
    setSearchedRecipe(null);
    
    try {
      const response = await axios.post(`${API}/recipes/search`, { 
        query: recipeSearchQuery.trim()
      }, { withCredentials: true });
      
      if (response.data.recipe) {
        setSearchedRecipe(response.data.recipe);
        toast.success('Recette trouvée !');
      } else {
        toast.error('Aucune recette générée');
      }
    } catch (error) {
      console.error('Error searching recipe:', error);
      toast.error('Erreur lors de la recherche');
    } finally {
      setLoadingSearch(false);
    }
  };

  const handleSaveAppointment = async () => {
    if (!newAppointment.title || !newAppointment.date || !newAppointment.time) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }
    
    try {
      if (editingAppointment) {
        await axios.put(`${API}/appointments/${editingAppointment.appointment_id}`, newAppointment, { withCredentials: true });
        toast.success('Rendez-vous modifié');
      } else {
        await axios.post(`${API}/appointments`, newAppointment, { withCredentials: true });
        toast.success('Rendez-vous créé');
      }
      
      setShowAppointmentDialog(false);
      setEditingAppointment(null);
      setNewAppointment({
        title: '',
        type: 'medical',
        date: new Date().toISOString().split('T')[0],
        time: '09:00',
        location: '',
        notes: '',
        pinned: false
      });
      fetchAppointments();
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde');
    }
  };

  const handleDeleteAppointment = async (appointmentId) => {
    try {
      await axios.delete(`${API}/appointments/${appointmentId}`, { withCredentials: true });
      toast.success('Rendez-vous supprimé');
      fetchAppointments();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const togglePinAppointment = async (apt) => {
    try {
      await axios.put(`${API}/appointments/${apt.appointment_id}`, { pinned: !apt.pinned }, { withCredentials: true });
      fetchAppointments();
    } catch (error) {
      toast.error('Erreur lors de l\'épinglage');
    }
  };

  const appointmentTypeLabels = {
    medical: { label: 'Médical', icon: '🏥', color: 'bg-red-100 text-red-700' },
    sport: { label: 'Sport', icon: '🏃', color: 'bg-green-100 text-green-700' },
    wellness: { label: 'Bien-être', icon: '🧘', color: 'bg-purple-100 text-purple-700' },
    nutrition: { label: 'Nutrition', icon: '🥗', color: 'bg-orange-100 text-orange-700' }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full gradient-primary" />
          <p className="text-muted-foreground">Chargement...</p>
        </div>
      </div>
    );
  }

  const calorieProgress = dailySummary 
    ? Math.min((dailySummary.consumed.calories / dailySummary.targets.calories) * 100, 100)
    : 0;

  // Sort appointments: pinned first, then today, then by date
  const sortedAppointments = [...appointments].sort((a, b) => {
    if (a.pinned && !b.pinned) return -1;
    if (!a.pinned && b.pinned) return 1;
    const today = new Date().toISOString().split('T')[0];
    if (a.date === today && b.date !== today) return -1;
    if (a.date !== today && b.date === today) return 1;
    return new Date(a.date) - new Date(b.date);
  });

  return (
    <div className="min-h-screen bg-background pb-safe" data-testid="dashboard-page">
      {/* Header */}
      <header className="sticky top-0 z-10 px-4 py-4 bg-background/80 backdrop-blur-lg border-b border-border">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-heading text-xl font-bold">
              Bonjour, {user?.name?.split(' ')[0]} 👋
            </h1>
            <p className="text-sm text-muted-foreground">
              {new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })}
            </p>
          </div>
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => navigate('/profile')}
            className="relative"
          >
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center overflow-hidden">
              {(userStats?.picture || user?.picture) ? (
                <img src={userStats?.picture || user?.picture} alt="Profile" className="w-full h-full rounded-full object-cover" />
              ) : (
                <span className="text-white font-bold">{user?.name?.[0]}</span>
              )}
            </div>
          </Button>
        </div>
      </header>

      <main className="p-4 space-y-4 max-w-lg mx-auto">
        {/* Days Counter & Badges */}
        {userStats && (
          <div className="flex gap-2">
            <Card className="flex-1 bg-gradient-to-br from-primary/10 to-primary/5">
              <CardContent className="p-3 text-center">
                <p className="text-2xl font-bold text-primary">{userStats.days_active}</p>
                <p className="text-xs text-muted-foreground">jours sur l'app</p>
              </CardContent>
            </Card>
            <Card className="flex-1 bg-gradient-to-br from-secondary/10 to-secondary/5">
              <CardContent className="p-3 text-center">
                <p className="text-2xl font-bold text-secondary">{userStats.streak}</p>
                <p className="text-xs text-muted-foreground">jours de suite</p>
              </CardContent>
            </Card>
            <Card className="flex-1 bg-gradient-to-br from-accent/10 to-accent/5">
              <CardContent className="p-3 text-center">
                <p className="text-2xl font-bold text-accent">{userStats.badges_count}</p>
                <p className="text-xs text-muted-foreground">badges</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Recent Badges Display - Show last 3 earned badges */}
        {userStats?.recent_badges && userStats.recent_badges.length > 0 && (
          <div className="flex gap-2 overflow-x-auto pb-2 hide-scrollbar">
            {userStats.recent_badges.slice(0, 3).map((badge) => (
              <div 
                key={badge.id}
                className="flex-shrink-0 px-3 py-2 rounded-full bg-gradient-to-r from-primary/20 to-secondary/20 border border-primary/30"
                title={badge.description}
              >
                <span className="text-lg mr-1">{badge.icon}</span>
                <span className="text-xs font-medium">{badge.name}</span>
              </div>
            ))}
          </div>
        )}

        {/* Today's Appointments Alert */}
        {todayAppointments.length > 0 && (
          <Card className="border-primary/50 bg-primary/5">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                  <Bell className="w-5 h-5 text-primary" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-sm">RDV aujourd'hui</p>
                  {todayAppointments.slice(0, 2).map((apt, i) => (
                    <p key={i} className="text-xs text-muted-foreground">
                      {apt.time} - {apt.title}
                    </p>
                  ))}
                </div>
                <Button variant="ghost" size="sm" onClick={() => document.getElementById('appointments-section')?.scrollIntoView({ behavior: 'smooth' })}>
                  Voir
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Daily Calories Progress */}
        <Card data-testid="calories-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm text-muted-foreground">Calories aujourd'hui</p>
                <p className="text-3xl font-bold font-heading">
                  {dailySummary?.consumed.calories || 0}
                  <span className="text-lg font-normal text-muted-foreground">
                    {' '}/ {dailySummary?.targets.calories || 2000} kcal
                  </span>
                </p>
              </div>
              <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
                calorieProgress >= 100 ? 'bg-destructive/20' : 'bg-primary/20'
              }`}>
                <Flame className={`w-8 h-8 ${
                  calorieProgress >= 100 ? 'text-destructive' : 'text-primary'
                }`} />
              </div>
            </div>
            <Progress 
              value={calorieProgress} 
              className="h-3"
            />
            
            {/* Macros */}
            <div className="grid grid-cols-3 gap-4 mt-4">
              <div className="text-center p-2 rounded-lg bg-muted/50">
                <p className="text-lg font-bold">{dailySummary?.consumed.protein || 0}g</p>
                <p className="text-xs text-muted-foreground">
                  / {dailySummary?.targets.protein || 100}g Prot.
                </p>
              </div>
              <div className="text-center p-2 rounded-lg bg-muted/50">
                <p className="text-lg font-bold">{dailySummary?.consumed.carbs || 0}g</p>
                <p className="text-xs text-muted-foreground">
                  / {dailySummary?.targets.carbs || 250}g Gluc.
                </p>
              </div>
              <div className="text-center p-2 rounded-lg bg-muted/50">
                <p className="text-lg font-bold">{dailySummary?.consumed.fat || 0}g</p>
                <p className="text-xs text-muted-foreground">
                  / {dailySummary?.targets.fat || 65}g Lip.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid grid-cols-4 gap-3">
          <Button
            variant="outline"
            className="flex flex-col items-center gap-1 h-auto py-4 card-interactive"
            onClick={() => navigate('/scanner')}
          >
            <Camera className="w-6 h-6 text-primary" />
            <span className="text-xs">Scanner</span>
          </Button>
          <Button
            variant="outline"
            className="flex flex-col items-center gap-1 h-auto py-4 card-interactive"
            onClick={() => navigate('/nutrition')}
          >
            <Apple className="w-6 h-6 text-secondary" />
            <span className="text-xs">Nutrition</span>
          </Button>
          <Button
            variant="outline"
            className="flex flex-col items-center gap-1 h-auto py-4 card-interactive"
            onClick={() => navigate('/workouts')}
          >
            <Dumbbell className="w-6 h-6 text-accent" />
            <span className="text-xs">Sport</span>
          </Button>
          <Button
            variant="outline"
            className="flex flex-col items-center gap-1 h-auto py-4 card-interactive"
            onClick={() => navigate('/progress')}
          >
            <TrendingUp className="w-6 h-6 text-primary" />
            <span className="text-xs">Progrès</span>
          </Button>
        </div>

        {/* Motivation Message */}
        {motivation && (
          <Card className="border-secondary/30 bg-gradient-to-r from-secondary/10 to-secondary/5">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-secondary flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-secondary">Citation du jour</p>
                  <p className="text-sm text-muted-foreground mt-1">{motivation.message}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Appointments Section */}
        <div id="appointments-section">
          <Card>
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <CardTitle className="font-heading text-lg flex items-center gap-2">
                <Calendar className="w-5 h-5 text-primary" />
                Mes rendez-vous
              </CardTitle>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setShowAppointmentDialog(true)}
              >
                <CalendarPlus className="w-4 h-4 mr-1" />
                Ajouter
              </Button>
            </CardHeader>
            <CardContent>
              {sortedAppointments.length > 0 ? (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {sortedAppointments.slice(0, 5).map((apt) => {
                    const typeInfo = appointmentTypeLabels[apt.type] || appointmentTypeLabels.medical;
                    const isToday = apt.date === new Date().toISOString().split('T')[0];
                    
                    return (
                      <div 
                        key={apt.appointment_id}
                        className={`flex items-center gap-3 p-3 rounded-xl border ${
                          isToday ? 'border-primary/50 bg-primary/5' : 'border-border'
                        } ${apt.pinned ? 'ring-2 ring-primary/30' : ''}`}
                      >
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg ${typeInfo.color}`}>
                          {typeInfo.icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-sm truncate">{apt.title}</p>
                            {apt.pinned && <Pin className="w-3 h-3 text-primary" />}
                            {isToday && <Badge variant="outline" className="text-xs">Aujourd'hui</Badge>}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {new Date(apt.date).toLocaleDateString('fr-FR')} à {apt.time}
                            {apt.location && ` • ${apt.location}`}
                          </p>
                        </div>
                        <div className="flex gap-1">
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8"
                            onClick={() => togglePinAppointment(apt)}
                          >
                            <Pin className={`w-4 h-4 ${apt.pinned ? 'text-primary fill-primary' : ''}`} />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8"
                            onClick={() => {
                              setEditingAppointment(apt);
                              setNewAppointment(apt);
                              setShowAppointmentDialog(true);
                            }}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-6">
                  <Calendar className="w-12 h-12 mx-auto text-muted-foreground mb-2" />
                  <p className="text-sm text-muted-foreground">Aucun rendez-vous</p>
                  <Button 
                    variant="link" 
                    size="sm" 
                    onClick={() => setShowAppointmentDialog(true)}
                  >
                    Ajouter un rendez-vous
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Daily Recipes */}
        {dailyRecipes.length > 0 && (
          <Card data-testid="daily-recipes-card">
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <CardTitle className="font-heading text-lg flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-secondary" />
                Recettes du jour
              </CardTitle>
              <Badge variant="outline" className="text-xs">
                {dailyRecipes.length} recettes
              </Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              {dailyRecipes.slice(0, 6).map((recipe, index) => (
                <div 
                  key={index}
                  className="flex items-center gap-3 p-3 rounded-xl border border-border hover:border-primary/30 transition-colors"
                >
                  {recipe.image && (
                    <img 
                      src={recipe.image} 
                      alt={recipe.name}
                      className="w-14 h-14 rounded-lg object-cover"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-sm truncate">{recipe.name}</p>
                      {recipe.nutri_score && (
                        <span className={`w-5 h-5 rounded text-white text-xs flex items-center justify-center font-bold ${getNutriScoreColor(recipe.nutri_score)}`}>
                          {recipe.nutri_score}
                        </span>
                      )}
                    </div>
                    <div className="flex gap-2 text-xs text-muted-foreground">
                      <span>{recipe.calories} kcal</span>
                      <span>•</span>
                      <span>{recipe.prep_time}</span>
                    </div>
                    <div className="flex gap-2 mt-1">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-6 text-xs px-2"
                        onClick={() => addRecipeToFavorites(recipe)}
                      >
                        <Heart className="w-3 h-3 mr-1" />
                        Favoris
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-6 text-xs px-2"
                        onClick={() => addIngredientsToShoppingList(recipe.ingredients)}
                      >
                        <ShoppingCart className="w-3 h-3 mr-1" />
                        Courses
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
              
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => navigate('/nutrition')}
              >
                Voir plus de recettes
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </CardContent>
          </Card>
        )}

        {/* AI Recipe Search */}
        <Card className="border-primary/30 bg-gradient-to-br from-primary/5 to-secondary/5">
          <CardHeader className="pb-2">
            <CardTitle className="font-heading text-lg flex items-center gap-2">
              <Search className="w-5 h-5 text-primary" />
              Rechercher une recette IA
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              placeholder='Ex: "Recette avec crevettes et riz en 30 min, saine"'
              value={recipeSearchQuery}
              onChange={(e) => setRecipeSearchQuery(e.target.value)}
              rows={2}
              className="resize-none text-sm"
            />
            <Button 
              onClick={searchRecipeByAI}
              disabled={loadingSearch || !recipeSearchQuery.trim()}
              className="w-full"
              size="sm"
            >
              {loadingSearch ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Recherche...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  Trouver ma recette
                </>
              )}
            </Button>
            
            {searchedRecipe && (
              <div className="mt-3 p-3 rounded-xl border border-primary/30 bg-background space-y-2">
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-sm">{searchedRecipe.name}</h4>
                  {searchedRecipe.nutri_score && (
                    <span className={`w-5 h-5 rounded text-white text-xs flex items-center justify-center font-bold ${getNutriScoreColor(searchedRecipe.nutri_score)}`}>
                      {searchedRecipe.nutri_score}
                    </span>
                  )}
                </div>
                <div className="flex gap-2 text-xs text-muted-foreground">
                  <span>{searchedRecipe.calories} kcal</span>
                  <span>•</span>
                  <span>{searchedRecipe.prep_time}</span>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs"
                    onClick={() => addRecipeToFavorites(searchedRecipe)}
                  >
                    <Heart className="w-3 h-3 mr-1" />
                    Favoris
                  </Button>
                  {searchedRecipe.ingredients && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 text-xs"
                      onClick={() => addIngredientsToShoppingList(searchedRecipe.ingredients)}
                    >
                      <ListPlus className="w-3 h-3 mr-1" />
                      Courses
                    </Button>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recipes Database Link */}
        <Card 
          className="cursor-pointer card-interactive"
          onClick={() => navigate('/nutrition')}
        >
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center">
                <BookOpen className="w-6 h-6 text-secondary" />
              </div>
              <div className="flex-1">
                <h3 className="font-heading font-semibold">Base de recettes</h3>
                <p className="text-xs text-muted-foreground">
                  50 000 recettes classées par Nutri-Score
                </p>
              </div>
              <ChevronRight className="w-5 h-5 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        {/* Daily Challenges */}
        {challenges?.daily && challenges.daily.length > 0 && (
          <Card data-testid="challenges-card">
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <CardTitle className="font-heading text-lg flex items-center gap-2">
                <Trophy className="w-5 h-5 text-accent" />
                Défis du jour
              </CardTitle>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="bg-gradient-to-r from-amber-500 to-orange-500 text-white font-bold px-3">
                  🏆 {challenges.total_points || 0} pts
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {challenges.daily.filter(c => c.completed).length}/{challenges.daily.length}
                </span>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {challenges.daily.map((challenge) => (
                <div 
                  key={challenge.id}
                  className={`flex items-center justify-between p-3 rounded-xl border transition-all ${
                    challenge.completed 
                      ? 'bg-gradient-to-r from-primary/10 to-secondary/10 border-primary/30' 
                      : 'border-border hover:border-primary/30'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${
                      challenge.completed 
                        ? 'bg-gradient-to-r from-primary to-secondary text-white' 
                        : 'bg-muted'
                    }`}>
                      {challenge.completed ? '✓' : challenge.icon}
                    </div>
                    <div className="flex-1">
                      <p className={`font-medium text-sm ${challenge.completed ? 'line-through opacity-70' : ''}`}>
                        {challenge.title}
                      </p>
                      <p className="text-xs text-muted-foreground">{challenge.description}</p>
                      {/* Progress bar */}
                      {!challenge.completed && challenge.target > 1 && (
                        <div className="mt-1">
                          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-primary rounded-full transition-all"
                              style={{ width: `${Math.min((challenge.progress / challenge.target) * 100, 100)}%` }}
                            />
                          </div>
                          <p className="text-[10px] text-muted-foreground mt-0.5">
                            {challenge.progress.toLocaleString()}/{challenge.target.toLocaleString()}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge 
                      variant={challenge.completed ? 'default' : 'outline'}
                      className={challenge.completed ? 'bg-gradient-to-r from-primary to-secondary' : ''}
                    >
                      {challenge.completed ? '✓ Fait' : `+${challenge.reward} pts`}
                    </Badge>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Social Card */}
        <Card className="shadow-sm hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/social')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-pink-500 to-purple-500 flex items-center justify-center text-white text-xl">
                  👥
                </div>
                <div>
                  <p className="font-semibold">Communauté</p>
                  <p className="text-sm text-muted-foreground">Amis, messagerie, défis</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </main>

      {/* Appointment Dialog */}
      <Dialog open={showAppointmentDialog} onOpenChange={setShowAppointmentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingAppointment ? 'Modifier le rendez-vous' : 'Nouveau rendez-vous'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="apt-title">Titre *</Label>
              <Input
                id="apt-title"
                value={newAppointment.title}
                onChange={(e) => setNewAppointment(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Ex: RDV Médecin"
              />
            </div>
            
            <div>
              <Label htmlFor="apt-type">Type</Label>
              <Select
                value={newAppointment.type}
                onValueChange={(value) => setNewAppointment(prev => ({ ...prev, type: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="medical">🏥 Médical</SelectItem>
                  <SelectItem value="sport">🏃 Sport</SelectItem>
                  <SelectItem value="wellness">🧘 Bien-être</SelectItem>
                  <SelectItem value="nutrition">🥗 Nutrition</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="apt-date">Date *</Label>
                <Input
                  id="apt-date"
                  type="date"
                  value={newAppointment.date}
                  onChange={(e) => setNewAppointment(prev => ({ ...prev, date: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="apt-time">Heure *</Label>
                <Input
                  id="apt-time"
                  type="time"
                  value={newAppointment.time}
                  onChange={(e) => setNewAppointment(prev => ({ ...prev, time: e.target.value }))}
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="apt-location">Lieu</Label>
              <Input
                id="apt-location"
                value={newAppointment.location}
                onChange={(e) => setNewAppointment(prev => ({ ...prev, location: e.target.value }))}
                placeholder="Ex: Cabinet Dr. Martin"
              />
            </div>
            
            <div>
              <Label htmlFor="apt-notes">Notes</Label>
              <Textarea
                id="apt-notes"
                value={newAppointment.notes}
                onChange={(e) => setNewAppointment(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Informations supplémentaires..."
                rows={2}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <Label htmlFor="apt-pinned">Épingler ce rendez-vous</Label>
              <Switch
                id="apt-pinned"
                checked={newAppointment.pinned}
                onCheckedChange={(checked) => setNewAppointment(prev => ({ ...prev, pinned: checked }))}
              />
            </div>
          </div>
          
          <DialogFooter className="flex gap-2">
            {editingAppointment && (
              <Button 
                variant="destructive" 
                onClick={() => {
                  handleDeleteAppointment(editingAppointment.appointment_id);
                  setShowAppointmentDialog(false);
                  setEditingAppointment(null);
                }}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Supprimer
              </Button>
            )}
            <Button variant="outline" onClick={() => {
              setShowAppointmentDialog(false);
              setEditingAppointment(null);
            }}>
              Annuler
            </Button>
            <Button onClick={handleSaveAppointment}>
              {editingAppointment ? 'Modifier' : 'Créer'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Smart Recommendation Popup */}
      <Dialog open={showRecommendation} onOpenChange={setShowRecommendation}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              Recommandation
            </DialogTitle>
          </DialogHeader>
          
          {recommendation && (
            <div className="py-4">
              <p className="text-sm leading-relaxed">{recommendation.message}</p>
            </div>
          )}
          
          <DialogFooter>
            <Button onClick={() => setShowRecommendation(false)} className="w-full">
              Merci !
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
