import { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Webcam from 'react-webcam';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { 
  Camera, 
  Upload, 
  X, 
  Loader2, 
  Check,
  Plus,
  ArrowLeft,
  Sparkles,
  History,
  Trash2,
  Calendar,
  Apple,
  Beef,
  Fish,
  Wheat,
  Milk,
  Cake,
  Coffee,
  Pizza,
  Soup,
  Egg,
  Salad,
  Grape,
  ChevronRight,
  Info,
  AlertTriangle,
  ScanBarcode,
  Search
} from 'lucide-react';
import { Input } from '@/components/ui/input';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CATEGORY_ICONS = {
  'Légumes': Salad,
  'Fruits': Grape,
  'Viandes': Beef,
  'Poissons': Fish,
  'Féculents': Wheat,
  'Produits laitiers': Milk,
  'Desserts': Cake,
  'Boissons': Coffee,
  'Fast-food': Pizza,
  'Soupes': Soup,
  'Œufs': Egg,
  'Plats préparés': Apple,
  'Autre': Apple
};

export default function FoodScannerPage() {
  const navigate = useNavigate();
  const webcamRef = useRef(null);
  const fileInputRef = useRef(null);
  const [activeTab, setActiveTab] = useState('scanner');
  const [scanMode, setScanMode] = useState('select'); // select, camera, barcode, preview, analyzing, result
  const [image, setImage] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Barcode state
  const [barcodeInput, setBarcodeInput] = useState('');
  const [barcodeLoading, setBarcodeLoading] = useState(false);
  
  // History state
  const [scanHistory, setScanHistory] = useState([]);
  const [historyByCategory, setHistoryByCategory] = useState({});
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [selectedScan, setSelectedScan] = useState(null);
  const [showScanModal, setShowScanModal] = useState(false);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [activeTab]);

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const response = await axios.get(`${API}/food/scan-history`, { withCredentials: true });
      setScanHistory(response.data.scans || []);
      setHistoryByCategory(response.data.by_category || {});
    } catch (error) {
      console.error('Error fetching history:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  // Barcode scan function
  const scanBarcode = async () => {
    if (!barcodeInput.trim()) {
      toast.error('Veuillez entrer un code-barres');
      return;
    }
    
    setBarcodeLoading(true);
    try {
      const response = await axios.get(`${API}/food/barcode/${barcodeInput.trim()}`, { withCredentials: true });
      setResult(response.data);
      setImage(response.data.image_url);
      setScanMode('result');
      toast.success('Produit trouvé !');
    } catch (error) {
      if (error.response?.status === 404) {
        toast.error('Produit non trouvé dans OpenFoodFacts');
      } else {
        toast.error('Erreur lors du scan');
      }
    } finally {
      setBarcodeLoading(false);
    }
  };

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      setImage(imageSrc);
      fetch(imageSrc)
        .then(res => res.blob())
        .then(blob => {
          const file = new File([blob], 'photo.jpg', { type: 'image/jpeg' });
          setImageFile(file);
          setScanMode('preview');
        });
    }
  }, [webcamRef]);

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = (event) => {
        setImage(event.target.result);
        setScanMode('preview');
      };
      reader.readAsDataURL(file);
    }
  };

  const analyzeFood = async () => {
    if (!imageFile) return;
    setScanMode('analyzing');
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', imageFile);
      
      const response = await axios.post(`${API}/food/analyze`, formData, {
        withCredentials: true,
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setResult(response.data);
      setScanMode('result');
    } catch (error) {
      console.error('Analysis error:', error);
      if (error.response?.status === 429) {
        const detail = error.response.data?.detail;
        toast.error(detail?.message || 'Limite quotidienne IA atteinte. Revenez demain !');
      } else {
        toast.error('Erreur lors de l\'analyse');
      }
      setScanMode('preview');
    } finally {
      setLoading(false);
    }
  };

  const addToLog = async () => {
    if (!result) return;
    try {
      await axios.post(`${API}/food/log`, {
        food_name: result.food_name,
        calories: result.calories,
        protein: result.protein,
        carbs: result.carbs,
        fat: result.fat,
        meal_type: 'snack'
      }, { withCredentials: true });
      
      toast.success('Aliment ajouté au journal !');
      navigate('/nutrition');
    } catch (error) {
      toast.error('Erreur lors de l\'ajout');
    }
  };

  const deleteScan = async (scanId) => {
    try {
      await axios.delete(`${API}/food/scan/${scanId}`, { withCredentials: true });
      toast.success('Scan supprimé');
      setShowScanModal(false);
      fetchHistory();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const reset = () => {
    setImage(null);
    setImageFile(null);
    setResult(null);
    setScanMode('select');
  };

  const getNutriScoreColor = (score) => {
    const colors = { 'A': 'nutri-a', 'B': 'nutri-b', 'C': 'nutri-c', 'D': 'nutri-d', 'E': 'nutri-e' };
    return colors[score] || 'bg-muted';
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const CategoryIcon = ({ category }) => {
    const Icon = CATEGORY_ICONS[category] || Apple;
    return <Icon className="w-5 h-5" />;
  };

  return (
    <div className="min-h-screen bg-background pb-safe" data-testid="scanner-page">
      {/* Header */}
      <header className="sticky top-0 z-10 px-4 pt-2 pb-3 bg-background/80 backdrop-blur-lg border-b border-border safe-area-top">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/dashboard')}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1">
            <h1 className="font-heading text-xl font-bold">Scanner IA</h1>
            <p className="text-sm text-muted-foreground">Analysez vos aliments</p>
          </div>
        </div>
      </header>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <div className="px-4 py-2 border-b border-border">
          <TabsList className="w-full grid grid-cols-2">
            <TabsTrigger value="scanner" className="flex items-center gap-2">
              <Camera className="w-4 h-4" />
              Scanner
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2">
              <History className="w-4 h-4" />
              Historique
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Scanner Tab */}
        <TabsContent value="scanner" className="p-4 pb-24">
          {scanMode === 'select' && (
            <div className="space-y-6 animate-fade-in">
              <div className="text-center py-6">
                <div className="w-20 h-20 mx-auto rounded-3xl gradient-premium flex items-center justify-center mb-4">
                  <Sparkles className="w-10 h-10 text-white" />
                </div>
                <h2 className="font-heading text-2xl font-bold mb-2">Analysez vos repas</h2>
                <p className="text-muted-foreground max-w-sm mx-auto">
                  Notre IA reconnaît vos aliments et calcule les valeurs nutritionnelles
                </p>
              </div>

              <div className="grid gap-4">
                <Card className="cursor-pointer card-interactive border-2 border-dashed border-secondary/50 hover:border-secondary" onClick={() => setScanMode('camera')}>
                  <CardContent className="p-6 flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-secondary/10 flex items-center justify-center">
                      <Camera className="w-7 h-7 text-secondary" />
                    </div>
                    <div>
                      <h3 className="font-heading font-semibold">Prendre une photo</h3>
                      <p className="text-sm text-muted-foreground">Utilisez l'appareil photo</p>
                    </div>
                  </CardContent>
                </Card>

                <Card className="cursor-pointer card-interactive border-2 border-dashed border-primary/50 hover:border-primary" onClick={() => fileInputRef.current?.click()}>
                  <CardContent className="p-6 flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center">
                      <Upload className="w-7 h-7 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-heading font-semibold">Importer une image</h3>
                      <p className="text-sm text-muted-foreground">Depuis votre galerie</p>
                    </div>
                  </CardContent>
                </Card>
                <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleFileUpload} />
              </div>
            </div>
          )}

          {scanMode === 'camera' && (
            <div className="space-y-4 animate-fade-in">
              <div className="relative rounded-2xl overflow-hidden bg-black aspect-square">
                <Webcam
                  ref={webcamRef}
                  screenshotFormat="image/jpeg"
                  className="w-full h-full object-cover"
                  videoConstraints={{ facingMode: 'environment' }}
                />
                <div className="scanner-overlay">
                  <div className="scanner-frame"><div className="scanner-line" /></div>
                </div>
              </div>
              <div className="flex justify-center gap-4">
                <Button variant="outline" size="icon" className="w-14 h-14 rounded-full" onClick={reset}>
                  <X className="w-6 h-6" />
                </Button>
                <Button size="icon" className="w-16 h-16 rounded-full shadow-glow-purple bg-secondary hover:bg-secondary/90" onClick={capture}>
                  <Camera className="w-8 h-8" />
                </Button>
                <Button variant="outline" size="icon" className="w-14 h-14 rounded-full" onClick={() => fileInputRef.current?.click()}>
                  <Upload className="w-6 h-6" />
                </Button>
              </div>
            </div>
          )}

          {scanMode === 'preview' && image && (
            <div className="space-y-4 animate-fade-in">
              <div className="relative rounded-2xl overflow-hidden">
                <img src={image} alt="Preview" className="w-full aspect-square object-cover" />
              </div>
              <div className="flex gap-4">
                <Button variant="outline" className="flex-1 rounded-full" onClick={reset}>
                  <X className="w-4 h-4 mr-2" />Annuler
                </Button>
                <Button className="flex-1 rounded-full shadow-glow-purple bg-secondary hover:bg-secondary/90" onClick={analyzeFood}>
                  <Sparkles className="w-4 h-4 mr-2" />Analyser
                </Button>
              </div>
            </div>
          )}

          {scanMode === 'analyzing' && (
            <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
              <div className="relative">
                <div className="w-24 h-24 rounded-full gradient-premium animate-pulse" />
                <Loader2 className="absolute inset-0 m-auto w-10 h-10 text-white animate-spin" />
              </div>
              <p className="mt-6 font-heading text-lg">Analyse en cours...</p>
              <p className="text-sm text-muted-foreground">Notre IA identifie vos aliments</p>
            </div>
          )}

          {scanMode === 'result' && result && (
            <div className="space-y-4 animate-fade-in">
              <div className="relative rounded-2xl overflow-hidden">
                <img src={image} alt="Food" className="w-full aspect-video object-cover" />
                <div className="absolute top-4 right-4">
                  <div className={`nutri-badge ${getNutriScoreColor(result.nutri_score)}`}>{result.nutri_score}</div>
                </div>
                {result.category && (
                  <Badge className="absolute bottom-4 left-4 bg-background/80 text-foreground">
                    <CategoryIcon category={result.category} />
                    <span className="ml-1">{result.category}</span>
                  </Badge>
                )}
              </div>

              <Card>
                <CardContent className="p-6">
                  <h2 className="font-heading text-2xl font-bold mb-2">{result.food_name}</h2>
                  <p className="text-sm text-muted-foreground mb-4">{result.serving_size}</p>

                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className="text-center p-3 rounded-xl bg-primary/10">
                      <p className="text-2xl font-bold text-primary">{result.calories}</p>
                      <p className="text-xs text-muted-foreground">kcal</p>
                    </div>
                    <div className="text-center p-3 rounded-xl bg-secondary/10">
                      <p className="text-2xl font-bold text-secondary">{result.protein}g</p>
                      <p className="text-xs text-muted-foreground">Prot.</p>
                    </div>
                    <div className="text-center p-3 rounded-xl bg-accent/10">
                      <p className="text-2xl font-bold text-accent">{result.carbs}g</p>
                      <p className="text-xs text-muted-foreground">Gluc.</p>
                    </div>
                    <div className="text-center p-3 rounded-xl bg-chart-4/10">
                      <p className="text-2xl font-bold text-chart-4">{result.fat}g</p>
                      <p className="text-xs text-muted-foreground">Lip.</p>
                    </div>
                  </div>

                  {result.health_tips?.length > 0 && (
                    <div className="space-y-2 mb-4">
                      <h3 className="font-semibold text-sm">💡 Conseils</h3>
                      {result.health_tips.map((tip, i) => (
                        <p key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                          <Check className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />{tip}
                        </p>
                      ))}
                    </div>
                  )}

                  {result.warnings?.length > 0 && (
                    <div className="space-y-2 mb-4 p-3 rounded-lg bg-destructive/10">
                      <h3 className="font-semibold text-sm text-destructive">⚠️ Attention</h3>
                      {result.warnings.map((warning, i) => (
                        <p key={i} className="text-sm text-destructive/80">{warning}</p>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <div className="flex gap-4">
                <Button variant="outline" className="flex-1 rounded-full" onClick={reset}>Nouvelle analyse</Button>
                <Button className="flex-1 rounded-full shadow-glow" onClick={addToLog}>
                  <Plus className="w-4 h-4 mr-2" />Ajouter
                </Button>
              </div>
            </div>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="p-4 pb-24">
          {loadingHistory ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : scanHistory.length === 0 ? (
            <div className="text-center py-16">
              <History className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
              <h3 className="font-heading font-semibold text-lg mb-2">Aucun scan</h3>
              <p className="text-muted-foreground text-sm">Vos scans apparaîtront ici</p>
              <Button className="mt-4" onClick={() => setActiveTab('scanner')}>
                <Camera className="w-4 h-4 mr-2" />Scanner un aliment
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Summary */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Total scans</span>
                    <span className="font-bold text-lg">{scanHistory.length}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Categories */}
              {Object.entries(historyByCategory).map(([category, scans]) => (
                <div key={category}>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <CategoryIcon category={category} />
                    </div>
                    <h3 className="font-heading font-semibold">{category}</h3>
                    <Badge variant="outline" className="ml-auto">{scans.length}</Badge>
                  </div>
                  
                  <div className="space-y-2">
                    {scans.map((scan) => (
                      <Card 
                        key={scan.scan_id} 
                        className="cursor-pointer hover:border-primary/50 transition-colors"
                        onClick={() => { setSelectedScan(scan); setShowScanModal(true); }}
                      >
                        <CardContent className="p-3">
                          <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold ${getNutriScoreColor(scan.nutri_score)}`}>
                              {scan.nutri_score || '?'}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="font-medium truncate">{scan.food_name}</p>
                              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                <span>{scan.calories} kcal</span>
                                <span>•</span>
                                <Calendar className="w-3 h-3" />
                                <span>{formatDate(scan.scanned_at)}</span>
                              </div>
                            </div>
                            <ChevronRight className="w-5 h-5 text-muted-foreground" />
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Scan Detail Modal */}
      <Dialog open={showScanModal} onOpenChange={setShowScanModal}>
        <DialogContent className="max-w-md max-h-[85vh] overflow-y-auto">
          {selectedScan && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {selectedScan.food_name}
                  <span className={`w-6 h-6 rounded flex items-center justify-center text-white text-xs font-bold ${getNutriScoreColor(selectedScan.nutri_score)}`}>
                    {selectedScan.nutri_score || '?'}
                  </span>
                </DialogTitle>
              </DialogHeader>
              
              <div className="space-y-4">
                {/* Date & Category */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="w-4 h-4 text-muted-foreground" />
                    <span>{formatDate(selectedScan.scanned_at)}</span>
                  </div>
                  <Badge variant="outline">
                    <CategoryIcon category={selectedScan.category} />
                    <span className="ml-1">{selectedScan.category}</span>
                  </Badge>
                </div>

                {/* Nutrition Grid */}
                <div className="grid grid-cols-4 gap-2 text-center">
                  <div className="p-3 rounded-lg bg-primary/10">
                    <p className="text-xl font-bold text-primary">{selectedScan.calories}</p>
                    <p className="text-xs text-muted-foreground">kcal</p>
                  </div>
                  <div className="p-3 rounded-lg bg-secondary/10">
                    <p className="text-xl font-bold text-secondary">{selectedScan.protein}g</p>
                    <p className="text-xs text-muted-foreground">Prot.</p>
                  </div>
                  <div className="p-3 rounded-lg bg-accent/10">
                    <p className="text-xl font-bold text-accent">{selectedScan.carbs}g</p>
                    <p className="text-xs text-muted-foreground">Gluc.</p>
                  </div>
                  <div className="p-3 rounded-lg bg-chart-4/10">
                    <p className="text-xl font-bold text-chart-4">{selectedScan.fat}g</p>
                    <p className="text-xs text-muted-foreground">Lip.</p>
                  </div>
                </div>

                {/* Extended Nutrition */}
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2 rounded-lg bg-muted/50">
                    <p className="font-semibold">{selectedScan.fiber || 0}g</p>
                    <p className="text-xs text-muted-foreground">Fibres</p>
                  </div>
                  <div className="p-2 rounded-lg bg-muted/50">
                    <p className="font-semibold">{selectedScan.sugar || 0}g</p>
                    <p className="text-xs text-muted-foreground">Sucres</p>
                  </div>
                  <div className="p-2 rounded-lg bg-muted/50">
                    <p className="font-semibold">{selectedScan.sodium || 0}mg</p>
                    <p className="text-xs text-muted-foreground">Sel</p>
                  </div>
                </div>

                {/* Serving Size */}
                <div className="flex items-center gap-2 text-sm">
                  <Info className="w-4 h-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Portion : {selectedScan.serving_size}</span>
                </div>

                {/* Health Tips */}
                {selectedScan.health_tips?.length > 0 && (
                  <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
                    <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-primary" />
                      Recommandations
                    </h4>
                    <ul className="space-y-1">
                      {selectedScan.health_tips.map((tip, i) => (
                        <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                          <Check className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />{tip}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Warnings */}
                {selectedScan.warnings?.length > 0 && (
                  <div className="p-3 rounded-lg bg-destructive/5 border border-destructive/20">
                    <h4 className="font-semibold text-sm mb-2 flex items-center gap-2 text-destructive">
                      <AlertTriangle className="w-4 h-4" />
                      Attention
                    </h4>
                    <ul className="space-y-1">
                      {selectedScan.warnings.map((warning, i) => (
                        <li key={i} className="text-sm text-destructive/80">{warning}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Button
                    variant="destructive"
                    className="flex-1"
                    onClick={() => deleteScan(selectedScan.scan_id)}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />Supprimer
                  </Button>
                  <Button
                    className="flex-1"
                    onClick={async () => {
                      try {
                        await axios.post(`${API}/food/log`, {
                          food_name: selectedScan.food_name,
                          calories: selectedScan.calories,
                          protein: selectedScan.protein,
                          carbs: selectedScan.carbs,
                          fat: selectedScan.fat,
                          meal_type: 'snack'
                        }, { withCredentials: true });
                        toast.success('Ajouté au journal !');
                        setShowScanModal(false);
                      } catch (error) {
                        toast.error('Erreur');
                      }
                    }}
                  >
                    <Plus className="w-4 h-4 mr-2" />Ajouter
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
