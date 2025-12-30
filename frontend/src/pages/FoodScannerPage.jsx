import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Webcam from 'react-webcam';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { 
  Camera, 
  Upload, 
  X, 
  Loader2, 
  Check,
  Plus,
  ArrowLeft,
  Sparkles
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function FoodScannerPage() {
  const navigate = useNavigate();
  const webcamRef = useRef(null);
  const fileInputRef = useRef(null);
  const [mode, setMode] = useState('select'); // select, camera, preview, analyzing, result
  const [image, setImage] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      setImage(imageSrc);
      // Convert base64 to blob
      fetch(imageSrc)
        .then(res => res.blob())
        .then(blob => {
          const file = new File([blob], 'photo.jpg', { type: 'image/jpeg' });
          setImageFile(file);
          setMode('preview');
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
        setMode('preview');
      };
      reader.readAsDataURL(file);
    }
  };

  const analyzeFood = async () => {
    if (!imageFile) return;
    
    setMode('analyzing');
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', imageFile);
      
      const response = await axios.post(`${API}/food/analyze`, formData, {
        withCredentials: true,
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setResult(response.data);
      setMode('result');
    } catch (error) {
      console.error('Analysis error:', error);
      if (error.response?.status === 429) {
        const detail = error.response.data?.detail;
        toast.error(detail?.message || 'Limite quotidienne IA atteinte. Revenez demain !');
      } else {
        toast.error('Erreur lors de l\'analyse');
      }
      setMode('preview');
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

  const reset = () => {
    setImage(null);
    setImageFile(null);
    setResult(null);
    setMode('select');
  };

  const getNutriScoreColor = (score) => {
    const colors = {
      'A': 'nutri-a',
      'B': 'nutri-b',
      'C': 'nutri-c',
      'D': 'nutri-d',
      'E': 'nutri-e',
    };
    return colors[score] || 'bg-muted';
  };

  return (
    <div className="min-h-screen bg-background" data-testid="scanner-page">
      {/* Header */}
      <header className="sticky top-0 z-10 px-4 py-4 bg-background/80 backdrop-blur-lg border-b border-border">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => navigate('/dashboard')}
            data-testid="back-btn"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="font-heading text-xl font-bold">Scanner IA</h1>
            <p className="text-sm text-muted-foreground">Analysez vos aliments</p>
          </div>
        </div>
      </header>

      <main className="p-4 pb-24">
        {/* Mode: Select */}
        {mode === 'select' && (
          <div className="space-y-6 animate-fade-in">
            <div className="text-center py-8">
              <div className="w-20 h-20 mx-auto rounded-3xl gradient-premium flex items-center justify-center mb-4">
                <Sparkles className="w-10 h-10 text-white" />
              </div>
              <h2 className="font-heading text-2xl font-bold mb-2">
                Analysez vos repas
              </h2>
              <p className="text-muted-foreground max-w-sm mx-auto">
                Notre IA reconnaît vos aliments et calcule instantanément les valeurs nutritionnelles
              </p>
            </div>

            <div className="grid gap-4">
              <Card 
                className="cursor-pointer card-interactive border-2 border-dashed border-secondary/50 hover:border-secondary"
                onClick={() => setMode('camera')}
                data-testid="camera-option"
              >
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

              <Card 
                className="cursor-pointer card-interactive border-2 border-dashed border-primary/50 hover:border-primary"
                onClick={() => fileInputRef.current?.click()}
                data-testid="upload-option"
              >
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
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileUpload}
              />
            </div>
          </div>
        )}

        {/* Mode: Camera */}
        {mode === 'camera' && (
          <div className="space-y-4 animate-fade-in">
            <div className="relative rounded-2xl overflow-hidden bg-black aspect-square">
              <Webcam
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                className="w-full h-full object-cover"
                videoConstraints={{
                  facingMode: 'environment'
                }}
              />
              <div className="scanner-overlay">
                <div className="scanner-frame">
                  <div className="scanner-line" />
                </div>
              </div>
            </div>

            <div className="flex justify-center gap-4">
              <Button
                variant="outline"
                size="icon"
                className="w-14 h-14 rounded-full"
                onClick={reset}
              >
                <X className="w-6 h-6" />
              </Button>
              <Button
                size="icon"
                className="w-16 h-16 rounded-full shadow-glow-purple bg-secondary hover:bg-secondary/90"
                onClick={capture}
                data-testid="capture-btn"
              >
                <Camera className="w-8 h-8" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="w-14 h-14 rounded-full"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-6 h-6" />
              </Button>
            </div>
          </div>
        )}

        {/* Mode: Preview */}
        {mode === 'preview' && image && (
          <div className="space-y-4 animate-fade-in">
            <div className="relative rounded-2xl overflow-hidden">
              <img src={image} alt="Preview" className="w-full aspect-square object-cover" />
            </div>

            <div className="flex gap-4">
              <Button
                variant="outline"
                className="flex-1 rounded-full"
                onClick={reset}
              >
                <X className="w-4 h-4 mr-2" />
                Annuler
              </Button>
              <Button
                className="flex-1 rounded-full shadow-glow-purple bg-secondary hover:bg-secondary/90"
                onClick={analyzeFood}
                data-testid="analyze-btn"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Analyser
              </Button>
            </div>
          </div>
        )}

        {/* Mode: Analyzing */}
        {mode === 'analyzing' && (
          <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
            <div className="relative">
              <div className="w-24 h-24 rounded-full gradient-premium animate-pulse" />
              <Loader2 className="absolute inset-0 m-auto w-10 h-10 text-white animate-spin" />
            </div>
            <p className="mt-6 font-heading text-lg">Analyse en cours...</p>
            <p className="text-sm text-muted-foreground">Notre IA identifie vos aliments</p>
          </div>
        )}

        {/* Mode: Result */}
        {mode === 'result' && result && (
          <div className="space-y-4 animate-fade-in">
            <div className="relative rounded-2xl overflow-hidden">
              <img src={image} alt="Food" className="w-full aspect-video object-cover" />
              <div className="absolute top-4 right-4">
                <div className={`nutri-badge ${getNutriScoreColor(result.nutri_score)}`}>
                  {result.nutri_score}
                </div>
              </div>
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
                    <p className="text-xs text-muted-foreground">Protéines</p>
                  </div>
                  <div className="text-center p-3 rounded-xl bg-accent/10">
                    <p className="text-2xl font-bold text-accent">{result.carbs}g</p>
                    <p className="text-xs text-muted-foreground">Glucides</p>
                  </div>
                  <div className="text-center p-3 rounded-xl bg-chart-4/10">
                    <p className="text-2xl font-bold text-chart-4">{result.fat}g</p>
                    <p className="text-xs text-muted-foreground">Lipides</p>
                  </div>
                </div>

                {result.health_tips?.length > 0 && (
                  <div className="space-y-2 mb-4">
                    <h3 className="font-semibold text-sm">Conseils</h3>
                    {result.health_tips.map((tip, i) => (
                      <p key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                        <Check className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                        {tip}
                      </p>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <div className="flex gap-4">
              <Button
                variant="outline"
                className="flex-1 rounded-full"
                onClick={reset}
              >
                Nouvelle analyse
              </Button>
              <Button
                className="flex-1 rounded-full shadow-glow"
                onClick={addToLog}
                data-testid="add-to-log-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Ajouter au journal
              </Button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
