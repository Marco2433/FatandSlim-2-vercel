import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { 
  TrendingUp, 
  ArrowLeft,
  Scale,
  Trophy,
  Target,
  Plus,
  Flame,
  Award
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ProgressPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [weightHistory, setWeightHistory] = useState([]);
  const [badges, setBadges] = useState(null);
  const [loading, setLoading] = useState(true);
  const [weightDialogOpen, setWeightDialogOpen] = useState(false);
  const [newWeight, setNewWeight] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, weightRes, badgesRes] = await Promise.all([
        axios.get(`${API}/progress/stats`, { withCredentials: true }),
        axios.get(`${API}/progress/weight`, { withCredentials: true }),
        axios.get(`${API}/badges`, { withCredentials: true })
      ]);
      setStats(statsRes.data);
      setWeightHistory(weightRes.data);
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
      await axios.post(`${API}/progress/weight`, {
        weight: parseFloat(newWeight)
      }, { withCredentials: true });
      
      toast.success('Poids enregistré !');
      setWeightDialogOpen(false);
      setNewWeight('');
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement');
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

  // Format weight data for chart
  const chartData = weightHistory.map(entry => ({
    date: new Date(entry.date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }),
    weight: entry.weight
  }));

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
        </div>
      </header>

      <main className="p-4 space-y-6 pb-24">
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
                <Dialog open={weightDialogOpen} onOpenChange={setWeightDialogOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm" className="rounded-full" data-testid="add-weight-btn">
                      <Plus className="w-4 h-4 mr-1" />
                      Ajouter
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

              <div className="grid grid-cols-3 gap-4 mt-4">
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
                  <p className="text-sm text-muted-foreground">IMC</p>
                  <p className="font-heading font-bold text-lg">{stats.bmi}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Weight Chart */}
        {chartData.length > 1 && (
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
                  <LineChart data={chartData}>
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
                    />
                    <Line 
                      type="monotone" 
                      dataKey="weight" 
                      stroke="hsl(var(--primary))"
                      strokeWidth={3}
                      dot={{ fill: 'hsl(var(--primary))', strokeWidth: 2 }}
                      activeDot={{ r: 6, fill: 'hsl(var(--primary))' }}
                    />
                  </LineChart>
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

        {/* Badges */}
        {badges && (
          <Card data-testid="badges-card">
            <CardHeader className="pb-2">
              <CardTitle className="font-heading text-lg flex items-center gap-2">
                <Trophy className="w-5 h-5 text-accent" />
                Badges ({badges.total_earned})
              </CardTitle>
            </CardHeader>
            <CardContent>
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
                {badges.available.slice(0, 3).map((badge) => (
                  <div 
                    key={badge.id}
                    className="flex flex-col items-center text-center p-3 opacity-50"
                  >
                    <div className="w-14 h-14 rounded-2xl badge-3d-locked flex items-center justify-center mb-2">
                      <Award className="w-7 h-7 text-muted-foreground" />
                    </div>
                    <p className="text-xs font-medium text-muted-foreground">{badge.name}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
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
      </main>
    </div>
  );
}
