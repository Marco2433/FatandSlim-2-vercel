import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
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
  Clock
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

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch data in parallel but handle failures independently
      const [statsRes, summaryRes, challengesRes, motivationRes, recipesRes] = await Promise.allSettled([
        axios.get(`${API}/progress/stats`, { withCredentials: true }),
        axios.get(`${API}/food/daily-summary`, { withCredentials: true }),
        axios.get(`${API}/challenges`, { withCredentials: true }),
        axios.get(`${API}/motivation`, { withCredentials: true }),
        axios.get(`${API}/recipes/daily`, { withCredentials: true }),
      ]);
      
      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
      if (summaryRes.status === 'fulfilled') setDailySummary(summaryRes.value.data);
      if (challengesRes.status === 'fulfilled') setChallenges(challengesRes.value.data);
      if (motivationRes.status === 'fulfilled') setMotivation(motivationRes.value.data);
      if (recipesRes.status === 'fulfilled') setDailyRecipes(recipesRes.value.data?.recipes || []);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
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
        toast.error('Erreur lors de l\'ajout');
      }
    }
  };

  const addIngredientsToShoppingList = async (ingredients) => {
    try {
      const items = ingredients.map(i => ({ item: i.item, quantity: i.quantity }));
      await axios.post(`${API}/shopping-list/bulk`, { items }, { withCredentials: true });
      toast.success(`${items.length} ingrédients ajoutés à la liste de courses !`);
    } catch (error) {
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

  const calorieProgress = dailySummary 
    ? Math.min(100, (dailySummary.consumed.calories / dailySummary.targets.calories) * 100)
    : 0;

  const macros = dailySummary ? [
    { 
      name: 'Protéines', 
      value: dailySummary.consumed.protein, 
      target: dailySummary.targets.protein, 
      unit: 'g',
      color: 'bg-secondary'
    },
    { 
      name: 'Glucides', 
      value: dailySummary.consumed.carbs, 
      target: dailySummary.targets.carbs, 
      unit: 'g',
      color: 'bg-accent'
    },
    { 
      name: 'Lipides', 
      value: dailySummary.consumed.fat, 
      target: dailySummary.targets.fat, 
      unit: 'g',
      color: 'bg-chart-4'
    },
  ] : [];

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

  return (
    <div className="min-h-screen bg-background pb-safe" data-testid="dashboard-page">
      {/* Header */}
      <header className="px-4 pt-6 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Bonjour,</p>
            <h1 className="font-heading text-2xl font-bold">{user?.name || 'Utilisateur'}</h1>
          </div>
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => navigate('/profile')}
            className="rounded-full"
            data-testid="profile-btn"
          >
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white font-bold">
              {user?.name?.charAt(0) || 'U'}
            </div>
          </Button>
        </div>

        {/* Streak */}
        {stats?.streak && (
          <div className="mt-4 flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 w-fit">
            <Flame className="w-5 h-5 text-accent" />
            <span className="text-sm font-medium">
              {stats.streak.current} jours de suite
            </span>
          </div>
        )}
        
        {/* Motivation Message */}
        {motivation && (
          <Card className="mt-4 bg-gradient-to-r from-primary/10 to-secondary/10 border-primary/20">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="font-medium text-foreground">{motivation.message}</p>
                  {motivation.bonus && (
                    <p className="text-sm text-muted-foreground mt-1">{motivation.bonus}</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </header>

      <main className="px-4 space-y-6 pb-24">
        {/* Calories Card */}
        <Card className="overflow-hidden" data-testid="calories-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center">
                  <Flame className="w-5 h-5 text-primary-foreground" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Calories aujourd'hui</p>
                  <p className="font-heading text-2xl font-bold">
                    {dailySummary?.consumed.calories || 0} 
                    <span className="text-sm font-normal text-muted-foreground ml-1">
                      / {dailySummary?.targets.calories || 2000} kcal
                    </span>
                  </p>
                </div>
              </div>
            </div>
            
            <Progress value={calorieProgress} className="h-3 mb-4" />
            
            <div className="grid grid-cols-3 gap-4">
              {macros.map((macro) => (
                <div key={macro.name} className="space-y-1">
                  <p className="text-xs text-muted-foreground">{macro.name}</p>
                  <div className="macro-bar">
                    <div 
                      className={`macro-bar-fill ${macro.color}`}
                      style={{ width: `${Math.min(100, (macro.value / macro.target) * 100)}%` }}
                    />
                  </div>
                  <p className="text-xs font-medium">
                    {macro.value}/{macro.target}{macro.unit}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-4">
          <Card 
            className="cursor-pointer card-interactive hover:shadow-glow-purple"
            onClick={() => navigate('/scanner')}
            data-testid="scanner-card"
          >
            <CardContent className="p-4 flex flex-col items-center text-center">
              <div className="w-14 h-14 rounded-2xl bg-secondary/10 flex items-center justify-center mb-3">
                <Camera className="w-7 h-7 text-secondary" />
              </div>
              <h3 className="font-heading font-semibold">Scanner</h3>
              <p className="text-xs text-muted-foreground">Analyser un repas</p>
            </CardContent>
          </Card>

          <Card 
            className="cursor-pointer card-interactive hover:shadow-glow"
            onClick={() => navigate('/nutrition')}
            data-testid="nutrition-card"
          >
            <CardContent className="p-4 flex flex-col items-center text-center">
              <div className="w-14 h-14 rounded-2xl bg-accent/10 flex items-center justify-center mb-3">
                <Apple className="w-7 h-7 text-accent" />
              </div>
              <h3 className="font-heading font-semibold">Nutrition</h3>
              <p className="text-xs text-muted-foreground">Voir mes repas</p>
            </CardContent>
          </Card>
        </div>

        {/* Weight Progress */}
        {stats && (
          <Card data-testid="weight-card">
            <CardHeader className="pb-2">
              <CardTitle className="font-heading text-lg flex items-center gap-2">
                <Target className="w-5 h-5 text-primary" />
                Objectif poids
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between mb-4">
                <div>
                  <p className="text-3xl font-bold font-heading">{stats.current_weight} kg</p>
                  <p className="text-sm text-muted-foreground">
                    {stats.weight_change > 0 ? '+' : ''}{stats.weight_change} kg depuis le début
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Objectif</p>
                  <p className="font-semibold">{stats.target_weight} kg</p>
                </div>
              </div>
              <Progress 
                value={Math.max(0, Math.min(100, ((stats.current_weight - stats.target_weight) / (stats.current_weight - stats.target_weight + 10)) * 100))}
                className="h-2"
              />
            </CardContent>
          </Card>
        )}

        {/* Daily Recipes - Recettes du jour */}
        {dailyRecipes.length > 0 && (
          <Card data-testid="daily-recipes-card">
            <CardHeader className="pb-2">
              <CardTitle className="font-heading text-lg flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-secondary" />
                Recettes du jour
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {dailyRecipes.map((recipe) => (
                <div 
                  key={recipe.id}
                  className="flex gap-3 p-3 rounded-xl border border-border hover:border-primary/30 transition-colors"
                >
                  {/* Recipe Image */}
                  <div className="w-20 h-20 rounded-lg overflow-hidden flex-shrink-0">
                    <img 
                      src={recipe.image} 
                      alt={recipe.name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.src = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400';
                      }}
                    />
                  </div>
                  
                  {/* Recipe Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-sm truncate">{recipe.name}</h4>
                      <span className={`w-5 h-5 rounded text-white text-xs flex items-center justify-center font-bold flex-shrink-0 ${getNutriScoreColor(recipe.nutri_score)}`}>
                        {recipe.nutri_score}
                      </span>
                    </div>
                    
                    <div className="flex gap-2 text-xs text-muted-foreground mb-2">
                      <span>{recipe.calories} kcal</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {recipe.prep_time}
                      </span>
                    </div>
                    
                    {/* Actions */}
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 text-xs"
                        onClick={() => addRecipeToFavorites(recipe)}
                      >
                        <Heart className="w-3 h-3 mr-1" />
                        Favoris
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 text-xs"
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

        {/* Daily Challenges */}
        {challenges?.daily && (
          <Card data-testid="challenges-card">
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <CardTitle className="font-heading text-lg flex items-center gap-2">
                <Trophy className="w-5 h-5 text-accent" />
                Défis du jour
              </CardTitle>
              <Button variant="ghost" size="sm" className="text-primary">
                Voir tout
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {challenges.daily.slice(0, 3).map((challenge) => (
                <div 
                  key={challenge.id}
                  className={`flex items-center justify-between p-3 rounded-xl border ${
                    challenge.completed ? 'bg-primary/5 border-primary/20' : 'border-border'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      challenge.completed ? 'bg-primary text-primary-foreground' : 'bg-muted'
                    }`}>
                      {challenge.completed ? (
                        <Zap className="w-4 h-4" />
                      ) : (
                        <span className="text-xs font-bold">{challenge.progress}/{challenge.target}</span>
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-sm">{challenge.name}</p>
                      <p className="text-xs text-muted-foreground">{challenge.xp} XP</p>
                    </div>
                  </div>
                  {challenge.completed && (
                    <span className="text-xs font-medium text-primary">Complété !</span>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Weekly Stats */}
        {stats?.weekly_stats && (
          <Card data-testid="weekly-stats-card">
            <CardHeader className="pb-2">
              <CardTitle className="font-heading text-lg flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-chart-4" />
                Cette semaine
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-3 rounded-xl bg-muted/50">
                  <p className="text-2xl font-bold font-heading">{stats.weekly_stats.workouts_completed}</p>
                  <p className="text-xs text-muted-foreground">Entraînements</p>
                </div>
                <div className="p-3 rounded-xl bg-muted/50">
                  <p className="text-2xl font-bold font-heading">{stats.weekly_stats.workout_minutes}</p>
                  <p className="text-xs text-muted-foreground">Minutes sport</p>
                </div>
                <div className="p-3 rounded-xl bg-muted/50">
                  <p className="text-2xl font-bold font-heading">{stats.weekly_stats.avg_daily_calories}</p>
                  <p className="text-xs text-muted-foreground">Moy. kcal/jour</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
