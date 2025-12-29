import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area, ComposedChart } from 'recharts';
import { 
  TrendingUp, 
  ArrowLeft,
  Scale,
  Trophy,
  Target,
  Plus,
  Flame,
  Award,
  Activity
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ProgressPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('weight');
  const [stats, setStats] = useState(null);
  const [weightHistory, setWeightHistory] = useState([]);
  const [bmiData, setBmiData] = useState(null);
  const [badges, setBadges] = useState(null);
  const [loading, setLoading] = useState(true);
  const [weightDialogOpen, setWeightDialogOpen] = useState(false);
  const [newWeight, setNewWeight] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, weightRes, bmiRes, badgesRes] = await Promise.all([
        axios.get(`${API}/progress/stats`, { withCredentials: true }),
        axios.get(`${API}/progress/weight`, { withCredentials: true }),
        axios.get(`${API}/progress/bmi`, { withCredentials: true }),
        axios.get(`${API}/badges`, { withCredentials: true })
      ]);
      setStats(statsRes.data);
      setWeightHistory(weightRes.data);
      setBmiData(bmiRes.data);
      setBadges(badgesRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const logWeight = async () => {
    if (!newWeight) {
      toast.error('Entrez votre poids');
      return;
    }

    try {
      const response = await axios.post(`${API}/progress/weight`, {
        weight: parseFloat(newWeight)
      }, { withCredentials: true });
      
      toast.success(`Poids enregistré ! IMC: ${response.data.bmi}`);
      setWeightDialogOpen(false);
      setNewWeight('');
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement');
    }
  };

  const getBmiCategory = (bmi) => {
    if (bmi < 18.5) return { label: 'Insuffisance pondérale', color: 'text-blue-500' };
    if (bmi < 25) return { label: 'Poids normal', color: 'text-green-500' };
    if (bmi < 30) return { label: 'Surpoids', color: 'text-orange-500' };
    return { label: 'Obésité', color: 'text-red-500' };
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

  // Format weight data for chart
  const weightChartData = weightHistory.map(entry => ({
    date: new Date(entry.date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }),
    weight: entry.weight,
    bmi: entry.bmi
  }));

  // Format BMI data for chart
  const bmiChartData = bmiData?.history?.map(entry => ({
    date: new Date(entry.date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }),
    bmi: entry.bmi
  })) || [];

  const bmiCategory = stats?.bmi ? getBmiCategory(stats.bmi) : null;

  return (
    <div className="min-h-screen bg-background pb-safe" data-testid="progress-page">
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
              <h1 className="font-heading text-xl font-bold">Progrès</h1>
              <p className="text-sm text-muted-foreground">Suivez votre évolution</p>
            </div>
          </div>
          <Dialog open={weightDialogOpen} onOpenChange={setWeightDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm" className="rounded-full" data-testid="add-weight-btn">
                <Plus className="w-4 h-4 mr-1" />
                Poids
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Enregistrer votre poids</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <Input
                  type="number"
                  step="0.1"
                  placeholder="70.5"
                  value={newWeight}
                  onChange={(e) => setNewWeight(e.target.value)}
                  data-testid="weight-input"
                />
                <Button onClick={logWeight} className="w-full">
                  Enregistrer
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <main className="p-4 space-y-6 pb-24">
        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="weight">Poids</TabsTrigger>
            <TabsTrigger value="bmi">IMC</TabsTrigger>
            <TabsTrigger value="badges">Badges</TabsTrigger>
          </TabsList>

          {/* Weight Tab */}
          <TabsContent value="weight" className="space-y-4 mt-4">
            {/* Weight Stats */}
            {stats && (
              <Card data-testid="weight-stats-card">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl gradient-primary flex items-center justify-center">
                        <Scale className="w-6 h-6 text-primary-foreground" />
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Poids actuel</p>
                        <p className="font-heading text-3xl font-bold">{stats.current_weight} kg</p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-3 rounded-xl bg-muted/50">
                      <p className="text-sm text-muted-foreground">Objectif</p>
                      <p className="font-heading font-bold text-lg">{stats.target_weight} kg</p>
                    </div>
                    <div className="text-center p-3 rounded-xl bg-muted/50">
                      <p className="text-sm text-muted-foreground">Évolution</p>
                      <p className={`font-heading font-bold text-lg ${stats.weight_change < 0 ? 'text-primary' : stats.weight_change > 0 ? 'text-destructive' : ''}`}>
                        {stats.weight_change > 0 ? '+' : ''}{stats.weight_change} kg
                      </p>
                    </div>
                    <div className="text-center p-3 rounded-xl bg-muted/50">
                      <p className="text-sm text-muted-foreground">Poids idéal</p>
                      <p className="font-heading font-bold text-lg">{stats.ideal_weight || '--'} kg</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Weight Chart */}
            {weightChartData.length > 1 && (
              <Card data-testid="weight-chart-card">
                <CardHeader className="pb-2">
                  <CardTitle className="font-heading text-lg flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-chart-4" />
                    Évolution du poids
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={weightChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis 
                          dataKey="date" 
                          stroke="hsl(var(--muted-foreground))"
                          fontSize={12}
                        />
                        <YAxis 
                          stroke="hsl(var(--muted-foreground))"
                          fontSize={12}
                          domain={['dataMin - 2', 'dataMax + 2']}
                        />
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '8px'
                          }}
                          formatter={(value, name) => [
                            name === 'weight' ? `${value} kg` : value,
                            name === 'weight' ? 'Poids' : 'IMC'
                          ]}
                        />
                        {stats?.target_weight && (
                          <ReferenceLine 
                            y={stats.target_weight} 
                            stroke="hsl(var(--primary))"
                            strokeDasharray="5 5"
                            label={{ value: 'Objectif', position: 'right', fontSize: 10 }}
                          />
                        )}
                        <Line 
                          type="monotone" 
                          dataKey="weight" 
                          stroke="hsl(var(--primary))"
                          strokeWidth={3}
                          dot={{ fill: 'hsl(var(--primary))', strokeWidth: 2 }}
                          activeDot={{ r: 6, fill: 'hsl(var(--primary))' }}
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Streak */}
            {stats?.streak && (
              <Card className="border-accent/20 bg-gradient-to-br from-accent/5 to-accent/10">
                <CardContent className="p-6 flex items-center gap-4">
                  <div className="w-16 h-16 rounded-2xl bg-accent flex items-center justify-center">
                    <Flame className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Série actuelle</p>
                    <p className="font-heading text-3xl font-bold">{stats.streak.current} jours</p>
                    <p className="text-sm text-muted-foreground">
                      Record: {stats.streak.longest} jours
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* BMI Tab */}
          <TabsContent value="bmi" className="space-y-4 mt-4">
            {/* Current BMI */}
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-16 h-16 rounded-2xl bg-secondary/10 flex items-center justify-center">
                    <Activity className="w-8 h-8 text-secondary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Votre IMC</p>
                    <p className="font-heading text-4xl font-bold">{stats?.bmi || '--'}</p>
                    {bmiCategory && (
                      <p className={`text-sm font-medium ${bmiCategory.color}`}>
                        {bmiCategory.label}
                      </p>
                    )}
                  </div>
                </div>

                {/* BMI Scale */}
                <div className="relative mt-6">
                  <div className="flex h-4 rounded-full overflow-hidden">
                    <div className="flex-1 bg-blue-400" title="< 18.5" />
                    <div className="flex-1 bg-green-400" title="18.5 - 24.9" />
                    <div className="flex-1 bg-orange-400" title="25 - 29.9" />
                    <div className="flex-1 bg-red-400" title="> 30" />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>16</span>
                    <span>18.5</span>
                    <span>25</span>
                    <span>30</span>
                    <span>40</span>
                  </div>
                  {stats?.bmi && (
                    <div 
                      className="absolute -top-1 w-0.5 h-6 bg-foreground"
                      style={{ 
                        left: `${Math.min(100, Math.max(0, ((stats.bmi - 16) / 24) * 100))}%`,
                        transform: 'translateX(-50%)'
                      }}
                    >
                      <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-xs font-bold whitespace-nowrap">
                        {stats.bmi}
                      </div>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4 mt-6">
                  <div className="p-3 rounded-xl bg-primary/5 border border-primary/20">
                    <p className="text-xs text-muted-foreground">IMC idéal</p>
                    <p className="font-heading font-bold text-xl text-primary">
                      {bmiData?.ideal_bmi || 22.0}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-muted/50">
                    <p className="text-xs text-muted-foreground">Poids idéal</p>
                    <p className="font-heading font-bold text-xl">
                      {bmiData?.ideal_weight || '--'} kg
                    </p>
                  </div>
                </div>

                {bmiData?.ideal_weight_range && (
                  <p className="text-sm text-muted-foreground mt-3 text-center">
                    Plage de poids sain: {bmiData.ideal_weight_range.min} - {bmiData.ideal_weight_range.max} kg
                  </p>
                )}
              </CardContent>
            </Card>

            {/* BMI Chart */}
            {bmiChartData.length > 1 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="font-heading text-lg flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-secondary" />
                    Évolution de l'IMC
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={bmiChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis 
                          dataKey="date" 
                          stroke="hsl(var(--muted-foreground))"
                          fontSize={12}
                        />
                        <YAxis 
                          stroke="hsl(var(--muted-foreground))"
                          fontSize={12}
                          domain={[15, 35]}
                        />
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '8px'
                          }}
                        />
                        {/* Healthy BMI zone */}
                        <ReferenceLine y={18.5} stroke="hsl(var(--chart-4))" strokeDasharray="3 3" />
                        <ReferenceLine y={24.9} stroke="hsl(var(--chart-4))" strokeDasharray="3 3" />
                        {/* Ideal BMI line */}
                        <ReferenceLine 
                          y={bmiData?.ideal_bmi || 22} 
                          stroke="hsl(var(--primary))"
                          strokeDasharray="5 5"
                          label={{ value: 'Idéal', position: 'right', fontSize: 10 }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="bmi" 
                          stroke="hsl(var(--secondary))"
                          strokeWidth={3}
                          dot={{ fill: 'hsl(var(--secondary))', strokeWidth: 2 }}
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                  <p className="text-xs text-muted-foreground text-center mt-2">
                    Zone verte = IMC sain (18.5 - 24.9)
                  </p>
                </CardContent>
              </Card>
            )}

            {/* BMI Info */}
            <Card className="bg-muted/30">
              <CardContent className="p-4">
                <h3 className="font-semibold mb-3">📊 Comprendre l'IMC</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded bg-blue-400" />
                    <span>{"< 18.5 : Insuffisance pondérale"}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded bg-green-400" />
                    <span>18.5 - 24.9 : Poids normal ✓</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded bg-orange-400" />
                    <span>25 - 29.9 : Surpoids</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded bg-red-400" />
                    <span>≥ 30 : Obésité</span>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-3">
                  IMC = Poids (kg) ÷ Taille (m)²
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Badges Tab */}
          <TabsContent value="badges" className="space-y-4 mt-4">
            {badges && (
              <>
                {/* Earned Badges */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="font-heading text-lg flex items-center gap-2">
                      <Trophy className="w-5 h-5 text-accent" />
                      Badges gagnés ({badges.total_earned})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {badges.earned.length > 0 ? (
                      <div className="grid grid-cols-3 gap-4">
                        {badges.earned.map((badge) => (
                          <div 
                            key={badge.badge_id}
                            className="flex flex-col items-center text-center p-3"
                          >
                            <div className="w-14 h-14 rounded-2xl badge-3d flex items-center justify-center mb-2">
                              <Award className="w-7 h-7 text-primary-foreground" />
                            </div>
                            <p className="text-xs font-medium">{badge.badge_name}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-center text-muted-foreground py-4">
                        Aucun badge gagné pour l'instant
                      </p>
                    )}
                  </CardContent>
                </Card>

                {/* Available Badges */}
                {badges.available.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="font-heading text-lg">
                        Badges à débloquer
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-4">
                        {badges.available.map((badge) => (
                          <div 
                            key={badge.id}
                            className="flex flex-col items-center text-center p-3 opacity-50"
                          >
                            <div className="w-14 h-14 rounded-2xl badge-3d-locked flex items-center justify-center mb-2">
                              <Award className="w-7 h-7 text-muted-foreground" />
                            </div>
                            <p className="text-xs font-medium text-muted-foreground">{badge.name}</p>
                            <p className="text-xs text-muted-foreground mt-1">{badge.description}</p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            )}

            {/* Weekly Summary */}
            {stats?.weekly_stats && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="font-heading text-lg flex items-center gap-2">
                    <Target className="w-5 h-5 text-secondary" />
                    Cette semaine
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-muted/50 text-center">
                      <p className="text-3xl font-bold font-heading">{stats.weekly_stats.workouts_completed}</p>
                      <p className="text-sm text-muted-foreground">Entraînements</p>
                    </div>
                    <div className="p-4 rounded-xl bg-muted/50 text-center">
                      <p className="text-3xl font-bold font-heading">{stats.weekly_stats.workout_minutes}</p>
                      <p className="text-sm text-muted-foreground">Minutes</p>
                    </div>
                    <div className="p-4 rounded-xl bg-muted/50 text-center col-span-2">
                      <p className="text-3xl font-bold font-heading">{stats.weekly_stats.calories_consumed.toLocaleString()}</p>
                      <p className="text-sm text-muted-foreground">Calories totales</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
