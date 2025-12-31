import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import AIWarningDialog from '@/components/AIWarningDialog';
import { 
  Dumbbell, 
  ArrowLeft,
  Sparkles,
  Loader2,
  Clock,
  Flame,
  Play,
  Check,
  Plus,
  Video,
  Trophy,
  Target,
  Calendar,
  Award,
  ChevronRight,
  Bot,
  Zap,
  Home,
  Building2,
  Heart,
  Timer,
  Pause,
  X,
  Share2
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Video categories - plus de catégories
const VIDEO_CATEGORIES = [
  { id: 'all', label: 'Toutes', icon: Video },
  { id: 'home', label: 'Maison', icon: Home },
  { id: 'gym', label: 'Salle', icon: Building2 },
  { id: 'cardio', label: 'Cardio', icon: Heart },
  { id: 'musculation', label: 'Musculation', icon: Dumbbell },
  { id: 'hiit', label: 'HIIT', icon: Flame },
  { id: 'gainage', label: 'Gainage', icon: Target },
  { id: 'yoga', label: 'Yoga', icon: Heart },
  { id: 'fitness', label: 'Fitness', icon: Zap },
  { id: 'stretching', label: 'Étirements', icon: Timer },
  { id: 'abdos', label: 'Abdos', icon: Target },
  { id: 'jambes', label: 'Jambes', icon: Dumbbell },
  { id: 'bras', label: 'Bras', icon: Dumbbell },
  { id: 'dos', label: 'Dos', icon: Dumbbell },
  { id: 'pectoraux', label: 'Pectoraux', icon: Dumbbell },
  { id: 'fessiers', label: 'Fessiers', icon: Zap },
  { id: 'debutant', label: 'Débutant', icon: Target },
  { id: 'expert', label: 'Expert', icon: Trophy },
];

// Difficulty levels
const DIFFICULTY_LABELS = {
  beginner: { label: 'Débutant', color: 'bg-green-500' },
  intermediate: { label: 'Intermédiaire', color: 'bg-yellow-500' },
  expert: { label: 'Expert', color: 'bg-red-500' },
};

// Coach IA program durations
const PROGRAM_DURATIONS = [
  { value: 'week', label: '1 semaine', desc: 'Découverte' },
  { value: '15days', label: '15 jours', desc: 'Court terme' },
  { value: 'month', label: '1 mois', desc: 'Standard' },
  { value: '3months', label: '3 mois', desc: 'Résultats visibles' },
  { value: '6months', label: '6 mois', desc: 'Transformation' },
  { value: 'year', label: '1 an', desc: 'Long terme' },
];

const TIME_OF_DAY = [
  { value: 'morning', label: '🌅 Matin', desc: '6h-10h' },
  { value: 'noon', label: '☀️ Midi', desc: '11h-14h' },
  { value: 'afternoon', label: '🌤️ Après-midi', desc: '15h-18h' },
  { value: 'evening', label: '🌙 Soirée', desc: '19h-22h' },
];

const DAILY_DURATION = [
  { value: '15', label: '15 min', desc: 'Express' },
  { value: '30', label: '30 min', desc: 'Standard' },
  { value: '45', label: '45 min', desc: 'Complet' },
  { value: '60', label: '1h', desc: 'Intensif' },
  { value: '90', label: '1h30', desc: 'Pro' },
];

const BODY_PARTS = [
  { id: 'full_body', label: 'Corps entier', emoji: '💪' },
  { id: 'upper_body', label: 'Haut du corps', emoji: '🏋️' },
  { id: 'lower_body', label: 'Bas du corps', emoji: '🦵' },
  { id: 'abs', label: 'Abdominaux', emoji: '🧘' },
  { id: 'arms', label: 'Bras', emoji: '💪' },
  { id: 'back', label: 'Dos', emoji: '🔙' },
  { id: 'chest', label: 'Pectoraux', emoji: '🫁' },
  { id: 'legs', label: 'Jambes', emoji: '🦿' },
  { id: 'glutes', label: 'Fessiers', emoji: '🍑' },
  { id: 'cardio', label: 'Cardio', emoji: '❤️' },
];

const FITNESS_LEVELS = [
  { value: 'beginner', label: 'Débutant', emoji: '🌱', desc: 'Je commence le sport' },
  { value: 'intermediate', label: 'Intermédiaire', emoji: '💪', desc: 'Je pratique régulièrement' },
  { value: 'advanced', label: 'Avancé', emoji: '🔥', desc: 'Je suis très actif' },
  { value: 'expert', label: 'Expert', emoji: '🏆', desc: 'Sportif confirmé' },
];

const TRAINING_FREQUENCY = [
  { value: '2', label: '2x/semaine', desc: 'Léger' },
  { value: '3', label: '3x/semaine', desc: 'Modéré' },
  { value: '4', label: '4x/semaine', desc: 'Régulier' },
  { value: '5', label: '5x/semaine', desc: 'Intense' },
  { value: '6', label: '6x/semaine', desc: 'Pro' },
];

const TRAINING_GOALS = [
  { id: 'weight_loss', label: 'Perdre du poids', emoji: '⬇️' },
  { id: 'muscle_gain', label: 'Gagner en muscle', emoji: '💪' },
  { id: 'endurance', label: 'Améliorer l\'endurance', emoji: '🏃' },
  { id: 'flexibility', label: 'Gagner en souplesse', emoji: '🧘' },
  { id: 'strength', label: 'Devenir plus fort', emoji: '🏋️' },
  { id: 'toning', label: 'Me tonifier', emoji: '✨' },
  { id: 'health', label: 'Être en meilleure santé', emoji: '❤️' },
  { id: 'stress', label: 'Réduire le stress', emoji: '🧠' },
];

// Congratulation messages for video completion
const CONGRATULATION_MESSAGES = [
  "🎉 Bravo champion ! Tu viens de terminer cette séance avec brio !",
  "💪 Incroyable ! Chaque entraînement te rapproche de ton objectif !",
  "🔥 Tu es en feu ! Continue comme ça, les résultats arrivent !",
  "⭐ Excellent travail ! Tu mérites amplement ce badge !",
  "🚀 Tu as tout donné ! La persévérance est la clé du succès !",
  "🏆 Victoire ! Un entraînement de plus vers la meilleure version de toi !",
  "💯 Parfait ! Ton corps te remercie pour cet effort !",
  "🌟 Superbe performance ! Tu deviens plus fort chaque jour !",
  "🎯 Objectif atteint ! Rien ne peut t'arrêter maintenant !",
  "✨ Magnifique ! Tu inspires ceux qui t'entourent !",
];

export default function WorkoutsPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('videos');
  const [loading, setLoading] = useState(true);
  
  // Videos state
  const [videos, setVideos] = useState([]);
  const [videoCategory, setVideoCategory] = useState('all');
  const [loadingVideos, setLoadingVideos] = useState(false);
  const [watchedVideos, setWatchedVideos] = useState([]);
  const [playingVideo, setPlayingVideo] = useState(null);
  const [showCongratsDialog, setShowCongratsDialog] = useState(false);
  const [congratsMessage, setCongratsMessage] = useState('');
  const [earnedBadge, setEarnedBadge] = useState(null);
  const videoRef = useRef(null);
  
  // Coach IA state
  const [showCoachDialog, setShowCoachDialog] = useState(false);
  const [coachStep, setCoachStep] = useState(1);
  const [coachLoading, setCoachLoading] = useState(false);
  const [generatedProgram, setGeneratedProgram] = useState(null);
  const [coachConfig, setCoachConfig] = useState({
    duration: 'month',
    frequency: '3',
    fitnessLevel: 'beginner',
    timeOfDay: 'morning',
    dailyDuration: '30',
    bodyParts: [],
    trainingGoals: [],
    equipment: 'none',
    goals: '',
    injuries: '',
    age: '',
    weight: '',
  });
  
  // AI Warning state
  const [showAIWarning, setShowAIWarning] = useState(false);
  
  // Programs & Logs state
  const [programs, setPrograms] = useState([]);
  const [workoutLogs, setWorkoutLogs] = useState([]);
  const [logDialogOpen, setLogDialogOpen] = useState(false);
  const [selectedProgram, setSelectedProgram] = useState(null);
  const [newLog, setNewLog] = useState({
    workout_name: '',
    duration_minutes: '',
    calories_burned: ''
  });

  useEffect(() => {
    fetchData();
    fetchVideos();
    loadWatchedVideos();
  }, []);

  useEffect(() => {
    fetchVideos();
  }, [videoCategory]);

  const fetchData = async () => {
    try {
      const [programsRes, logsRes] = await Promise.allSettled([
        axios.get(`${API}/workouts/programs`, { withCredentials: true }),
        axios.get(`${API}/workouts/logs`, { withCredentials: true })
      ]);
      if (programsRes.status === 'fulfilled') setPrograms(programsRes.value.data || []);
      if (logsRes.status === 'fulfilled') setWorkoutLogs(logsRes.value.data || []);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchVideos = async () => {
    setLoadingVideos(true);
    try {
      const response = await axios.get(`${API}/workouts/videos`, {
        params: { category: videoCategory !== 'all' ? videoCategory : undefined },
        withCredentials: true
      });
      setVideos(response.data || []);
    } catch (error) {
      console.error('Error fetching videos:', error);
      // Use mock data if API fails
      setVideos(getMockVideos());
    } finally {
      setLoadingVideos(false);
    }
  };

  const loadWatchedVideos = () => {
    const saved = localStorage.getItem('watchedWorkoutVideos');
    if (saved) {
      setWatchedVideos(JSON.parse(saved));
    }
  };

  const getMockVideos = () => {
    return [
      // Cardio
      {
        id: 'v1',
        title: 'HIIT Brûle-Graisse 20 min - Sans équipement',
        thumbnail: 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400',
        duration: '20:00',
        category: 'cardio',
        level: 'intermediate',
        views: 125000,
        publishedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'v2',
        title: 'Cardio Dance Party - 30 min',
        thumbnail: 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400',
        duration: '30:00',
        category: 'cardio',
        level: 'beginner',
        views: 234000,
        publishedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Gainage
      {
        id: 'v3',
        title: 'Gainage Complet - 15 min pour des abdos en béton',
        thumbnail: 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400',
        duration: '15:00',
        category: 'gainage',
        level: 'beginner',
        views: 89000,
        publishedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'v4',
        title: 'Challenge Planche - 10 variations',
        thumbnail: 'https://images.unsplash.com/photo-1566241142559-40e1dab266c6?w=400',
        duration: '12:00',
        category: 'gainage',
        level: 'intermediate',
        views: 67000,
        publishedAt: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Home
      {
        id: 'v5',
        title: 'Musculation à la maison - Full Body',
        thumbnail: 'https://images.unsplash.com/photo-1581009146145-b5ef050c149a?w=400',
        duration: '35:00',
        category: 'home',
        level: 'intermediate',
        views: 156000,
        publishedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'v6',
        title: 'Séance express - 15 min sans matériel',
        thumbnail: 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=400',
        duration: '15:00',
        category: 'home',
        level: 'beginner',
        views: 198000,
        publishedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Gym
      {
        id: 'v7',
        title: 'Entraînement Jambes & Fessiers - Salle',
        thumbnail: 'https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=400',
        duration: '45:00',
        category: 'gym',
        level: 'expert',
        views: 78000,
        publishedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'v8',
        title: 'Push Day - Pectoraux & Épaules',
        thumbnail: 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=400',
        duration: '50:00',
        category: 'gym',
        level: 'expert',
        views: 145000,
        publishedAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // HIIT
      {
        id: 'v9',
        title: 'HIIT Extreme - 25 min Tabata',
        thumbnail: 'https://images.unsplash.com/photo-1549576490-b0b4831ef60a?w=400',
        duration: '25:00',
        category: 'hiit',
        level: 'expert',
        views: 112000,
        publishedAt: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'v10',
        title: 'HIIT Débutant - 15 min',
        thumbnail: 'https://images.unsplash.com/photo-1601422407692-ec4eeec1d9b3?w=400',
        duration: '15:00',
        category: 'hiit',
        level: 'beginner',
        views: 187000,
        publishedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Musculation
      {
        id: 'v11',
        title: 'Musculation Haut du Corps - Prise de masse',
        thumbnail: 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=400',
        duration: '40:00',
        category: 'musculation',
        level: 'expert',
        views: 145000,
        publishedAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'v12',
        title: 'Biceps & Triceps - Bras sculptés',
        thumbnail: 'https://images.unsplash.com/photo-1581009146145-b5ef050c149a?w=400',
        duration: '30:00',
        category: 'bras',
        level: 'intermediate',
        views: 98000,
        publishedAt: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Yoga
      {
        id: 'v13',
        title: 'Yoga Flow Matinal - 20 min',
        thumbnail: 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400',
        duration: '20:00',
        category: 'yoga',
        level: 'beginner',
        views: 256000,
        publishedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'v14',
        title: 'Yoga Vinyasa - Séance complète',
        thumbnail: 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=400',
        duration: '45:00',
        category: 'yoga',
        level: 'intermediate',
        views: 134000,
        publishedAt: new Date(Date.now() - 9 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Fitness
      {
        id: 'v15',
        title: 'Fitness Dance - Cardio Fun 30 min',
        thumbnail: 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400',
        duration: '30:00',
        category: 'fitness',
        level: 'beginner',
        views: 234000,
        publishedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'v16',
        title: 'Fitness Total Body - 40 min',
        thumbnail: 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400',
        duration: '40:00',
        category: 'fitness',
        level: 'intermediate',
        views: 178000,
        publishedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Abdos
      {
        id: 'v17',
        title: 'Abdos en 10 min - Routine quotidienne',
        thumbnail: 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
        duration: '10:00',
        category: 'abdos',
        level: 'beginner',
        views: 312000,
        publishedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'v18',
        title: 'Abdos Sculptés - Challenge 21 jours',
        thumbnail: 'https://images.unsplash.com/photo-1566241142559-40e1dab266c6?w=400',
        duration: '20:00',
        category: 'abdos',
        level: 'intermediate',
        views: 245000,
        publishedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Jambes
      {
        id: 'v19',
        title: 'Jambes & Fessiers - 25 min',
        thumbnail: 'https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=400',
        duration: '25:00',
        category: 'jambes',
        level: 'intermediate',
        views: 167000,
        publishedAt: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'v20',
        title: 'Squat Challenge - 100 répétitions',
        thumbnail: 'https://images.unsplash.com/photo-1434682881908-b43d0467b798?w=400',
        duration: '15:00',
        category: 'jambes',
        level: 'expert',
        views: 89000,
        publishedAt: new Date(Date.now() - 11 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Stretching
      {
        id: 'v21',
        title: 'Étirements Complets - Récupération',
        thumbnail: 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=400',
        duration: '20:00',
        category: 'stretching',
        level: 'beginner',
        views: 198000,
        publishedAt: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'v22',
        title: 'Stretching du Soir - Détente 15 min',
        thumbnail: 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400',
        duration: '15:00',
        category: 'stretching',
        level: 'beginner',
        views: 156000,
        publishedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Dos
      {
        id: 'v23',
        title: 'Renforcement du Dos - 20 min',
        thumbnail: 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=400',
        duration: '20:00',
        category: 'dos',
        level: 'intermediate',
        views: 87000,
        publishedAt: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Pectoraux
      {
        id: 'v24',
        title: 'Pectoraux Sans Matériel - Pompes variées',
        thumbnail: 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
        duration: '18:00',
        category: 'pectoraux',
        level: 'intermediate',
        views: 134000,
        publishedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Fessiers
      {
        id: 'v25',
        title: 'Fessiers Bombés - 20 min',
        thumbnail: 'https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=400',
        duration: '20:00',
        category: 'fessiers',
        level: 'intermediate',
        views: 289000,
        publishedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Débutant
      {
        id: 'v26',
        title: 'Sport pour Débutants - Premiers pas',
        thumbnail: 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=400',
        duration: '15:00',
        category: 'debutant',
        level: 'beginner',
        views: 345000,
        publishedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      },
      // Expert
      {
        id: 'v27',
        title: 'Challenge Extrême - 45 min intensif',
        thumbnail: 'https://images.unsplash.com/photo-1549576490-b0b4831ef60a?w=400',
        duration: '45:00',
        category: 'expert',
        level: 'expert',
        views: 67000,
        publishedAt: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000).toISOString(),
      },
    ];
  };

  const handleVideoComplete = async (video) => {
    // Add to watched list
    const newWatched = [...watchedVideos, video.id];
    setWatchedVideos(newWatched);
    localStorage.setItem('watchedWorkoutVideos', JSON.stringify(newWatched));
    
    // Generate random congratulation message
    const message = CONGRATULATION_MESSAGES[Math.floor(Math.random() * CONGRATULATION_MESSAGES.length)];
    setCongratsMessage(message);
    
    // Award badge
    try {
      const response = await axios.post(`${API}/badges/award`, {
        type: 'video_complete',
        video_id: video.id,
        video_title: video.title
      }, { withCredentials: true });
      
      if (response.data.badge) {
        setEarnedBadge(response.data.badge);
      }
    } catch (error) {
      console.error('Error awarding badge:', error);
    }
    
    // Log workout
    try {
      const durationMinutes = parseInt(video.duration.split(':')[0]);
      await axios.post(`${API}/workouts/log`, {
        workout_name: video.title,
        duration_minutes: durationMinutes,
        calories_burned: Math.round(durationMinutes * 8),
        exercises: [],
        source: 'video'
      }, { withCredentials: true });
    } catch (error) {
      console.error('Error logging workout:', error);
    }
    
    setPlayingVideo(null);
    setShowCongratsDialog(true);
  };

  const generateCoachProgram = async () => {
    setCoachLoading(true);
    try {
      const response = await axios.post(`${API}/workouts/coach/generate`, coachConfig, { withCredentials: true });
      setGeneratedProgram(response.data);
      setCoachStep(7);
      toast.success('Programme généré avec succès !');
    } catch (error) {
      console.error('Error generating program:', error);
      if (error.response?.status === 429) {
        const detail = error.response.data?.detail;
        toast.error(detail?.message || 'Limite quotidienne IA atteinte. Revenez demain !');
      } else {
        toast.error('Erreur lors de la génération du programme');
      }
    } finally {
      setCoachLoading(false);
    }
  };

  // Request coach program with AI warning
  const requestCoachProgram = () => {
    setShowAIWarning(true);
  };

  const handleAIWarningConfirm = () => {
    generateCoachProgram();
  };

  const addProgramToAgenda = async () => {
    if (!generatedProgram) return;
    
    try {
      await axios.post(`${API}/workouts/coach/add-to-agenda`, {
        program: generatedProgram,
        config: coachConfig
      }, { withCredentials: true });
      toast.success('Programme ajouté à votre agenda avec rappels !');
      setShowCoachDialog(false);
      setCoachStep(1);
      setGeneratedProgram(null);
    } catch (error) {
      console.error('Error adding to agenda:', error);
      toast.error('Erreur lors de l\'ajout à l\'agenda');
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

  const filteredVideos = videos.filter(v => 
    videoCategory === 'all' || v.category === videoCategory
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-safe" data-testid="workouts-page">
      {/* Header */}
      <header className="sticky top-0 z-10 px-4 py-4 bg-background/80 backdrop-blur-lg border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/dashboard')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h1 className="font-heading text-xl font-bold">Entraînements</h1>
          </div>
          <Button variant="outline" size="sm" onClick={() => setShowCoachDialog(true)}>
            <Bot className="w-4 h-4 mr-2" />
            Coach IA
          </Button>
        </div>
      </header>

      <main className="p-4 space-y-4 max-w-lg mx-auto">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="videos" className="flex items-center gap-1">
              <Video className="w-4 h-4" />
              Vidéos
            </TabsTrigger>
            <TabsTrigger value="programs" className="flex items-center gap-1">
              <Target className="w-4 h-4" />
              Programmes
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              Historique
            </TabsTrigger>
          </TabsList>

          {/* Videos Tab */}
          <TabsContent value="videos" className="space-y-4 mt-4">
            {/* Category Filter - Scrollable horizontal */}
            <div className="relative -mx-4">
              <div 
                className="flex gap-2 px-4 pb-3 overflow-x-auto horizontal-scroll"
                style={{ WebkitOverflowScrolling: 'touch', scrollSnapType: 'x proximity' }}
              >
                {VIDEO_CATEGORIES.map((cat) => (
                  <Button
                    key={cat.id}
                    variant={videoCategory === cat.id ? 'default' : 'outline'}
                    size="sm"
                    className="flex-shrink-0 whitespace-nowrap scroll-snap-align-start"
                    onClick={() => setVideoCategory(cat.id)}
                  >
                    <cat.icon className="w-4 h-4 mr-1" />
                    {cat.label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Videos Grid */}
            {loadingVideos ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : (
              <div className="space-y-3">
                {filteredVideos.map((video) => (
                  <Card 
                    key={video.id}
                    className={`cursor-pointer transition-all hover:border-primary/50 ${
                      watchedVideos.includes(video.id) ? 'border-green-500/50 bg-green-500/5' : ''
                    }`}
                    onClick={() => setPlayingVideo(video)}
                  >
                    <CardContent className="p-3">
                      <div className="flex gap-3">
                        <div className="relative flex-shrink-0">
                          <img 
                            src={video.thumbnail} 
                            alt={video.title}
                            className="w-32 h-20 object-cover rounded-lg"
                          />
                          <div className="absolute bottom-1 right-1 px-1.5 py-0.5 bg-black/80 rounded text-xs text-white">
                            {video.duration}
                          </div>
                          {watchedVideos.includes(video.id) && (
                            <div className="absolute top-1 right-1 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
                              <Check className="w-3 h-3 text-white" />
                            </div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-sm line-clamp-2">{video.title}</h3>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge className={`text-xs ${DIFFICULTY_LABELS[video.level]?.color}`}>
                              {DIFFICULTY_LABELS[video.level]?.label}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {(video.views / 1000).toFixed(0)}k vues
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            Publié il y a {Math.floor((Date.now() - new Date(video.publishedAt).getTime()) / (24 * 60 * 60 * 1000))} jours
                          </p>
                        </div>
                        <Button variant="ghost" size="icon" className="self-center">
                          <Play className="w-5 h-5" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {filteredVideos.length === 0 && (
                  <div className="text-center py-12">
                    <Video className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">Aucune vidéo dans cette catégorie</p>
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          {/* Programs Tab */}
          <TabsContent value="programs" className="space-y-4 mt-4">
            <Card className="bg-gradient-to-r from-primary/10 to-secondary/10 border-primary/30">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                    <Bot className="w-6 h-6 text-primary" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold">Coach IA Personnel</h3>
                    <p className="text-sm text-muted-foreground">
                      Créez un programme sur mesure adapté à vos objectifs
                    </p>
                  </div>
                  <Button onClick={() => setShowCoachDialog(true)}>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Créer
                  </Button>
                </div>
              </CardContent>
            </Card>

            {programs.length > 0 ? (
              <div className="space-y-3">
                {programs.map((program, index) => (
                  <Card 
                    key={index} 
                    className="cursor-pointer hover:border-primary/50 transition-colors"
                    onClick={() => setSelectedProgram(program)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold">{program.workout_plan?.name || program.workout_plan?.program_name || 'Programme personnalisé'}</h3>
                          <p className="text-sm text-muted-foreground">
                            {program.workout_plan?.weeks?.length || 0} semaines • {program.workout_plan?.weeks?.reduce((acc, w) => acc + (w.days?.length || 0), 0) || 0} séances
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Créé le {new Date(program.created_at).toLocaleDateString('fr-FR')}
                          </p>
                        </div>
                        <ChevronRight className="w-5 h-5 text-muted-foreground" />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Dumbbell className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Aucun programme créé</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Utilisez le Coach IA pour créer votre premier programme
                </p>
              </div>
            )}
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" className="space-y-4 mt-4">
            <Dialog open={logDialogOpen} onOpenChange={setLogDialogOpen}>
              <DialogTrigger asChild>
                <Button className="w-full">
                  <Plus className="w-4 h-4 mr-2" />
                  Enregistrer un entraînement
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

            {workoutLogs.length > 0 ? (
              <div className="space-y-2">
                {workoutLogs.map((log, index) => (
                  <Card key={index}>
                    <CardContent className="p-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{log.workout_name}</p>
                          <div className="flex gap-3 text-xs text-muted-foreground mt-1">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {log.duration_minutes} min
                            </span>
                            <span className="flex items-center gap-1">
                              <Flame className="w-3 h-3" />
                              {log.calories_burned} kcal
                            </span>
                          </div>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(log.logged_at).toLocaleDateString('fr-FR')}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Clock className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Aucun entraînement enregistré</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>

      {/* Video Player Dialog */}
      <Dialog open={!!playingVideo} onOpenChange={() => setPlayingVideo(null)}>
        <DialogContent className="max-w-2xl p-0">
          {playingVideo && (
            <>
              <div className="relative aspect-video bg-black">
                <img 
                  src={playingVideo.thumbnail} 
                  alt={playingVideo.title}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                  <div className="text-center text-white">
                    <Play className="w-16 h-16 mx-auto mb-4" />
                    <p className="text-sm">Lecture intégrée disponible prochainement</p>
                    <p className="text-xs mt-2 opacity-70">Cliquez sur "J'ai terminé" une fois la vidéo regardée</p>
                  </div>
                </div>
              </div>
              <div className="p-4">
                <h3 className="font-semibold">{playingVideo.title}</h3>
                <div className="flex items-center gap-2 mt-2">
                  <Badge className={DIFFICULTY_LABELS[playingVideo.level]?.color}>
                    {DIFFICULTY_LABELS[playingVideo.level]?.label}
                  </Badge>
                  <span className="text-sm text-muted-foreground">{playingVideo.duration}</span>
                </div>
                <div className="flex gap-2 mt-4">
                  <Button 
                    className="flex-1" 
                    onClick={() => handleVideoComplete(playingVideo)}
                  >
                    <Check className="w-4 h-4 mr-2" />
                    J'ai terminé !
                  </Button>
                  <Button variant="outline" onClick={() => setPlayingVideo(null)}>
                    Fermer
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Congratulations Dialog */}
      <Dialog open={showCongratsDialog} onOpenChange={setShowCongratsDialog}>
        <DialogContent className="text-center">
          <div className="py-6">
            <div className="w-20 h-20 rounded-full bg-gradient-to-r from-primary to-secondary mx-auto flex items-center justify-center mb-4">
              <Trophy className="w-10 h-10 text-white" />
            </div>
            <DialogTitle className="text-2xl mb-4">Félicitations !</DialogTitle>
            <p className="text-muted-foreground mb-4">{congratsMessage}</p>
            {earnedBadge && (
              <div className="p-4 bg-primary/10 rounded-lg mb-4">
                <p className="text-sm text-muted-foreground mb-2">Badge gagné :</p>
                <div className="flex items-center justify-center gap-2">
                  <span className="text-3xl">{earnedBadge.icon}</span>
                  <span className="font-semibold">{earnedBadge.name}</span>
                </div>
              </div>
            )}
            <Button onClick={() => setShowCongratsDialog(false)} className="w-full">
              Continuer
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Coach IA Dialog - Onboarding amélioré */}
      <Dialog open={showCoachDialog} onOpenChange={(open) => {
        setShowCoachDialog(open);
        if (!open) {
          setCoachStep(1);
          setGeneratedProgram(null);
        }
      }}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-primary" />
              Coach IA - Programme personnalisé
            </DialogTitle>
            <DialogDescription>
              {coachStep < 7 ? `Étape ${coachStep}/6 - Personnalisation avancée` : 'Votre programme est prêt !'}
            </DialogDescription>
          </DialogHeader>

          {/* Progress bar */}
          {coachStep < 7 && (
            <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
              <div 
                className="h-full bg-primary transition-all duration-300" 
                style={{ width: `${(coachStep / 6) * 100}%` }}
              />
            </div>
          )}

          {/* Step 1: Fitness Level & Goals */}
          {coachStep === 1 && (
            <div className="space-y-4 py-4">
              <div>
                <h3 className="font-semibold mb-3">🎯 Quel est votre niveau actuel ?</h3>
                <div className="grid grid-cols-2 gap-2">
                  {FITNESS_LEVELS.map((level) => (
                    <Button
                      key={level.value}
                      variant={coachConfig.fitnessLevel === level.value ? 'default' : 'outline'}
                      className="h-auto py-3 flex-col"
                      onClick={() => setCoachConfig({ ...coachConfig, fitnessLevel: level.value })}
                    >
                      <span className="text-xl mb-1">{level.emoji}</span>
                      <span className="font-medium">{level.label}</span>
                      <span className="text-xs text-muted-foreground">{level.desc}</span>
                    </Button>
                  ))}
                </div>
              </div>
              <Button className="w-full mt-4" onClick={() => setCoachStep(2)}>
                Suivant
              </Button>
            </div>
          )}

          {/* Step 2: Training Goals */}
          {coachStep === 2 && (
            <div className="space-y-4 py-4">
              <h3 className="font-semibold mb-3">🎯 Quels sont vos objectifs ? (plusieurs choix)</h3>
              <div className="grid grid-cols-2 gap-2">
                {TRAINING_GOALS.map((goal) => (
                  <Button
                    key={goal.id}
                    variant={coachConfig.trainingGoals.includes(goal.id) ? 'default' : 'outline'}
                    className="h-auto py-2 justify-start"
                    onClick={() => {
                      const newGoals = coachConfig.trainingGoals.includes(goal.id)
                        ? coachConfig.trainingGoals.filter(g => g !== goal.id)
                        : [...coachConfig.trainingGoals, goal.id];
                      setCoachConfig({ ...coachConfig, trainingGoals: newGoals });
                    }}
                  >
                    <span className="mr-2">{goal.emoji}</span>
                    {goal.label}
                  </Button>
                ))}
              </div>
              <div className="flex gap-2 mt-4">
                <Button variant="outline" onClick={() => setCoachStep(1)}>Retour</Button>
                <Button className="flex-1" onClick={() => setCoachStep(3)} disabled={coachConfig.trainingGoals.length === 0}>
                  Suivant
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Duration & Frequency */}
          {coachStep === 3 && (
            <div className="space-y-4 py-4">
              <div>
                <h3 className="font-semibold mb-2">📅 Durée du programme</h3>
                <div className="grid grid-cols-3 gap-2">
                  {PROGRAM_DURATIONS.map((d) => (
                    <Button
                      key={d.value}
                      variant={coachConfig.duration === d.value ? 'default' : 'outline'}
                      className="h-auto py-2 flex-col"
                      size="sm"
                      onClick={() => setCoachConfig({ ...coachConfig, duration: d.value })}
                    >
                      <span className="font-medium text-sm">{d.label}</span>
                      <span className="text-xs text-muted-foreground">{d.desc}</span>
                    </Button>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-2">🔄 Fréquence d'entraînement</h3>
                <div className="grid grid-cols-5 gap-2">
                  {TRAINING_FREQUENCY.map((f) => (
                    <Button
                      key={f.value}
                      variant={coachConfig.frequency === f.value ? 'default' : 'outline'}
                      size="sm"
                      className="h-auto py-2 flex-col"
                      onClick={() => setCoachConfig({ ...coachConfig, frequency: f.value })}
                    >
                      <span className="font-medium">{f.value}x</span>
                      <span className="text-xs text-muted-foreground">{f.desc}</span>
                    </Button>
                  ))}
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <Button variant="outline" onClick={() => setCoachStep(2)}>Retour</Button>
                <Button className="flex-1" onClick={() => setCoachStep(4)}>Suivant</Button>
              </div>
            </div>
          )}

          {/* Step 4: Time & Duration per session */}
          {coachStep === 4 && (
            <div className="space-y-4 py-4">
              <div>
                <h3 className="font-semibold mb-2">⏰ Moment de la journée préféré</h3>
                <div className="grid grid-cols-2 gap-2">
                  {TIME_OF_DAY.map((t) => (
                    <Button
                      key={t.value}
                      variant={coachConfig.timeOfDay === t.value ? 'default' : 'outline'}
                      className="h-auto py-2"
                      onClick={() => setCoachConfig({ ...coachConfig, timeOfDay: t.value })}
                    >
                      <span className="mr-2">{t.label}</span>
                      <span className="text-xs text-muted-foreground">({t.desc})</span>
                    </Button>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-2">⏱️ Temps par séance</h3>
                <div className="grid grid-cols-5 gap-2">
                  {DAILY_DURATION.map((d) => (
                    <Button
                      key={d.value}
                      variant={coachConfig.dailyDuration === d.value ? 'default' : 'outline'}
                      size="sm"
                      className="h-auto py-2 flex-col"
                      onClick={() => setCoachConfig({ ...coachConfig, dailyDuration: d.value })}
                    >
                      <span className="font-medium">{d.label}</span>
                      <span className="text-xs text-muted-foreground">{d.desc}</span>
                    </Button>
                  ))}
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <Button variant="outline" onClick={() => setCoachStep(3)}>Retour</Button>
                <Button className="flex-1" onClick={() => setCoachStep(5)}>Suivant</Button>
              </div>
            </div>
          )}

          {/* Step 5: Body parts */}
          {coachStep === 5 && (
            <div className="space-y-4 py-4">
              <h3 className="font-semibold">🏋️ Parties du corps à travailler</h3>
              <div className="grid grid-cols-2 gap-2">
                {BODY_PARTS.map((part) => (
                  <Button
                    key={part.id}
                    variant={coachConfig.bodyParts.includes(part.id) ? 'default' : 'outline'}
                    className="h-auto py-2 justify-start"
                    onClick={() => {
                      const newParts = coachConfig.bodyParts.includes(part.id)
                        ? coachConfig.bodyParts.filter(p => p !== part.id)
                        : [...coachConfig.bodyParts, part.id];
                      setCoachConfig({ ...coachConfig, bodyParts: newParts });
                    }}
                  >
                    <span className="mr-2">{part.emoji}</span>
                    {part.label}
                  </Button>
                ))}
              </div>
              <div className="flex gap-2 mt-4">
                <Button variant="outline" onClick={() => setCoachStep(4)}>Retour</Button>
                <Button className="flex-1" onClick={() => setCoachStep(6)} disabled={coachConfig.bodyParts.length === 0}>
                  Suivant
                </Button>
              </div>
            </div>
          )}

          {/* Step 6: Equipment & Additional info */}
          {coachStep === 6 && (
            <div className="space-y-4 py-4">
              <div>
                <h3 className="font-semibold mb-2">🏠 Équipement disponible</h3>
                <Select 
                  value={coachConfig.equipment} 
                  onValueChange={(v) => setCoachConfig({ ...coachConfig, equipment: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Aucun (poids du corps)</SelectItem>
                    <SelectItem value="basic">Basique (haltères, tapis)</SelectItem>
                    <SelectItem value="home">À la maison (élastiques, kettlebell)</SelectItem>
                    <SelectItem value="full">Salle de sport complète</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-sm">Âge (optionnel)</Label>
                  <Input
                    type="number"
                    placeholder="Ex: 35"
                    value={coachConfig.age}
                    onChange={(e) => setCoachConfig({ ...coachConfig, age: e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-sm">Poids kg (optionnel)</Label>
                  <Input
                    type="number"
                    placeholder="Ex: 70"
                    value={coachConfig.weight}
                    onChange={(e) => setCoachConfig({ ...coachConfig, weight: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <Label>⚠️ Blessures ou limitations (optionnel)</Label>
                <Textarea
                  placeholder="Ex: Problème de genou, douleur au dos..."
                  value={coachConfig.injuries}
                  onChange={(e) => setCoachConfig({ ...coachConfig, injuries: e.target.value })}
                />
              </div>
              <div>
                <Label>💬 Instructions spécifiques (optionnel)</Label>
                <Textarea
                  placeholder="Ex: Je veux inclure du yoga, des étirements le matin..."
                  value={coachConfig.goals}
                  onChange={(e) => setCoachConfig({ ...coachConfig, goals: e.target.value })}
                />
              </div>
              <div className="flex gap-2 mt-4">
                <Button variant="outline" onClick={() => setCoachStep(5)}>Retour</Button>
                <Button 
                  className="flex-1" 
                  onClick={requestCoachProgram}
                  disabled={coachLoading}
                >
                  {coachLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Génération...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Générer mon programme
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* Step 7: Generated Program */}
          {coachStep === 7 && generatedProgram && (
            <div className="space-y-4 py-4">
              <div className="p-4 bg-primary/10 rounded-lg">
                <h3 className="font-semibold text-lg">{generatedProgram.name}</h3>
                <p className="text-sm text-muted-foreground mt-1">{generatedProgram.description}</p>
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">Aperçu du programme :</h4>
                <ScrollArea className="h-48">
                  {generatedProgram.weeks?.slice(0, 2).map((week, weekIndex) => (
                    <div key={weekIndex} className="mb-4">
                      <p className="font-medium text-sm text-primary">Semaine {weekIndex + 1}</p>
                      {week.days?.slice(0, 3).map((day, dayIndex) => (
                        <div key={dayIndex} className="ml-4 text-sm py-1 border-l-2 border-primary/30 pl-3">
                          <span className="font-medium">{day.name}:</span> {day.exercises?.length || 0} exercices
                        </div>
                      ))}
                    </div>
                  ))}
                </ScrollArea>
              </div>

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setCoachStep(6)}>
                  Modifier
                </Button>
                <Button className="flex-1" onClick={addProgramToAgenda}>
                  <Calendar className="w-4 h-4 mr-2" />
                  Ajouter à l'agenda
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Program Details Dialog */}
      <Dialog open={!!selectedProgram} onOpenChange={() => setSelectedProgram(null)}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-primary" />
              {selectedProgram?.workout_plan?.name || 'Programme personnalisé'}
            </DialogTitle>
            <DialogDescription>
              {selectedProgram?.workout_plan?.description || 'Votre programme d\'entraînement personnalisé'}
            </DialogDescription>
          </DialogHeader>

          {selectedProgram && (
            <div className="space-y-4 py-4">
              {/* Program Info */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-primary/10 rounded-lg text-center">
                  <p className="text-2xl font-bold text-primary">
                    {selectedProgram.workout_plan?.weeks?.length || 0}
                  </p>
                  <p className="text-xs text-muted-foreground">Semaines</p>
                </div>
                <div className="p-3 bg-secondary/10 rounded-lg text-center">
                  <p className="text-2xl font-bold text-secondary">
                    {selectedProgram.workout_plan?.weeks?.reduce((acc, w) => acc + (w.days?.length || 0), 0) || 0}
                  </p>
                  <p className="text-xs text-muted-foreground">Séances</p>
                </div>
              </div>

              {/* Program Details */}
              <ScrollArea className="h-64">
                {selectedProgram.workout_plan?.weeks?.map((week, weekIndex) => (
                  <div key={weekIndex} className="mb-4">
                    <h4 className="font-semibold text-primary mb-2 flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      Semaine {week.week_number || weekIndex + 1}
                    </h4>
                    {week.days?.map((day, dayIndex) => (
                      <div key={dayIndex} className="ml-4 mb-3 p-3 bg-muted/30 rounded-lg">
                        <p className="font-medium text-sm mb-2">{day.name || `Jour ${dayIndex + 1}`}</p>
                        <div className="space-y-1">
                          {day.exercises?.map((exercise, exIndex) => (
                            <div key={exIndex} className="flex items-center justify-between text-xs">
                              <span>{exercise.name}</span>
                              <span className="text-muted-foreground">
                                {exercise.sets}x{exercise.reps} {exercise.rest && `• ${exercise.rest}`}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
              </ScrollArea>

              {/* Actions */}
              <div className="flex gap-2 pt-2">
                <Button variant="outline" className="flex-1" onClick={() => setSelectedProgram(null)}>
                  Fermer
                </Button>
                <Button 
                  className="flex-1" 
                  onClick={() => {
                    addProgramToAgenda();
                    setSelectedProgram(null);
                  }}
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  Ajouter à l'agenda
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* AI Warning Dialog */}
      <AIWarningDialog
        open={showAIWarning}
        onOpenChange={setShowAIWarning}
        onConfirm={handleAIWarningConfirm}
        title="Génération de programme IA"
        description="Cette fonctionnalité utilise l'intelligence artificielle et consomme un crédit quotidien."
      />
    </div>
  );
}
