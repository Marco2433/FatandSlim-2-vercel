import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { 
  ChevronRight, 
  ChevronLeft, 
  Target, 
  Activity, 
  Apple, 
  Dumbbell,
  Scale,
  Ruler,
  Calendar,
  Heart,
  Clock,
  Wallet,
  ThumbsUp,
  ThumbsDown,
  AlertTriangle,
  ChefHat,
  User,
  Stethoscope,
  Pill,
  Hospital,
  Info
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const goals = [
  { value: 'lose_weight', label: 'Perdre du poids', icon: Scale },
  { value: 'gain_muscle', label: 'Prendre du muscle', icon: Dumbbell },
  { value: 'maintain', label: 'Maintenir ma forme', icon: Activity },
  { value: 'improve_health', label: 'Améliorer ma santé', icon: Apple },
];

const activityLevels = [
  { value: 'sedentary', label: 'Sédentaire', description: 'Peu ou pas d\'exercice' },
  { value: 'light', label: 'Légèrement actif', description: '1-2 séances/semaine' },
  { value: 'moderate', label: 'Modérément actif', description: '3-4 séances/semaine' },
  { value: 'active', label: 'Très actif', description: '5+ séances/semaine' },
  { value: 'very_active', label: 'Athlète', description: 'Entraînement intensif quotidien' },
];

const fitnessLevels = [
  { value: 'beginner', label: 'Débutant', description: 'Je débute ou reprends le sport' },
  { value: 'intermediate', label: 'Intermédiaire', description: 'Je fais du sport régulièrement' },
  { value: 'advanced', label: 'Avancé', description: 'Je m\'entraîne depuis des années' },
];

const dietaryOptions = [
  { value: 'vegetarian', label: 'Végétarien' },
  { value: 'vegan', label: 'Végan' },
  { value: 'halal', label: 'Halal' },
  { value: 'kosher', label: 'Casher' },
  { value: 'gluten_free', label: 'Sans gluten' },
  { value: 'lactose_free', label: 'Sans lactose' },
  { value: 'keto', label: 'Keto / Low carb' },
  { value: 'paleo', label: 'Paléo' },
];

const allergyOptions = [
  { value: 'nuts', label: 'Fruits à coque' },
  { value: 'peanuts', label: 'Arachides' },
  { value: 'shellfish', label: 'Crustacés' },
  { value: 'eggs', label: 'Œufs' },
  { value: 'soy', label: 'Soja' },
  { value: 'fish', label: 'Poisson' },
  { value: 'milk', label: 'Lait' },
  { value: 'wheat', label: 'Blé' },
];

const healthConditions = [
  { value: 'diabetes', label: 'Diabète', icon: '🩸' },
  { value: 'sleep_apnea', label: 'Apnée du sommeil', icon: '😴' },
  { value: 'thyroid', label: 'Problèmes de thyroïde', icon: '🦋' },
  { value: 'bypass', label: 'By-pass gastrique', icon: '⚕️' },
  { value: 'sleeve', label: 'Sleeve gastrectomie', icon: '⚕️' },
  { value: 'hypertension', label: 'Hypertension', icon: '❤️' },
  { value: 'cholesterol', label: 'Cholestérol élevé', icon: '🫀' },
  { value: 'heart_disease', label: 'Maladie cardiaque', icon: '💔' },
  { value: 'arthritis', label: 'Arthrite / Douleurs articulaires', icon: '🦴' },
  { value: 'digestive', label: 'Problèmes digestifs', icon: '🫃' },
];

const foodCategories = [
  { value: 'vegetables', label: 'Légumes verts' },
  { value: 'fruits', label: 'Fruits' },
  { value: 'red_meat', label: 'Viande rouge' },
  { value: 'white_meat', label: 'Volaille' },
  { value: 'fish', label: 'Poisson' },
  { value: 'seafood', label: 'Fruits de mer' },
  { value: 'pasta', label: 'Pâtes' },
  { value: 'rice', label: 'Riz' },
  { value: 'bread', label: 'Pain' },
  { value: 'cheese', label: 'Fromage' },
  { value: 'eggs', label: 'Œufs' },
  { value: 'legumes', label: 'Légumineuses' },
  { value: 'nuts', label: 'Noix / Graines' },
  { value: 'dairy', label: 'Produits laitiers' },
  { value: 'spicy', label: 'Plats épicés' },
  { value: 'sweet', label: 'Desserts sucrés' },
];

const timeConstraints = [
  { value: 'very_limited', label: 'Très limité', description: '< 15 min par repas' },
  { value: 'limited', label: 'Limité', description: '15-30 min par repas' },
  { value: 'moderate', label: 'Modéré', description: '30-45 min par repas' },
  { value: 'flexible', label: 'Flexible', description: 'Je peux cuisiner longtemps' },
];

const budgetOptions = [
  { value: 'tight', label: 'Serré', description: 'Économiser au maximum' },
  { value: 'medium', label: 'Moyen', description: 'Équilibre qualité/prix' },
  { value: 'comfortable', label: 'Confortable', description: 'La qualité avant tout' },
];

const cookingSkills = [
  { value: 'beginner', label: 'Débutant', description: 'Recettes simples uniquement' },
  { value: 'intermediate', label: 'Intermédiaire', description: 'Je me débrouille bien' },
  { value: 'advanced', label: 'Confirmé', description: 'J\'aime les défis culinaires' },
];

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { updateUser } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Dynamic total steps based on bariatric selection
  const getActualTotalSteps = () => {
    if (formData.bariatric_surgery) {
      return 10; // 8 normal + 2 bariatric steps
    }
    return 8;
  };

  const [formData, setFormData] = useState({
    gender: '',
    age: '',
    height: '',
    weight: '',
    target_weight: '',
    goal: '',
    activity_level: '',
    fitness_level: '',
    dietary_preferences: [],
    allergies: [],
    health_conditions: [],
    food_likes: [],
    food_dislikes: [],
    time_constraint: 'moderate',
    budget: 'medium',
    cooking_skill: 'intermediate',
    meals_per_day: 3,
    // Bariatric fields
    bariatric_surgery: null,
    bariatric_surgery_date: '',
    bariatric_pre_op_weight: '',
    bariatric_pre_op_height: '',
    bariatric_parcours: '',
    bariatric_phase: null,
    bariatric_supplements: [],
    bariatric_intolerances: [],
    bariatric_clinic: '',
    bariatric_surgeon: '',
    bariatric_nutritionist: '',
    bariatric_psychologist: '',
  });

  const totalSteps = getActualTotalSteps();

  const handleNext = () => {
    if (step < totalSteps) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const submitData = {
        ...formData,
        age: parseInt(formData.age),
        height: parseFloat(formData.height),
        weight: parseFloat(formData.weight),
        target_weight: parseFloat(formData.target_weight),
      };
      
      // Add bariatric numeric fields if applicable
      if (formData.bariatric_surgery) {
        submitData.bariatric_pre_op_weight = formData.bariatric_pre_op_weight ? parseFloat(formData.bariatric_pre_op_weight) : null;
        submitData.bariatric_pre_op_height = formData.bariatric_pre_op_height ? parseFloat(formData.bariatric_pre_op_height) : null;
      }
      
      await axios.post(`${API}/profile/onboarding`, submitData, { withCredentials: true });
      
      updateUser({ onboarding_completed: true });
      toast.success('Profil complété ! Bienvenue 🎉');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const toggleArrayItem = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter(v => v !== value)
        : [...prev[field], value]
    }));
  };

  const canProceed = () => {
    switch (step) {
      case 1:
        return formData.gender;
      case 2:
        return formData.age && formData.height && formData.weight;
      case 3:
        return formData.goal && formData.target_weight;
      case 4:
        return formData.activity_level && formData.fitness_level;
      case 5:
        return true; // Health conditions optional
      case 6:
        return true; // Food preferences optional
      case 7:
        return true; // Dietary/allergies optional
      case 8:
        return formData.time_constraint && formData.budget;
      case 9:
        // Bariatric step 1 - surgery info
        if (formData.bariatric_surgery) {
          return formData.bariatric_surgery_date && formData.bariatric_parcours;
        }
        return true;
      case 10:
        // Bariatric step 2 - medical team (optional)
        return true;
      default:
        return false;
    }
  };

  return (
    <div className="min-h-screen bg-background p-4 md:p-8" data-testid="onboarding-page">
      <div className="max-w-xl mx-auto">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Étape {step} sur {totalSteps}</span>
            <span className="text-sm font-medium">{Math.round((step / totalSteps) * 100)}%</span>
          </div>
          <Progress value={(step / totalSteps) * 100} className="h-2" />
        </div>

        {/* Step 1: Gender */}
        {step === 1 && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="font-heading text-2xl flex items-center gap-2">
                <User className="w-6 h-6 text-primary" />
                Vous êtes
              </CardTitle>
              <CardDescription>
                Cela nous aide à personnaliser vos recommandations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { value: 'male', label: 'Homme', emoji: '👨' },
                  { value: 'female', label: 'Femme', emoji: '👩' },
                ].map((option) => (
                  <div
                    key={option.value}
                    onClick={() => setFormData({ ...formData, gender: option.value })}
                    data-testid={`gender-${option.value}`}
                    className={`flex flex-col items-center justify-center p-6 rounded-2xl border-2 cursor-pointer transition-all ${
                      formData.gender === option.value 
                        ? 'border-primary bg-primary/10 shadow-glow' 
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <span className="text-4xl mb-2">{option.emoji}</span>
                    <span className="font-medium">{option.label}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Basic Info */}
        {step === 2 && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="font-heading text-2xl flex items-center gap-2">
                <Ruler className="w-6 h-6 text-primary" />
                Vos mensurations
              </CardTitle>
              <CardDescription>
                Ces informations nous aident à calculer votre IMC et vos besoins caloriques
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="age">Âge</Label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="age"
                    type="number"
                    placeholder="25"
                    className="pl-10"
                    value={formData.age}
                    onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                    data-testid="age-input"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="height">Taille (cm)</Label>
                  <Input
                    id="height"
                    type="number"
                    placeholder="175"
                    value={formData.height}
                    onChange={(e) => setFormData({ ...formData, height: e.target.value })}
                    data-testid="height-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="weight">Poids (kg)</Label>
                  <Input
                    id="weight"
                    type="number"
                    placeholder="70"
                    value={formData.weight}
                    onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
                    data-testid="weight-input"
                  />
                </div>
              </div>
              {formData.height && formData.weight && (
                <div className="p-4 rounded-xl bg-primary/10 border border-primary/20">
                  <p className="text-sm text-muted-foreground">Votre IMC actuel</p>
                  <p className="font-heading text-2xl font-bold text-primary">
                    {(parseFloat(formData.weight) / Math.pow(parseFloat(formData.height) / 100, 2)).toFixed(1)}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Step 3: Goal */}
        {step === 3 && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="font-heading text-2xl flex items-center gap-2">
                <Target className="w-6 h-6 text-primary" />
                Votre objectif
              </CardTitle>
              <CardDescription>
                Quel est votre principal objectif ?
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-3">
                {goals.map((goal) => (
                  <div
                    key={goal.value}
                    onClick={() => setFormData({ ...formData, goal: goal.value })}
                    data-testid={`goal-${goal.value}`}
                    className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-all ${
                      formData.goal === goal.value 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <goal.icon className="w-5 h-5 text-primary" />
                    <span className="font-medium">{goal.label}</span>
                  </div>
                ))}
              </div>

              <div className="space-y-2">
                <Label htmlFor="target_weight">Poids cible (kg)</Label>
                <Input
                  id="target_weight"
                  type="number"
                  placeholder="65"
                  value={formData.target_weight}
                  onChange={(e) => setFormData({ ...formData, target_weight: e.target.value })}
                  data-testid="target-weight-input"
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 4: Activity & Fitness Level */}
        {step === 4 && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="font-heading text-2xl flex items-center gap-2">
                <Activity className="w-6 h-6 text-primary" />
                Niveau d'activité
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-3">
                {activityLevels.map((level) => (
                  <div
                    key={level.value}
                    onClick={() => setFormData({ ...formData, activity_level: level.value })}
                    data-testid={`activity-${level.value}`}
                    className={`flex items-start gap-4 p-4 rounded-xl border cursor-pointer transition-all ${
                      formData.activity_level === level.value 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <div>
                      <span className="font-medium">{level.label}</span>
                      <p className="text-sm text-muted-foreground">{level.description}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="pt-4 border-t">
                <Label className="mb-3 block">Niveau sportif</Label>
                <div className="grid gap-3">
                  {fitnessLevels.map((level) => (
                    <div
                      key={level.value}
                      onClick={() => setFormData({ ...formData, fitness_level: level.value })}
                      data-testid={`fitness-${level.value}`}
                      className={`flex items-start gap-4 p-4 rounded-xl border cursor-pointer transition-all ${
                        formData.fitness_level === level.value 
                          ? 'border-primary bg-primary/5' 
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <div>
                        <span className="font-medium">{level.label}</span>
                        <p className="text-sm text-muted-foreground">{level.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 5: Health Conditions */}
        {step === 5 && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="font-heading text-2xl flex items-center gap-2">
                <Heart className="w-6 h-6 text-primary" />
                Conditions de santé
              </CardTitle>
              <CardDescription>
                Important pour adapter vos repas et exercices (optionnel)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2">
                {healthConditions.map((condition) => (
                  <div
                    key={condition.value}
                    onClick={() => toggleArrayItem('health_conditions', condition.value)}
                    className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-all ${
                      formData.health_conditions.includes(condition.value)
                        ? 'border-destructive bg-destructive/10'
                        : 'border-border hover:border-destructive/50'
                    }`}
                  >
                    <span>{condition.icon}</span>
                    <span className="text-sm">{condition.label}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-4 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" />
                Ces informations restent confidentielles et servent uniquement à personnaliser vos recommandations
              </p>
            </CardContent>
          </Card>
        )}

        {/* Step 6: Food Likes & Dislikes */}
        {step === 6 && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="font-heading text-2xl flex items-center gap-2">
                <Apple className="w-6 h-6 text-primary" />
                Vos goûts alimentaires
              </CardTitle>
              <CardDescription>
                Sélectionnez ce que vous aimez et n'aimez pas
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label className="mb-3 flex items-center gap-2">
                  <ThumbsUp className="w-4 h-4 text-primary" />
                  J'aime
                </Label>
                <div className="grid grid-cols-3 gap-2">
                  {foodCategories.map((food) => (
                    <div
                      key={`like-${food.value}`}
                      onClick={() => {
                        // Remove from dislikes if present
                        const newDislikes = formData.food_dislikes.filter(v => v !== food.value);
                        setFormData(prev => ({
                          ...prev,
                          food_dislikes: newDislikes,
                          food_likes: prev.food_likes.includes(food.value)
                            ? prev.food_likes.filter(v => v !== food.value)
                            : [...prev.food_likes, food.value]
                        }));
                      }}
                      className={`p-2 rounded-lg border text-center cursor-pointer transition-all text-sm ${
                        formData.food_likes.includes(food.value)
                          ? 'border-primary bg-primary/10 text-primary'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      {food.label}
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <Label className="mb-3 flex items-center gap-2">
                  <ThumbsDown className="w-4 h-4 text-destructive" />
                  Je n'aime pas
                </Label>
                <div className="grid grid-cols-3 gap-2">
                  {foodCategories.map((food) => (
                    <div
                      key={`dislike-${food.value}`}
                      onClick={() => {
                        // Remove from likes if present
                        const newLikes = formData.food_likes.filter(v => v !== food.value);
                        setFormData(prev => ({
                          ...prev,
                          food_likes: newLikes,
                          food_dislikes: prev.food_dislikes.includes(food.value)
                            ? prev.food_dislikes.filter(v => v !== food.value)
                            : [...prev.food_dislikes, food.value]
                        }));
                      }}
                      className={`p-2 rounded-lg border text-center cursor-pointer transition-all text-sm ${
                        formData.food_dislikes.includes(food.value)
                          ? 'border-destructive bg-destructive/10 text-destructive'
                          : 'border-border hover:border-destructive/50'
                      }`}
                    >
                      {food.label}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 7: Dietary Preferences & Allergies */}
        {step === 7 && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="font-heading text-2xl flex items-center gap-2">
                <AlertTriangle className="w-6 h-6 text-primary" />
                Régimes & Allergies
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label className="mb-3 block">Régimes alimentaires</Label>
                <div className="grid grid-cols-2 gap-2">
                  {dietaryOptions.map((option) => (
                    <div
                      key={option.value}
                      onClick={() => toggleArrayItem('dietary_preferences', option.value)}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                        formData.dietary_preferences.includes(option.value)
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <Checkbox checked={formData.dietary_preferences.includes(option.value)} />
                      <span className="text-sm">{option.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <Label className="mb-3 block text-destructive">Allergies alimentaires</Label>
                <div className="grid grid-cols-2 gap-2">
                  {allergyOptions.map((option) => (
                    <div
                      key={option.value}
                      onClick={() => toggleArrayItem('allergies', option.value)}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                        formData.allergies.includes(option.value)
                          ? 'border-destructive bg-destructive/5'
                          : 'border-border hover:border-destructive/50'
                      }`}
                    >
                      <Checkbox checked={formData.allergies.includes(option.value)} />
                      <span className="text-sm">{option.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 8: Constraints */}
        {step === 8 && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="font-heading text-2xl flex items-center gap-2">
                <Clock className="w-6 h-6 text-primary" />
                Vos contraintes
              </CardTitle>
              <CardDescription>
                Pour des recommandations réalistes
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label className="mb-3 flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Temps disponible pour cuisiner
                </Label>
                <div className="grid gap-2">
                  {timeConstraints.map((option) => (
                    <div
                      key={option.value}
                      onClick={() => setFormData({ ...formData, time_constraint: option.value })}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        formData.time_constraint === option.value
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <span className="font-medium">{option.label}</span>
                      <p className="text-xs text-muted-foreground">{option.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <Label className="mb-3 flex items-center gap-2">
                  <Wallet className="w-4 h-4" />
                  Budget alimentation
                </Label>
                <div className="grid gap-2">
                  {budgetOptions.map((option) => (
                    <div
                      key={option.value}
                      onClick={() => setFormData({ ...formData, budget: option.value })}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        formData.budget === option.value
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <span className="font-medium">{option.label}</span>
                      <p className="text-xs text-muted-foreground">{option.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <Label className="mb-3 flex items-center gap-2">
                  <ChefHat className="w-4 h-4" />
                  Niveau en cuisine
                </Label>
                <div className="grid gap-2">
                  {cookingSkills.map((option) => (
                    <div
                      key={option.value}
                      onClick={() => setFormData({ ...formData, cooking_skill: option.value })}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        formData.cooking_skill === option.value
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <span className="font-medium">{option.label}</span>
                      <p className="text-xs text-muted-foreground">{option.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-6">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={step === 1}
            className="rounded-full"
            data-testid="back-btn"
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Retour
          </Button>

          {step < totalSteps ? (
            <Button
              onClick={handleNext}
              disabled={!canProceed()}
              className="rounded-full"
              data-testid="next-btn"
            >
              Suivant
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button
              onClick={handleSubmit}
              disabled={loading}
              className="rounded-full shadow-glow"
              data-testid="submit-btn"
            >
              {loading ? 'Enregistrement...' : 'Terminer'}
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
