import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Slider } from '@/components/ui/slider';
import { toast } from 'sonner';
import AIWarningDialog from '@/components/AIWarningDialog';
import { 
  ArrowLeft,
  Activity,
  Droplets,
  Pill,
  Scale,
  ChefHat,
  BookOpen,
  Bot,
  AlertTriangle,
  Heart,
  TrendingDown,
  Calendar,
  Check,
  Send,
  Loader2,
  Info,
  Sparkles,
  Clock,
  User,
  Stethoscope,
  Apple,
  Zap,
  Share2,
  Bell
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function BariatricPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Dashboard data
  const [dashboard, setDashboard] = useState(null);
  const [recipes, setRecipes] = useState([]);
  const [articles, setArticles] = useState([]);
  
  // Daily log form
  const [logForm, setLogForm] = useState({
    weight: '',
    food_tolerance: 'ok',
    energy_level: 3,
    hydration: '',
    supplements_taken: [],
    notes: ''
  });
  const [savingLog, setSavingLog] = useState(false);
  
  // Coach
  const [coachQuestion, setCoachQuestion] = useState('');
  const [coachResponse, setCoachResponse] = useState('');
  const [coachLoading, setCoachLoading] = useState(false);
  
  // AI Warning state
  const [showAIWarning, setShowAIWarning] = useState(false);
  const [pendingCoachQuestion, setPendingCoachQuestion] = useState('');
  
  // Disclaimer
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(false);
  
  // Article modal
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [showArticleModal, setShowArticleModal] = useState(false);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const [dashRes, recipesRes, articlesRes, disclaimerRes] = await Promise.allSettled([
        axios.get(`${API}/bariatric/dashboard`, { withCredentials: true }),
        axios.get(`${API}/bariatric/recipes`, { withCredentials: true }),
        axios.get(`${API}/bariatric/articles`, { withCredentials: true }),
        axios.get(`${API}/bariatric/check-disclaimer`, { withCredentials: true })
      ]);
      
      if (dashRes.status === 'fulfilled') {
        setDashboard(dashRes.value.data);
        if (dashRes.value.data.today_log) {
          setLogForm({
            weight: dashRes.value.data.today_log.weight || '',
            food_tolerance: dashRes.value.data.today_log.food_tolerance || 'ok',
            energy_level: dashRes.value.data.today_log.energy_level || 3,
            hydration: dashRes.value.data.today_log.hydration || '',
            supplements_taken: dashRes.value.data.today_log.supplements_taken || [],
            notes: dashRes.value.data.today_log.notes || ''
          });
        }
      }
      if (recipesRes.status === 'fulfilled') setRecipes(recipesRes.value.data.recipes || []);
      if (articlesRes.status === 'fulfilled') setArticles(articlesRes.value.data.articles || []);
      
      // Show disclaimer if not seen
      if (disclaimerRes.status === 'fulfilled' && !disclaimerRes.value.data.seen_disclaimer) {
        setShowDisclaimer(true);
      }
    } catch (error) {
      console.error('Error fetching bariatric data:', error);
      if (error.response?.status === 404) {
        toast.error('Profil bariatrique non trouvé');
        navigate('/dashboard');
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const acceptDisclaimer = async () => {
    try {
      await axios.post(`${API}/bariatric/accept-disclaimer`, {}, { withCredentials: true });
      setShowDisclaimer(false);
      setDisclaimerAccepted(true);
    } catch (error) {
      console.error(error);
    }
  };

  const saveLog = async () => {
    setSavingLog(true);
    try {
      const response = await axios.post(`${API}/bariatric/log`, {
        ...logForm,
        weight: logForm.weight ? parseFloat(logForm.weight) : null,
        hydration: logForm.hydration ? parseInt(logForm.hydration) : null
      }, { withCredentials: true });
      
      toast.success('Suivi enregistré !');
      
      if (response.data.alerts?.length > 0) {
        response.data.alerts.forEach(alert => toast.warning(alert));
      }
      
      fetchDashboard();
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setSavingLog(false);
    }
  };

  const handleAskCoach = () => {
    if (!coachQuestion.trim()) return;
    setPendingCoachQuestion(coachQuestion.trim());
    setShowAIWarning(true);
  };

  const askCoach = async () => {
    if (!pendingCoachQuestion) return;
    
    setCoachLoading(true);
    setCoachResponse('');
    
    try {
      const response = await axios.post(`${API}/bariatric/coach`, {
        question: pendingCoachQuestion
      }, { withCredentials: true });
      
      setCoachResponse(response.data.response);
      if (response.data.from_cache) {
        toast.info('Réponse depuis le cache (0 crédit utilisé)');
      }
    } catch (error) {
      if (error.response?.status === 429) {
        toast.error('Limite quotidienne IA atteinte (2/jour)');
      } else {
        toast.error('Erreur lors de la génération');
      }
    } finally {
      setCoachLoading(false);
      setPendingCoachQuestion('');
    }
  };

  const toggleSupplement = (supp) => {
    setLogForm(prev => ({
      ...prev,
      supplements_taken: prev.supplements_taken.includes(supp)
        ? prev.supplements_taken.filter(s => s !== supp)
        : [...prev.supplements_taken, supp]
    }));
  };

  const shareBariatricArticle = async (article) => {
    try {
      await axios.post(`${API}/social/post`, {
        content: `📰 **${article.title}**\n\n${article.content || article.summary}\n\n📖 Source : ${article.source || 'Fat & Slim Bariatrique'} • ⏱️ ${article.read_time || '3 min'}`,
        type: 'share_article',
        image_url: article.image || null,
        shared_item: {
          title: article.title,
          summary: article.summary,
          category: article.category,
          source: article.source,
          image: article.image
        }
      }, { withCredentials: true });
      toast.success('Article partagé sur la communauté !');
    } catch (error) {
      toast.error('Erreur lors du partage');
    }
  };

  const getPhaseColor = (phase) => {
    switch(phase) {
      case 1: return 'bg-blue-500';
      case 2: return 'bg-orange-500';
      case 3: return 'bg-yellow-500';
      case 4: return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <AlertTriangle className="w-12 h-12 mx-auto text-destructive mb-4" />
            <h2 className="font-bold text-lg mb-2">Profil bariatrique non trouvé</h2>
            <p className="text-muted-foreground mb-4">Vous devez d'abord compléter votre profil avec les informations de chirurgie bariatrique.</p>
            <Button onClick={() => navigate('/dashboard')}>Retour au dashboard</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { profile, phase } = dashboard;
  const surgeryName = profile.surgery_type === 'bypass' ? 'By-pass gastrique' : 'Sleeve gastrectomie';

  return (
    <div className="min-h-screen bg-background pb-safe">
      {/* Disclaimer Dialog */}
      <Dialog open={showDisclaimer} onOpenChange={() => {}}>
        <DialogContent className="sm:max-w-lg" onPointerDownOutside={(e) => e.preventDefault()}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="w-5 h-5" />
              Mentions légales importantes
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-lg">
              <p className="font-semibold text-destructive mb-2">⚠️ AVERTISSEMENT</p>
              <ul className="text-sm space-y-2">
                <li>• Cette application <strong>ne fournit PAS de diagnostic médical</strong></li>
                <li>• Elle <strong>ne remplace PAS</strong> votre équipe soignante (chirurgien, nutritionniste, psychologue)</li>
                <li>• Elle <strong>ne modifie PAS</strong> vos traitements ou prescriptions</li>
                <li>• Elle <strong>ne fait aucune promesse médicale</strong></li>
              </ul>
            </div>
            <div className="p-4 bg-primary/10 border border-primary/30 rounded-lg">
              <p className="font-semibold mb-2">✅ Cette application vous aide à :</p>
              <ul className="text-sm space-y-1">
                <li>• Suivre votre progression quotidienne</li>
                <li>• Trouver des recettes adaptées à votre phase</li>
                <li>• Obtenir des conseils généraux validés</li>
                <li>• Rester motivé(e) dans votre parcours</li>
              </ul>
            </div>
            <p className="text-sm text-muted-foreground">
              En cas de symptômes inquiétants (douleurs, vomissements répétés, malaise), 
              <strong> contactez immédiatement votre équipe médicale</strong>.
            </p>
          </div>
          <DialogFooter>
            <Button onClick={acceptDisclaimer} className="w-full">
              <Check className="w-4 h-4 mr-2" />
              J'ai compris et j'accepte
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Header */}
      <header className="sticky top-0 z-10 px-4 py-3 bg-background/80 backdrop-blur-lg border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => navigate('/dashboard')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-lg font-bold">Dossier {profile.surgery_type === 'bypass' ? 'By-pass' : 'Sleeve'}</h1>
              <p className="text-xs text-muted-foreground">{phase.phase_name}</p>
            </div>
          </div>
          <Badge className={getPhaseColor(phase.phase)}>Phase {phase.phase}</Badge>
        </div>
      </header>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="w-full grid grid-cols-5 h-12 mx-0 rounded-none border-b">
          <TabsTrigger value="dashboard" className="text-xs"><Activity className="w-4 h-4" /></TabsTrigger>
          <TabsTrigger value="log" className="text-xs"><Scale className="w-4 h-4" /></TabsTrigger>
          <TabsTrigger value="recipes" className="text-xs"><ChefHat className="w-4 h-4" /></TabsTrigger>
          <TabsTrigger value="articles" className="text-xs"><BookOpen className="w-4 h-4" /></TabsTrigger>
          <TabsTrigger value="coach" className="text-xs"><Bot className="w-4 h-4" /></TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="p-4 space-y-4">
          {/* Surgery Info */}
          <Card className="border-primary/30 bg-gradient-to-r from-primary/5 to-secondary/5">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                  <Stethoscope className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-bold">{surgeryName}</h3>
                  <p className="text-sm text-muted-foreground">
                    {phase.days_since_surgery >= 0 
                      ? `J+${phase.days_since_surgery}` 
                      : `J${phase.days_since_surgery} (pré-op)`}
                  </p>
                </div>
              </div>
              
              {/* Phase Progress */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Progression</span>
                  <span className="font-medium">{phase.phase_name}</span>
                </div>
                <div className="flex gap-1">
                  {[1, 2, 3, 4].map(p => (
                    <div 
                      key={p} 
                      className={`h-2 flex-1 rounded ${p <= phase.phase ? getPhaseColor(p) : 'bg-muted'}`}
                    />
                  ))}
                </div>
                <p className="text-xs text-muted-foreground">
                  Texture autorisée : <span className="font-medium">{
                    phase.texture === 'liquid' ? 'Liquide' :
                    phase.texture === 'mixed' ? 'Mixé' :
                    phase.texture === 'soft' ? 'Mou' : 'Solide adapté'
                  }</span>
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Weight Progress */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-green-500" />
                Perte de poids
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold">{profile.pre_op_weight}</p>
                  <p className="text-xs text-muted-foreground">Pré-op (kg)</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-primary">{profile.current_weight}</p>
                  <p className="text-xs text-muted-foreground">Actuel (kg)</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-green-500">-{profile.weight_lost}</p>
                  <p className="text-xs text-muted-foreground">Perdu (kg)</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Today's Summary */}
          {dashboard.today_log && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-primary" />
                  Aujourd'hui
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-2">
                    <Heart className={`w-4 h-4 ${
                      dashboard.today_log.food_tolerance === 'ok' ? 'text-green-500' :
                      dashboard.today_log.food_tolerance === 'nausea' ? 'text-yellow-500' : 'text-red-500'
                    }`} />
                    <span className="text-sm">
                      {dashboard.today_log.food_tolerance === 'ok' ? 'Bonne tolérance' :
                       dashboard.today_log.food_tolerance === 'nausea' ? 'Nausées' : 'Vomissements'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-yellow-500" />
                    <span className="text-sm">Énergie : {dashboard.today_log.energy_level}/5</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Droplets className="w-4 h-4 text-blue-500" />
                    <span className="text-sm">{dashboard.today_log.hydration || 0} ml</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Pill className="w-4 h-4 text-purple-500" />
                    <span className="text-sm">{dashboard.today_log.supplements_taken?.length || 0} suppl.</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Medical Team */}
          {(profile.surgeon || profile.nutritionist || profile.clinic) && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <User className="w-5 h-5 text-primary" />
                  Mon équipe médicale
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {profile.clinic && (
                  <p className="text-sm"><strong>Clinique :</strong> {profile.clinic}</p>
                )}
                {profile.surgeon && (
                  <p className="text-sm"><strong>Chirurgien :</strong> {profile.surgeon}</p>
                )}
                {profile.nutritionist && (
                  <p className="text-sm"><strong>Nutritionniste :</strong> {profile.nutritionist}</p>
                )}
                {profile.psychologist && (
                  <p className="text-sm"><strong>Psychologue :</strong> {profile.psychologist}</p>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Daily Log Tab */}
        <TabsContent value="log" className="p-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Suivi quotidien</CardTitle>
              <CardDescription>Enregistrez vos données du jour</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Weight */}
              <div>
                <Label>Poids (kg)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={logForm.weight}
                  onChange={(e) => setLogForm({ ...logForm, weight: e.target.value })}
                  placeholder="Ex: 85.5"
                />
              </div>

              {/* Food Tolerance */}
              <div>
                <Label>Tolérance alimentaire</Label>
                <Select value={logForm.food_tolerance} onValueChange={(v) => setLogForm({ ...logForm, food_tolerance: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ok">✅ OK - Bonne tolérance</SelectItem>
                    <SelectItem value="nausea">🤢 Nausées</SelectItem>
                    <SelectItem value="vomiting">🤮 Vomissements</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Energy Level */}
              <div>
                <Label>Niveau d'énergie : {logForm.energy_level}/5</Label>
                <Slider
                  value={[logForm.energy_level]}
                  onValueChange={([v]) => setLogForm({ ...logForm, energy_level: v })}
                  max={5}
                  min={1}
                  step={1}
                  className="mt-2"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>Épuisé</span>
                  <span>En forme</span>
                </div>
              </div>

              {/* Hydration */}
              <div>
                <Label>Hydratation (ml)</Label>
                <Input
                  type="number"
                  value={logForm.hydration}
                  onChange={(e) => setLogForm({ ...logForm, hydration: e.target.value })}
                  placeholder="Ex: 1500"
                />
                <p className="text-xs text-muted-foreground mt-1">Objectif : 1500-2000 ml/jour</p>
              </div>

              {/* Supplements */}
              {profile.supplements?.length > 0 && (
                <div>
                  <Label>Compléments pris</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {profile.supplements.map(supp => (
                      <Badge
                        key={supp}
                        variant={logForm.supplements_taken.includes(supp) ? 'default' : 'outline'}
                        className="cursor-pointer"
                        onClick={() => toggleSupplement(supp)}
                      >
                        {logForm.supplements_taken.includes(supp) && <Check className="w-3 h-3 mr-1" />}
                        {supp}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Notes */}
              <div>
                <Label>Notes</Label>
                <Textarea
                  value={logForm.notes}
                  onChange={(e) => setLogForm({ ...logForm, notes: e.target.value })}
                  placeholder="Comment vous sentez-vous aujourd'hui ?"
                  rows={3}
                />
              </div>

              <Button onClick={saveLog} disabled={savingLog} className="w-full">
                {savingLog ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Check className="w-4 h-4 mr-2" />}
                Enregistrer
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Recipes Tab */}
        <TabsContent value="recipes" className="p-4 space-y-4">
          <div className="p-3 bg-primary/10 rounded-lg border border-primary/30">
            <p className="text-sm flex items-center gap-2">
              <Info className="w-4 h-4 text-primary" />
              <span>Recettes adaptées à la <strong>{phase.phase_name}</strong></span>
            </p>
          </div>

          {recipes.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <ChefHat className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Aucune recette disponible pour cette phase</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {recipes.map((recipe, idx) => (
                <Card key={idx}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-medium">{recipe.name}</h3>
                      <Badge variant="outline" className="text-xs">
                        {recipe.texture === 'liquid' ? 'Liquide' :
                         recipe.texture === 'mixed' ? 'Mixé' :
                         recipe.texture === 'soft' ? 'Mou' : 'Solide'}
                      </Badge>
                    </div>
                    <div className="flex gap-4 text-sm text-muted-foreground mb-2">
                      <span>🥩 {recipe.protein}g protéines</span>
                      <span>🔥 {recipe.calories} kcal</span>
                      <span>📏 {recipe.portion}</span>
                    </div>
                    <p className="text-sm">
                      <strong>Ingrédients :</strong> {recipe.ingredients?.join(', ')}
                    </p>
                    <p className="text-sm mt-1">
                      <strong>Préparation :</strong> {recipe.instructions}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Guidelines */}
          <Card className="border-yellow-500/30 bg-yellow-500/5">
            <CardContent className="p-4">
              <h4 className="font-medium mb-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-yellow-500" />
                Rappels importants
              </h4>
              <ul className="text-sm space-y-1">
                <li>• Portions de 60-120g maximum par repas</li>
                <li>• Toujours commencer par les protéines</li>
                <li>• Mâcher au moins 20 fois chaque bouchée</li>
                <li>• Ne pas boire pendant les repas</li>
              </ul>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Articles Tab */}
        <TabsContent value="articles" className="p-4 space-y-4">
          <p className="text-sm text-muted-foreground">Articles du jour sur le {surgeryName.toLowerCase()}</p>
          
          {/* Daily Log Reminder */}
          {dashboard.reminders && dashboard.reminders.length > 0 && (
            <Card className="border-amber-500/30 bg-amber-500/5">
              <CardContent className="p-3">
                <div className="flex items-start gap-2">
                  <Bell className="w-4 h-4 text-amber-500 mt-0.5" />
                  <div>
                    {dashboard.reminders.map((reminder, idx) => (
                      <p key={idx} className="text-sm">{reminder.message}</p>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
          
          {articles.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <BookOpen className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Aucun article disponible</p>
              </CardContent>
            </Card>
          ) : (
            articles.map((article, idx) => (
              <Card 
                key={idx} 
                className="cursor-pointer hover:border-primary/50 transition-colors"
                onClick={() => { setSelectedArticle(article); setShowArticleModal(true); }}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                      <BookOpen className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium">{article.title}</h3>
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{article.summary}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                        <span>📖 {article.source}</span>
                        <span>⏱️ {article.read_time}</span>
                        <Badge variant="outline" className="text-xs">{article.category}</Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        {/* Coach Tab */}
        <TabsContent value="coach" className="p-4 space-y-4">
          <Card className="border-primary/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                Coach IA Bariatrique
              </CardTitle>
              <CardDescription>
                Posez vos questions sur votre parcours (2 questions/jour max)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                <p className="text-xs text-amber-700 dark:text-amber-400">
                  ⚕️ Le coach IA ne remplace pas votre équipe médicale. Pour toute question médicale urgente, contactez votre chirurgien.
                </p>
              </div>

              <Textarea
                value={coachQuestion}
                onChange={(e) => setCoachQuestion(e.target.value)}
                placeholder="Ex: Je n'ai que du yaourt et des œufs, que manger en phase 2 ?"
                rows={3}
              />

              <Button 
                onClick={askCoach} 
                disabled={coachLoading || !coachQuestion.trim()}
                className="w-full"
              >
                {coachLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    Réflexion...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Envoyer ma question
                  </>
                )}
              </Button>

              {coachResponse && (
                <Card className="bg-muted/50">
                  <CardContent className="p-4">
                    <p className="text-sm whitespace-pre-wrap">{coachResponse}</p>
                  </CardContent>
                </Card>
              )}

              {/* Example Questions */}
              <div>
                <p className="text-sm font-medium mb-2">Exemples de questions :</p>
                <div className="space-y-2">
                  {[
                    "Que manger si j'ai des nausées ?",
                    "Pourquoi je stagne en poids ?",
                    "Comment augmenter mes protéines ?",
                    "J'ai envie de craquer, que faire ?"
                  ].map((q, idx) => (
                    <Button
                      key={idx}
                      variant="outline"
                      size="sm"
                      className="w-full justify-start text-left h-auto py-2"
                      onClick={() => setCoachQuestion(q)}
                    >
                      {q}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Article Modal */}
      <Dialog open={showArticleModal} onOpenChange={setShowArticleModal}>
        <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
          {selectedArticle && (
            <>
              <DialogHeader>
                <DialogTitle className="pr-4">{selectedArticle.title}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                {selectedArticle.image && (
                  <img 
                    src={selectedArticle.image} 
                    alt={selectedArticle.title}
                    className="w-full h-48 rounded-lg object-cover"
                  />
                )}
                
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Badge variant="secondary">{selectedArticle.category}</Badge>
                  <span>📖 {selectedArticle.source}</span>
                  <span>•</span>
                  <span>⏱️ {selectedArticle.read_time}</span>
                </div>
                
                <div className="prose prose-sm dark:prose-invert text-sm">
                  <p className="whitespace-pre-wrap">{selectedArticle.content || selectedArticle.summary}</p>
                </div>
                
                <div className="flex gap-2 pt-2">
                  <Button 
                    variant="outline" 
                    className="flex-1"
                    onClick={() => setShowArticleModal(false)}
                  >
                    Fermer
                  </Button>
                  <Button 
                    className="flex-1"
                    onClick={() => {
                      shareBariatricArticle(selectedArticle);
                      setShowArticleModal(false);
                    }}
                  >
                    <Share2 className="w-4 h-4 mr-2" />
                    Partager
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
