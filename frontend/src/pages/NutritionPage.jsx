import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import AIWarningDialog from '@/components/AIWarningDialog';
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
  Check,
  Clock,
  ChefHat,
  Heart,
  HeartOff,
  Utensils,
  CalendarPlus,
  StickyNote,
  Loader2,
  BookOpen,
  ShoppingCart,
  X,
  Search,
  ListPlus,
  Newspaper,
  Share2
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
  const [agendaNotes, setAgendaNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [noteDialogOpen, setNoteDialogOpen] = useState(false);
  const [recommendDialogOpen, setRecommendDialogOpen] = useState(false);
  const [aiMealDialogOpen, setAiMealDialogOpen] = useState(false);
  const [recipesDialogOpen, setRecipesDialogOpen] = useState(false);
  const [datePickerOpen, setDatePickerOpen] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loadingRecommend, setLoadingRecommend] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(new Date().toISOString().slice(0, 7));
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().slice(0, 10));
  
  // AI Meal Plan state
  const [aiMealPlan, setAiMealPlan] = useState(null);
  const [loadingMealPlan, setLoadingMealPlan] = useState(false);
  const [mealPlanType, setMealPlanType] = useState('daily');
  const [mealToAdd, setMealToAdd] = useState(null);
  
  // AI Recipes state
  const [recipes, setRecipes] = useState([]);
  const [loadingRecipes, setLoadingRecipes] = useState(false);
  const [favoriteRecipes, setFavoriteRecipes] = useState([]);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  
  // AI Recipe Search state
  const [recipeSearchQuery, setRecipeSearchQuery] = useState('');
  const [searchedRecipe, setSearchedRecipe] = useState(null);
  const [loadingSearch, setLoadingSearch] = useState(false);
  
  // Shopping list state
  const [shoppingList, setShoppingList] = useState([]);
  const [editingItem, setEditingItem] = useState(null);
  
  // Catalog state
  const [catalogRecipes, setCatalogRecipes] = useState([]);
  const [catalogFilter, setCatalogFilter] = useState('all');
  const [catalogDishType, setCatalogDishType] = useState('all');
  const [catalogStats, setCatalogStats] = useState(null);
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  
  // Articles state
  const [articles, setArticles] = useState([]);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [showArticleDialog, setShowArticleDialog] = useState(false);
  
  // Add to agenda state
  const [showAgendaDialog, setShowAgendaDialog] = useState(false);
  const [agendaItem, setAgendaItem] = useState(null);
  const [agendaDate, setAgendaDate] = useState('');
  const [agendaTime, setAgendaTime] = useState('12:00');
  
  // Note state
  const [newNote, setNewNote] = useState({ date: '', content: '' });
  
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
    fetchFavoriteRecipes();
    fetchShoppingList();
    fetchArticles();
  }, []);

  useEffect(() => {
    if (activeTab === 'diary') {
      fetchDiary();
      fetchAgendaNotes();
    }
    if (activeTab === 'catalog') {
      fetchCatalogRecipes();
    }
    if (activeTab === 'shopping') {
      fetchShoppingList();
    }
  }, [activeTab, currentMonth]);

  const fetchArticles = async () => {
    try {
      const response = await axios.get(`${API}/articles`, { withCredentials: true });
      setArticles(response.data.articles || []);
    } catch (error) {
      console.error('Error fetching articles:', error);
    }
  };

  const addToAgenda = async () => {
    if (!agendaItem || !agendaDate) {
      toast.error('Veuillez sélectionner une date');
      return;
    }
    
    try {
      const appointmentData = {
        title: agendaItem.name || agendaItem.title || 'Repas planifié',
        description: agendaItem.description || `Recette: ${agendaItem.name}`,
        datetime: `${agendaDate}T${agendaTime}:00`,
        type: 'meal'
      };
      
      await axios.post(`${API}/appointments`, appointmentData, { withCredentials: true });
      toast.success('Ajouté à l\'agenda !');
      setShowAgendaDialog(false);
      setAgendaItem(null);
      setAgendaDate('');
    } catch (error) {
      toast.error('Erreur lors de l\'ajout');
    }
  };

  const shareArticle = async (article) => {
    try {
      await axios.post(`${API}/social/post`, {
        content: `📰 Article intéressant : "${article.title}"\n\n${article.summary}`,
        type: 'article'
      }, { withCredentials: true });
      toast.success('Article partagé sur le mur !');
    } catch (error) {
      toast.error('Erreur lors du partage');
    }
  };

  const fetchData = async () => {
    try {
      const [summaryRes, logsRes] = await Promise.allSettled([
        axios.get(`${API}/food/daily-summary`, { withCredentials: true }),
        axios.get(`${API}/food/logs`, { withCredentials: true })
      ]);
      if (summaryRes.status === 'fulfilled') setDailySummary(summaryRes.value.data);
      if (logsRes.status === 'fulfilled') setFoodLogs(logsRes.value.data);
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

  const fetchAgendaNotes = async () => {
    try {
      const response = await axios.get(`${API}/agenda/notes?month=${currentMonth}`, { withCredentials: true });
      setAgendaNotes(response.data);
    } catch (error) {
      console.error('Error fetching notes:', error);
    }
  };

  const fetchFavoriteRecipes = async () => {
    try {
      const response = await axios.get(`${API}/recipes/favorites`, { withCredentials: true });
      setFavoriteRecipes(response.data);
    } catch (error) {
      console.error('Error fetching favorites:', error);
    }
  };

  const fetchShoppingList = async () => {
    try {
      const response = await axios.get(`${API}/shopping-list`, { withCredentials: true });
      setShoppingList(response.data);
    } catch (error) {
      console.error('Error fetching shopping list:', error);
    }
  };

  const fetchCatalogRecipes = async (filter = catalogFilter, dishType = catalogDishType) => {
    setLoadingCatalog(true);
    try {
      const params = new URLSearchParams({ limit: '50' });
      if (filter && filter !== 'all') {
        params.append('nutri_score', filter);
      }
      if (dishType && dishType !== 'all') {
        params.append('dish_type', dishType);
      }
      // This endpoint doesn't require auth
      const response = await axios.get(`${API}/recipes/all?${params}`);
      setCatalogRecipes(response.data.recipes || []);
      setCatalogStats(response.data.stats);
    } catch (error) {
      console.error('Error fetching catalog:', error);
      toast.error('Erreur lors du chargement du catalogue');
    } finally {
      setLoadingCatalog(false);
    }
  };

  const addToShoppingList = async (item, quantity = '') => {
    if (!item || !item.trim()) {
      toast.error('Nom de l\'article requis');
      return;
    }
    try {
      await axios.post(`${API}/shopping-list`, { item: item.trim(), quantity }, { withCredentials: true });
      toast.success('Ajouté à la liste de courses');
      fetchShoppingList();
    } catch (error) {
      console.error('Error adding to shopping list:', error);
      toast.error('Erreur lors de l\'ajout: ' + (error.response?.data?.detail || 'Veuillez réessayer'));
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
      toast.success(`${response.data.added_count || items.length} ingrédients ajoutés à la liste de courses`);
      fetchShoppingList();
      // Switch to shopping tab to show the result
      setActiveTab('shopping');
    } catch (error) {
      console.error('Error adding ingredients:', error);
      toast.error('Erreur lors de l\'ajout: ' + (error.response?.data?.detail || 'Veuillez réessayer'));
    }
  };

  const toggleShoppingItem = async (itemId, checked) => {
    try {
      await axios.put(`${API}/shopping-list/${itemId}`, { checked }, { withCredentials: true });
      setShoppingList(prev => prev.map(item => 
        item.item_id === itemId ? { ...item, checked } : item
      ));
    } catch (error) {
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const updateShoppingItem = async (itemId, data) => {
    try {
      await axios.put(`${API}/shopping-list/${itemId}`, data, { withCredentials: true });
      setShoppingList(prev => prev.map(item => 
        item.item_id === itemId ? { ...item, ...data } : item
      ));
      setEditingItem(null);
    } catch (error) {
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const deleteShoppingItem = async (itemId) => {
    try {
      await axios.delete(`${API}/shopping-list/${itemId}`, { withCredentials: true });
      setShoppingList(prev => prev.filter(item => item.item_id !== itemId));
      toast.success('Supprimé de la liste');
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const clearCheckedItems = async () => {
    try {
      await axios.delete(`${API}/shopping-list`, { withCredentials: true });
      setShoppingList(prev => prev.filter(item => !item.checked));
      toast.success('Articles cochés supprimés');
    } catch (error) {
      toast.error('Erreur lors de la suppression');
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

  const handleSaveAgendaNote = async () => {
    if (!newNote.content.trim()) {
      toast.error('Le contenu de la note est requis');
      return;
    }
    
    try {
      await axios.post(`${API}/agenda/notes`, {
        date: newNote.date || selectedDate,
        content: newNote.content,
        type: 'general'
      }, { withCredentials: true });
      toast.success('Note enregistrée');
      setNewNote({ date: '', content: '' });
      fetchAgendaNotes();
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement');
    }
  };

  const handleDeleteAgendaNote = async (noteId) => {
    try {
      await axios.delete(`${API}/agenda/notes/${noteId}`, { withCredentials: true });
      toast.success('Note supprimée');
      fetchAgendaNotes();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
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
      if (error.response?.status === 429) {
        const detail = error.response.data?.detail;
        setRecommendations({ analysis: detail?.message || 'Limite quotidienne IA atteinte', alternatives: [], tips: ['Revenez demain pour plus de recommandations IA !'] });
        toast.error(detail?.message || 'Limite quotidienne IA atteinte.');
      } else {
        setRecommendations({ analysis: 'Erreur', alternatives: [], tips: [] });
      }
    } finally {
      setLoadingRecommend(false);
    }
  };

  // AI Meal Plan Generation
  const generateMealPlan = async (type) => {
    // Reset state before generating new plan
    setAiMealPlan(null);
    setLoadingMealPlan(true);
    setMealPlanType(type);
    setAiMealDialogOpen(true);
    
    try {
      const response = await axios.post(`${API}/meals/generate`, { type }, { withCredentials: true });
      setAiMealPlan(response.data);
      if (response.data.from_cache) {
        toast.success('Plan récupéré depuis le cache !');
      }
    } catch (error) {
      console.error('Error generating meal plan:', error);
      if (error.response?.status === 429) {
        const detail = error.response.data?.detail;
        toast.error(detail?.message || 'Limite quotidienne IA atteinte. Revenez demain !');
      } else {
        toast.error('Erreur lors de la génération. Veuillez réessayer.');
      }
      setAiMealPlan(null);
    } finally {
      setLoadingMealPlan(false);
    }
  };

  // Regenerate meal plan
  const regenerateMealPlan = () => {
    generateMealPlan(mealPlanType);
  };

  // Open date picker to select date for meal
  const openDatePickerForMeal = (meal, mealType) => {
    setMealToAdd({ meal, mealType });
    setDatePickerOpen(true);
  };

  // Add meal to diary with selected date
  const addMealToDiary = async (meal, mealType, date = null) => {
    const targetDate = date || selectedDate;
    try {
      await axios.post(`${API}/meals/add-to-diary`, {
        meal,
        meal_type: mealType,
        date: targetDate
      }, { withCredentials: true });
      
      // Also add to agenda notes for visibility
      await axios.post(`${API}/agenda/notes`, {
        date: targetDate,
        content: `🍽️ ${mealTypes.find(t => t.value === mealType)?.label || 'Repas'}: ${meal.name} (${meal.calories} kcal)`,
        type: 'meal_plan'
      }, { withCredentials: true });
      
      toast.success(`${meal.name} ajouté au ${new Date(targetDate).toLocaleDateString('fr-FR')}`);
      fetchData();
      fetchAgendaNotes();
      setDatePickerOpen(false);
      setMealToAdd(null);
    } catch (error) {
      toast.error('Erreur lors de l\'ajout');
    }
  };

  // Confirm add meal with selected date
  const confirmAddMeal = () => {
    if (mealToAdd) {
      addMealToDiary(mealToAdd.meal, mealToAdd.mealType, selectedDate);
    }
  };

  // AI Recipes Generation
  const generateRecipes = async () => {
    // Reset state before generating
    setRecipes([]);
    setSelectedRecipe(null);
    setLoadingRecipes(true);
    setRecipesDialogOpen(true);
    
    try {
      const response = await axios.post(`${API}/recipes/generate`, { count: 10 }, { withCredentials: true });
      setRecipes(response.data.recipes || []);
    } catch (error) {
      console.error('Error generating recipes:', error);
      if (error.response?.status === 429) {
        const detail = error.response.data?.detail;
        toast.error(detail?.message || 'Limite quotidienne IA atteinte. Revenez demain !');
      } else {
        toast.error('Erreur lors de la génération. Veuillez réessayer.');
      }
    } finally {
      setLoadingRecipes(false);
    }
  };

  // Regenerate recipes
  const regenerateRecipes = () => {
    generateRecipes();
  };

  // Search recipe by AI
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
        if (response.data.from_cache) {
          toast.success('Recette trouvée depuis le cache !');
        } else {
          toast.success('Recette trouvée !');
        }
      } else {
        toast.error('Aucune recette générée. Réessayez avec une autre description.');
      }
    } catch (error) {
      console.error('Error searching recipe:', error);
      if (error.response?.status === 429) {
        const detail = error.response.data?.detail;
        toast.error(detail?.message || 'Limite quotidienne IA atteinte. Revenez demain !');
      } else {
        const errorMsg = error.response?.data?.detail || 'Erreur lors de la recherche';
        toast.error(errorMsg + '. Veuillez réessayer.');
      }
    } finally {
      setLoadingSearch(false);
    }
  };

  const toggleFavoriteRecipe = async (recipe, e) => {
    if (e) e.stopPropagation();
    const isFavorite = favoriteRecipes.some(f => f.recipe.name === recipe.name);
    
    try {
      if (isFavorite) {
        const fav = favoriteRecipes.find(f => f.recipe.name === recipe.name);
        await axios.delete(`${API}/recipes/favorites/${fav.favorite_id}`, { withCredentials: true });
        // Update local state immediately
        setFavoriteRecipes(prev => prev.filter(f => f.recipe.name !== recipe.name));
        toast.success('Recette retirée des favoris');
      } else {
        const response = await axios.post(`${API}/recipes/favorites`, { recipe }, { withCredentials: true });
        // Update local state immediately
        setFavoriteRecipes(prev => [...prev, { favorite_id: response.data.favorite_id, recipe }]);
        toast.success('Recette ajoutée aux favoris');
      }
    } catch (error) {
      if (error.response?.status === 400) {
        toast.error('Cette recette est déjà dans vos favoris');
      } else {
        toast.error('Erreur lors de la mise à jour');
      }
    }
  };

  // Add recipe to agenda
  const addRecipeToAgenda = async (recipe, date) => {
    try {
      await axios.post(`${API}/agenda/notes`, {
        date: date || selectedDate,
        content: `🍽️ Recette planifiée: ${recipe.name} (${recipe.calories} kcal)`,
        type: 'meal_plan'
      }, { withCredentials: true });
      toast.success('Recette ajoutée à l\'agenda');
      fetchAgendaNotes();
    } catch (error) {
      toast.error('Erreur lors de l\'ajout');
    }
  };

  // Add all meals of the day to favorites
  const addAllMealsToFavorites = async (meals) => {
    try {
      const mealList = Object.values(meals).filter(m => m && m.name);
      for (const meal of mealList) {
        const isFavorite = favoriteRecipes.some(f => f.recipe.name === meal.name);
        if (!isFavorite) {
          await axios.post(`${API}/recipes/favorites`, { recipe: meal }, { withCredentials: true });
        }
      }
      toast.success(`${mealList.length} repas ajoutés aux favoris`);
      fetchFavoriteRecipes();
    } catch (error) {
      toast.error('Erreur lors de l\'ajout');
    }
  };

  // Add weekly plan to agenda
  const addWeeklyPlanToAgenda = async (days) => {
    try {
      const today = new Date();
      for (let i = 0; i < days.length; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() + i);
        const dateStr = date.toISOString().slice(0, 10);
        const day = days[i];
        
        const meals = Object.entries(day.meals || {})
          .filter(([_, m]) => m && m.name)
          .map(([type, m]) => `${mealTypes.find(t => t.value === type)?.emoji || '🍽️'} ${m.name}`)
          .join(', ');
        
        await axios.post(`${API}/agenda/notes`, {
          date: dateStr,
          content: `📅 ${day.day}: ${meals}`,
          type: 'meal_plan'
        }, { withCredentials: true });
      }
      toast.success('Plan hebdomadaire ajouté à l\'agenda');
      fetchAgendaNotes();
    } catch (error) {
      toast.error('Erreur lors de l\'ajout');
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

  const getNotesForDate = (date) => {
    return agendaNotes.filter(n => n.date === date);
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
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="today" className="flex items-center gap-1 text-xs px-1">
              <Apple className="w-3 h-3" />
              <span className="hidden sm:inline">Aujourd'hui</span>
              <span className="sm:hidden">Jour</span>
            </TabsTrigger>
            <TabsTrigger value="diary" className="flex items-center gap-1 text-xs px-1">
              <Calendar className="w-3 h-3" />
              <span className="hidden sm:inline">Agenda</span>
              <span className="sm:hidden">📅</span>
            </TabsTrigger>
            <TabsTrigger value="ai" className="flex items-center gap-1 text-xs px-1">
              <Sparkles className="w-3 h-3" />
              IA
            </TabsTrigger>
            <TabsTrigger value="catalog" className="flex items-center gap-1 text-xs px-1">
              <BookOpen className="w-3 h-3" />
              <span className="hidden sm:inline">Recettes</span>
              <span className="sm:hidden">📖</span>
            </TabsTrigger>
            <TabsTrigger value="favorites" className="flex items-center gap-1 text-xs px-1">
              <Heart className="w-3 h-3" />
              <span className="hidden sm:inline">Favoris</span>
              <span className="sm:hidden">❤️</span>
            </TabsTrigger>
            <TabsTrigger value="shopping" className="flex items-center gap-1 text-xs px-1">
              <ShoppingCart className="w-3 h-3" />
              <span className="hidden sm:inline">Courses</span>
              <span className="sm:hidden">🛒</span>
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
                            {log.source === 'ai_plan' && (
                              <Badge variant="secondary" className="text-xs">IA</Badge>
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

            {/* Add Note Section */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="font-heading text-base flex items-center gap-2">
                  <StickyNote className="w-4 h-4" />
                  Ajouter une note
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input
                  type="date"
                  value={newNote.date || selectedDate}
                  onChange={(e) => setNewNote({ ...newNote, date: e.target.value })}
                />
                <Textarea
                  placeholder="Écrire une note pour cette date..."
                  value={newNote.content}
                  onChange={(e) => setNewNote({ ...newNote, content: e.target.value })}
                  rows={2}
                />
                <Button onClick={handleSaveAgendaNote} size="sm" className="w-full">
                  <Plus className="w-4 h-4 mr-2" />
                  Enregistrer la note
                </Button>
              </CardContent>
            </Card>

            {/* Diary Entries */}
            {diary.length > 0 ? (
              diary.map((day) => {
                const dayNotes = getNotesForDate(day.date);
                return (
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
                      {/* Notes for this day */}
                      {dayNotes.length > 0 && (
                        <div className="mb-3 space-y-2">
                          {dayNotes.map((note) => (
                            <div key={note.note_id} className="flex items-start justify-between p-2 rounded-lg bg-primary/5 border border-primary/20">
                              <div className="flex items-start gap-2">
                                <StickyNote className="w-4 h-4 text-primary mt-0.5" />
                                <p className="text-sm">{note.content}</p>
                              </div>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                                onClick={() => handleDeleteAgendaNote(note.note_id)}
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      <div className="space-y-2">
                        {day.meals.map((meal, i) => (
                          <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-muted/30">
                            <div className="flex items-center gap-2">
                              <span>{mealTypes.find(t => t.value === meal.meal_type)?.emoji || '🍽️'}</span>
                              <span className="text-sm">{meal.food_name}</span>
                              {meal.source === 'ai_plan' && (
                                <Badge variant="secondary" className="text-xs">IA</Badge>
                              )}
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
                );
              })
            ) : (
              <div className="text-center py-12">
                <Calendar className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Aucun repas ce mois-ci</p>
              </div>
            )}
          </TabsContent>

          {/* AI Tab */}
          <TabsContent value="ai" className="space-y-4 mt-4">
            {/* AI Recipe Search */}
            <Card className="border-primary/30 bg-gradient-to-br from-primary/5 to-secondary/5">
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <Search className="w-5 h-5 text-primary" />
                  Rechercher une recette
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Décrivez la recette que vous cherchez et l'IA la créera pour vous !
                </p>
                <Textarea
                  placeholder='Ex: "Trouve moi une recette avec des crevettes et du riz faites en 30 minutes maximum, saine et bon pour la santé"'
                  value={recipeSearchQuery}
                  onChange={(e) => setRecipeSearchQuery(e.target.value)}
                  rows={3}
                  className="resize-none"
                />
                <Button 
                  onClick={searchRecipeByAI}
                  disabled={loadingSearch || !recipeSearchQuery.trim()}
                  className="w-full rounded-full"
                >
                  {loadingSearch ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Recherche en cours...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" />
                      Trouver ma recette
                    </>
                  )}
                </Button>
                
                {/* Search Result */}
                {searchedRecipe && (
                  <Card className="mt-4 border-primary/50">
                    <CardContent className="p-4 space-y-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-lg">{searchedRecipe.name}</h3>
                            {searchedRecipe.nutri_score && (
                              <span className={`w-6 h-6 rounded text-white text-xs flex items-center justify-center font-bold ${getNutriScoreColor(searchedRecipe.nutri_score)}`}>
                                {searchedRecipe.nutri_score}
                              </span>
                            )}
                          </div>
                          <div className="flex gap-2 text-sm text-muted-foreground mt-1">
                            <span>{searchedRecipe.calories} kcal</span>
                            <span>•</span>
                            <span>{searchedRecipe.prep_time}</span>
                            <span>•</span>
                            <span>{searchedRecipe.difficulty}</span>
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => toggleFavoriteRecipe(searchedRecipe)}
                            title="Ajouter aux favoris"
                          >
                            {favoriteRecipes.some(f => f.recipe.name === searchedRecipe.name) ? (
                              <Heart className="w-4 h-4 text-destructive fill-destructive" />
                            ) : (
                              <Heart className="w-4 h-4" />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => addRecipeToAgenda(searchedRecipe)}
                            title="Ajouter à l'agenda"
                          >
                            <CalendarPlus className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-4 gap-2 text-center text-xs">
                        <div className="p-2 rounded bg-muted">
                          <p className="font-bold">{searchedRecipe.protein || 0}g</p>
                          <p className="text-muted-foreground">Protéines</p>
                        </div>
                        <div className="p-2 rounded bg-muted">
                          <p className="font-bold">{searchedRecipe.carbs || 0}g</p>
                          <p className="text-muted-foreground">Glucides</p>
                        </div>
                        <div className="p-2 rounded bg-muted">
                          <p className="font-bold">{searchedRecipe.fat || 0}g</p>
                          <p className="text-muted-foreground">Lipides</p>
                        </div>
                        <div className="p-2 rounded bg-muted">
                          <p className="font-bold">{searchedRecipe.servings || 2}</p>
                          <p className="text-muted-foreground">Portions</p>
                        </div>
                      </div>
                      
                      {searchedRecipe.ingredients && searchedRecipe.ingredients.length > 0 && (
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <p className="font-medium text-sm">📝 Ingrédients</p>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => addIngredientsToShoppingList(searchedRecipe.ingredients)}
                              className="text-xs"
                            >
                              <ListPlus className="w-3 h-3 mr-1" />
                              Ajouter aux courses
                            </Button>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {searchedRecipe.ingredients.map((ing, j) => (
                              <Badge key={j} variant="outline" className="text-xs">
                                {ing.quantity} {ing.item}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {searchedRecipe.steps && searchedRecipe.steps.length > 0 && (
                        <div>
                          <p className="font-medium text-sm mb-2">👨‍🍳 Préparation</p>
                          <ol className="space-y-2">
                            {searchedRecipe.steps.map((step, j) => (
                              <li key={j} className="text-sm text-muted-foreground flex gap-2">
                                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary/20 text-primary text-xs flex items-center justify-center font-medium">
                                  {j + 1}
                                </span>
                                <span>{step.replace(/^Étape \d+:\s*/i, '')}</span>
                              </li>
                            ))}
                          </ol>
                        </div>
                      )}
                      
                      {searchedRecipe.tips && (
                        <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
                          <p className="text-sm">💡 {searchedRecipe.tips}</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}
              </CardContent>
            </Card>

            {/* AI Meal Plan Generation */}
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <Utensils className="w-5 h-5 text-primary" />
                  Générer des repas IA
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  L'IA génère des repas personnalisés selon votre profil, vos goûts et vos objectifs.
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <Button 
                    onClick={() => generateMealPlan('daily')}
                    className="rounded-full"
                    variant="outline"
                  >
                    <CalendarPlus className="w-4 h-4 mr-2" />
                    Plan journalier
                  </Button>
                  <Button 
                    onClick={() => generateMealPlan('weekly')}
                    className="rounded-full"
                  >
                    <Calendar className="w-4 h-4 mr-2" />
                    Plan hebdomadaire
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* AI Recipes Generation */}
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <ChefHat className="w-5 h-5 text-secondary" />
                  Recettes IA
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Découvrez des recettes simples, économiques et adaptées à vos préférences.
                </p>
                <Button 
                  onClick={generateRecipes}
                  className="w-full rounded-full shadow-glow-purple bg-secondary hover:bg-secondary/90"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Générer 10 recettes
                </Button>
              </CardContent>
            </Card>

            {/* Favorite Recipes */}
            {favoriteRecipes.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="font-heading text-lg flex items-center gap-2">
                    <Heart className="w-5 h-5 text-destructive" />
                    Mes recettes favorites ({favoriteRecipes.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-48">
                    <div className="space-y-2">
                      {favoriteRecipes.map((fav) => (
                        <div 
                          key={fav.favorite_id}
                          className="flex items-center justify-between p-3 rounded-xl bg-muted/50"
                        >
                          <div>
                            <p className="font-medium text-sm">{fav.recipe.name}</p>
                            <div className="flex gap-2 text-xs text-muted-foreground">
                              <span>{fav.recipe.calories} kcal</span>
                              <span>•</span>
                              <span>{fav.recipe.prep_time}</span>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-destructive"
                            onClick={() => toggleFavoriteRecipe(fav.recipe)}
                          >
                            <HeartOff className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Catalog Tab - Base de recettes */}
          <TabsContent value="catalog" className="space-y-4 mt-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-secondary" />
                  Catalogue de recettes
                </CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  {catalogStats ? `${catalogStats.total} recettes disponibles` : 'Chargement...'}
                </p>
              </CardHeader>
              <CardContent>
                {/* Nutri-Score Filter */}
                <div className="flex gap-2 mb-3 flex-wrap">
                  {['all', 'A', 'B', 'C', 'D'].map((score) => (
                    <Button
                      key={score}
                      variant={catalogFilter === score ? 'default' : 'outline'}
                      size="sm"
                      className={`h-8 ${score !== 'all' ? getNutriScoreColor(score) + (catalogFilter === score ? '' : ' bg-opacity-20') : ''}`}
                      onClick={() => {
                        setCatalogFilter(score);
                        fetchCatalogRecipes(score, catalogDishType);
                      }}
                    >
                      {score === 'all' ? 'Toutes' : `Nutri-Score ${score}`}
                      {catalogStats && score !== 'all' && (
                        <span className="ml-1 text-xs opacity-80">
                          ({catalogStats.by_nutri_score?.[score] || 0})
                        </span>
                      )}
                    </Button>
                  ))}
                </div>

                {/* Dish Type Filter */}
                <div className="flex gap-2 mb-4 flex-wrap">
                  {[
                    { value: 'all', label: 'Tous', emoji: '🍽️' },
                    { value: 'entree', label: 'Entrée', emoji: '🥗' },
                    { value: 'plat', label: 'Plat', emoji: '🍝' },
                    { value: 'dessert', label: 'Dessert', emoji: '🍰' },
                    { value: 'accompagnement', label: 'Accompagnement', emoji: '🥔' },
                    { value: 'viande', label: 'Viande', emoji: '🥩' },
                    { value: 'gouter', label: 'Goûter', emoji: '🧁' },
                  ].map((type) => (
                    <Button
                      key={type.value}
                      variant={catalogDishType === type.value ? 'default' : 'outline'}
                      size="sm"
                      className="h-8"
                      onClick={() => {
                        setCatalogDishType(type.value);
                        fetchCatalogRecipes(catalogFilter, type.value);
                      }}
                    >
                      <span className="mr-1">{type.emoji}</span>
                      {type.label}
                      {catalogStats?.by_dish_type && type.value !== 'all' && (
                        <span className="ml-1 text-xs opacity-80">
                          ({catalogStats.by_dish_type?.[type.value] || 0})
                        </span>
                      )}
                    </Button>
                  ))}
                </div>

                {/* Stats by Score */}
                {catalogStats && (
                  <div className="grid grid-cols-4 gap-2 mb-4">
                    {['A', 'B', 'C', 'D'].map((score) => (
                      <div 
                        key={score}
                        className={`p-2 rounded-lg text-center text-white ${getNutriScoreColor(score)}`}
                      >
                        <p className="font-bold text-lg">{catalogStats.by_nutri_score?.[score] || 0}</p>
                        <p className="text-xs opacity-90">Score {score}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Recipes List */}
                {loadingCatalog ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                  </div>
                ) : catalogRecipes.length > 0 ? (
                  <ScrollArea className="h-96">
                    <div className="space-y-2">
                      {catalogRecipes.map((recipe) => (
                        <Card 
                          key={recipe.id}
                          className="cursor-pointer hover:border-primary/50 transition-colors"
                          onClick={() => setSelectedRecipe(selectedRecipe?.id === recipe.id ? null : recipe)}
                        >
                          <CardContent className="p-3">
                            <div className="flex items-start gap-3">
                              {recipe.image && (
                                <img 
                                  src={recipe.image} 
                                  alt={recipe.name}
                                  className="w-16 h-16 rounded-lg object-cover"
                                  onError={(e) => e.target.style.display = 'none'}
                                />
                              )}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <p className="font-semibold text-sm truncate">{recipe.name}</p>
                                  <span className={`w-5 h-5 rounded text-white text-xs flex items-center justify-center font-bold flex-shrink-0 ${getNutriScoreColor(recipe.nutri_score)}`}>
                                    {recipe.nutri_score}
                                  </span>
                                </div>
                                <div className="flex gap-2 text-xs text-muted-foreground mt-1">
                                  <span>{recipe.calories} kcal</span>
                                  <span>•</span>
                                  <span>{recipe.prep_time}</span>
                                  <span>•</span>
                                  <span>{recipe.difficulty}</span>
                                </div>
                                
                                {/* Expanded details */}
                                {selectedRecipe?.id === recipe.id && (
                                  <div className="mt-3 pt-3 border-t space-y-3">
                                    <div className="grid grid-cols-4 gap-2 text-center text-xs">
                                      <div className="p-2 rounded bg-muted">
                                        <p className="font-bold">{recipe.protein}g</p>
                                        <p className="text-muted-foreground">Prot.</p>
                                      </div>
                                      <div className="p-2 rounded bg-muted">
                                        <p className="font-bold">{recipe.carbs}g</p>
                                        <p className="text-muted-foreground">Gluc.</p>
                                      </div>
                                      <div className="p-2 rounded bg-muted">
                                        <p className="font-bold">{recipe.fat}g</p>
                                        <p className="text-muted-foreground">Lip.</p>
                                      </div>
                                      <div className="p-2 rounded bg-muted">
                                        <p className="font-bold">{recipe.servings}</p>
                                        <p className="text-muted-foreground">Pers.</p>
                                      </div>
                                    </div>
                                    
                                    {recipe.ingredients && (
                                      <div>
                                        <div className="flex items-center justify-between mb-2">
                                          <p className="font-medium text-xs">📝 Ingrédients</p>
                                          <Button
                                            variant="outline"
                                            size="sm"
                                            className="h-6 text-xs"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              addIngredientsToShoppingList(recipe.ingredients);
                                            }}
                                          >
                                            <ListPlus className="w-3 h-3 mr-1" />
                                            Courses
                                          </Button>
                                        </div>
                                        <div className="flex flex-wrap gap-1">
                                          {recipe.ingredients.map((ing, j) => (
                                            <Badge key={j} variant="outline" className="text-xs">
                                              {ing.quantity} {ing.item}
                                            </Badge>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                    
                                    {recipe.steps && (
                                      <div>
                                        <p className="font-medium text-xs mb-2">👨‍🍳 Préparation</p>
                                        <ol className="space-y-1">
                                          {recipe.steps.map((step, j) => (
                                            <li key={j} className="text-xs text-muted-foreground flex gap-2">
                                              <span className="flex-shrink-0 w-4 h-4 rounded-full bg-primary/20 text-primary text-xs flex items-center justify-center">
                                                {j + 1}
                                              </span>
                                              <span>{step}</span>
                                            </li>
                                          ))}
                                        </ol>
                                      </div>
                                    )}
                                    
                                    <div className="flex gap-2">
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        className="h-7 text-xs"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          toggleFavoriteRecipe(recipe);
                                        }}
                                      >
                                        {favoriteRecipes.some(f => f.recipe.name === recipe.name) ? (
                                          <>
                                            <Heart className="w-3 h-3 mr-1 fill-destructive text-destructive" />
                                            Favori
                                          </>
                                        ) : (
                                          <>
                                            <Heart className="w-3 h-3 mr-1" />
                                            Ajouter
                                          </>
                                        )}
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="ghost"
                                        className="h-7 text-xs"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          addRecipeToAgenda(recipe);
                                        }}
                                      >
                                        <CalendarPlus className="w-3 h-3 mr-1" />
                                        Agenda
                                      </Button>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </ScrollArea>
                ) : (
                  <div className="text-center py-12">
                    <BookOpen className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">Aucune recette trouvée</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Favorites Tab */}
          <TabsContent value="favorites" className="space-y-4 mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <Heart className="w-5 h-5 text-destructive fill-destructive" />
                  Mes recettes favorites
                </CardTitle>
              </CardHeader>
              <CardContent>
                {favoriteRecipes.length > 0 ? (
                  <div className="space-y-3">
                    {favoriteRecipes.map((fav) => (
                      <Card 
                        key={fav.favorite_id}
                        className="cursor-pointer hover:border-primary/50 transition-colors"
                        onClick={() => setSelectedRecipe(selectedRecipe?.name === fav.recipe.name ? null : fav.recipe)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <p className="font-semibold">{fav.recipe.name}</p>
                                {fav.recipe.nutri_score && (
                                  <span className={`w-6 h-6 rounded text-white text-xs flex items-center justify-center font-bold ${getNutriScoreColor(fav.recipe.nutri_score)}`}>
                                    {fav.recipe.nutri_score}
                                  </span>
                                )}
                              </div>
                              <div className="flex gap-2 text-xs text-muted-foreground mt-1">
                                <span>{fav.recipe.calories} kcal</span>
                                <span>•</span>
                                <span>{fav.recipe.prep_time || '15 min'}</span>
                                {fav.recipe.difficulty && (
                                  <>
                                    <span>•</span>
                                    <span>{fav.recipe.difficulty}</span>
                                  </>
                                )}
                              </div>
                            </div>
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  addRecipeToAgenda(fav.recipe);
                                }}
                                title="Ajouter à l'agenda"
                              >
                                <CalendarPlus className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-destructive"
                                onClick={(e) => toggleFavoriteRecipe(fav.recipe, e)}
                              >
                                <HeartOff className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                          
                          {/* Expanded recipe details */}
                          {selectedRecipe?.name === fav.recipe.name && (
                            <div className="mt-4 pt-4 border-t space-y-4">
                              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                                <div className="p-2 rounded bg-muted">
                                  <p className="font-bold">{fav.recipe.protein || 0}g</p>
                                  <p className="text-muted-foreground">Protéines</p>
                                </div>
                                <div className="p-2 rounded bg-muted">
                                  <p className="font-bold">{fav.recipe.carbs || 0}g</p>
                                  <p className="text-muted-foreground">Glucides</p>
                                </div>
                                <div className="p-2 rounded bg-muted">
                                  <p className="font-bold">{fav.recipe.fat || 0}g</p>
                                  <p className="text-muted-foreground">Lipides</p>
                                </div>
                                <div className="p-2 rounded bg-muted">
                                  <p className="font-bold">{fav.recipe.servings || 2}</p>
                                  <p className="text-muted-foreground">Portions</p>
                                </div>
                              </div>
                              
                              {fav.recipe.ingredients && fav.recipe.ingredients.length > 0 && (
                                <div>
                                  <div className="flex items-center justify-between mb-2">
                                    <p className="font-medium text-sm">📝 Ingrédients</p>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        addIngredientsToShoppingList(fav.recipe.ingredients);
                                      }}
                                      className="text-xs h-7"
                                    >
                                      <ListPlus className="w-3 h-3 mr-1" />
                                      Ajouter aux courses
                                    </Button>
                                  </div>
                                  <div className="flex flex-wrap gap-1">
                                    {fav.recipe.ingredients.map((ing, j) => (
                                      <Badge key={j} variant="outline" className="text-xs">
                                        {ing.quantity} {ing.item}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                              
                              {fav.recipe.steps && fav.recipe.steps.length > 0 && (
                                <div>
                                  <p className="font-medium text-sm mb-2">👨‍🍳 Préparation</p>
                                  <ol className="space-y-2">
                                    {fav.recipe.steps.map((step, j) => (
                                      <li key={j} className="text-sm text-muted-foreground flex gap-2">
                                        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary/20 text-primary text-xs flex items-center justify-center font-medium">
                                          {j + 1}
                                        </span>
                                        <span>{step.replace(/^Étape \d+:\s*/i, '')}</span>
                                      </li>
                                    ))}
                                  </ol>
                                </div>
                              )}
                              
                              {fav.recipe.tips && (
                                <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
                                  <p className="text-sm">💡 {fav.recipe.tips}</p>
                                </div>
                              )}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Heart className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">Aucune recette favorite</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Générez des recettes dans l'onglet IA et ajoutez-les en favoris
                    </p>
                    <Button 
                      variant="outline" 
                      className="mt-4"
                      onClick={() => setActiveTab('ai')}
                    >
                      <Sparkles className="w-4 h-4 mr-2" />
                      Générer des recettes
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Shopping List Tab */}
          <TabsContent value="shopping" className="space-y-4 mt-4">
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="font-heading text-lg flex items-center gap-2">
                    <ShoppingCart className="w-5 h-5 text-primary" />
                    Liste de courses
                  </CardTitle>
                  {shoppingList.some(item => item.checked) && (
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={clearCheckedItems}
                      className="text-xs"
                    >
                      <Trash2 className="w-3 h-3 mr-1" />
                      Supprimer cochés
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {shoppingList.length > 0 ? (
                  <div className="space-y-4">
                    {/* Group by category */}
                    {Object.entries(
                      shoppingList.reduce((acc, item) => {
                        const cat = item.category || '📦 Autres';
                        if (!acc[cat]) acc[cat] = [];
                        acc[cat].push(item);
                        return acc;
                      }, {})
                    ).sort(([a], [b]) => a.localeCompare(b)).map(([category, items]) => (
                      <div key={category} className="space-y-2">
                        <h4 className="text-sm font-semibold text-primary">{category}</h4>
                        {items.map((item) => (
                          <div 
                            key={item.item_id}
                            className={`flex items-center justify-between p-3 rounded-xl ${
                              item.checked ? 'bg-muted/30 opacity-60' : 'bg-muted/50'
                            }`}
                          >
                            <div className="flex items-center gap-3 flex-1">
                              <Checkbox
                                checked={item.checked}
                                onCheckedChange={(checked) => toggleShoppingItem(item.item_id, checked)}
                              />
                              <div className="flex-1">
                                <p className={`font-medium text-sm ${item.checked ? 'line-through' : ''}`}>
                                  {item.display_name}
                                </p>
                                {editingItem === item.item_id ? (
                                  <div className="flex gap-2 mt-1">
                                    <Input
                                      defaultValue={item.quantity}
                                      placeholder="Quantité"
                                      className="h-7 text-xs w-20"
                                      onBlur={(e) => {
                                        updateShoppingItem(item.item_id, { quantity: e.target.value });
                                      }}
                                    />
                                    <Input
                                      type="number"
                                      defaultValue={item.portions || 1}
                                      placeholder="Portions"
                                      className="h-7 text-xs w-16"
                                      min="1"
                                      onBlur={(e) => {
                                        updateShoppingItem(item.item_id, { portions: parseInt(e.target.value) || 1 });
                                      }}
                                    />
                                    <Button size="sm" variant="ghost" className="h-7 px-2" onClick={() => setEditingItem(null)}>
                                      <Check className="w-3 h-3" />
                                    </Button>
                                  </div>
                                ) : (
                                  <p className="text-xs text-muted-foreground cursor-pointer hover:text-primary" onClick={() => setEditingItem(item.item_id)}>
                                    {item.quantity || 'Quantité ?'} {item.portions > 1 ? `• ${item.portions} portions` : ''}
                                    <span className="ml-1 text-primary">✏️</span>
                                  </p>
                                )}
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-destructive"
                              onClick={() => deleteShoppingItem(item.item_id)}
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <ShoppingCart className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">Liste de courses vide</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Ajoutez des ingrédients depuis les recettes
                    </p>
                  </div>
                )}

                {/* Add item manually */}
                <div className="mt-4 pt-4 border-t">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Ajouter un article..."
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && e.target.value) {
                          addToShoppingList(e.target.value);
                          e.target.value = '';
                        }
                      }}
                    />
                    <Button
                      size="icon"
                      onClick={(e) => {
                        const input = e.target.closest('div').querySelector('input');
                        if (input.value) {
                          addToShoppingList(input.value);
                          input.value = '';
                        }
                      }}
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Articles Section */}
        {articles.length > 0 && activeTab === 'diary' && (
          <div className="mt-6">
            <h3 className="font-heading text-lg mb-3 flex items-center gap-2">
              <Newspaper className="w-5 h-5 text-primary" />
              Articles du jour
            </h3>
            <div className="space-y-3">
              {articles.slice(0, 3).map((article) => (
                <Card 
                  key={article.id} 
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => { setSelectedArticle(article); setShowArticleDialog(true); }}
                >
                  <CardContent className="p-3">
                    <div className="flex gap-3">
                      <img 
                        src={article.image} 
                        alt={article.title}
                        className="w-20 h-20 rounded-lg object-cover flex-shrink-0"
                      />
                      <div className="flex-1 min-w-0">
                        <Badge variant="secondary" className="text-[10px] mb-1">{article.category}</Badge>
                        <h4 className="font-medium text-sm line-clamp-2">{article.title}</h4>
                        <p className="text-xs text-muted-foreground mt-1">{article.source} • {article.read_time}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Article Dialog */}
      <Dialog open={showArticleDialog} onOpenChange={setShowArticleDialog}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
          {selectedArticle && (
            <>
              <DialogHeader>
                <DialogTitle className="text-lg pr-4">{selectedArticle.title}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <img 
                  src={selectedArticle.image} 
                  alt={selectedArticle.title}
                  className="w-full h-48 rounded-lg object-cover"
                />
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Badge variant="secondary">{selectedArticle.category}</Badge>
                  <span>{selectedArticle.source}</span>
                  <span>•</span>
                  <span>{selectedArticle.read_time}</span>
                </div>
                <div className="prose prose-sm dark:prose-invert whitespace-pre-wrap text-sm">
                  {selectedArticle.content}
                </div>
                <DialogFooter className="flex-row gap-2">
                  <Button variant="outline" className="flex-1" onClick={() => setShowArticleDialog(false)}>
                    Fermer
                  </Button>
                  <Button className="flex-1" onClick={() => { shareArticle(selectedArticle); setShowArticleDialog(false); }}>
                    <Share2 className="w-4 h-4 mr-2" />
                    Partager
                  </Button>
                </DialogFooter>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Add to Agenda Dialog */}
      <Dialog open={showAgendaDialog} onOpenChange={setShowAgendaDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ajouter à l'agenda</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {agendaItem && (
              <p className="text-sm text-muted-foreground">
                {agendaItem.name || agendaItem.title}
              </p>
            )}
            <div className="space-y-2">
              <label className="text-sm font-medium">Date</label>
              <Input
                type="date"
                value={agendaDate}
                onChange={(e) => setAgendaDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Heure</label>
              <Input
                type="time"
                value={agendaTime}
                onChange={(e) => setAgendaTime(e.target.value)}
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAgendaDialog(false)}>Annuler</Button>
              <Button onClick={addToAgenda}>Ajouter</Button>
            </DialogFooter>
          </div>
        </DialogContent>
      </Dialog>

      {/* Date Picker Dialog for adding meals */}
      <Dialog open={datePickerOpen} onOpenChange={setDatePickerOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Choisir la date</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {mealToAdd && (
              <p className="text-sm text-muted-foreground">
                Ajouter "{mealToAdd.meal.name}" à quelle date ?
              </p>
            )}
            <Input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            />
            <DialogFooter>
              <Button variant="outline" onClick={() => setDatePickerOpen(false)}>
                Annuler
              </Button>
              <Button onClick={confirmAddMeal}>
                <CalendarPlus className="w-4 h-4 mr-2" />
                Ajouter
              </Button>
            </DialogFooter>
          </div>
        </DialogContent>
      </Dialog>

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
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
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

      {/* AI Meal Plan Dialog */}
      <Dialog open={aiMealDialogOpen} onOpenChange={setAiMealDialogOpen}>
        <DialogContent className="max-h-[90vh] overflow-y-auto max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Utensils className="w-5 h-5 text-primary" />
              Plan repas {mealPlanType === 'daily' ? 'du jour' : 'de la semaine'}
            </DialogTitle>
          </DialogHeader>
          
          {loadingMealPlan ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-10 h-10 animate-spin text-primary mb-4" />
              <p className="text-muted-foreground">Génération en cours...</p>
              <p className="text-xs text-muted-foreground">L'IA prépare vos repas personnalisés</p>
            </div>
          ) : aiMealPlan?.meal_plan ? (
            <ScrollArea className="max-h-[55vh]">
              <div className="space-y-4 pr-4">
                {mealPlanType === 'daily' && aiMealPlan.meal_plan.meals ? (
                  // Daily plan
                  <>
                    {['breakfast', 'lunch', 'dinner'].map((mealKey) => {
                      const meal = aiMealPlan.meal_plan.meals[mealKey];
                      if (!meal) return null;
                      const mealType = mealTypes.find(t => t.value === mealKey);
                      const isFav = favoriteRecipes.some(f => f.recipe.name === meal.name);
                      return (
                        <Card key={mealKey}>
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <span>{mealType?.emoji}</span>
                                <span className="font-medium">{mealType?.label}</span>
                              </div>
                              <div className="flex gap-1">
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => toggleFavoriteRecipe(meal)}
                                  className={isFav ? "text-destructive" : ""}
                                >
                                  <Heart className={`w-3 h-3 ${isFav ? "fill-current" : ""}`} />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => openDatePickerForMeal(meal, mealKey)}
                                >
                                  <CalendarPlus className="w-3 h-3 mr-1" />
                                  Ajouter
                                </Button>
                              </div>
                            </div>
                            <p className="font-semibold">{meal.name}</p>
                            <div className="flex gap-2 text-xs text-muted-foreground mt-1">
                              <span>{meal.calories} kcal</span>
                              <span>•</span>
                              <span>P: {meal.protein}g</span>
                              <span>•</span>
                              <span>G: {meal.carbs}g</span>
                              <span>•</span>
                              <span>L: {meal.fat}g</span>
                            </div>
                            {meal.recipe && (
                              <p className="text-xs text-muted-foreground mt-2 italic">{meal.recipe}</p>
                            )}
                            {meal.prep_time && (
                              <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                                <Clock className="w-3 h-3" />
                                {meal.prep_time}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      );
                    })}
                    {aiMealPlan.meal_plan.shopping_list && (
                      <Card>
                        <CardHeader className="pb-2">
                          <div className="flex items-center justify-between">
                            <CardTitle className="text-sm">🛒 Liste de courses</CardTitle>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => addIngredientsToShoppingList(
                                aiMealPlan.meal_plan.shopping_list.map(item => ({ item, quantity: '' }))
                              )}
                            >
                              <ShoppingCart className="w-3 h-3 mr-1" />
                              Tout ajouter
                            </Button>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="flex flex-wrap gap-2">
                            {aiMealPlan.meal_plan.shopping_list.map((item, i) => (
                              <Badge key={i} variant="secondary">{item}</Badge>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                    {/* Action buttons for daily plan */}
                    <div className="flex gap-2 pt-2">
                      <Button 
                        variant="outline" 
                        className="flex-1"
                        onClick={() => addAllMealsToFavorites(aiMealPlan.meal_plan.meals)}
                      >
                        <Heart className="w-4 h-4 mr-2" />
                        Tout en favoris
                      </Button>
                    </div>
                  </>
                ) : aiMealPlan.meal_plan.days ? (
                  // Weekly plan
                  <>
                    {aiMealPlan.meal_plan.days.map((day, dayIndex) => (
                      <Card key={dayIndex}>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-base">{day.day}</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                          {['breakfast', 'lunch', 'dinner'].map((mealKey) => {
                            const meal = day.meals?.[mealKey];
                            if (!meal) return null;
                            const mealType = mealTypes.find(t => t.value === mealKey);
                            return (
                              <div key={mealKey} className="flex items-center justify-between p-2 rounded-lg bg-muted/30">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm">{mealType?.emoji}</span>
                                    <span className="text-sm font-medium">{meal.name}</span>
                                  </div>
                                  <span className="text-xs text-muted-foreground">{meal.calories} kcal</span>
                                </div>
                                <div className="flex gap-1">
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => toggleFavoriteRecipe(meal)}
                                  >
                                    <Heart className="w-3 h-3" />
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => openDatePickerForMeal(meal, mealKey)}
                                  >
                                    <CalendarPlus className="w-3 h-3" />
                                  </Button>
                                </div>
                              </div>
                            );
                          })}
                          <div className="text-xs text-muted-foreground text-right">
                            Total: {day.total_calories} kcal
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                    {/* Action buttons for weekly plan */}
                    <div className="flex gap-2 pt-2">
                      <Button 
                        variant="outline" 
                        className="flex-1"
                        onClick={() => addWeeklyPlanToAgenda(aiMealPlan.meal_plan.days)}
                      >
                        <CalendarPlus className="w-4 h-4 mr-2" />
                        Ajouter à l'agenda
                      </Button>
                    </div>
                  </>
                ) : null}
              </div>
            </ScrollArea>
          ) : (
            <div className="text-center py-8">
              <p className="text-muted-foreground">Aucun plan généré</p>
            </div>
          )}
          
          {/* Regenerate button */}
          {!loadingMealPlan && (
            <div className="pt-4 border-t">
              <Button 
                onClick={regenerateMealPlan} 
                className="w-full"
                variant="outline"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Générer un nouveau plan
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Recipes Dialog */}
      <Dialog open={recipesDialogOpen} onOpenChange={setRecipesDialogOpen}>
        <DialogContent className="max-h-[90vh] overflow-y-auto max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ChefHat className="w-5 h-5 text-secondary" />
              Recettes personnalisées
            </DialogTitle>
          </DialogHeader>
          
          {loadingRecipes ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-10 h-10 animate-spin text-secondary mb-4" />
              <p className="text-muted-foreground">Génération en cours...</p>
              <p className="text-xs text-muted-foreground">L'IA prépare vos recettes</p>
            </div>
          ) : (
            <ScrollArea className="max-h-[60vh]">
              <div className="space-y-3 pr-4">
                {recipes.map((recipe, i) => {
                  const isFavorite = favoriteRecipes.some(f => f.recipe.name === recipe.name);
                  return (
                    <Card 
                      key={i} 
                      className="cursor-pointer hover:border-secondary/50 transition-colors"
                      onClick={() => setSelectedRecipe(selectedRecipe?.id === recipe.id ? null : recipe)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <p className="font-semibold">{recipe.name}</p>
                              {recipe.nutri_score && (
                                <span className={`w-5 h-5 rounded text-white text-xs flex items-center justify-center font-bold ${getNutriScoreColor(recipe.nutri_score)}`}>
                                  {recipe.nutri_score}
                                </span>
                              )}
                            </div>
                            <div className="flex gap-2 text-xs text-muted-foreground mt-1">
                              <span>{recipe.calories} kcal</span>
                              <span>•</span>
                              <span>{recipe.prep_time}</span>
                              <span>•</span>
                              <span>{recipe.difficulty}</span>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className={isFavorite ? "text-destructive" : ""}
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleFavoriteRecipe(recipe);
                            }}
                          >
                            {isFavorite ? <Heart className="w-5 h-5 fill-current" /> : <Heart className="w-5 h-5" />}
                          </Button>
                        </div>
                        
                        {/* Expanded recipe details */}
                        {selectedRecipe?.id === recipe.id && (
                          <div className="mt-4 pt-4 border-t space-y-3">
                            <div className="grid grid-cols-4 gap-2 text-center text-xs">
                              <div className="p-2 rounded bg-muted">
                                <p className="font-bold">{recipe.protein}g</p>
                                <p className="text-muted-foreground">Protéines</p>
                              </div>
                              <div className="p-2 rounded bg-muted">
                                <p className="font-bold">{recipe.carbs}g</p>
                                <p className="text-muted-foreground">Glucides</p>
                              </div>
                              <div className="p-2 rounded bg-muted">
                                <p className="font-bold">{recipe.fat}g</p>
                                <p className="text-muted-foreground">Lipides</p>
                              </div>
                              <div className="p-2 rounded bg-muted">
                                <p className="font-bold">{recipe.servings}</p>
                                <p className="text-muted-foreground">Portions</p>
                              </div>
                            </div>
                            
                            {recipe.ingredients && (
                              <div>
                                <p className="font-medium text-sm mb-2">📝 Ingrédients</p>
                                <div className="flex flex-wrap gap-1">
                                  {recipe.ingredients.map((ing, j) => (
                                    <Badge key={j} variant="outline" className="text-xs">
                                      {ing.quantity} {ing.item}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {recipe.steps && (
                              <div>
                                <p className="font-medium text-sm mb-2">👨‍🍳 Préparation</p>
                                <ol className="space-y-1">
                                  {recipe.steps.map((step, j) => (
                                    <li key={j} className="text-xs text-muted-foreground">
                                      {step}
                                    </li>
                                  ))}
                                </ol>
                              </div>
                            )}
                            
                            {recipe.tips && (
                              <div className="p-2 rounded bg-primary/5 border border-primary/20">
                                <p className="text-xs">💡 {recipe.tips}</p>
                              </div>
                            )}
                            
                            {/* Add to agenda button */}
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="w-full mt-2"
                              onClick={(e) => {
                                e.stopPropagation();
                                addRecipeToAgenda(recipe);
                              }}
                            >
                              <CalendarPlus className="w-4 h-4 mr-2" />
                              Ajouter à l'agenda
                            </Button>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </ScrollArea>
          )}
          
          {/* Regenerate button */}
          {!loadingRecipes && recipes.length > 0 && (
            <div className="pt-4 border-t">
              <Button 
                onClick={regenerateRecipes} 
                className="w-full"
                variant="outline"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Générer de nouvelles recettes
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
