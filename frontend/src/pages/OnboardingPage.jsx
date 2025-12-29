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
  Calendar
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
  { value: 'gluten_free', label: 'Sans gluten' },
  { value: 'lactose_free', label: 'Sans lactose' },
  { value: 'keto', label: 'Keto' },
];

const allergyOptions = [
  { value: 'nuts', label: 'Fruits à coque' },
  { value: 'shellfish', label: 'Crustacés' },
  { value: 'eggs', label: 'Œufs' },
  { value: 'soy', label: 'Soja' },
  { value: 'fish', label: 'Poisson' },
];

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { updateUser } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const totalSteps = 5;

  const [formData, setFormData] = useState({
    age: '',
    height: '',
    weight: '',
    target_weight: '',
    goal: '',
    activity_level: '',
    fitness_level: '',
    dietary_preferences: [],
    allergies: [],
  });

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
      await axios.post(`${API}/profile/onboarding`, {
        ...formData,
        age: parseInt(formData.age),
        height: parseFloat(formData.height),
        weight: parseFloat(formData.weight),
        target_weight: parseFloat(formData.target_weight),
      }, { withCredentials: true });
      
      updateUser({ onboarding_completed: true });
      toast.success('Profil complété ! Bienvenue 🎉');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    switch (step) {
      case 1:
        return formData.age && formData.height && formData.weight;
      case 2:
        return formData.goal && formData.target_weight;
      case 3:
        return formData.activity_level;
      case 4:
        return formData.fitness_level;
      case 5:
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

        {/* Step 1: Basic Info */}
        {step === 1 && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="font-heading text-2xl flex items-center gap-2">
                <Ruler className="w-6 h-6 text-primary" />
                Vos mensurations
              </CardTitle>
              <CardDescription>
                Ces informations nous aident à calculer vos besoins
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
            </CardContent>
          </Card>
        )}

        {/* Step 2: Goal */}
        {step === 2 && (
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
              <RadioGroup
                value={formData.goal}
                onValueChange={(value) => setFormData({ ...formData, goal: value })}
              >
                <div className="grid gap-3">
                  {goals.map((goal) => (
                    <Label
                      key={goal.value}
                      htmlFor={goal.value}
                      className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-all ${
                        formData.goal === goal.value 
                          ? 'border-primary bg-primary/5' 
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <RadioGroupItem value={goal.value} id={goal.value} />
                      <goal.icon className="w-5 h-5 text-primary" />
                      <span className="font-medium">{goal.label}</span>
                    </Label>
                  ))}
                </div>
              </RadioGroup>

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

        {/* Step 3: Activity Level */}
        {step === 3 && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="font-heading text-2xl flex items-center gap-2">
                <Activity className="w-6 h-6 text-primary" />
                Niveau d'activité
              </CardTitle>
              <CardDescription>
                Décrivez votre niveau d'activité quotidien
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RadioGroup
                value={formData.activity_level}
                onValueChange={(value) => setFormData({ ...formData, activity_level: value })}
              >
                <div className="grid gap-3">
                  {activityLevels.map((level) => (
                    <Label
                      key={level.value}
                      htmlFor={level.value}
                      className={`flex items-start gap-4 p-4 rounded-xl border cursor-pointer transition-all ${
                        formData.activity_level === level.value 
                          ? 'border-primary bg-primary/5' 
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <RadioGroupItem value={level.value} id={level.value} className="mt-1" />
                      <div>
                        <span className="font-medium">{level.label}</span>
                        <p className="text-sm text-muted-foreground">{level.description}</p>
                      </div>
                    </Label>
                  ))}
                </div>
              </RadioGroup>
            </CardContent>
          </Card>
        )}

        {/* Step 4: Fitness Level */}
        {step === 4 && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="font-heading text-2xl flex items-center gap-2">
                <Dumbbell className="w-6 h-6 text-primary" />
                Niveau sportif
              </CardTitle>
              <CardDescription>
                Cela nous aide à personnaliser vos entraînements
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RadioGroup
                value={formData.fitness_level}
                onValueChange={(value) => setFormData({ ...formData, fitness_level: value })}
              >
                <div className="grid gap-3">
                  {fitnessLevels.map((level) => (
                    <Label
                      key={level.value}
                      htmlFor={`fitness-${level.value}`}
                      className={`flex items-start gap-4 p-4 rounded-xl border cursor-pointer transition-all ${
                        formData.fitness_level === level.value 
                          ? 'border-primary bg-primary/5' 
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <RadioGroupItem value={level.value} id={`fitness-${level.value}`} className="mt-1" />
                      <div>
                        <span className="font-medium">{level.label}</span>
                        <p className="text-sm text-muted-foreground">{level.description}</p>
                      </div>
                    </Label>
                  ))}
                </div>
              </RadioGroup>
            </CardContent>
          </Card>
        )}

        {/* Step 5: Dietary Preferences */}
        {step === 5 && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="font-heading text-2xl flex items-center gap-2">
                <Apple className="w-6 h-6 text-primary" />
                Préférences alimentaires
              </CardTitle>
              <CardDescription>
                Optionnel - Sélectionnez vos régimes et allergies
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <Label>Régimes alimentaires</Label>
                <div className="grid grid-cols-2 gap-2">
                  {dietaryOptions.map((option) => (
                    <Label
                      key={option.value}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                        formData.dietary_preferences.includes(option.value)
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <Checkbox
                        checked={formData.dietary_preferences.includes(option.value)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setFormData({
                              ...formData,
                              dietary_preferences: [...formData.dietary_preferences, option.value]
                            });
                          } else {
                            setFormData({
                              ...formData,
                              dietary_preferences: formData.dietary_preferences.filter(v => v !== option.value)
                            });
                          }
                        }}
                      />
                      <span className="text-sm">{option.label}</span>
                    </Label>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <Label>Allergies</Label>
                <div className="grid grid-cols-2 gap-2">
                  {allergyOptions.map((option) => (
                    <Label
                      key={option.value}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                        formData.allergies.includes(option.value)
                          ? 'border-destructive bg-destructive/5'
                          : 'border-border hover:border-destructive/50'
                      }`}
                    >
                      <Checkbox
                        checked={formData.allergies.includes(option.value)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setFormData({
                              ...formData,
                              allergies: [...formData.allergies, option.value]
                            });
                          } else {
                            setFormData({
                              ...formData,
                              allergies: formData.allergies.filter(v => v !== option.value)
                            });
                          }
                        }}
                      />
                      <span className="text-sm">{option.label}</span>
                    </Label>
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
