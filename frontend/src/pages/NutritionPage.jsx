import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { 
  Apple, 
  Plus, 
  Trash2, 
  Camera,
  ArrowLeft,
  Flame,
  Calendar,
  Lightbulb,
  ChevronLeft,
  ChevronRight,
  Edit,
  Sparkles,
  AlertTriangle,
  Check
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const mealTypes = [
  { value: 'breakfast', label: 'Petit-déjeuner', emoji: '🌅' },
  { value: 'lunch', label: 'Déjeuner', emoji: '☀️' },
  { value: 'dinner', label: 'Dîner', emoji: '🌙' },
  { value: 'snack', label: 'Collation', emoji: '🍎' },
];

export default function NutritionPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('today');
  const [dailySummary, setDailySummary] = useState(null);
  const [foodLogs, setFoodLogs] = useState([]);
  const [diary, setDiary] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [noteDialogOpen, setNoteDialogOpen] = useState(false);
  const [recommendDialogOpen, setRecommendDialogOpen] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loadingRecommend, setLoadingRecommend] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(new Date().toISOString().slice(0, 7));
  const [newFood, setNewFood] = useState({
    food_name: '',
    calories: '',
    protein: '',
    carbs: '',
    fat: '',
    quantity: 1,
    meal_type: 'snack',
    note: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (activeTab === 'diary') {
      fetchDiary();
    }
  }, [activeTab, currentMonth]);

  const fetchData = async () => {
    try {
      const [summaryRes, logsRes] = await Promise.all([
        axios.get(`${API}/food/daily-summary`, { withCredentials: true }),
        axios.get(`${API}/food/logs`, { withCredentials: true })
      ]);
      setDailySummary(summaryRes.data);
      setFoodLogs(logsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDiary = async () => {
    try {
      const response = await axios.get(`${API}/food/diary?month=${currentMonth}`, { withCredentials: true });
      setDiary(response.data);
    } catch (error) {
      console.error('Error fetching diary:', error);
    }
  };

  const handleAddFood = async () => {
    if (!newFood.food_name || !newFood.calories) {
      toast.error('Nom et calories requis');
      return;
    }

    try {
      await axios.post(`${API}/food/log`, {
        ...newFood,
        calories: parseFloat(newFood.calories),
        protein: parseFloat(newFood.protein) || 0,
        carbs: parseFloat(newFood.carbs) || 0,
        fat: parseFloat(newFood.fat) || 0,
      }, { withCredentials: true });
      
      toast.success('Aliment ajouté !');
      setDialogOpen(false);
      setNewFood({
        food_name: '',
        calories: '',
        protein: '',
        carbs: '',
        fat: '',
        quantity: 1,
        meal_type: 'snack',
        note: ''
      });
      fetchData();
      
      // Check if unhealthy and suggest alternatives
      if (parseFloat(newFood.calories) > 500 || parseFloat(newFood.fat) > 25) {
        getRecommendations({
          food_name: newFood.food_name,
          calories: parseFloat(newFood.calories),
          protein: parseFloat(newFood.protein) || 0,
          carbs: parseFloat(newFood.carbs) || 0,
          fat: parseFloat(newFood.fat) || 0,
        });
      }
    } catch (error) {
      toast.error('Erreur lors de l\'ajout');
    }
  };

  const handleDeleteFood = async (entryId) => {
    try {
      await axios.delete(`${API}/food/log/${entryId}`, { withCredentials: true });
      toast.success('Aliment supprimé');
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const handleUpdateNote = async () => {
    if (!selectedEntry) return;
    
    try {
      await axios.put(`${API}/food/log/${selectedEntry.entry_id}/note`, {
        note: selectedEntry.note
      }, { withCredentials: true });
      toast.success('Note mise à jour');
      setNoteDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const getRecommendations = async (foodEntry) => {
    setLoadingRecommend(true);
    setRecommendDialogOpen(true);
    
    try {
      const response = await axios.post(`${API}/food/recommend-alternatives`, foodEntry, { withCredentials: true });
      setRecommendations(response.data);
    } catch (error) {
      console.error('Error getting recommendations:', error);
      setRecommendations({ analysis: 'Erreur', alternatives: [], tips: [] });
    } finally {
      setLoadingRecommend(false);
    }
  };

  const groupedLogs = foodLogs.reduce((acc, log) => {
    const type = log.meal_type || 'snack';
    if (!acc[type]) acc[type] = [];
    acc[type].push(log);
    return acc;
  }, {});

  const isUnhealthy = (log) => {
    return log.calories > 600 || log.fat > 30 || (log.sugar && log.sugar > 25);
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full gradient-primary" />
        </div>
      </div>
    );
  }

  const calorieProgress = dailySummary 
    ? Math.min(100, (dailySummary.consumed.calories / dailySummary.targets.calories) * 100)
    : 0;

  return (
    <div className="min-h-screen bg-background pb-safe" data-testid="nutrition-page">
      {/* Header */}
      <header className="sticky top-0 z-10 px-4 py-4 bg-background/80 backdrop-blur-lg border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              size="icon"
              onClick={() => navigate('/dashboard')}
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="font-heading text-xl font-bold">Nutrition</h1>
              <p className="text-sm text-muted-foreground">
                {new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })}
              </p>
            </div>
          </div>
          <Button
            size="icon"
            className="rounded-full shadow-glow-purple bg-secondary"
            onClick={() => navigate('/scanner')}
            data-testid="scanner-btn"
          >
            <Camera className="w-5 h-5" />
          </Button>
        </div>
      </header>

      <main className="p-4 space-y-6 pb-24">
        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="today" className="flex items-center gap-2">
              <Apple className="w-4 h-4" />
              Aujourd'hui
            </TabsTrigger>
            <TabsTrigger value="diary" className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Agenda
            </TabsTrigger>
          </TabsList>

          {/* Today Tab */}
          <TabsContent value="today" className="space-y-6 mt-4">
            {/* Daily Summary */}
            {dailySummary && (
              <Card data-testid="daily-summary-card">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl gradient-primary flex items-center justify-center">
                        <Flame className="w-6 h-6 text-primary-foreground" />
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Calories restantes</p>
                        <p className="font-heading text-2xl font-bold">
                          {Math.max(0, dailySummary.remaining.calories)} kcal
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span>Consommé: {dailySummary.consumed.calories} kcal</span>
                      <span>Objectif: {dailySummary.targets.calories} kcal</span>
                    </div>
                    <Progress value={calorieProgress} className="h-3" />
                  </div>

                  <div className="grid grid-cols-3 gap-4 mt-6">
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Protéines</p>
                      <Progress 
                        value={Math.min(100, (dailySummary.consumed.protein / dailySummary.targets.protein) * 100)} 
                        className="h-2"
                      />
                      <p className="text-xs font-medium">
                        {dailySummary.consumed.protein}/{dailySummary.targets.protein}g
                      </p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Glucides</p>
                      <Progress 
                        value={Math.min(100, (dailySummary.consumed.carbs / dailySummary.targets.carbs) * 100)} 
                        className="h-2"
                      />
                      <p className="text-xs font-medium">
                        {dailySummary.consumed.carbs}/{dailySummary.targets.carbs}g
                      </p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Lipides</p>
                      <Progress 
                        value={Math.min(100, (dailySummary.consumed.fat / dailySummary.targets.fat) * 100)} 
                        className="h-2"
                      />
                      <p className="text-xs font-medium">
                        {dailySummary.consumed.fat}/{dailySummary.targets.fat}g
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Add Food Button */}
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="w-full rounded-full" data-testid="add-food-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Ajouter un aliment
                </Button>
              </DialogTrigger>
              <DialogContent className="max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Ajouter un aliment</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Nom de l'aliment</Label>
                    <Input
                      placeholder="Ex: Salade César"
                      value={newFood.food_name}
                      onChange={(e) => setNewFood({ ...newFood, food_name: e.target.value })}
                      data-testid="food-name-input"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Calories (kcal)</Label>
                      <Input
                        type="number"
                        placeholder="320"
                        value={newFood.calories}
                        onChange={(e) => setNewFood({ ...newFood, calories: e.target.value })}
                        data-testid="calories-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Type de repas</Label>
                      <Select
                        value={newFood.meal_type}
                        onValueChange={(value) => setNewFood({ ...newFood, meal_type: value })}
                      >
                        <SelectTrigger data-testid="meal-type-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {mealTypes.map((type) => (
                            <SelectItem key={type.value} value={type.value}>
                              {type.emoji} {type.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Protéines (g)</Label>
                      <Input
                        type="number"
                        placeholder="20"
                        value={newFood.protein}
                        onChange={(e) => setNewFood({ ...newFood, protein: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Glucides (g)</Label>
                      <Input
                        type="number"
                        placeholder="30"
                        value={newFood.carbs}
                        onChange={(e) => setNewFood({ ...newFood, carbs: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Lipides (g)</Label>
                      <Input
                        type="number"
                        placeholder="15"
                        value={newFood.fat}
                        onChange={(e) => setNewFood({ ...newFood, fat: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Note (optionnel)</Label>
                    <Textarea
                      placeholder="Ajouter une note..."
                      value={newFood.note}
                      onChange={(e) => setNewFood({ ...newFood, note: e.target.value })}
                    />
                  </div>
                  <Button onClick={handleAddFood} className="w-full" data-testid="submit-food-btn">
                    Ajouter
                  </Button>
                </div>
              </DialogContent>
            </Dialog>

            {/* Food Logs by Meal Type */}
            {mealTypes.map((mealType) => (
              groupedLogs[mealType.value]?.length > 0 && (
                <Card key={mealType.value}>
                  <CardHeader className="pb-2">
                    <CardTitle className="font-heading text-lg flex items-center gap-2">
                      <span>{mealType.emoji}</span>
                      {mealType.label}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {groupedLogs[mealType.value].map((log) => (
                      <div 
                        key={log.entry_id}
                        className={`flex items-center justify-between p-3 rounded-xl ${
                          isUnhealthy(log) ? 'bg-destructive/10 border border-destructive/20' : 'bg-muted/50'
                        }`}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{log.food_name}</p>
                            {log.nutri_score && (
                              <span className={`w-5 h-5 rounded text-white text-xs flex items-center justify-center font-bold ${getNutriScoreColor(log.nutri_score)}`}>
                                {log.nutri_score}
                              </span>
                            )}
                            {isUnhealthy(log) && (
                              <button
                                onClick={() => getRecommendations(log)}
                                className="text-destructive hover:text-destructive/80"
                                title="Voir alternatives"
                              >
                                <Lightbulb className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                          <div className="flex gap-3 text-xs text-muted-foreground mt-1">
                            <span>{log.calories} kcal</span>
                            <span>P: {log.protein}g</span>
                            <span>G: {log.carbs}g</span>
                            <span>L: {log.fat}g</span>
                          </div>
                          {log.note && (
                            <p className="text-xs text-muted-foreground mt-1 italic">📝 {log.note}</p>
                          )}
                        </div>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => {
                              setSelectedEntry(log);
                              setNoteDialogOpen(true);
                            }}
                          >
                            <Edit className="w-3 h-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            onClick={() => handleDeleteFood(log.entry_id)}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )
            ))}

            {foodLogs.length === 0 && (
              <div className="text-center py-12">
                <Apple className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Aucun aliment enregistré aujourd'hui</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Scannez ou ajoutez vos repas pour suivre votre nutrition
                </p>
              </div>
            )}
          </TabsContent>

          {/* Diary Tab */}
          <TabsContent value="diary" className="space-y-4 mt-4">
            {/* Month Navigation */}
            <div className="flex items-center justify-between">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  const date = new Date(currentMonth + '-01');
                  date.setMonth(date.getMonth() - 1);
                  setCurrentMonth(date.toISOString().slice(0, 7));
                }}
              >
                <ChevronLeft className="w-5 h-5" />
              </Button>
              <span className="font-heading font-semibold">
                {new Date(currentMonth + '-01').toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })}
              </span>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  const date = new Date(currentMonth + '-01');
                  date.setMonth(date.getMonth() + 1);
                  setCurrentMonth(date.toISOString().slice(0, 7));
                }}
              >
                <ChevronRight className="w-5 h-5" />
              </Button>
            </div>

            {/* Diary Entries */}
            {diary.length > 0 ? (
              diary.map((day) => (
                <Card key={day.date}>
                  <CardHeader className="pb-2">
                    <CardTitle className="font-heading text-base flex items-center justify-between">
                      <span>
                        {new Date(day.date).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'short' })}
                      </span>
                      <span className="text-sm font-normal text-muted-foreground">
                        {Math.round(day.total_calories)} kcal
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {day.meals.map((meal, i) => (
                        <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-muted/30">
                          <div className="flex items-center gap-2">
                            <span>{mealTypes.find(t => t.value === meal.meal_type)?.emoji || '🍽️'}</span>
                            <span className="text-sm">{meal.food_name}</span>
                          </div>
                          <span className="text-xs text-muted-foreground">{meal.calories} kcal</span>
                        </div>
                      ))}
                    </div>
                    <div className="mt-3 pt-3 border-t grid grid-cols-3 gap-2 text-center text-xs">
                      <div>
                        <p className="text-muted-foreground">Protéines</p>
                        <p className="font-medium">{Math.round(day.total_protein)}g</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Glucides</p>
                        <p className="font-medium">{Math.round(day.total_carbs)}g</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Lipides</p>
                        <p className="font-medium">{Math.round(day.total_fat)}g</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <div className="text-center py-12">
                <Calendar className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Aucun repas ce mois-ci</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>

      {/* Note Dialog */}
      <Dialog open={noteDialogOpen} onOpenChange={setNoteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Modifier la note</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="font-medium">{selectedEntry?.food_name}</p>
            <Textarea
              placeholder="Ajouter une note..."
              value={selectedEntry?.note || ''}
              onChange={(e) => setSelectedEntry({ ...selectedEntry, note: e.target.value })}
            />
            <Button onClick={handleUpdateNote} className="w-full">
              Enregistrer
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Recommendations Dialog */}
      <Dialog open={recommendDialogOpen} onOpenChange={setRecommendDialogOpen}>
        <DialogContent className="max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              Alternatives plus saines
            </DialogTitle>
          </DialogHeader>
          {loadingRecommend ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full" />
            </div>
          ) : recommendations ? (
            <div className="space-y-4">
              {recommendations.analysis && (
                <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-destructive mt-0.5" />
                    <p className="text-sm">{recommendations.analysis}</p>
                  </div>
                </div>
              )}
              
              {recommendations.alternatives?.length > 0 && (
                <div className="space-y-2">
                  <p className="font-medium text-sm">Essayez plutôt :</p>
                  {recommendations.alternatives.map((alt, i) => (
                    <div key={i} className="p-3 rounded-lg bg-primary/5 border border-primary/20">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{alt.name}</span>
                        <span className="text-sm text-muted-foreground">{alt.calories} kcal</span>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1 flex items-start gap-1">
                        <Check className="w-3 h-3 text-primary mt-0.5" />
                        {alt.benefit}
                      </p>
                    </div>
                  ))}
                </div>
              )}
              
              {recommendations.tips?.length > 0 && (
                <div className="p-3 rounded-lg bg-muted">
                  <p className="font-medium text-sm mb-2">💡 Conseils</p>
                  <ul className="space-y-1">
                    {recommendations.tips.map((tip, i) => (
                      <li key={i} className="text-sm text-muted-foreground">• {tip}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
