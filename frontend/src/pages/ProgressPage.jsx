import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area, ComposedChart, BarChart, Bar } from 'recharts';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { 
  TrendingUp, 
  ArrowLeft,
  Scale,
  Trophy,
  Target,
  Plus,
  Flame,
  Award,
  Activity,
  Footprints,
  Download,
  FileText,
  Loader2,
  RefreshCw,
  Zap
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
  
  // Steps & calories burned
  const [stepsData, setStepsData] = useState(null);
  const [stepsHistory, setStepsHistory] = useState([]);
  const [newSteps, setNewSteps] = useState('');
  const [stepsDialogOpen, setStepsDialogOpen] = useState(false);
  const [loadingSteps, setLoadingSteps] = useState(false);
  
  // PDF generation
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const [reportData, setReportData] = useState(null);

  useEffect(() => {
    fetchData();
    fetchStepsData();
  }, []);

  // Auto-refresh steps every 60 seconds when page is visible
  useEffect(() => {
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible' && activeTab === 'steps') {
        fetchStepsData();
      }
    }, 60000);
    
    return () => clearInterval(interval);
  }, [activeTab]);

  const fetchData = async () => {
    try {
      const [statsRes, weightRes, bmiRes, badgesRes] = await Promise.allSettled([
        axios.get(`${API}/progress/stats`, { withCredentials: true }),
        axios.get(`${API}/progress/weight`, { withCredentials: true }),
        axios.get(`${API}/progress/bmi`, { withCredentials: true }),
        axios.get(`${API}/badges`, { withCredentials: true })
      ]);
      
      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
      if (weightRes.status === 'fulfilled') setWeightHistory(weightRes.value.data);
      if (bmiRes.status === 'fulfilled') setBmiData(bmiRes.value.data);
      if (badgesRes.status === 'fulfilled') setBadges(badgesRes.value.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStepsData = async () => {
    try {
      const [todayRes, historyRes] = await Promise.allSettled([
        axios.get(`${API}/steps/today`, { withCredentials: true }),
        axios.get(`${API}/steps/history?days=7`, { withCredentials: true })
      ]);
      
      if (todayRes.status === 'fulfilled') setStepsData(todayRes.value.data);
      if (historyRes.status === 'fulfilled') setStepsHistory(historyRes.value.data || []);
    } catch (error) {
      console.error('Error fetching steps:', error);
    }
  };

  const logWeight = async () => {
    if (!newWeight) {
      toast.error('Veuillez entrer votre poids');
      return;
    }
    
    try {
      await axios.post(`${API}/progress/weight`, { weight: parseFloat(newWeight) }, { withCredentials: true });
      toast.success('Poids enregistré !');
      
      // Refresh data immediately
      const [weightRes, bmiRes] = await Promise.all([
        axios.get(`${API}/progress/weight`, { withCredentials: true }),
        axios.get(`${API}/progress/bmi`, { withCredentials: true })
      ]);
      setWeightHistory(weightRes.data);
      setBmiData(bmiRes.data);
      
      setNewWeight('');
      setWeightDialogOpen(false);
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement');
    }
  };

  const logSteps = async () => {
    if (!newSteps || parseInt(newSteps) < 0) {
      toast.error('Veuillez entrer un nombre de pas valide');
      return;
    }
    
    setLoadingSteps(true);
    try {
      const response = await axios.post(`${API}/steps/log`, { 
        steps: parseInt(newSteps),
        source: 'manual'
      }, { withCredentials: true });
      
      toast.success(`${newSteps} pas enregistrés ! (${response.data.calories_burned} kcal brûlées)`);
      setNewSteps('');
      setStepsDialogOpen(false);
      fetchStepsData();
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement');
    } finally {
      setLoadingSteps(false);
    }
  };

  const generatePdfReport = async () => {
    setGeneratingPdf(true);
    
    try {
      // Fetch report data
      const response = await axios.get(`${API}/reports/progress-pdf`, { withCredentials: true });
      const data = response.data;
      setReportData(data);
      
      // Generate PDF
      const doc = new jsPDF();
      const pageWidth = doc.internal.pageSize.getWidth();
      
      // Header
      doc.setFontSize(24);
      doc.setTextColor(244, 114, 182); // Primary color
      doc.text('Fat & Slim', pageWidth / 2, 20, { align: 'center' });
      
      doc.setFontSize(14);
      doc.setTextColor(100);
      doc.text('Rapport de Progression', pageWidth / 2, 30, { align: 'center' });
      
      // User info
      doc.setFontSize(10);
      doc.setTextColor(60);
      doc.text(`Généré le: ${new Date().toLocaleDateString('fr-FR')}`, 20, 45);
      doc.text(`Utilisateur: ${data.user?.name || 'Non défini'}`, 20, 52);
      doc.text(`Membre depuis: ${data.user?.created_at ? new Date(data.user.created_at).toLocaleDateString('fr-FR') : 'Non défini'}`, 20, 59);
      doc.text(`Jours actifs: ${data.user?.days_active || 0}`, 20, 66);
      
      // Profile section
      doc.setFontSize(14);
      doc.setTextColor(0);
      doc.text('Profil', 20, 82);
      
      let lastY = 87;
      
      autoTable(doc, {
        startY: lastY,
        head: [['Paramètre', 'Valeur']],
        body: [
          ['Âge', `${data.profile?.age || 'N/A'} ans`],
          ['Taille', `${data.profile?.height || 'N/A'} cm`],
          ['Objectif calories', `${data.profile?.daily_calorie_target || 'N/A'} kcal/jour`],
          ['Poids objectif', `${data.profile?.target_weight || 'N/A'} kg`],
        ],
        theme: 'grid',
        headStyles: { fillColor: [244, 114, 182] },
        styles: { fontSize: 9 }
      });
      
      lastY = doc.lastAutoTable.finalY + 15;
      
      // Weight progress section
      doc.setFontSize(14);
      doc.text('Progression du poids', 20, lastY);
      
      autoTable(doc, {
        startY: lastY + 5,
        head: [['Métrique', 'Valeur']],
        body: [
          ['Poids initial', `${data.weight_progress?.start_weight || 'N/A'} kg`],
          ['Poids actuel', `${data.weight_progress?.current_weight || 'N/A'} kg`],
          ['Variation', `${(data.weight_progress?.weight_change || 0) > 0 ? '+' : ''}${data.weight_progress?.weight_change || 0} kg`],
          ['IMC initial', `${data.weight_progress?.bmi_start || 'N/A'}`],
          ['IMC actuel', `${data.weight_progress?.bmi_current || 'N/A'}`],
          ['Pesées enregistrées', `${data.weight_progress?.entries_count || 0}`],
        ],
        theme: 'grid',
        headStyles: { fillColor: [163, 230, 53] },
        styles: { fontSize: 9 }
      });
      
      lastY = doc.lastAutoTable.finalY + 15;
      
      // Nutrition stats
      doc.setFontSize(14);
      doc.text('Statistiques nutritionnelles', 20, lastY);
      
      autoTable(doc, {
        startY: lastY + 5,
        head: [['Métrique', 'Valeur']],
        body: [
          ['Repas enregistrés', `${data.nutrition_stats?.total_meals_logged || 0}`],
          ['Calories totales', `${(data.nutrition_stats?.total_calories_logged || 0).toLocaleString()} kcal`],
          ['Moyenne journalière', `${data.nutrition_stats?.avg_daily_calories || 0} kcal`],
          ['Objectif journalier', `${data.nutrition_stats?.target_calories || 0} kcal`],
        ],
        theme: 'grid',
        headStyles: { fillColor: [251, 191, 36] },
        styles: { fontSize: 9 }
      });
      
      lastY = doc.lastAutoTable.finalY + 15;
      
      // Activity stats
      doc.setFontSize(14);
      doc.text('Activité physique', 20, lastY);
      
      autoTable(doc, {
        startY: lastY + 5,
        head: [['Métrique', 'Valeur']],
        body: [
          ['Pas totaux', `${(data.activity_stats?.total_steps || 0).toLocaleString()}`],
          ['Calories brûlées', `${(data.activity_stats?.total_calories_burned || 0).toLocaleString()} kcal`],
          ['Moyenne journalière', `${(data.activity_stats?.avg_daily_steps || 0).toLocaleString()} pas`],
          ['Jours suivis', `${data.activity_stats?.days_tracked || 0}`],
        ],
        theme: 'grid',
        headStyles: { fillColor: [147, 51, 234] },
        styles: { fontSize: 9 }
      });
      
      // Footer
      const pageCount = doc.internal.getNumberOfPages();
      doc.setFontSize(8);
      doc.setTextColor(150);
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.text(
          `Fat & Slim - Rapport généré le ${new Date().toLocaleDateString('fr-FR')} - Page ${i}/${pageCount}`,
          pageWidth / 2,
          doc.internal.pageSize.getHeight() - 10,
          { align: 'center' }
        );
      }
      
      // Save PDF
      doc.save(`fat-slim-rapport-${new Date().toISOString().split('T')[0]}.pdf`);
      toast.success('Rapport PDF téléchargé !');
      
    } catch (error) {
      console.error('Error generating PDF:', error);
      toast.error('Erreur lors de la génération du rapport: ' + (error.message || 'Erreur inconnue'));
    } finally {
      setGeneratingPdf(false);
    }
  };

  const getBmiCategory = (bmi) => {
    if (bmi < 18.5) return { label: 'Insuffisance pondérale', color: 'text-blue-500' };
    if (bmi < 25) return { label: 'Poids normal', color: 'text-green-500' };
    if (bmi < 30) return { label: 'Surpoids', color: 'text-yellow-500' };
    return { label: 'Obésité', color: 'text-red-500' };
  };

  const getStepsRecommendation = () => {
    if (!stepsData) return '';
    const remaining = stepsData.goal - stepsData.steps;
    if (remaining <= 0) return '🎉 Objectif atteint ! Bravo !';
    if (remaining < 2000) return `💪 Plus que ${remaining.toLocaleString()} pas, vous y êtes presque !`;
    if (remaining < 5000) return `🚶 Encore ${remaining.toLocaleString()} pas, une petite marche ?`;
    return `🎯 ${remaining.toLocaleString()} pas restants pour aujourd'hui`;
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

  const chartData = weightHistory.map(entry => ({
    date: new Date(entry.date).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }),
    weight: entry.weight
  }));

  const stepsChartData = stepsHistory.map(entry => ({
    date: new Date(entry.date).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }),
    steps: entry.steps,
    calories: entry.calories_burned
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
            <h1 className="font-heading text-xl font-bold">Mes Progrès</h1>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={generatePdfReport}
            disabled={generatingPdf}
          >
            {generatingPdf ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Download className="w-4 h-4 mr-2" />
            )}
            Rapport PDF
          </Button>
        </div>
      </header>

      <main className="p-4 space-y-4 max-w-lg mx-auto">
        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="weight" className="flex items-center gap-1">
              <Scale className="w-4 h-4" />
              Poids
            </TabsTrigger>
            <TabsTrigger value="steps" className="flex items-center gap-1">
              <Footprints className="w-4 h-4" />
              Pas
            </TabsTrigger>
            <TabsTrigger value="badges" className="flex items-center gap-1">
              <Trophy className="w-4 h-4" />
              Badges
            </TabsTrigger>
          </TabsList>

          {/* Weight Tab */}
          <TabsContent value="weight" className="space-y-4">
            {/* BMI Card */}
            {bmiData && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="font-heading text-lg flex items-center gap-2">
                    <Activity className="w-5 h-5 text-primary" />
                    Indice de Masse Corporelle
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-4xl font-bold">{bmiData.bmi}</p>
                      <p className={`text-sm font-medium ${getBmiCategory(bmiData.bmi).color}`}>
                        {getBmiCategory(bmiData.bmi).label}
                      </p>
                    </div>
                    <div className="text-right text-sm text-muted-foreground">
                      <p>Taille: {bmiData.height} cm</p>
                      <p>Poids: {bmiData.weight} kg</p>
                    </div>
                  </div>
                  
                  {/* BMI Scale */}
                  <div className="relative h-3 rounded-full bg-gradient-to-r from-blue-500 via-green-500 via-yellow-500 to-red-500">
                    <div 
                      className="absolute w-3 h-5 bg-white border-2 border-black rounded-sm -top-1"
                      style={{ 
                        left: `${Math.min(Math.max((bmiData.bmi - 15) / 25 * 100, 0), 100)}%`,
                        transform: 'translateX(-50%)'
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>15</span>
                    <span>18.5</span>
                    <span>25</span>
                    <span>30</span>
                    <span>40</span>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Weight Chart */}
            <Card>
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <Scale className="w-5 h-5 text-secondary" />
                  Évolution du poids
                </CardTitle>
                <Dialog open={weightDialogOpen} onOpenChange={setWeightDialogOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm" className="rounded-full">
                      <Plus className="w-4 h-4 mr-1" />
                      Ajouter
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Enregistrer mon poids</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div>
                        <label className="text-sm text-muted-foreground">Poids (kg)</label>
                        <Input
                          type="number"
                          step="0.1"
                          placeholder="Ex: 72.5"
                          value={newWeight}
                          onChange={(e) => setNewWeight(e.target.value)}
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button onClick={logWeight}>Enregistrer</Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                {chartData.length > 0 ? (
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis dataKey="date" stroke="#666" fontSize={10} />
                        <YAxis 
                          stroke="#666" 
                          fontSize={10}
                          domain={['auto', 'auto']}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#1a1a1a', 
                            border: '1px solid #333',
                            borderRadius: '8px'
                          }}
                        />
                        {stats?.target_weight && (
                          <ReferenceLine 
                            y={stats.target_weight} 
                            stroke="#a3e635" 
                            strokeDasharray="5 5"
                            label={{ value: 'Objectif', fill: '#a3e635', fontSize: 10 }}
                          />
                        )}
                        <Area 
                          type="monotone" 
                          dataKey="weight" 
                          fill="rgba(244, 114, 182, 0.2)" 
                          stroke="none"
                        />
                        <Line 
                          type="monotone" 
                          dataKey="weight" 
                          stroke="#F472B6" 
                          strokeWidth={2}
                          dot={{ fill: '#F472B6', r: 4 }}
                          activeDot={{ r: 6, fill: '#F472B6' }}
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-64 flex items-center justify-center text-center">
                    <div>
                      <Scale className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">Aucune donnée</p>
                      <p className="text-sm text-muted-foreground">Commencez à enregistrer votre poids</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Stats Summary */}
            {stats && (
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold text-primary">
                      {stats.current_weight || '—'}
                    </p>
                    <p className="text-xs text-muted-foreground">Poids actuel (kg)</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold text-secondary">
                      {stats.target_weight || '—'}
                    </p>
                    <p className="text-xs text-muted-foreground">Objectif (kg)</p>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* Steps Tab */}
          <TabsContent value="steps" className="space-y-4">
            {/* Today's Steps Card */}
            <Card className="bg-gradient-to-br from-primary/10 to-secondary/5">
              <CardHeader className="pb-2">
                <CardTitle className="font-heading text-lg flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Footprints className="w-5 h-5 text-primary" />
                    Pas aujourd'hui
                  </div>
                  <Button 
                    variant="ghost" 
                    size="icon"
                    onClick={fetchStepsData}
                  >
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center mb-4">
                  <p className="text-5xl font-bold text-primary">
                    {(stepsData?.steps || 0).toLocaleString()}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    sur {(stepsData?.goal || 10000).toLocaleString()} pas
                  </p>
                </div>
                
                <Progress 
                  value={stepsData?.progress || 0} 
                  className="h-4 mb-4"
                />
                
                <p className="text-center text-sm text-muted-foreground mb-4">
                  {getStepsRecommendation()}
                </p>
                
                {/* Calories Burned */}
                <div className="flex items-center justify-center gap-6 p-4 rounded-xl bg-background/50">
                  <div className="text-center">
                    <div className="flex items-center gap-1 justify-center">
                      <Flame className="w-5 h-5 text-orange-500" />
                      <p className="text-2xl font-bold">{stepsData?.calories_burned || 0}</p>
                    </div>
                    <p className="text-xs text-muted-foreground">kcal brûlées</p>
                  </div>
                  <div className="h-10 w-px bg-border" />
                  <div className="text-center">
                    <div className="flex items-center gap-1 justify-center">
                      <Zap className="w-5 h-5 text-yellow-500" />
                      <p className="text-2xl font-bold">{stepsData?.progress || 0}%</p>
                    </div>
                    <p className="text-xs text-muted-foreground">objectif</p>
                  </div>
                </div>
                
                <Dialog open={stepsDialogOpen} onOpenChange={setStepsDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="w-full mt-4">
                      <Plus className="w-4 h-4 mr-2" />
                      Enregistrer mes pas
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Enregistrer mes pas</DialogTitle>
                      <DialogDescription>
                        Entrez le nombre de pas de votre podomètre ou montre connectée
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <Input
                        type="number"
                        placeholder="Ex: 8500"
                        value={newSteps}
                        onChange={(e) => setNewSteps(e.target.value)}
                      />
                      <p className="text-xs text-muted-foreground">
                        💡 Les calories seront calculées automatiquement selon votre profil
                      </p>
                    </div>
                    <DialogFooter>
                      <Button onClick={logSteps} disabled={loadingSteps}>
                        {loadingSteps ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : null}
                        Enregistrer
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </CardContent>
            </Card>

            {/* Steps History Chart */}
            {stepsChartData.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="font-heading text-lg">Historique (7 jours)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={stepsChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis dataKey="date" stroke="#666" fontSize={10} />
                        <YAxis stroke="#666" fontSize={10} />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#1a1a1a', 
                            border: '1px solid #333',
                            borderRadius: '8px'
                          }}
                          formatter={(value, name) => [
                            value.toLocaleString(), 
                            name === 'steps' ? 'Pas' : 'Calories'
                          ]}
                        />
                        <Bar dataKey="steps" fill="#F472B6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Recommendations */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <Target className="w-5 h-5 text-accent" />
                  Objectifs recommandés
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-3 rounded-xl bg-muted/50">
                  <p className="font-medium text-sm">🎯 Objectif quotidien</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {(stepsData?.goal || 10000).toLocaleString()} pas/jour basé sur votre niveau d'activité
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-muted/50">
                  <p className="font-medium text-sm">🔥 Calories à brûler</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Environ {Math.round((stepsData?.goal || 10000) * 0.04)} kcal avec l'objectif de pas
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-muted/50">
                  <p className="font-medium text-sm">🚶 Distance estimée</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    ~{(((stepsData?.goal || 10000) * 0.75) / 1000).toFixed(1)} km pour atteindre l'objectif
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Badges Tab */}
          <TabsContent value="badges" className="space-y-4">
            {/* Stats */}
            <div className="grid grid-cols-3 gap-3">
              <Card className="p-4 text-center">
                <p className="text-2xl font-bold text-primary">{badges?.total_earned || 0}</p>
                <p className="text-xs text-muted-foreground">Obtenus</p>
              </Card>
              <Card className="p-4 text-center">
                <p className="text-2xl font-bold text-muted-foreground">{(badges?.total_available || 0) - (badges?.total_earned || 0)}</p>
                <p className="text-xs text-muted-foreground">À débloquer</p>
              </Card>
              <Card className="p-4 text-center">
                <p className="text-2xl font-bold text-accent">{badges?.total_available || 0}</p>
                <p className="text-xs text-muted-foreground">Total</p>
              </Card>
            </div>

            {/* Next badges to earn */}
            {badges?.next_badges?.length > 0 && (
              <Card className="border-primary/30 bg-gradient-to-br from-primary/5 to-secondary/5">
                <CardHeader className="pb-2">
                  <CardTitle className="font-heading text-base flex items-center gap-2">
                    🎯 Prochains badges à débloquer
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {badges.next_badges.map((badge) => (
                    <div key={badge.id} className="flex items-center gap-3 p-3 rounded-lg bg-background/50">
                      <span className="text-2xl">{badge.icon}</span>
                      <div className="flex-1">
                        <p className="font-medium text-sm">{badge.name}</p>
                        <p className="text-xs text-muted-foreground">{badge.description}</p>
                        <div className="mt-1.5">
                          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                            <span>{badge.progress}/{badge.target}</span>
                            <span>{badge.progress_percent}%</span>
                          </div>
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gradient-to-r from-primary to-secondary rounded-full transition-all"
                              style={{ width: `${badge.progress_percent}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Earned Badges */}
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <Trophy className="w-5 h-5 text-accent" />
                  Badges obtenus ({badges?.earned?.length || 0})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {badges?.earned?.length > 0 ? (
                  <div className="grid grid-cols-2 gap-3">
                    {badges.earned.map((badge) => (
                      <div 
                        key={badge.id}
                        className="p-4 rounded-xl border text-center bg-gradient-to-br from-primary/10 to-secondary/10 border-primary/30"
                      >
                        <span className="text-3xl">{badge.icon}</span>
                        <p className="font-medium text-sm mt-2">{badge.name}</p>
                        <p className="text-xs text-muted-foreground">{badge.description}</p>
                        <p className="text-xs text-primary mt-1">✓ Obtenu</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-muted-foreground text-sm">Aucun badge obtenu encore</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* All Available Badges */}
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  🏅 Tous les badges
                </CardTitle>
              </CardHeader>
              <CardContent>
                {badges?.available?.length > 0 ? (
                  <div className="grid grid-cols-2 gap-3">
                    {badges.available.map((badge) => (
                      <div 
                        key={badge.id}
                        className="p-4 rounded-xl border text-center bg-muted/30 border-border"
                      >
                        <span className="text-3xl opacity-50">{badge.icon}</span>
                        <p className="font-medium text-sm mt-2 text-muted-foreground">{badge.name}</p>
                        <p className="text-xs text-muted-foreground">{badge.description}</p>
                        <div className="mt-2">
                          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-primary/50 rounded-full"
                              style={{ width: `${badge.progress_percent || 0}%` }}
                            />
                          </div>
                          <p className="text-[10px] text-muted-foreground mt-1">{badge.progress}/{badge.target}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Trophy className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">Vous avez débloqué tous les badges ! 🎉</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
