import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { 
  Dumbbell, 
  ArrowLeft,
  Sparkles,
  Loader2,
  Clock,
  Flame,
  Play,
  Check,
  Plus
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function WorkoutsPage() {
  const navigate = useNavigate();
  const [programs, setPrograms] = useState([]);
  const [currentProgram, setCurrentProgram] = useState(null);
  const [workoutLogs, setWorkoutLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [logDialogOpen, setLogDialogOpen] = useState(false);
  const [newLog, setNewLog] = useState({
    workout_name: '',
    duration_minutes: '',
    calories_burned: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [programsRes, logsRes] = await Promise.all([
        axios.get(`${API}/workouts/programs`, { withCredentials: true }),
        axios.get(`${API}/workouts/logs`, { withCredentials: true })
      ]);
      setPrograms(programsRes.data);
      if (programsRes.data.length > 0) {
        setCurrentProgram(programsRes.data[0].workout_plan);
      }
      setWorkoutLogs(logsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateProgram = async () => {
    setGenerating(true);
    try {
      const response = await axios.post(`${API}/workouts/generate`, {}, { withCredentials: true });
      setCurrentProgram(response.data.workout_plan);
      toast.success('Programme d\'entraînement généré !');
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de la génération');
    } finally {
      setGenerating(false);
    }
  };

  const logWorkout = async () => {
    if (!newLog.workout_name || !newLog.duration_minutes) {
      toast.error('Nom et durée requis');
      return;
    }

    try {
      await axios.post(`${API}/workouts/log`, {
        workout_name: newLog.workout_name,
        duration_minutes: parseInt(newLog.duration_minutes),
        calories_burned: parseInt(newLog.calories_burned) || 0,
        exercises: []
      }, { withCredentials: true });
      
      toast.success('Entraînement enregistré !');
      setLogDialogOpen(false);
      setNewLog({ workout_name: '', duration_minutes: '', calories_burned: '' });
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

  const workouts = currentProgram?.workouts || [];

  return (
    <div className="min-h-screen bg-background pb-safe" data-testid="workouts-page">
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
              <h1 className="font-heading text-xl font-bold">Entraînements</h1>
              <p className="text-sm text-muted-foreground">
                {currentProgram?.program_name || 'Programmes personnalisés'}
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="p-4 space-y-6 pb-24">
        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button
            className="flex-1 rounded-full shadow-glow bg-primary"
            onClick={generateProgram}
            disabled={generating}
            data-testid="generate-workout-btn"
          >
            {generating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Génération...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Nouveau programme
              </>
            )}
          </Button>
          
          <Dialog open={logDialogOpen} onOpenChange={setLogDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="rounded-full" data-testid="log-workout-btn">
                <Plus className="w-4 h-4 mr-2" />
                Logger
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Enregistrer un entraînement</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Nom de l'entraînement</Label>
                  <Input
                    placeholder="Ex: Cardio HIIT"
                    value={newLog.workout_name}
                    onChange={(e) => setNewLog({ ...newLog, workout_name: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Durée (minutes)</Label>
                    <Input
                      type="number"
                      placeholder="30"
                      value={newLog.duration_minutes}
                      onChange={(e) => setNewLog({ ...newLog, duration_minutes: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Calories brûlées</Label>
                    <Input
                      type="number"
                      placeholder="250"
                      value={newLog.calories_burned}
                      onChange={(e) => setNewLog({ ...newLog, calories_burned: e.target.value })}
                    />
                  </div>
                </div>
                <Button onClick={logWorkout} className="w-full">
                  Enregistrer
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Program Info */}
        {currentProgram && (
          <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-secondary/5">
            <CardContent className="p-4">
              <h2 className="font-heading font-bold text-lg">{currentProgram.program_name}</h2>
              <div className="flex gap-4 mt-2 text-sm text-muted-foreground">
                <span>{currentProgram.duration_weeks} semaines</span>
                <span>{currentProgram.days_per_week} jours/semaine</span>
              </div>
              {currentProgram.equipment_needed?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {currentProgram.equipment_needed.map((equip, i) => (
                    <span key={i} className="px-2 py-1 rounded-full bg-muted text-xs">
                      {equip}
                    </span>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Workouts List */}
        {workouts.length > 0 ? (
          <div className="space-y-4">
            <h3 className="font-heading font-semibold">Programme de la semaine</h3>
            {workouts.map((workout, index) => (
              <Card key={index} className="workout-card overflow-hidden">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="text-sm text-muted-foreground">{workout.day}</p>
                      <h4 className="font-heading font-semibold text-lg">{workout.focus}</h4>
                    </div>
                    <Button size="sm" className="rounded-full">
                      <Play className="w-4 h-4 mr-1" />
                      Commencer
                    </Button>
                  </div>
                  
                  <div className="flex gap-4 text-sm text-muted-foreground mb-4">
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {workout.duration_minutes} min
                    </span>
                    <span className="flex items-center gap-1">
                      <Flame className="w-4 h-4 text-accent" />
                      ~{workout.calories_burn_estimate} kcal
                    </span>
                  </div>

                  {workout.exercises?.length > 0 && (
                    <div className="space-y-2">
                      {workout.exercises.slice(0, 4).map((exercise, i) => (
                        <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-muted/50">
                          <span className="text-sm font-medium">{exercise.name}</span>
                          <span className="text-xs text-muted-foreground">
                            {exercise.sets}x{exercise.reps}
                          </span>
                        </div>
                      ))}
                      {workout.exercises.length > 4 && (
                        <p className="text-xs text-muted-foreground text-center">
                          +{workout.exercises.length - 4} exercices de plus
                        </p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Dumbbell className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Aucun programme</p>
            <p className="text-sm text-muted-foreground mt-1">
              Générez votre premier programme personnalisé
            </p>
          </div>
        )}

        {/* Recent Workouts */}
        {workoutLogs.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="font-heading text-lg flex items-center gap-2">
                <Check className="w-5 h-5 text-primary" />
                Entraînements récents
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {workoutLogs.slice(0, 5).map((log) => (
                <div key={log.log_id} className="flex items-center justify-between p-3 rounded-xl bg-muted/50">
                  <div>
                    <p className="font-medium">{log.workout_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(log.logged_at).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                  <div className="text-right text-sm">
                    <p>{log.duration_minutes} min</p>
                    <p className="text-muted-foreground">{log.calories_burned} kcal</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Tips */}
        {currentProgram?.tips?.length > 0 && (
          <Card className="border-accent/20 bg-accent/5">
            <CardContent className="p-4">
              <h3 className="font-semibold mb-2">💪 Conseils</h3>
              <ul className="space-y-1">
                {currentProgram.tips.map((tip, i) => (
                  <li key={i} className="text-sm text-muted-foreground">• {tip}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
