import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { 
  Apple, 
  Plus, 
  Trash2, 
  Camera,
  ArrowLeft,
  Flame,
  Clock
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const mealTypes = [
  { value: 'breakfast', label: 'Petit-déjeuner' },
  { value: 'lunch', label: 'Déjeuner' },
  { value: 'dinner', label: 'Dîner' },
  { value: 'snack', label: 'Collation' },
];

export default function NutritionPage() {
  const navigate = useNavigate();
  const [dailySummary, setDailySummary] = useState(null);
  const [foodLogs, setFoodLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newFood, setNewFood] = useState({
    food_name: '',
    calories: '',
    protein: '',
    carbs: '',
    fat: '',
    quantity: 1,
    meal_type: 'snack'
  });

  useEffect(() => {
    fetchData();
  }, []);

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
        meal_type: 'snack'
      });
      fetchData();
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

  const groupedLogs = foodLogs.reduce((acc, log) => {
    const type = log.meal_type || 'snack';
    if (!acc[type]) acc[type] = [];
    acc[type].push(log);
    return acc;
  }, {});

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
          <DialogContent>
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
                          {type.label}
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
                  <Apple className="w-5 h-5 text-primary" />
                  {mealType.label}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {groupedLogs[mealType.value].map((log) => (
                  <div 
                    key={log.entry_id}
                    className="flex items-center justify-between p-3 rounded-xl bg-muted/50"
                  >
                    <div className="flex-1">
                      <p className="font-medium">{log.food_name}</p>
                      <div className="flex gap-3 text-xs text-muted-foreground mt-1">
                        <span>{log.calories} kcal</span>
                        <span>P: {log.protein}g</span>
                        <span>G: {log.carbs}g</span>
                        <span>L: {log.fat}g</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive hover:text-destructive"
                      onClick={() => handleDeleteFood(log.entry_id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
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
      </main>
    </div>
  );
}
