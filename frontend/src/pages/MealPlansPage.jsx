import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { 
  Utensils, 
  ArrowLeft,
  Sparkles,
  Loader2,
  Clock,
  Flame,
  ShoppingCart,
  ChevronRight
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function MealPlansPage() {
  const navigate = useNavigate();
  const [plans, setPlans] = useState([]);
  const [currentPlan, setCurrentPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedDay, setSelectedDay] = useState(0);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API}/meals/plans`, { withCredentials: true });
      setPlans(response.data);
      if (response.data.length > 0) {
        setCurrentPlan(response.data[0].meal_plan);
      }
    } catch (error) {
      console.error('Error fetching plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const generatePlan = async () => {
    setGenerating(true);
    try {
      const response = await axios.post(`${API}/meals/generate`, {}, { withCredentials: true });
      setCurrentPlan(response.data.meal_plan);
      toast.success('Nouveau plan de repas généré !');
      fetchPlans();
    } catch (error) {
      toast.error('Erreur lors de la génération');
    } finally {
      setGenerating(false);
    }
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

  const days = currentPlan?.days || [];
  const selectedDayData = days[selectedDay];

  return (
    <div className="min-h-screen bg-background pb-safe" data-testid="meals-page">
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
              <h1 className="font-heading text-xl font-bold">Plans repas</h1>
              <p className="text-sm text-muted-foreground">Menus personnalisés par IA</p>
            </div>
          </div>
        </div>
      </header>

      <main className="p-4 space-y-6 pb-24">
        {/* Generate Button */}
        <Button
          className="w-full rounded-full shadow-glow-purple bg-secondary hover:bg-secondary/90"
          onClick={generatePlan}
          disabled={generating}
          data-testid="generate-plan-btn"
        >
          {generating ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Génération en cours...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-2" />
              Générer un nouveau plan
            </>
          )}
        </Button>

        {currentPlan && days.length > 0 ? (
          <>
            {/* Day Tabs */}
            <div className="flex gap-2 overflow-x-auto pb-2 no-scrollbar">
              {days.map((day, index) => (
                <Button
                  key={index}
                  variant={selectedDay === index ? 'default' : 'outline'}
                  size="sm"
                  className="rounded-full whitespace-nowrap"
                  onClick={() => setSelectedDay(index)}
                >
                  {day.day}
                </Button>
              ))}
            </div>

            {/* Selected Day Meals */}
            {selectedDayData && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="font-heading text-lg font-semibold">{selectedDayData.day}</h2>
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    <Flame className="w-4 h-4 text-accent" />
                    <span>{selectedDayData.total_calories} kcal</span>
                  </div>
                </div>

                {/* Breakfast */}
                {selectedDayData.meals?.breakfast && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="font-heading text-base flex items-center gap-2">
                        <span className="text-lg">🌅</span>
                        Petit-déjeuner
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <MealCard meal={selectedDayData.meals.breakfast} />
                    </CardContent>
                  </Card>
                )}

                {/* Lunch */}
                {selectedDayData.meals?.lunch && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="font-heading text-base flex items-center gap-2">
                        <span className="text-lg">☀️</span>
                        Déjeuner
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <MealCard meal={selectedDayData.meals.lunch} />
                    </CardContent>
                  </Card>
                )}

                {/* Dinner */}
                {selectedDayData.meals?.dinner && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="font-heading text-base flex items-center gap-2">
                        <span className="text-lg">🌙</span>
                        Dîner
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <MealCard meal={selectedDayData.meals.dinner} />
                    </CardContent>
                  </Card>
                )}

                {/* Snacks */}
                {selectedDayData.meals?.snacks?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="font-heading text-base flex items-center gap-2">
                        <span className="text-lg">🍎</span>
                        Collations
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {selectedDayData.meals.snacks.map((snack, i) => (
                        <div key={i} className="flex justify-between items-center p-2 rounded-lg bg-muted/50">
                          <span>{snack.name}</span>
                          <span className="text-sm text-muted-foreground">{snack.calories} kcal</span>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {/* Shopping List */}
            {currentPlan.shopping_list?.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="font-heading text-lg flex items-center gap-2">
                    <ShoppingCart className="w-5 h-5 text-primary" />
                    Liste de courses
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-2">
                    {currentPlan.shopping_list.slice(0, 8).map((item, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-muted/50 text-sm">
                        <div className="w-2 h-2 rounded-full bg-primary" />
                        {item}
                      </div>
                    ))}
                  </div>
                  {currentPlan.shopping_list.length > 8 && (
                    <Button variant="ghost" size="sm" className="w-full mt-2">
                      Voir tout ({currentPlan.shopping_list.length} articles)
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </Button>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Tips */}
            {currentPlan.tips?.length > 0 && (
              <Card className="border-primary/20 bg-primary/5">
                <CardContent className="p-4">
                  <h3 className="font-semibold mb-2">💡 Conseils</h3>
                  <ul className="space-y-1">
                    {currentPlan.tips.map((tip, i) => (
                      <li key={i} className="text-sm text-muted-foreground">• {tip}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <Utensils className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Aucun plan de repas</p>
            <p className="text-sm text-muted-foreground mt-1">
              Générez votre premier plan personnalisé avec l'IA
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

function MealCard({ meal }) {
  return (
    <div className="space-y-3">
      <h3 className="font-semibold">{meal.name}</h3>
      <div className="flex gap-4 text-sm">
        <span className="flex items-center gap-1">
          <Flame className="w-3 h-3 text-accent" />
          {meal.calories} kcal
        </span>
        <span className="text-muted-foreground">P: {meal.protein}g</span>
        <span className="text-muted-foreground">G: {meal.carbs}g</span>
        <span className="text-muted-foreground">L: {meal.fat}g</span>
      </div>
      {meal.recipe && (
        <p className="text-sm text-muted-foreground leading-relaxed">{meal.recipe}</p>
      )}
    </div>
  );
}
